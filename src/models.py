"""データモデル定義"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import uuid


class ParseError(Exception):
    """パースエラー"""
    pass


class BufferFullError(Exception):
    """バッファが満杯の場合に発生する例外"""
    pass


@dataclass
class LogEntry:
    """正規化後のログエントリ"""
    
    # 必須フィールド
    timestamp: datetime      # UTCタイムスタンプ
    level: str              # ログレベル (debug, info, warning, error, critical)
    message: str            # ログメッセージ
    
    # オプションフィールド
    source: Optional[str] = None          # ログソース（waf-engine-01等）
    hostname: Optional[str] = None        # ホスト名
    
    # メタデータ（Engine側から送信された情報を保持）
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 内部管理
    received_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    log_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "log_id": self.log_id,
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "message": self.message,
            "source": self.source,
            "hostname": self.hostname,
            "metadata": self.metadata,
            "received_at": self.received_at.isoformat(),
        }
