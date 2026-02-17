"""エントリーポイント"""

import uvicorn
from src.config import get_config
from src.server.api import app

if __name__ == "__main__":
    config = get_config()

    # SSL設定
    ssl_config = {}
    if config.server_use_ssl:
        if not config.server_ssl_certfile or not config.server_ssl_keyfile:
            raise ValueError("SSL is enabled but certfile or keyfile is not configured")
        ssl_config = {
            "ssl_certfile": config.server_ssl_certfile,
            "ssl_keyfile": config.server_ssl_keyfile,
        }

    uvicorn.run(
        app, host=config.server_host, port=config.server_port, log_level="info", **ssl_config
    )
