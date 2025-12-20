"""数据提供者测试

测试 src/data/providers/ 中的提供者功能。
"""
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock
import sys

import pytest

from src.core.models import SearchResult, CategoryResult, EpisodeList, VideoInfo, DramaInfo
from src.data.providers.provider_base import (
    BaseDataProvider, ProviderInfo, ProviderCapabilities
)

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.providers.provider_base import (
    BaseDataProvider, IDataProvider, ProviderInfo, ProviderCapabilities
)
from src.data.providers.provider_registry import (
    ProviderRegistry, get_registry, get_current_provider
)
from src.core.models import SearchResult, DramaInfo, EpisodeList, VideoInfo, CategoryResult


class TestProviderCapabilities:
    """ProviderCapabilities 测试"""
    
    def test_default_capabilities(self):
        """测试默认能力"""
        caps = ProviderCapabilities()
        
        assert caps.supports_search is True
        assert caps.supports_categories is True
        assert caps.supports_recommendations is True
        assert caps.supports_episodes is True
        assert caps.supports_video_url is True
        assert caps.supports_quality_selection is True
        assert caps.supports_pagination is True
        assert caps.supports_dynamic_categories is False
    
    def test_custom_capabilities(self):
        """测试自定义能力"""
        caps = ProviderCapabilities(
            supports_search=True,
            supports_categories=False,
            supports_dynamic_categories=True,
            available_qualities=["720p", "480p"]
        )
        
        assert caps.supports_categories is False
        assert caps.supports_dynamic_categories is True
        assert "720p" in caps.available_qualities
    
    def test_available_qualities_default(self):
        """测试默认清晰度列表"""
        caps = ProviderCapabilities()
        
        assert "1080p" in caps.available_qualities
        assert "720p" in caps.available_qualities
        assert "480p" in caps.available_qualities


class TestProviderInfo:
    """ProviderInfo 测试"""
    
    def test_create_provider_info(self):
        """测试创建提供者信息"""
        info = ProviderInfo(
            id="test_provider",
            name="测试提供者",
            description="测试用提供者",
            version="1.0.0",
            author="Test",
            base_url="https://api.test.com"
        )
        
        assert info.id == "test_provider"
        assert info.name == "测试提供者"
        assert info.version == "1.0.0"
    
    def test_default_values(self):
        """测试默认值"""
        info = ProviderInfo(id="test", name="Test")
        
        assert info.description == ""
        assert info.version == "1.0.0"
        assert info.author == ""
        assert info.base_url == ""
        assert info.capabilities is not None


