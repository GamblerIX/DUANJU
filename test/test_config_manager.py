"""配置管理器测试

测试 src/data/config/config_manager.py 中的配置功能。
"""
import pytest
import json
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.config_manager import ConfigManager, QualityOption
from src.core.models import AppConfig, ThemeMode


class TestConfigManager:
    """ConfigManager 测试"""
    
    @pytest.fixture
    def config_file(self, tmp_path):
        """创建临时配置文件路径"""
        return tmp_path / "config" / "config.json"
    
    @pytest.fixture
    def config_manager(self, config_file):
        """创建配置管理器"""
        return ConfigManager(str(config_file))
    
    def test_init_creates_default_config(self, config_manager, config_file):
        """测试初始化创建默认配置"""
        assert config_file.exists()
        assert config_manager.config is not None
    
    def test_default_values(self, config_manager):
        """测试默认配置值"""
        config = config_manager.config
        assert config.api_timeout == 10000
        assert config.default_quality == "1080p"
        assert config.theme_mode == ThemeMode.AUTO
        assert config.enable_cache is True
    
    def test_load_existing_config(self, config_file):
        """测试加载已存在的配置"""
        # 先创建配置文件
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_data = {
            "apiTimeout": 5000,
            "defaultQuality": "720p",
            "themeMode": "dark",
            "lastSearchKeyword": "测试",
            "searchHistory": ["a", "b"],
            "maxSearchHistory": 10,
            "currentProvider": "test",
            "enableCache": False,
            "cacheTTL": 100000,
            "maxRetries": 5,
            "retryDelay": 2000
        }
        config_file.write_text(json.dumps(config_data), encoding="utf-8")
        
        # 加载配置
        manager = ConfigManager(str(config_file))
        
        assert manager.api_timeout == 5000
        assert manager.default_quality == "720p"
        assert manager.theme_mode == ThemeMode.DARK
        assert manager.last_search_keyword == "测试"
    
    def test_save_config(self, config_manager, config_file):
        """测试保存配置"""
        config_manager.api_timeout = 5000
        
        # 重新加载验证
        new_manager = ConfigManager(str(config_file))
        assert new_manager.api_timeout == 5000
    
    def test_get_config_item(self, config_manager):
        """测试获取配置项"""
        assert config_manager.get("api_timeout") == 10000
        assert config_manager.get("nonexistent") is None
    
    def test_set_config_item(self, config_manager):
        """测试设置配置项"""
        config_manager.set("api_timeout", 5000)
        assert config_manager.api_timeout == 5000
    
    def test_api_timeout_property(self, config_manager):
        """测试 api_timeout 属性"""
        config_manager.api_timeout = 5000
        assert config_manager.api_timeout == 5000
    
    def test_api_timeout_validation(self, config_manager):
        """测试 api_timeout 验证"""
        # 测试最小值限制
        config_manager.api_timeout = 100
        assert config_manager.api_timeout == 1000
        
        # 测试最大值限制
        config_manager.api_timeout = 100000
        assert config_manager.api_timeout == 60000
    
    def test_default_quality_property(self, config_manager):
        """测试 default_quality 属性"""
        config_manager.default_quality = "720p"
        assert config_manager.default_quality == "720p"
    
    def test_default_quality_invalid(self, config_manager):
        """测试无效的清晰度设置"""
        original = config_manager.default_quality
        config_manager.default_quality = "invalid"
        assert config_manager.default_quality == original  # 保持不变
    
    def test_theme_mode_property(self, config_manager):
        """测试 theme_mode 属性"""
        config_manager.theme_mode = ThemeMode.DARK
        assert config_manager.theme_mode == ThemeMode.DARK
    
    def test_search_history(self, config_manager):
        """测试搜索历史"""
        config_manager.add_search_history("keyword1")
        config_manager.add_search_history("keyword2")
        
        history = config_manager.search_history
        assert "keyword2" in history
        assert "keyword1" in history
        assert history[0] == "keyword2"  # 最新的在前
    
    def test_search_history_dedup(self, config_manager):
        """测试搜索历史去重"""
        config_manager.add_search_history("keyword1")
        config_manager.add_search_history("keyword2")
        config_manager.add_search_history("keyword1")  # 重复
        
        history = config_manager.search_history
        assert history.count("keyword1") == 1
        assert history[0] == "keyword1"  # 移到最前
    
    def test_search_history_max_limit(self, config_manager):
        """测试搜索历史最大数量限制"""
        for i in range(30):
            config_manager.add_search_history(f"keyword{i}")
        
        history = config_manager.search_history
        assert len(history) <= config_manager.config.max_search_history
    
    def test_clear_search_history(self, config_manager):
        """测试清除搜索历史"""
        config_manager.add_search_history("keyword1")
        config_manager.clear_search_history()
        
        assert len(config_manager.search_history) == 0
    
    def test_reload(self, config_manager, config_file):
        """测试重新加载配置"""
        # 直接修改文件
        config_data = {
            "apiTimeout": 8000,
            "defaultQuality": "1080p",
            "themeMode": "auto",
            "lastSearchKeyword": "",
            "searchHistory": [],
            "maxSearchHistory": 20,
            "currentProvider": "cenguigui",
            "enableCache": True,
            "cacheTTL": 300000,
            "maxRetries": 3,
            "retryDelay": 1000
        }
        config_file.write_text(json.dumps(config_data), encoding="utf-8")
        
        config_manager.reload()
        assert config_manager.api_timeout == 8000
    
    def test_invalid_json_recovery(self, config_file):
        """测试无效 JSON 恢复"""
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text("invalid json", encoding="utf-8")
        
        manager = ConfigManager(str(config_file))
        # 应该使用默认配置
        assert manager.api_timeout == 10000
    
    def test_validate_timeout(self, config_manager):
        """测试超时验证函数"""
        assert config_manager.validate_timeout(500) == 1000
        assert config_manager.validate_timeout(5000) == 5000
        assert config_manager.validate_timeout(100000) == 60000


class TestQualityOption:
    """QualityOption 枚举测试"""
    
    def test_quality_values(self):
        """测试清晰度枚举值"""
        assert QualityOption.Q360P.value == "360p"
        assert QualityOption.Q720P.value == "720p"
        assert QualityOption.Q1080P.value == "1080p"
    
    def test_quality_list(self):
        """测试获取所有清晰度"""
        qualities = [q.value for q in QualityOption]
        assert "360p" in qualities
        assert "720p" in qualities
        assert "1080p" in qualities

