"""認証機能"""

import secrets
from typing import Optional
from fastapi import Header, HTTPException, status


class APIKeyAuth:
    """APIキー認証"""

    def __init__(self, api_keys: Optional[list] = None):
        """
        Args:
            api_keys: 有効なAPIキーのリスト。Noneの場合は認証を無効化（開発用）
        """
        self.api_keys = set(api_keys) if api_keys else None
        self.enabled = api_keys is not None and len(api_keys) > 0

    async def __call__(self, x_api_key: Optional[str] = Header(None)):
        """
        APIキーを検証

        Args:
            x_api_key: X-API-Keyヘッダーの値

        Raises:
            HTTPException: 認証が必要だが提供されていない、または無効な場合
        """
        # 認証が無効化されている場合はスキップ
        if not self.enabled:
            return None

        # APIキーが提供されていない
        if not x_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing API Key",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        # APIキーの検証（タイミング攻撃対策のためsecrets.compare_digestを使用）
        if not any(secrets.compare_digest(x_api_key, key) for key in self.api_keys):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API Key",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        return x_api_key