class TestProviderRegistry:
    """ProviderRegistry 测试"""
    
    @pytest.fixture
    def mock_provider(self):
        """创建模拟提供者"""
        provider = MagicMock(spec=IDataProvider)
        provider.info = ProviderInfo(id="mock_provider", name="Mock Provider")
        return provider
    
    @pytest.fixture
    def mock_provider2(self):
        """创建第二个模拟提供者"""
        provider = MagicMock(spec=IDataProvider)
        provider.info = ProviderInfo(id="mock_provider2", name="Mock Provider 2")
        return provider
    
    @pytest.fixture
    def fresh_registry(self):
        """创建新的注册中心（重置单例）"""
        # 重置单例
        ProviderRegistry._instance = None
        registry = ProviderRegistry()
        yield registry
        # 清理
        ProviderRegistry._instance = None
    
    def test_singleton(self):
        """测试单例模式"""
        registry1 = ProviderRegistry()
        registry2 = ProviderRegistry()
        
        assert registry1 is registry2
    
    def test_register_provider(self, fresh_registry, mock_provider):
        """测试注册提供者"""
        fresh_registry.register(mock_provider)
        
        assert fresh_registry.count == 1
        assert fresh_registry.get("mock_provider") is mock_provider
    
    def test_register_sets_first_as_current(self, fresh_registry, mock_provider):
        """测试注册第一个提供者自动设为当前"""
        fresh_registry.register(mock_provider)
        
        assert fresh_registry.current_id == "mock_provider"
    
    def test_unregister_provider(self, fresh_registry, mock_provider):
        """测试注销提供者"""
        fresh_registry.register(mock_provider)
        result = fresh_registry.unregister("mock_provider")
        
        assert result is True
        assert fresh_registry.count == 0
        assert fresh_registry.get("mock_provider") is None
    
    def test_unregister_nonexistent(self, fresh_registry):
        """测试注销不存在的提供者"""
        result = fresh_registry.unregister("nonexistent")
        assert result is False
    
    def test_unregister_current_switches(self, fresh_registry, mock_provider, mock_provider2):
        """测试注销当前提供者会切换"""
        fresh_registry.register(mock_provider)
        fresh_registry.register(mock_provider2)
        fresh_registry.set_current("mock_provider")
        
        fresh_registry.unregister("mock_provider")
        
        assert fresh_registry.current_id == "mock_provider2"
    
    def test_get_provider(self, fresh_registry, mock_provider):
        """测试获取提供者"""
        fresh_registry.register(mock_provider)
        
        provider = fresh_registry.get("mock_provider")
        assert provider is mock_provider
    
    def test_get_nonexistent(self, fresh_registry):
        """测试获取不存在的提供者"""
        provider = fresh_registry.get("nonexistent")
        assert provider is None
    
    def test_get_current(self, fresh_registry, mock_provider):
        """测试获取当前提供者"""
        fresh_registry.register(mock_provider)
        
        current = fresh_registry.get_current()
        assert current is mock_provider
    
    def test_get_current_none(self, fresh_registry):
        """测试无当前提供者"""
        current = fresh_registry.get_current()
        assert current is None
    
    def test_set_current(self, fresh_registry, mock_provider, mock_provider2):
        """测试设置当前提供者"""
        fresh_registry.register(mock_provider)
        fresh_registry.register(mock_provider2)
        
        result = fresh_registry.set_current("mock_provider2")
        
        assert result is True
        assert fresh_registry.current_id == "mock_provider2"
    
    def test_set_current_nonexistent(self, fresh_registry, mock_provider):
        """测试设置不存在的提供者为当前"""
        fresh_registry.register(mock_provider)
        
        result = fresh_registry.set_current("nonexistent")
        
        assert result is False
        assert fresh_registry.current_id == "mock_provider"
    
    def test_list_providers(self, fresh_registry, mock_provider, mock_provider2):
        """测试列出所有提供者"""
        fresh_registry.register(mock_provider)
        fresh_registry.register(mock_provider2)
        
        providers = fresh_registry.list_providers()
        
        assert len(providers) == 2
        assert all(isinstance(p, ProviderInfo) for p in providers)
    
    def test_list_provider_ids(self, fresh_registry, mock_provider, mock_provider2):
        """测试列出所有提供者 ID"""
        fresh_registry.register(mock_provider)
        fresh_registry.register(mock_provider2)
        
        ids = fresh_registry.list_provider_ids()
        
        assert "mock_provider" in ids
        assert "mock_provider2" in ids


