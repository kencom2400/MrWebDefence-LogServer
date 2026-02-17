"""ログパーサー"""

from src.models import ParseError


class LogParser:
    """Engine側のログをパース"""

    def __init__(self, config=None):
        """
        Args:
            config: 設定オブジェクト。Noneの場合はデフォルト値を使用
        """
        if config:
            self.MAX_FIELD_LENGTH = config.parser_max_field_length
            self.MAX_MESSAGE_LENGTH = config.parser_max_message_length
            self.MAX_OPTIONAL_FIELD_LENGTH = config.parser_max_optional_field_length
        else:
            # デフォルト値
            self.MAX_FIELD_LENGTH = 1024
            self.MAX_MESSAGE_LENGTH = 10240
            self.MAX_OPTIONAL_FIELD_LENGTH = 2048

    # 必須フィールド
    REQUIRED_FIELDS = ["time", "log_type", "hostname", "fqdn"]

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

            # 必須フィールド値の型と長さの検証（セキュリティ対策）
            for field in self.REQUIRED_FIELDS:
                value = engine_log[field]
                if not isinstance(value, str):
                    raise ParseError(f"Field {field} must be a string, got {type(value)}")
                if len(value) > self.MAX_FIELD_LENGTH:
                    raise ParseError(
                        f"Field {field} exceeds maximum length of {self.MAX_FIELD_LENGTH}"
                    )

            # 非必須フィールドの長さ検証（DoS対策）
            for field, value in engine_log.items():
                if field in self.REQUIRED_FIELDS:
                    continue  # 必須フィールドは既に検証済み

                # 文字列フィールドの長さチェック
                if isinstance(value, str):
                    if field == "message" and len(value) > self.MAX_MESSAGE_LENGTH:
                        raise ParseError(
                            f"Message exceeds maximum length of {self.MAX_MESSAGE_LENGTH}"
                        )
                    elif len(value) > self.MAX_OPTIONAL_FIELD_LENGTH:
                        raise ParseError(
                            f"Field {field} exceeds maximum length of "
                            f"{self.MAX_OPTIONAL_FIELD_LENGTH}"
                        )

                # dict型フィールドのサイズチェック（ネストされたデータのDoS対策）
                elif isinstance(value, dict):
                    dict_size = len(str(value))
                    if dict_size > self.MAX_OPTIONAL_FIELD_LENGTH:
                        raise ParseError(
                            f"Field {field} (dict) exceeds maximum size of "
                            f"{self.MAX_OPTIONAL_FIELD_LENGTH}"
                        )

            return engine_log
        except ParseError:
            raise
        except Exception as e:
            raise ParseError(f"Failed to parse log: {e}")
