"""ログパーサー"""

from src.models import ParseError


class LogParser:
    """Engine側のログをパース"""
    
    # 必須フィールド
    REQUIRED_FIELDS = ['time', 'log_type', 'hostname', 'fqdn']
    
    # フィールド値の最大長（DoS攻撃対策）
    MAX_FIELD_LENGTH = 1024
    MAX_MESSAGE_LENGTH = 10240  # 10KB
    
    def parse(self, engine_log: dict) -> dict:
        """
        Engine側のログを検証・パース
        
        Args:
            engine_log: Engine側のログ辞書
            
        Returns:
            検証済みログ辞書
            
        Raises:
            ParseError: 必須フィールドが欠けている、または不正な値の場合
        """
        try:
            # 必須フィールドの確認
            for field in self.REQUIRED_FIELDS:
                if field not in engine_log or engine_log[field] is None:
                    raise ParseError(f"Missing required field: {field}")
            
            # フィールド値の型と長さの検証（セキュリティ対策）
            for field in self.REQUIRED_FIELDS:
                value = engine_log[field]
                if not isinstance(value, str):
                    raise ParseError(f"Field {field} must be a string, got {type(value)}")
                if len(value) > self.MAX_FIELD_LENGTH:
                    raise ParseError(f"Field {field} exceeds maximum length of {self.MAX_FIELD_LENGTH}")
            
            # メッセージフィールドの長さ検証（存在する場合）
            if 'message' in engine_log and isinstance(engine_log['message'], str):
                if len(engine_log['message']) > self.MAX_MESSAGE_LENGTH:
                    raise ParseError(f"Message exceeds maximum length of {self.MAX_MESSAGE_LENGTH}")
            
            return engine_log
        except ParseError:
            raise
        except Exception as e:
            raise ParseError(f"Failed to parse log: {e}")