class TestMockDataProvider:
    """模拟数据提供者测试（用于验证接口）"""
    
    @pytest.fixture
    def mock_provider(self):
        """创建完整的模拟提供者"""
        provider = MagicMock(spec=IDataProvider)
        provider.info = ProviderInfo(id="test", name="Test")
        
        # 设置异步方法返回值
        provider.search = AsyncMock(return_value=SearchResult(
            code=200, msg="success", data=[], page=1
        ))
        provider.get_categories = AsyncMock(return_value=["都市", "甜宠"])
        provider.get_category_dramas = AsyncMock(return_value=CategoryResult(
            code=200, category="都市", data=[]
        ))
        provider.get_recommendations = AsyncMock(return_value=[])
        provider.get_episodes = AsyncMock(return_value=EpisodeList(
            code=200, book_name="Test", episodes=[]
        ))
        provider.get_video_url = AsyncMock(return_value=VideoInfo(
            code=200, url="https://example.com/video.m3u8"
        ))
        
        return provider
    
    @pytest.mark.asyncio
    async def test_search(self, mock_provider):
        """测试搜索接口"""
        result = await mock_provider.search("测试", 1)
        
        assert isinstance(result, SearchResult)
        assert result.code == 200
        mock_provider.search.assert_called_once_with("测试", 1)
    
    @pytest.mark.asyncio
    async def test_get_categories(self, mock_provider):
        """测试获取分类接口"""
        result = await mock_provider.get_categories()
        
        assert isinstance(result, list)
        assert "都市" in result
    
    @pytest.mark.asyncio
    async def test_get_category_dramas(self, mock_provider):
        """测试获取分类短剧接口"""
        result = await mock_provider.get_category_dramas("都市", 1)
        
        assert isinstance(result, CategoryResult)
        assert result.category == "都市"
    
    @pytest.mark.asyncio
    async def test_get_recommendations(self, mock_provider):
        """测试获取推荐接口"""
        result = await mock_provider.get_recommendations()
        
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_get_episodes(self, mock_provider):
        """测试获取剧集接口"""
        result = await mock_provider.get_episodes("123")
        
        assert isinstance(result, EpisodeList)
        mock_provider.get_episodes.assert_called_once_with("123")
    
    @pytest.mark.asyncio
    async def test_get_video_url(self, mock_provider):
        """测试获取视频地址接口"""
        result = await mock_provider.get_video_url("v123", "1080p")
        
        assert isinstance(result, VideoInfo)
        assert result.url.startswith("http")
    
    def test_set_timeout(self, mock_provider):
        """测试设置超时"""
        mock_provider.set_timeout(5000)
        mock_provider.set_timeout.assert_called_once_with(5000)


class TestIDataProviderProtocol:
    """IDataProvider 协议测试"""
    
    def test_protocol_check(self):
        """测试协议检查"""
        # 创建符合协议的模拟对象
        provider = MagicMock()
        provider.info = ProviderInfo(id="test", name="Test")
        provider.search = AsyncMock()
        provider.get_categories = AsyncMock()
        provider.get_category_dramas = AsyncMock()
        provider.get_recommendations = AsyncMock()
        provider.get_episodes = AsyncMock()
        provider.get_video_url = AsyncMock()
        provider.set_timeout = MagicMock()
        
        # 验证符合协议
        assert isinstance(provider, IDataProvider)




# ============================================================
# From: test_provider_base_coverage.py
# ============================================================
class TestProviderCapabilities_Coverage:
    """测试 ProviderCapabilities"""
    
    def test_default_capabilities(self):
        """测试默认能力"""
        caps = ProviderCapabilities()
        
        assert caps.supports_search == True
        assert caps.supports_categories == True
        assert caps.supports_recommendations == True
        assert caps.supports_episodes == True
        assert caps.supports_video_url == True
        assert caps.supports_quality_selection == True
        assert caps.supports_pagination == True
        assert caps.supports_dynamic_categories == False
        assert caps.available_qualities == ["1080p", "720p", "480p"]
    
    def test_custom_capabilities(self):
        """测试自定义能力"""
        caps = ProviderCapabilities(
            supports_search=False,
            supports_categories=False,
            supports_recommendations=False,
            supports_episodes=False,
            supports_video_url=False,
            supports_quality_selection=False,
            supports_pagination=False,
            supports_dynamic_categories=True,
            available_qualities=["4K", "1080p"]
        )
        
        assert caps.supports_search == False
        assert caps.supports_dynamic_categories == True
        assert caps.available_qualities == ["4K", "1080p"]


class TestProviderInfo_Coverage:
    """测试 ProviderInfo"""
    
    def test_provider_info_creation(self):
        """测试创建 ProviderInfo"""
        info = ProviderInfo(
            id="test",
            name="Test Provider",
            description="A test provider",
            version="1.0.0",
            base_url="https://api.test.com"
        )
        
        assert info.id == "test"
        assert info.name == "Test Provider"
        assert info.description == "A test provider"
        assert info.version == "1.0.0"
        assert info.base_url == "https://api.test.com"
    
    def test_provider_info_with_capabilities(self):
        """测试带能力的 ProviderInfo"""
        caps = ProviderCapabilities(supports_search=False)
        info = ProviderInfo(
            id="test",
            name="Test",
            description="Test",
            version="1.0.0",
            base_url="https://test.com",
            capabilities=caps
        )
        
        assert info.capabilities.supports_search == False


