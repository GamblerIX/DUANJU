import json
from pathlib import Path
from typing import List, Optional, Any
from enum import Enum
from ...core.models import AppConfig, ThemeMode
from ...core.utils.json_serializer import serialize_config, deserialize_config


class QualityOption(Enum):
    Q360P = "360p"
    Q720P = "720p"
    Q1080P = "1080p"


class ConfigManager:
    DEFAULT_CONFIG_PATH = "config/config.json"
    MIN_TIMEOUT = 1000
    MAX_TIMEOUT = 60000
    
    def __init__(self, config_path: Optional[str] = None):
        self._config_path = Path(config_path or self.DEFAULT_CONFIG_PATH)
        self._config: AppConfig = AppConfig()
        self._load_config()
    
    def _load_config(self) -> None:
        try:
            if self._config_path.exists():
                json_str = self._config_path.read_text(encoding='utf-8')
                self._config = deserialize_config(json_str)
            else:
                self._config = AppConfig()
                self._save_config()
        except (json.JSONDecodeError, ValueError):
            self._config = AppConfig()
            self._save_config()
    
    def _save_config(self) -> None:
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        json_str = serialize_config(self._config)
        self._config_path.write_text(json_str, encoding='utf-8')
    
    def load(self) -> AppConfig:
        self._load_config()
        return self._config
    
    def save(self, config: Optional[AppConfig] = None) -> None:
        if config:
            self._config = config
        self._save_config()
    
    def get(self, key: str) -> Any:
        return getattr(self._config, key, None)
    
    def set(self, key: str, value: Any) -> None:
        if hasattr(self._config, key):
            setattr(self._config, key, value)
            self._save_config()
    
    @property
    def config(self) -> AppConfig:
        return self._config
    
    @property
    def api_timeout(self) -> int:
        return self._config.api_timeout
    
    @api_timeout.setter
    def api_timeout(self, value: int) -> None:
        self._config.api_timeout = self.validate_timeout(value)
        self._save_config()
    
    @property
    def default_quality(self) -> str:
        return self._config.default_quality
    
    @default_quality.setter
    def default_quality(self, value: str) -> None:
        valid_qualities = [q.value for q in QualityOption]
        if value in valid_qualities:
            self._config.default_quality = value
            self._save_config()
    
    @property
    def theme_mode(self) -> ThemeMode:
        return self._config.theme_mode
    
    @theme_mode.setter
    def theme_mode(self, value: ThemeMode) -> None:
        self._config.theme_mode = value
        self._save_config()
    
    @property
    def last_search_keyword(self) -> str:
        return self._config.last_search_keyword
    
    @last_search_keyword.setter
    def last_search_keyword(self, value: str) -> None:
        self._config.last_search_keyword = value
        self._save_config()
    
    @property
    def search_history(self) -> List[str]:
        return self._config.search_history.copy()
    
    def add_search_history(self, keyword: str) -> None:
        history = self._config.search_history
        if keyword in history:
            history.remove(keyword)
        history.insert(0, keyword)
        max_history = self._config.max_search_history
        self._config.search_history = history[:max_history]
        self._save_config()
    
    def clear_search_history(self) -> None:
        self._config.search_history = []
        self._save_config()
    
    def validate_timeout(self, value: int) -> int:
        return max(self.MIN_TIMEOUT, min(self.MAX_TIMEOUT, value))
    
    def reload(self) -> None:
        self._load_config()
