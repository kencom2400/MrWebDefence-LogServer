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
            self._validate_required_fields(engine_log)
            self._validate_optional_fields(engine_log)
            return engine_log
        except ParseError:
            raise
        except Exception as e:
            raise ParseError(f"Failed to parse log: {e}")

    def _validate_required_fields(self, engine_log: dict):
        """必須フィールドの検証"""
        # 必須フィールドの存在確認
        for field in self.REQUIRED_FIELDS:
            if field not in engine_log or engine_log[field] is None:
                raise ParseError(f"Missing required field: {field}")

        # 必須フィールド値の型と長さの検証
        for field in self.REQUIRED_FIELDS:
            value = engine_log[field]
            if not isinstance(value, str):
                raise ParseError(f"Field {field} must be a string, got {type(value)}")
            if len(value) > self.MAX_FIELD_LENGTH:
                raise ParseError(f"Field {field} exceeds maximum length of {self.MAX_FIELD_LENGTH}")

    def _validate_optional_fields(self, engine_log: dict):
        """非必須フィールドの検証"""
        for field, value in engine_log.items():
            if field in self.REQUIRED_FIELDS:
                continue

            if isinstance(value, str):
                self._validate_string_field(field, value)
            elif isinstance(value, dict):
                self._validate_dict_field(field, value)

    def _validate_string_field(self, field: str, value: str):
        """文字列フィールドの検証"""
        if field == "message":
            max_length = self.MAX_MESSAGE_LENGTH
            error_msg = f"Message exceeds maximum length of {max_length}"
        else:
            max_length = self.MAX_OPTIONAL_FIELD_LENGTH
            error_msg = f"Field {field} exceeds maximum length of {max_length}"

        if len(value) > max_length:
            raise ParseError(error_msg)

    def _validate_dict_field(self, field: str, value: dict):
        """dict型フィールドの検証"""
        dict_size = len(str(value))
        if dict_size > self.MAX_OPTIONAL_FIELD_LENGTH:
            raise ParseError(
                f"Field {field} (dict) exceeds maximum size of " f"{self.MAX_OPTIONAL_FIELD_LENGTH}"
            )
