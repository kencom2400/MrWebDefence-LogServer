"""Parserのユニットテスト"""

import pytest
from src.parser.log_parser import LogParser
from src.models import ParseError


class TestLogParser:
    """LogParserのテストクラス"""

    def setup_method(self):
        """テストメソッド実行前の準備"""
        self.parser = LogParser()

    def test_parse_valid_log(self):
        """正常なログのパース"""
        log = {
            "time": "2024-02-17T10:00:00Z",
            "log_type": "nginx",
            "hostname": "waf-engine-01",
            "fqdn": "example.com",
        }

        result = self.parser.parse(log)
        assert result == log

    def test_parse_missing_required_field(self):
        """必須フィールドが欠けている場合"""
        log = {
            "time": "2024-02-17T10:00:00Z",
            "log_type": "nginx",
            # hostname が欠けている
            "fqdn": "example.com",
        }

        with pytest.raises(ParseError) as exc_info:
            self.parser.parse(log)
        assert "Missing required field: hostname" in str(exc_info.value)

    def test_parse_invalid_field_type(self):
        """フィールドの型が不正な場合"""
        log = {
            "time": "2024-02-17T10:00:00Z",
            "log_type": 123,  # 数値（文字列ではない）
            "hostname": "waf-engine-01",
            "fqdn": "example.com",
        }

        with pytest.raises(ParseError) as exc_info:
            self.parser.parse(log)
        assert "must be a string" in str(exc_info.value)

    def test_parse_field_too_long(self):
        """フィールド値が長すぎる場合"""
        log = {
            "time": "2024-02-17T10:00:00Z",
            "log_type": "nginx",
            "hostname": "a" * 2000,  # 最大長を超える
            "fqdn": "example.com",
        }

        with pytest.raises(ParseError) as exc_info:
            self.parser.parse(log)
        assert "exceeds maximum length" in str(exc_info.value)

    def test_parse_message_too_long(self):
        """メッセージが長すぎる場合"""
        log = {
            "time": "2024-02-17T10:00:00Z",
            "log_type": "nginx",
            "hostname": "waf-engine-01",
            "fqdn": "example.com",
            "message": "x" * 20000,  # メッセージ最大長を超える
        }

        with pytest.raises(ParseError) as exc_info:
            self.parser.parse(log)
        assert "Message exceeds maximum length" in str(exc_info.value)
