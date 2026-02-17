"""タイムスタンプ補正"""

from datetime import datetime, timezone, timedelta
import logging
from src.models import LogEntry

logger = logging.getLogger(__name__)


class TimeCorrector:
    """タイムスタンプの補正と検証"""

    def __init__(self, config=None):
        """
        Args:
            config: 設定オブジェクト。Noneの場合はデフォルト値を使用
        """
        if config:
            self.FUTURE_TOLERANCE_SECONDS = config.corrector_future_tolerance_sec
        else:
            self.FUTURE_TOLERANCE_SECONDS = 300  # デフォルト: 5分

    def correct(self, log_entry: LogEntry) -> LogEntry:
        """
        タイムスタンプを検証・補正

        Args:
            log_entry: 正規化されたログエントリ

        Returns:
            タイムスタンプが補正されたログエントリ
        """
        now = datetime.now(timezone.utc)
        future_threshold = now + timedelta(seconds=self.FUTURE_TOLERANCE_SECONDS)

        # タイムスタンプが未来すぎる場合は警告して現在時刻に補正
        if log_entry.timestamp > future_threshold:
            original_timestamp = log_entry.timestamp  # 補正前の値を保存
            logger.warning(
                f"Log timestamp is too far in the future. "
                f"Original: {original_timestamp}, "
                f"Corrected to: {now}, "
                f"log_id: {log_entry.log_id}"
            )
            log_entry.timestamp = now
            # メタデータに補正フラグと元の値を追加
            log_entry.metadata["timestamp_corrected"] = True
            log_entry.metadata["original_timestamp"] = original_timestamp.isoformat()

        return log_entry
