"""認証機能のユニットテスト"""

import pytest
from fastapi import HTTPException
from src.auth import APIKeyAuth


class TestAPIKeyAuth:
    """APIKeyAuthのテストクラス"""

    def test_auth_disabled(self):
        """認証が無効化されている場合"""
        auth = APIKeyAuth(api_keys=None)
        assert not auth.enabled

        auth_empty = APIKeyAuth(api_keys=[])
        assert not auth_empty.enabled

    def test_auth_enabled(self):
        """認証が有効化されている場合"""
        auth = APIKeyAuth(api_keys=["test-key"])
        assert auth.enabled

    @pytest.mark.asyncio
    async def test_valid_api_key(self):
        """有効なAPIキー"""
        auth = APIKeyAuth(api_keys=["valid-key-123"])

        result = await auth(x_api_key="valid-key-123")
        assert result == "valid-key-123"

    @pytest.mark.asyncio
    async def test_invalid_api_key(self):
        """無効なAPIキー"""
        auth = APIKeyAuth(api_keys=["valid-key-123"])

        with pytest.raises(HTTPException) as exc_info:
            await auth(x_api_key="invalid-key")

        assert exc_info.value.status_code == 401
        assert "Invalid API Key" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_missing_api_key(self):
        """APIキーが提供されていない場合"""
        auth = APIKeyAuth(api_keys=["valid-key-123"])

        with pytest.raises(HTTPException) as exc_info:
            await auth(x_api_key=None)

        assert exc_info.value.status_code == 401
        assert "Missing API Key" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_auth_disabled_allows_any_key(self):
        """認証が無効化されている場合は任意のキーを許可"""
        auth = APIKeyAuth(api_keys=None)

        result = await auth(x_api_key=None)
        assert result is None

        result2 = await auth(x_api_key="any-key")
        assert result2 is None

    @pytest.mark.asyncio
    async def test_multiple_valid_keys(self):
        """複数の有効なAPIキー"""
        auth = APIKeyAuth(api_keys=["key1", "key2", "key3"])

        result1 = await auth(x_api_key="key1")
        assert result1 == "key1"

        result2 = await auth(x_api_key="key2")
        assert result2 == "key2"

        result3 = await auth(x_api_key="key3")
        assert result3 == "key3"
