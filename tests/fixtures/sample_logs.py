"""テストフィクスチャ"""

import pytest
from datetime import datetime, timezone
from src.models import LogEntry


@pytest.fixture
def sample_nginx_log():
    """サンプルNginxログ"""
    return {
        "time": "2024-02-17T10:00:00Z",
        "log_type": "nginx",
        "hostname": "waf-engine-01",
        "fqdn": "example.com",
        "customer_name": "test_customer",
        "request": "GET /api/users HTTP/1.1",
        "status": "200",
        "remote_addr": "192.168.1.100"
    }


@pytest.fixture
def sample_openappsec_log():
    """サンプルOpenAppSecログ"""
    return {
        "time": "2024-02-17T10:00:00Z",
        "log_type": "openappsec",
        "hostname": "waf-engine-01",
        "fqdn": "example.com",
        "customer_name": "test_customer",
        "signature": "SQL Injection Detected",
        "level": "error",
        "source_ip": "203.0.113.45"
    }


@pytest.fixture
def sample_log_entry():
    """サンプルLogEntry"""
    return LogEntry(
        timestamp=datetime(2024, 2, 17, 10, 0, 0, tzinfo=timezone.utc),
        level="info",
        message="Test message",
        source="waf-engine-01",
        hostname="waf-engine-01",
        metadata={
            "log_type": "nginx",
            "customer_name": "test_customer",
            "fqdn": "example.com"
        }
    )
