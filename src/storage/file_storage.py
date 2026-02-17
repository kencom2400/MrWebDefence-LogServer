"""ファイルストレージ"""

import json
import re
import logging
from pathlib import Path
from typing import List
import aiofiles
from src.models import LogEntry

logger = logging.getLogger(__name__)


class FileStorage:
    """
    ログをファイルに保存（非同期I/O、Path Traversal対策付き）
    """

    def __init__(self, base_dir: str = "logs"):
        """
        Args:
            base_dir: ログファイルの保存ディレクトリ
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_path_component(self, component: str) -> str:
        """
        パスコンポーネントをサニタイズ（Path Traversal対策）

        Args:
            component: パスコンポーネント（customer_name, log_type, fqdn等）

        Returns:
            サニタイズされた文字列
        """
        if not component:
            return "unknown"

        # ../, ..\, および危険な文字を削除
        sanitized = component.replace("../", "").replace("..\\", "")

        # パスセパレータと安全でない文字を_に置換
        sanitized = re.sub(r'[<>:"|?*\x00-\x1f\\/]', "_", sanitized)

        # 先頭と末尾のドットを削除（隠しファイル防止）
        sanitized = sanitized.strip(".")

        # 空になった場合はデフォルト値
        if not sanitized:
            return "unknown"

        return sanitized

    def _get_log_file_path(self, log_entry: LogEntry) -> Path:
        """
        ログエントリのファイルパスを取得

        パス構造: logs/{customer_name}/{log_type}/{fqdn}/{year}/{month}/{day}/{hour}.log

        Args:
            log_entry: ログエントリ

        Returns:
            ログファイルパス
        """
        metadata = log_entry.metadata
        timestamp = log_entry.timestamp

        # メタデータから情報を取得（サニタイズ）
        customer_name = self._sanitize_path_component(metadata.get("customer_name", "unknown"))
        log_type = self._sanitize_path_component(metadata.get("log_type", "unknown"))
        fqdn = self._sanitize_path_component(metadata.get("fqdn", "unknown"))

        # 時刻情報
        year = timestamp.strftime("%Y")
        month = timestamp.strftime("%m")
        day = timestamp.strftime("%d")
        hour = timestamp.strftime("%H")

        # パスを構築
        file_path = (
            self.base_dir / customer_name / log_type / fqdn / year / month / day / f"{hour}.log"
        )

        return file_path

    async def write_batch(self, log_entries: List[LogEntry]):
        """
        ログのバッチを非同期でファイルに書き込み

        Args:
            log_entries: ログエントリのリスト
        """
        # ファイルパスごとにログをグループ化
        file_groups = {}
        for log_entry in log_entries:
            file_path = self._get_log_file_path(log_entry)
            if file_path not in file_groups:
                file_groups[file_path] = []
            file_groups[file_path].append(log_entry)

        # ファイルごとに書き込み
        for file_path, logs in file_groups.items():
            await self._write_to_file(file_path, logs)

    async def _write_to_file(self, file_path: Path, log_entries: List[LogEntry]):
        """
        指定されたファイルにログを追記

        Args:
            file_path: ファイルパス
            log_entries: ログエントリのリスト
        """
        try:
            # ディレクトリを作成
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # ログをJSON行として追記
            async with aiofiles.open(file_path, mode="a", encoding="utf-8") as f:
                for log_entry in log_entries:
                    log_line = json.dumps(log_entry.to_dict(), ensure_ascii=False) + "\n"
                    await f.write(log_line)

            logger.debug(f"Wrote {len(log_entries)} logs to {file_path}")
        except Exception as e:
            logger.error(f"Failed to write logs to {file_path}: {e}")
            raise
