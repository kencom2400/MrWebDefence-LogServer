"""Log Bufferのユニットテスト"""

import pytest
import asyncio
from datetime import datetime, timezone
from src.buffer.log_buffer import LogBuffer
from src.models import LogEntry, BufferFullError


class MockStorage:
    """テスト用のモックストレージ"""
    
    def __init__(self):
        self.written_logs = []
    
    async def write_batch(self, log_entries):
        """書き込み操作をシミュレート"""
        self.written_logs.extend(log_entries)


class TestLogBuffer:
    """LogBufferのテストクラス"""
    
    @pytest.mark.asyncio
    async def test_add_batch_normal(self):
        """正常なログ追加"""
        mock_storage = MockStorage()
        buffer = LogBuffer(
            max_count=10,
            max_memory_mb=1,
            flush_interval_sec=60,
            storage=mock_storage
        )
        
        log_entries = [
            LogEntry(
                timestamp=datetime.now(timezone.utc),
                level="info",
                message=f"Test message {i}"
            )
            for i in range(5)
        ]
        
        await buffer.add_batch(log_entries)
        
        assert len(buffer.buffer) == 5
    
    @pytest.mark.asyncio
    async def test_buffer_full_error(self):
        """バッファ満杯時のエラー"""
        mock_storage = MockStorage()
        buffer = LogBuffer(
            max_count=10,
            max_memory_mb=1,
            flush_interval_sec=60,
            storage=mock_storage
        )
        
        # バッファを満杯近くまで埋める
        log_entries = [
            LogEntry(
                timestamp=datetime.now(timezone.utc),
                level="info",
                message=f"Test message {i}"
            )
            for i in range(9)  # 90%閾値
        ]
        
        await buffer.add_batch(log_entries)
        
        # 追加でログを入れるとBufferFullErrorが発生するはず
        more_logs = [
            LogEntry(
                timestamp=datetime.now(timezone.utc),
                level="info",
                message="One more log"
            )
        ]
        
        with pytest.raises(BufferFullError):
            await buffer.add_batch(more_logs)
    
    @pytest.mark.asyncio
    async def test_flush(self):
        """フラッシュ機能"""
        mock_storage = MockStorage()
        buffer = LogBuffer(
            max_count=10,
            max_memory_mb=1,
            flush_interval_sec=60,
            storage=mock_storage
        )
        
        log_entries = [
            LogEntry(
                timestamp=datetime.now(timezone.utc),
                level="info",
                message=f"Test message {i}"
            )
            for i in range(5)
        ]
        
        await buffer.add_batch(log_entries)
        await buffer.flush()
        
        # バッファが空になり、ストレージに書き込まれたことを確認
        assert len(buffer.buffer) == 0
        assert len(mock_storage.written_logs) == 5
