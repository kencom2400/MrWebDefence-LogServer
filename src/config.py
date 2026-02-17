"""設定管理"""

from pathlib import Path
from typing import Optional
import yaml


class Config:
    """アプリケーション設定"""

    def __init__(self, config_file: Optional[str] = None):
        """
        Args:
            config_file: 設定ファイルのパス。Noneの場合はデフォルト設定を使用
        """
        # デフォルト設定
        self.server_host = "0.0.0.0"
        self.server_port = 8080
        self.server_log_level = "info"
        self.server_use_ssl = False
        self.server_ssl_certfile = None
        self.server_ssl_keyfile = None

        self.auth_api_keys = []  # 空の場合は認証無効（開発用）

        self.buffer_max_count = 1000
        self.buffer_max_memory_mb = 50
        self.buffer_flush_interval_sec = 10
        self.buffer_max_retries = 3

        self.storage_base_dir = "logs"

        self.parser_max_field_length = 1024
        self.parser_max_message_length = 10240
        self.parser_max_optional_field_length = 2048

        self.corrector_future_tolerance_sec = 300

        # 設定ファイルから読み込み
        if config_file:
            self._load_from_file(config_file)

    def _load_from_file(self, config_file: str):
        """
        YAMLファイルから設定を読み込み

        Args:
            config_file: YAMLファイルのパス
        """
        config_path = Path(config_file)
        if not config_path.exists():
            return

        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        if not config_data:
            return

        # Server設定
        if "server" in config_data:
            server = config_data["server"]
            self.server_host = server.get("host", self.server_host)
            self.server_port = server.get("port", self.server_port)
            self.server_log_level = server.get("log_level", self.server_log_level)
            self.server_use_ssl = server.get("use_ssl", self.server_use_ssl)
            self.server_ssl_certfile = server.get("ssl_certfile", self.server_ssl_certfile)
            self.server_ssl_keyfile = server.get("ssl_keyfile", self.server_ssl_keyfile)

        # Auth設定
        if "auth" in config_data:
            auth = config_data["auth"]
            self.auth_api_keys = auth.get("api_keys", self.auth_api_keys)

        # Buffer設定
        if "buffer" in config_data:
            buffer = config_data["buffer"]
            self.buffer_max_count = buffer.get("max_count", self.buffer_max_count)
            self.buffer_max_memory_mb = buffer.get("max_memory_mb", self.buffer_max_memory_mb)
            self.buffer_flush_interval_sec = buffer.get(
                "flush_interval_sec", self.buffer_flush_interval_sec
            )
            self.buffer_max_retries = buffer.get("max_retries", self.buffer_max_retries)

        # Storage設定
        if "storage" in config_data:
            storage = config_data["storage"]
            self.storage_base_dir = storage.get("base_dir", self.storage_base_dir)

        # Parser設定
        if "parser" in config_data:
            parser = config_data["parser"]
            self.parser_max_field_length = parser.get(
                "max_field_length", self.parser_max_field_length
            )
            self.parser_max_message_length = parser.get(
                "max_message_length", self.parser_max_message_length
            )
            self.parser_max_optional_field_length = parser.get(
                "max_optional_field_length", self.parser_max_optional_field_length
            )

        # Corrector設定
        if "corrector" in config_data:
            corrector = config_data["corrector"]
            self.corrector_future_tolerance_sec = corrector.get(
                "future_tolerance_sec", self.corrector_future_tolerance_sec
            )


# グローバル設定インスタンス
_config: Optional[Config] = None


def get_config() -> Config:
    """設定インスタンスを取得"""
    global _config
    if _config is None:
        # ローカル設定ファイルがあればそれを使用、なければデフォルト
        local_config = Path("config/server.local.yaml")
        default_config = Path("config/server.yaml")

        if local_config.exists():
            _config = Config(str(local_config))
        elif default_config.exists():
            _config = Config(str(default_config))
        else:
            _config = Config()  # デフォルト設定

    return _config


def set_config(config: Config):
    """設定インスタンスを設定（主にテスト用）"""
    global _config
    _config = config
