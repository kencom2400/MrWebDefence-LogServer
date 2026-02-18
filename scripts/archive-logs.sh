#!/bin/bash
# ログアーカイブスクリプト
# 古いログをS3にアーカイブして、ローカルから削除

set -euo pipefail

# 設定
LOG_BASE_DIR="${LOG_BASE_DIR:-/var/log/mrwebdefence}"
S3_BUCKET="${S3_BUCKET:-mrwebdefence-logs}"
S3_PREFIX="${S3_PREFIX:-archive}"
ARCHIVE_DAYS="${ARCHIVE_DAYS:-30}"
DELETE_DAYS="${DELETE_DAYS:-90}"

# AWS CLI確認
if ! command -v aws &> /dev/null; then
  echo "Error: AWS CLI is not installed" >&2
  exit 1
fi

# ログディレクトリ確認
if [[ ! -d "${LOG_BASE_DIR}" ]]; then
  echo "Error: Log directory not found: ${LOG_BASE_DIR}" >&2
  exit 1
fi

echo "Starting log archive process..."
echo "Log directory: ${LOG_BASE_DIR}"
echo "S3 bucket: s3://${S3_BUCKET}/${S3_PREFIX}"
echo "Archive files older than ${ARCHIVE_DAYS} days"
echo "Delete files older than ${DELETE_DAYS} days"

# アーカイブ処理
ARCHIVE_COUNT=0
ARCHIVE_FAILED=0

if [[ "${ARCHIVE_DAYS}" -gt 0 ]]; then
  echo "Archiving logs older than ${ARCHIVE_DAYS} days..."
  
  while IFS= read -r -d '' file; do
    # S3パスの構築（ベースディレクトリを除く相対パス）
    relative_path="${file#${LOG_BASE_DIR}/}"
    s3_path="s3://${S3_BUCKET}/${S3_PREFIX}/${relative_path}"
    
    # S3にアップロード
    if aws s3 cp "${file}" "${s3_path}" --storage-class GLACIER; then
      echo "Archived: ${file} -> ${s3_path}"
      ((ARCHIVE_COUNT++))
    else
      echo "Error: Failed to archive ${file}" >&2
      ((ARCHIVE_FAILED++))
    fi
  done < <(find "${LOG_BASE_DIR}" -name "*.log.gz" -mtime +"${ARCHIVE_DAYS}" -type f -print0)
  
  echo "Archive completed: ${ARCHIVE_COUNT} files archived"
  
  # アーカイブ失敗時は削除を実行しない
  if [[ ${ARCHIVE_FAILED} -gt 0 ]]; then
    echo "Error: ${ARCHIVE_FAILED} files failed to archive" >&2
    echo "Skipping deletion due to archive failures"
    exit 1
  fi
fi

# 削除処理
echo "Deleting logs older than ${DELETE_DAYS} days..."
DELETE_COUNT=$(find "${LOG_BASE_DIR}" -name "*.log.gz" -mtime +"${DELETE_DAYS}" -type f | wc -l)
find "${LOG_BASE_DIR}" -name "*.log.gz" -mtime +"${DELETE_DAYS}" -type f -delete

# 空のディレクトリを削除
find "${LOG_BASE_DIR}" -type d -empty -delete

echo "Log archive completed."
echo "Summary:"
echo "  - Archived: ${ARCHIVE_COUNT} files"
echo "  - Deleted: ${DELETE_COUNT} files"
