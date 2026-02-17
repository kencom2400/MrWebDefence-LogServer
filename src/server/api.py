"""FastAPI Log Server"""

import logging
import asyncio
from typing import List, Dict, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from src.config import get_config
from src.parser import LogParser, LogNormalizer
from src.corrector import TimeCorrector
from src.buffer import LogBuffer
from src.storage import FileStorage
from src.models import ParseError, BufferFullError

# 設定を読み込み
config = get_config()

# ロガー設定
logging.basicConfig(
    level=getattr(logging, config.server_log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# コンポーネント初期化（設定から値を取得）
parser = LogParser(config=config)
normalizer = LogNormalizer()
corrector = TimeCorrector(config=config)
storage = FileStorage(base_dir=config.storage_base_dir)
buffer = LogBuffer(
    max_count=config.buffer_max_count,
    max_memory_mb=config.buffer_max_memory_mb,
    flush_interval_sec=config.buffer_flush_interval_sec,
    max_retries=config.buffer_max_retries,
    storage=storage,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションライフサイクル管理"""
    # Startup
    logger.info("Starting Log Server...")
    asyncio.create_task(buffer.start_periodic_flush())
    logger.info("Log Server started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Log Server...")
    await buffer.flush()
    logger.info("Log Server shutdown complete")


app = FastAPI(title="MrWebDefence Log Server", version="0.1.0", lifespan=lifespan)


class LogRequest(BaseModel):
    """ログ受信リクエスト"""

    logs: List[Dict[str, Any]]


@app.post("/api/logs", status_code=status.HTTP_200_OK)
async def receive_logs(request: LogRequest):
    """
    Engine側からログを受信

    Args:
        request: ログリクエスト

    Returns:
        受信結果

    Raises:
        HTTPException: エラー時
    """
    try:
        # 受信したログを処理
        parsed_logs = []
        failed_count = 0

        for raw_log in request.logs:
            try:
                # 1. パース（検証）
                validated_log = parser.parse(raw_log)

                # 2. 正規化
                log_entry = normalizer.normalize(validated_log)

                # 3. 時刻補正
                log_entry = corrector.correct(log_entry)

                parsed_logs.append(log_entry)
            except ParseError as e:
                # パースエラーは警告レベル（個別ログの失敗は継続）
                logger.warning(f"Failed to parse log: {e}")
                failed_count += 1
            except Exception as e:
                # その他のエラーもログして継続
                logger.error(f"Unexpected error processing log: {e}")
                failed_count += 1

        # すべてのログが失敗した場合は400エラー
        if not parsed_logs and failed_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="All logs failed to parse"
            )

        # 4. バッファに追加
        try:
            await buffer.add_batch(parsed_logs)
        except BufferFullError:
            # バッファが満杯の場合は503を返す（バックプレッシャー）
            logger.warning("Buffer full, returning 503")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service temporarily unavailable. Please retry later.",
            )

        # 成功レスポンス
        return {"status": "ok", "received": len(parsed_logs), "failed": failed_count}

    except HTTPException:
        # FastAPIのHTTPExceptionはそのまま再送出
        raise
    except Exception as e:
        # その他のエラーは500として返す（詳細は隠す）
        logger.error(f"Internal error processing logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error"
        )


@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "healthy"}
