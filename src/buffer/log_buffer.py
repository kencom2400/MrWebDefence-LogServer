"""ログバッファ"""

import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from typing import List
from src.models import LogEntry, BufferFullError

logger = logging.getLogger(__name__)


class LogBuffer:
    """
    ログバッファ（バックプレッシャー機能付き）
    """

    def __init__(
        self,
        max_count: int = 1000,
        max_memory_mb: int = 50,
        flush_interval_sec: int = 10,
        max_retries: int = 3,
        storage=None,
    ):
        """
        Args:
            max_count: バッファに保持する最大ログ数
            max_memory_mb: バッファの最大メモリサイズ（MB）
            flush_interval_sec: 定期的にフラッシュする間隔（秒）
            max_retries: フラッシュ失敗時の最大リトライ回数
            storage: FileStorageインスタンス
        """
        self.max_count = max_count
        self.max_memory_mb = max_memory_mb
        self.flush_interval_sec = flush_interval_sec
        self.max_retries = max_retries
        self.storage = storage

        self.buffer: List[LogEntry] = []
        self.lock = asyncio.Lock()

        self._last_flush = datetime.now(timezone.utc)

    def _get_buffer_size_bytes(self) -> int:
        """バッファの実際のメモリサイズを取得（バイト単位）"""
        total_size = sys.getsizeof(self.buffer)
        for entry in self.buffer:
            # LogEntryオブジェクト自体のサイズ
            total_size += sys.getsizeof(entry)
            # 各属性のサイズを計測
            total_size += sys.getsizeof(entry.timestamp)
            total_size += sys.getsizeof(entry.level)
            total_size += sys.getsizeof(entry.message)
            if entry.source:
                total_size += sys.getsizeof(entry.source)
            if entry.hostname:
                total_size += sys.getsizeof(entry.hostname)
            total_size += sys.getsizeof(entry.metadata)
            # metadata内の各アイテムも計測
            for key, value in entry.metadata.items():
                total_size += sys.getsizeof(key) + sys.getsizeof(value)
            total_size += sys.getsizeof(entry.received_at)
            total_size += sys.getsizeof(entry.log_id)
        return total_size

    def _is_buffer_full(self) -> bool:
        """バッファが満杯かチェック（90%閾値）"""
        count_threshold = int(self.max_count * 0.9)
        memory_threshold_bytes = int(self.max_memory_mb * 1024 * 1024 * 0.9)

        if len(self.buffer) >= count_threshold:
            return True

        actual_memory = self._get_buffer_size_bytes()
        if actual_memory >= memory_threshold_bytes:
            logger.warning(
                f"Buffer memory threshold reached: {actual_memory / (1024 * 1024):.2f}MB / "
                f"{self.max_memory_mb}MB"
            )
            return True

        return False

    async def add_batch(self, log_entries: List[LogEntry]):
        """
        バッチでログを追加

        Args:
            log_entries: ログエントリのリスト

        Raises:
            BufferFullError: バッファが満杯の場合
        """
        async with self.lock:
            # バッファが満杯かチェック
            if self._is_buffer_full():
                logger.warning("Buffer is full, rejecting new logs")
                raise BufferFullError("Buffer capacity exceeded")

            self.buffer.extend(log_entries)

        # ロック解放後にフラッシュ判定（デッドロック回避）
        await self._check_and_flush()

    async def _check_and_flush(self):
        """必要に応じてフラッシュ"""
        now = datetime.now(timezone.utc)
        time_elapsed = (now - self._last_flush).total_seconds()

        should_flush = False
        async with self.lock:
            if len(self.buffer) >= self.max_count:
                should_flush = True
            elif time_elapsed >= self.flush_interval_sec and len(self.buffer) > 0:
                should_flush = True

        if should_flush:
            await self.flush()

    async def flush(self, max_retries: int = None):
        """
        バッファの内容をストレージに書き込み

        Args:
            max_retries: 最大リトライ回数。Noneの場合はインスタンスのデフォルトを使用
        """
        if max_retries is None:
            max_retries = self.max_retries

        if not self.storage:
            logger.warning("No storage configured, cannot flush")
            return

        async with self.lock:
            if not self.buffer:
                return

            # バッファのコピーを作成してクリア
            logs_to_write = self.buffer.copy()
            self.buffer.clear()
            self._last_flush = datetime.now(timezone.utc)

        # ストレージに書き込み（ロック外で実行）
        retry_count = 0
        last_error = None

        while retry_count < max_retries:
            try:
                await self.storage.write_batch(logs_to_write)
                logger.info(f"Flushed {len(logs_to_write)} logs to storage")
                return  # 成功
            except Exception as e:
                last_error = e
                retry_count += 1
                logger.warning(f"Failed to flush logs (attempt {retry_count}/{max_retries}): {e}")
                if retry_count < max_retries:
                    await asyncio.sleep(1 * retry_count)  # 指数バックオフ

        # 全てのリトライが失敗した場合
        logger.error(
            f"Failed to flush {len(logs_to_write)} logs after {max_retries} attempts: "
            f"{last_error}"
        )
        # 失敗したログを別のファイルに保存（データ損失防止）
        await self._save_failed_logs(logs_to_write)

    async def _save_failed_logs(self, logs: List[LogEntry]):
        """
        フラッシュに失敗したログを別のファイルに保存

        Args:
            logs: 保存に失敗したログのリスト
        """
        try:
            import aiofiles
            from pathlib import Path

            failed_logs_dir = Path("logs/failed")
            failed_logs_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            failed_log_file = failed_logs_dir / f"failed_{timestamp}.jsonl"

            async with aiofiles.open(failed_log_file, mode="w", encoding="utf-8") as f:
                for log_entry in logs:
                    log_line = json.dumps(log_entry.to_dict(), ensure_ascii=False) + "\n"
                    await f.write(log_line)

            logger.info(f"Saved {len(logs)} failed logs to {failed_log_file}")
        except Exception as e:
            logger.error(f"Failed to save failed logs: {e}")
            # 最後の手段: ログを標準エラー出力に出力
            for log_entry in logs[:10]:  # 最初の10件のみ
                logger.critical(f"LOST LOG: {log_entry.to_dict()}")

    async def start_periodic_flush(self):
        """定期的なフラッシュタスクを開始"""
        while True:
            await asyncio.sleep(self.flush_interval_sec)
            await self.flush()