class ConcreteProvider(BaseDataProvider):
    """具体的 Provider 实现用于测试"""
    
    def __init__(self, timeout: int = 10000):
        super().__init__(timeout)
        self._info = ProviderInfo(
            id="concrete",
            name="Concrete Provider",
            description="A concrete provider for testing",
            version="1.0.0",
            base_url="https://api.concrete.com"
        )
    
    @property
    def info(self) -> ProviderInfo:
        return self._info
    
    async def search(self, keyword: str, page: int = 1) -> SearchResult:
        return SearchResult(code=200, msg="success", data=[], page=page)
    
    async def get_categories(self):
        return ["分类1", "分类2"]
    
    async def get_category_dramas(self, category: str, page: int = 1) -> CategoryResult:
        return CategoryResult(code=200, category=category, data=[], offset=page)
    
    async def get_recommendations(self):
        return []
    
    async def get_episodes(self, drama_id: str) -> EpisodeList:
        return EpisodeList(code=200, book_name="测试", episodes=[], total=0)
    
    async def get_video_url(self, episode_id: str, quality: str = "1080p") -> VideoInfo:
        return VideoInfo(code=200, url="http://test.m3u8", pic="", quality=quality)


class TestBaseDataProvider:
    """测试 BaseDataProvider"""
    
    @pytest.fixture
    def provider(self):
        return ConcreteProvider()
    
    def test_provider_info(self, provider):
        """测试获取 provider info"""
        info = provider.info
        
        assert info.id == "concrete"
        assert info.name == "Concrete Provider"
    
    def test_timeout_property(self, provider):
        """测试 timeout 属性"""
        assert provider._timeout == 10000
    
    def test_custom_timeout(self):
        """测试自定义 timeout"""
        provider = ConcreteProvider(timeout=5000)
        assert provider._timeout == 5000
    
    @pytest.mark.asyncio
    async def test_search(self, provider):
        """测试搜索"""
        result = await provider.search("测试")
        
        assert result.code == 200
        assert result.page == 1
    
    @pytest.mark.asyncio
    async def test_get_categories(self, provider):
        """测试获取分类"""
        categories = await provider.get_categories()
        
        assert len(categories) == 2
        assert "分类1" in categories
    
    @pytest.mark.asyncio
    async def test_get_category_dramas(self, provider):
        """测试获取分类短剧"""
        result = await provider.get_category_dramas("分类1", page=2)
        
        assert result.code == 200
        assert result.category == "分类1"
        assert result.offset == 2
    
    @pytest.mark.asyncio
    async def test_get_recommendations(self, provider):
        """测试获取推荐"""
        result = await provider.get_recommendations()
        
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_get_episodes(self, provider):
        """测试获取剧集"""
        result = await provider.get_episodes("123")
        
        assert result.code == 200
        assert result.book_name == "测试"
    
    @pytest.mark.asyncio
    async def test_get_video_url(self, provider):
        """测试获取视频地址"""
        result = await provider.get_video_url("v1", "720p")
        
        assert result.code == 200
        assert result.url == "http://test.m3u8"
        assert result.quality == "720p"


class TestBaseDataProviderAbstract:
    """测试 BaseDataProvider 抽象方法"""
    
    def test_abstract_methods_exist(self):
        """测试抽象方法存在"""
        # 验证 BaseDataProvider 有这些抽象方法
        assert hasattr(BaseDataProvider, 'info')
        assert hasattr(BaseDataProvider, 'search')
        assert hasattr(BaseDataProvider, 'get_categories')
        assert hasattr(BaseDataProvider, 'get_category_dramas')
        assert hasattr(BaseDataProvider, 'get_recommendations')
        assert hasattr(BaseDataProvider, 'get_episodes')
        assert hasattr(BaseDataProvider, 'get_video_url')
