"""ログ正規化"""

from datetime import datetime, timezone
from dateutil import parser as date_parser
from src.models import LogEntry


class LogNormalizer:
    """Engine側のログをLogServerのデータモデルに正規化"""
    
    LEVEL_MAP = {
        "debug": "debug",
        "info": "info",
        "warn": "warning",
        "warning": "warning",
        "error": "error",
        "critical": "critical",
    }
    
    def normalize(self, engine_log: dict) -> LogEntry:
        """
        Engine側のログを正規化
        
        Args:
            engine_log: パース済みログ辞書
            
        Returns:
            正規化されたLogEntry
        """
        # タイムスタンプをdatetimeに変換
        timestamp = self._parse_timestamp(engine_log.get("time"))
        
        # ログレベルの正規化（存在する場合）
        level = self._normalize_level(engine_log.get("level", "info"))
        
        # メッセージの抽出
        message = self._extract_message(engine_log)
        
        return LogEntry(
            timestamp=timestamp,
            level=level,
            message=message,
            source=engine_log.get("hostname"),
            hostname=engine_log.get("hostname"),
            metadata={
                "log_type": engine_log.get("log_type"),
                "customer_name": engine_log.get("customer_name"),
                "fqdn": engine_log.get("fqdn"),
                "year": engine_log.get("year"),
                "month": engine_log.get("month"),
                "day": engine_log.get("day"),
                "hour": engine_log.get("hour"),
                "minute": engine_log.get("minute"),
                "second": engine_log.get("second"),
                # Engine側のその他のフィールドをそのまま保持
                "original_fields": {
                    k: v for k, v in engine_log.items() 
                    if k not in ['time', 'log_type', 'hostname', 'customer_name', 'fqdn']
                }
            }
        )
    
    def _parse_timestamp(self, time_str: str) -> datetime:
        """タイムスタンプをdatetimeに変換"""
        try:
            dt = date_parser.parse(time_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, TypeError):
            return datetime.now(timezone.utc)
    
    def _normalize_level(self, level: str) -> str:
        """ログレベルを正規化"""
        level_lower = str(level).lower().strip()
        return self.LEVEL_MAP.get(level_lower, "info")
    
    def _extract_message(self, engine_log: dict) -> str:
        """ログメッセージを抽出"""
        log_type = engine_log.get("log_type")
        
        if log_type == "nginx":
            # Nginxログの場合: requestフィールドをメッセージとして使用
            return engine_log.get("request", "")
        elif log_type == "openappsec":
            # OpenAppSecログの場合: signatureをメッセージとして使用
            return engine_log.get("signature", "WAF Detection")
        else:
            # その他: message フィールドまたは空文字列
            return engine_log.get("message", "")
