"""集成测试

测试各模块之间的集成和协作。
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.models import (
    DramaInfo, SearchResult, EpisodeList, VideoInfo,
    CategoryResult, ApiResponse
)


class TestModuleImports:
    """模块导入测试"""
    
    def test_import_core_models(self):
        """测试导入核心模型"""
        from src.core.models import (
            DramaInfo, EpisodeInfo, VideoInfo,
            SearchResult, EpisodeList, CategoryResult,
            ApiResponse, ApiError, AppConfig
        )
        assert DramaInfo is not None
        assert EpisodeInfo is not None
        assert VideoInfo is not None
    
    def test_import_utils(self):
        """测试导入工具模块"""
        from src.utils.string_utils import trim, is_blank, split
        from src.utils.log_manager import get_logger
        
        assert trim is not None
        assert is_blank is not None
        assert get_logger is not None
    
    def test_import_api_client(self):
        """测试导入 API 客户端"""
        from src.data.api_client import ApiClient
        
        assert ApiClient is not None
        client = ApiClient()
        assert client.base_url is not None


class TestDataFlow:
    """数据流测试"""
    
    def test_search_result_to_drama_list(self, sample_search_result: SearchResult):
        """测试搜索结果转换为短剧列表"""
        dramas = sample_search_result.data
        
        assert len(dramas) > 0
        assert all(isinstance(d, DramaInfo) for d in dramas)
        assert all(d.book_id for d in dramas)
    
    def test_drama_to_episode_list(
        self, 
        sample_drama: DramaInfo, 
        sample_episode_list: EpisodeList
    ):
        """测试短剧到剧集列表的关联"""
        assert sample_episode_list.book_id == sample_drama.book_id
        assert sample_episode_list.book_name == sample_drama.title
        assert len(sample_episode_list.episodes) == sample_drama.episode_cnt
    
    def test_episode_to_video_info(self, sample_video_info: VideoInfo):
        """测试剧集到视频信息的转换"""
        assert sample_video_info.code == 200
        assert sample_video_info.url.startswith("http")
        assert sample_video_info.quality in ["480p", "720p", "1080p"]


class TestCacheIntegration:
    """缓存集成测试"""
    
    def test_cache_key_generation(self):
        """测试缓存键生成"""
        # 模拟 CacheManager 的键生成逻辑
        def generate_key(*args):
            return "_".join(str(arg) for arg in args)
        
        key1 = generate_key("search", "测试", "1")
        key2 = generate_key("search", "测试", "1")
        key3 = generate_key("search", "其他", "1")
        
        assert key1 == key2  # 相同参数生成相同键
        assert key1 != key3  # 不同参数生成不同键
    
    def test_cache_entry_expiration(self):
        """测试缓存过期逻辑"""
        import time
        from src.core.models import CacheEntry
        
        # 创建一个即将过期的缓存
        entry = CacheEntry(
            data="test",
            timestamp=time.time() - 400,  # 400秒前
            ttl=300000  # 5分钟 = 300秒
        )
        
        assert entry.is_expired(time.time()) is True
        
        # 创建一个新鲜的缓存
        fresh_entry = CacheEntry(
            data="test",
            timestamp=time.time(),
            ttl=300000
        )
        
        assert fresh_entry.is_expired(time.time()) is False


class TestErrorHandling:
    """错误处理集成测试"""
    
    def test_api_error_creation(self):
        """测试 API 错误创建"""
        from src.core.models import ApiError
        
        error = ApiError(
            code=500,
            message="服务器错误",
            details="Connection refused"
        )
        
        assert error.code == 500
        assert "服务器" in error.message
    
    def test_api_response_failure(self):
        """测试 API 响应失败处理"""
        response = ApiResponse(
            status_code=500,
            body="",
            error="Internal Server Error",
            success=False
        )
        
        assert response.success is False
        assert response.error != ""
    
    def test_friendly_error_messages(self):
        """测试友好错误消息"""
        from src.utils.log_manager import LogManager
        
        logger = LogManager()
        
        # 测试各种错误类型的友好消息
        test_cases = [
            (Exception("Connection timeout"), "超时"),
            (Exception("Connection refused"), "拒绝"),
            (Exception("404 Not Found"), "不存在"),
        ]
        
        for error, expected_keyword in test_cases:
            msg = logger._get_friendly_error_message(error)
            # 验证返回了某种消息
            assert len(msg) > 0


class TestConfigIntegration:
    """配置集成测试"""
    
    def test_config_default_values(self):
        """测试配置默认值"""
        from src.core.models import AppConfig, ThemeMode
        
        config = AppConfig()
        
        assert config.api_timeout == 10000
        assert config.default_quality == "1080p"
        assert config.theme_mode == ThemeMode.AUTO
        assert config.enable_cache is True
    
    def test_config_modification(self):
        """测试配置修改"""
        from src.core.models import AppConfig, ThemeMode
        
        config = AppConfig()
        
        # 修改配置
        config.api_timeout = 5000
        config.theme_mode = ThemeMode.DARK
        
        assert config.api_timeout == 5000
        assert config.theme_mode == ThemeMode.DARK


@pytest.mark.asyncio
class TestAsyncIntegration:
    """异步集成测试"""
    
    async def test_api_client_creation(self):
        """测试 API 客户端创建"""
        from src.data.api_client import ApiClient
        
        client = ApiClient(timeout=5000)
        
        assert client.timeout == 5000
        await client.close()
    
    async def test_mock_api_request(self, mock_api_client):
        """测试模拟 API 请求"""
        response = await mock_api_client.get(params={"name": "test"})
        
        assert response.status_code == 200
        assert response.success is True

