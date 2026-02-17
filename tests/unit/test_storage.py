"""File Storageのユニットテスト"""

import pytest
import asyncio
import json
from pathlib import Path
from datetime import datetime, timezone
from src.storage.file_storage import FileStorage
from src.models import LogEntry


class TestFileStorage:
    """FileStorageのテストクラス"""

    def setup_method(self):
        """テストメソッド実行前の準備"""
        self.test_dir = Path("test_logs")
        self.storage = FileStorage(base_dir=str(self.test_dir))

    def teardown_method(self):
        """テストメソッド実行後のクリーンアップ"""
        # テストディレクトリを削除
        import shutil

        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_sanitize_path_component(self):
        """パスコンポーネントのサニタイズ"""
        test_cases = [
            ("normal_name", "normal_name"),
            ("../../../etc/passwd", "etc_passwd"),  # / も _ に置換される
            ("name<>:test", "name___test"),  # <, >, : が個別に _ に置換される
            ("..hidden", "hidden"),
            ("", "unknown"),
            (None, "unknown"),
        ]

        for input_val, expected in test_cases:
            result = self.storage._sanitize_path_component(input_val)
            assert result == expected

    @pytest.mark.asyncio
    async def test_write_batch(self):
        """ログバッチの書き込み"""
        log_entry = LogEntry(
            timestamp=datetime(2024, 2, 17, 10, 30, 0, tzinfo=timezone.utc),
            level="info",
            message="Test message",
            metadata={"customer_name": "test_customer", "log_type": "nginx", "fqdn": "example.com"},
        )

        await self.storage.write_batch([log_entry])

        # ファイルが作成されたことを確認
        expected_path = (
            self.test_dir
            / "test_customer"
            / "nginx"
            / "example.com"
            / "2024"
            / "02"
            / "17"
            / "10.log"
        )

        assert expected_path.exists()

        # ファイル内容を確認
        with open(expected_path, "r") as f:
            line = f.readline()
            log_dict = json.loads(line)
            assert log_dict["message"] == "Test message"
            assert log_dict["level"] == "info"

    @pytest.mark.asyncio
    async def test_write_batch_path_traversal_prevention(self):
        """Path Traversal攻撃の防止"""
        log_entry = LogEntry(
            timestamp=datetime(2024, 2, 17, 10, 30, 0, tzinfo=timezone.utc),
            level="info",
            message="Malicious log",
            metadata={
                "customer_name": "../../malicious",
                "log_type": "nginx",
                "fqdn": "example.com",
            },
        )

        await self.storage.write_batch([log_entry])

        # サニタイズされたパスが使用されることを確認
        # ../../malicious -> malicious になるはず
        expected_path = (
            self.test_dir / "malicious" / "nginx" / "example.com" / "2024" / "02" / "17" / "10.log"
        )

        assert expected_path.exists()

        # 親ディレクトリ外にファイルが作成されていないことを確認
        assert str(expected_path).startswith(str(self.test_dir))
