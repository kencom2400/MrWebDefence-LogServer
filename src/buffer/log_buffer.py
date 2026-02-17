"""ログバッファ"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
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
        storage=None
    ):
        """
        Args:
            max_count: バッファに保持する最大ログ数
            max_memory_mb: バッファの最大メモリサイズ（MB）
            flush_interval_sec: 定期的にフラッシュする間隔（秒）
            storage: FileStorageインスタンス
        """
        self.max_count = max_count
        self.max_memory_mb = max_memory_mb
        self.flush_interval_sec = flush_interval_sec
        self.storage = storage
        
        self.buffer: List[LogEntry] = []
        self.lock = asyncio.Lock()
        
        # メモリ使用量の推定（サンプリングベース）
        self._estimated_entry_size: int = 2048  # デフォルト推定サイズ
        self._sample_count: int = 0
        self._sample_size_total: int = 0
        
        self._last_flush = datetime.now(timezone.utc)
        
    def _is_buffer_full(self) -> bool:
        """バッファが満杯かチェック（90%閾値）"""
        count_threshold = int(self.max_count * 0.9)
        memory_threshold_bytes = int(self.max_memory_mb * 1024 * 1024 * 0.9)
        
        if len(self.buffer) >= count_threshold:
            return True
        
        estimated_memory = len(self.buffer) * self._estimated_entry_size
        if estimated_memory >= memory_threshold_bytes:
            return True
        
        return False
    
    def _update_entry_size_estimate(self, log_entry: LogEntry):
        """ログエントリのサイズ推定を更新（最初の10件をサンプリング）"""
        if self._sample_count < 10:
            entry_json = json.dumps(log_entry.to_dict())
            entry_size = len(entry_json.encode('utf-8'))
            self._sample_size_total += entry_size
            self._sample_count += 1
            self._estimated_entry_size = self._sample_size_total // self._sample_count
    
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
            
            for log_entry in log_entries:
                self.buffer.append(log_entry)
                self._update_entry_size_estimate(log_entry)
        
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
    
    async def flush(self):
        """バッファの内容をストレージに書き込み"""
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
        try:
            await self.storage.write_batch(logs_to_write)
            logger.info(f"Flushed {len(logs_to_write)} logs to storage")
        except Exception as e:
            logger.error(f"Failed to flush logs: {e}")
            # エラー時はログを破棄（メモリリーク防止）
            # 本番環境では別途エラーログをファイルに保存するなどの対応が必要
    
    async def start_periodic_flush(self):
        """定期的なフラッシュタスクを開始"""
        while True:
            await asyncio.sleep(self.flush_interval_sec)
            await self.flush()
