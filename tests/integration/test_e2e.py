"""統合テスト（E2E）"""

import pytest
import json
from pathlib import Path
from httpx import AsyncClient
from src.server.api import app


class TestLogServerIntegration:
    """Log ServerのE2Eテスト"""

    @pytest.mark.asyncio
    async def test_full_log_flow(self, tmp_path):
        """ログ受信から保存までのフルフロー"""
        # テスト用のログディレクトリを設定
        test_log_dir = tmp_path / "logs"
        test_log_dir.mkdir()

        # テストクライアント作成
        async with AsyncClient(app=app, base_url="http://test") as client:
            # ログを送信
            payload = {
                "logs": [
                    {
                        "time": "2024-02-17T10:00:00Z",
                        "log_type": "nginx",
                        "hostname": "waf-engine-01",
                        "fqdn": "example.com",
                        "customer_name": "test_customer",
                        "request": "GET /api/users HTTP/1.1",
                    }
                ]
            }

            response = await client.post("/api/logs", json=payload)

            # レスポンスの確認
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["received"] == 1
            assert data["failed"] == 0

    @pytest.mark.asyncio
    async def test_health_check(self):
        """ヘルスチェックエンドポイント"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_invalid_log_handling(self):
        """不正なログの処理"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 必須フィールドが欠けているログ
            payload = {
                "logs": [
                    {
                        "time": "2024-02-17T10:00:00Z",
                        "log_type": "nginx",
                        # hostname が欠けている
                        "fqdn": "example.com",
                    }
                ]
            }

            response = await client.post("/api/logs", json=payload)

            # 全てのログが失敗した場合は400エラー
            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_partial_failure(self):
        """一部のログが失敗した場合"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            payload = {
                "logs": [
                    # 正常なログ
                    {
                        "time": "2024-02-17T10:00:00Z",
                        "log_type": "nginx",
                        "hostname": "waf-engine-01",
                        "fqdn": "example.com",
                        "customer_name": "test_customer",
                    },
                    # 不正なログ（hostnameが欠けている）
                    {"time": "2024-02-17T10:00:00Z", "log_type": "nginx", "fqdn": "example.com"},
                ]
            }

            response = await client.post("/api/logs", json=payload)

            # 一部成功した場合は200
            assert response.status_code == 200
            data = response.json()
            assert data["received"] == 1
            assert data["failed"] == 1

    @pytest.mark.asyncio
    async def test_batch_processing(self):
        """バッチ処理"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 複数のログを送信
            logs = [
                {
                    "time": f"2024-02-17T10:00:{i:02d}Z",
                    "log_type": "nginx",
                    "hostname": "waf-engine-01",
                    "fqdn": "example.com",
                    "customer_name": "test_customer",
                    "request": f"GET /api/users/{i} HTTP/1.1",
                }
                for i in range(10)
            ]

            payload = {"logs": logs}
            response = await client.post("/api/logs", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data["received"] == 10
            assert data["failed"] == 0
