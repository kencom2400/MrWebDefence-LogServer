#!/bin/bash
# ヘルスチェックスクリプト
# Fluentd LogServerの健全性を確認

set -euo pipefail

# 設定
HEALTH_ENDPOINT="${HEALTH_ENDPOINT:-http://localhost:8889/health}"
METRICS_ENDPOINT="${METRICS_ENDPOINT:-http://localhost:24231/metrics}"
TIMEOUT="${TIMEOUT:-3}"

# 色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ヘルスチェック結果
HEALTH_OK=0
EXIT_CODE=0

echo "========================================"
echo "  Fluentd LogServer Health Check"
echo "========================================"
echo ""

# 1. ヘルスチェックエンドポイント
echo -n "1. Health endpoint check... "
if curl -sf --max-time "${TIMEOUT}" "${HEALTH_ENDPOINT}" > /dev/null 2>&1; then
  echo -e "${GREEN}OK${NC}"
else
  echo -e "${RED}FAILED${NC}"
  EXIT_CODE=1
fi

# 2. Prometheusメトリクスエンドポイント
echo -n "2. Metrics endpoint check... "
if curl -sf --max-time "${TIMEOUT}" "${METRICS_ENDPOINT}" > /dev/null 2>&1; then
  echo -e "${GREEN}OK${NC}"
else
  echo -e "${RED}FAILED${NC}"
  EXIT_CODE=1
fi

# 3. Dockerコンテナステータス（docker-compose使用時）
if command -v docker &> /dev/null; then
  echo -n "3. Docker container status... "
  if docker ps --filter "name=mrwebdefence-logserver" --filter "status=running" | grep -q mrwebdefence-logserver; then
    echo -e "${GREEN}RUNNING${NC}"
  else
    echo -e "${RED}NOT RUNNING${NC}"
    EXIT_CODE=1
  fi
else
  echo -n "3. Docker container status... "
  echo -e "${YELLOW}SKIPPED (Docker not found)${NC}"
fi

# 4. バッファサイズチェック
echo ""
echo "4. Buffer status:"
if curl -sf --max-time "${TIMEOUT}" "${METRICS_ENDPOINT}" > /tmp/metrics.txt 2>&1; then
  buffer_bytes=$(grep 'fluentd_output_status_buffer_total_bytes' /tmp/metrics.txt | grep -v '#' | awk '{sum+=$2} END {print sum}')
  buffer_mb=$((buffer_bytes / 1024 / 1024))
  
  if [[ ${buffer_mb} -lt 1024 ]]; then
    echo -e "   Total buffer size: ${GREEN}${buffer_mb} MB${NC}"
  elif [[ ${buffer_mb} -lt 1536 ]]; then
    echo -e "   Total buffer size: ${YELLOW}${buffer_mb} MB (Warning: >1GB)${NC}"
  else
    echo -e "   Total buffer size: ${RED}${buffer_mb} MB (Critical: >1.5GB)${NC}"
    EXIT_CODE=1
  fi
  
  rm -f /tmp/metrics.txt
else
  echo -e "   ${RED}Unable to fetch metrics${NC}"
  EXIT_CODE=1
fi

# 5. ログ出力カウント
echo ""
echo "5. Log output stats:"
if curl -sf --max-time "${TIMEOUT}" "${METRICS_ENDPOINT}" > /tmp/metrics.txt 2>&1; then
  input_count=$(grep 'fluentd_input_status_num_records_total' /tmp/metrics.txt | grep -v '#' | awk '{sum+=$2} END {print sum}')
  output_count=$(grep 'fluentd_output_status_num_records_total' /tmp/metrics.txt | grep -v '#' | awk '{sum+=$2} END {print sum}')
  
  echo "   Input records: ${input_count:-0}"
  echo "   Output records: ${output_count:-0}"
  
  rm -f /tmp/metrics.txt
else
  echo -e "   ${RED}Unable to fetch metrics${NC}"
fi

# 結果サマリー
echo ""
echo "========================================"
if [[ ${EXIT_CODE} -eq 0 ]]; then
  echo -e "Status: ${GREEN}HEALTHY${NC}"
else
  echo -e "Status: ${RED}UNHEALTHY${NC}"
fi
echo "========================================"

exit ${EXIT_CODE}
