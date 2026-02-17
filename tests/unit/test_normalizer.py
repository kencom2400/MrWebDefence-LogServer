"""Normalizerのユニットテスト"""

import pytest
from datetime import datetime, timezone
from src.parser.normalizer import LogNormalizer


class TestLogNormalizer:
    """LogNormalizerのテストクラス"""
    
    def setup_method(self):
        """テストメソッド実行前の準備"""
        self.normalizer = LogNormalizer()
    
    def test_normalize_nginx_log(self):
        """Nginxログの正規化"""
        engine_log = {
            "time": "2024-02-17T10:00:00Z",
            "log_type": "nginx",
            "hostname": "waf-engine-01",
            "fqdn": "example.com",
            "customer_name": "test_customer",
            "request": "GET /api/users HTTP/1.1"
        }
        
        result = self.normalizer.normalize(engine_log)
        
        assert result.level == "info"
        assert result.message == "GET /api/users HTTP/1.1"
        assert result.source == "waf-engine-01"
        assert result.metadata["log_type"] == "nginx"
        assert result.metadata["customer_name"] == "test_customer"
    
    def test_normalize_openappsec_log(self):
        """OpenAppSecログの正規化"""
        engine_log = {
            "time": "2024-02-17T10:00:00Z",
            "log_type": "openappsec",
            "hostname": "waf-engine-01",
            "fqdn": "example.com",
            "customer_name": "test_customer",
            "signature": "SQL Injection Detected",
            "level": "error"
        }
        
        result = self.normalizer.normalize(engine_log)
        
        assert result.level == "error"
        assert result.message == "SQL Injection Detected"
        assert result.metadata["log_type"] == "openappsec"
    
    def test_normalize_level_mapping(self):
        """ログレベルの正規化"""
        test_cases = [
            ("warn", "warning"),
            ("WARNING", "warning"),
            ("Error", "error"),
            ("unknown", "info"),  # デフォルト
        ]
        
        for input_level, expected_level in test_cases:
            engine_log = {
                "time": "2024-02-17T10:00:00Z",
                "log_type": "nginx",
                "hostname": "waf-engine-01",
                "fqdn": "example.com",
                "level": input_level
            }
            
            result = self.normalizer.normalize(engine_log)
            assert result.level == expected_level
    
    def test_normalize_timestamp_parsing(self):
        """タイムスタンプのパース"""
        engine_log = {
            "time": "2024-02-17T10:30:45Z",
            "log_type": "nginx",
            "hostname": "waf-engine-01",
            "fqdn": "example.com"
        }
        
        result = self.normalizer.normalize(engine_log)
        
        assert result.timestamp.year == 2024
        assert result.timestamp.month == 2
        assert result.timestamp.day == 17
        assert result.timestamp.hour == 10
        assert result.timestamp.minute == 30
