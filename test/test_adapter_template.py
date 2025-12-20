"""适配器模板测试"""
import pytest
import asyncio
import time
from unittest.mock import MagicMock, AsyncMock, patch

from src.data.providers.adapters.adapter_template import TemplateAdapter
from src.core.models import DramaInfo, EpisodeInfo


class TestTemplateAdapter:
    """测试模板适配器"""
    
    @pytest.fixture
    def adapter(self):
        return TemplateAdapter(timeout=10000)
    
    def test_adapter_creation(self, adapter):
        assert adapter._timeout == 10000
        assert adapter.info.id == "your_provider_id"
        assert adapter.info.name == "Your Provider Name"
        assert adapter.info.base_url == TemplateAdapter.BASE_URL
    
    def test_provider_info(self, adapter):
        info = adapter.info
        assert info.capabilities.supports_search is True
        assert info.capabilities.supports_categories is True
        assert info.capabilities.supports_recommendations is True
        assert info.capabilities.supports_episodes is True
        assert info.capabilities.supports_video_url is True
        assert info.capabilities.supports_quality_selection is True
        assert info.capabilities.supports_pagination is True
        assert info.capabilities.supports_dynamic_categories is False
        assert "1080p" in info.capabilities.available_qualities
    
    def test_categories_static(self, adapter):
        """测试静态分类列表"""
        categories = adapter.CATEGORIES
        assert isinstance(categories, list)
        assert len(categories) > 0
    
    @pytest.mark.asyncio
    async def test_get_categories(self, adapter):
        """测试获取分类"""
        categories = await adapter.get_categories()
        assert categories == adapter.CATEGORIES
    
    def test_convert_to_drama(self, adapter):
        """测试转换为 DramaInfo"""
        item = {
            "id": "123",
            "name": "测试短剧",
            "cover_url": "https://example.com/cover.jpg",
            "episode_count": 20,
            "description": "这是简介",
            "category": "都市",
            "author": "作者",
            "views": 10000
        }
        drama = adapter._convert_to_drama(item)
        
        assert drama.book_id == "123"
        assert drama.title == "测试短剧"
        assert drama.cover == "https://example.com/cover.jpg"
        assert drama.episode_cnt == 20
        assert drama.intro == "这是简介"
        assert drama.type == "都市"
        assert drama.author == "作者"
        assert drama.play_cnt == 10000
    
    def test_convert_to_drama_empty(self, adapter):
        """测试空数据转换"""
        item = {}
        drama = adapter._convert_to_drama(item)
        
        assert drama.book_id == ""
        assert drama.title == ""
        assert drama.cover == ""
        assert drama.episode_cnt == 0
    
    def test_convert_to_episode(self, adapter):
        """测试转换为 EpisodeInfo"""
        item = {
            "id": "video_001",
            "title": "第1集",
            "number": 1,
            "word_count": 1000
        }
        episode = adapter._convert_to_episode(item, 0)
        
        assert episode.video_id == "video_001"
        assert episode.title == "第1集"
        assert episode.episode_number == 1
        assert episode.chapter_word_number == 1000
    
    def test_convert_to_episode_default_title(self, adapter):
        """测试默认标题"""
        item = {"id": "video_001"}
        episode = adapter._convert_to_episode(item, 4)
        
        assert episode.title == "第5集"
        assert episode.episode_number == 5
    
    @pytest.mark.asyncio
    async def test_search_not_implemented(self, adapter):
        """测试搜索未实现"""
        with pytest.raises(NotImplementedError, match="请实现 search 方法"):
            await adapter.search("test")
    
    @pytest.mark.asyncio
    async def test_get_category_dramas_not_implemented(self, adapter):
        """测试分类短剧未实现"""
        with pytest.raises(NotImplementedError, match="请实现 get_category_dramas 方法"):
            await adapter.get_category_dramas("都市")
    
    @pytest.mark.asyncio
    async def test_get_recommendations_not_implemented(self, adapter):
        """测试推荐未实现"""
        with pytest.raises(NotImplementedError, match="请实现 get_recommendations 方法"):
            await adapter.get_recommendations()
    
    @pytest.mark.asyncio
    async def test_get_episodes_not_implemented(self, adapter):
        """测试剧集未实现"""
        with pytest.raises(NotImplementedError, match="请实现 get_episodes 方法"):
            await adapter.get_episodes("drama_001")
    
    @pytest.mark.asyncio
    async def test_get_video_url_not_implemented(self, adapter):
        """测试视频地址未实现"""
        with pytest.raises(NotImplementedError, match="请实现 get_video_url 方法"):
            await adapter.get_video_url("video_001")


class TestTemplateAdapterRateLimit:
    """测试限流功能"""
    
    @pytest.fixture
    def adapter(self):
        adapter = TemplateAdapter(timeout=10000)
        adapter.RATE_LIMIT_WINDOW = 1.0
        adapter.RATE_LIMIT_MAX_REQUESTS = 3
        return adapter
    
    @pytest.mark.asyncio
    async def test_rate_limit_tracking(self, adapter):
        """测试限流时间戳记录"""
        await adapter._wait_for_rate_limit()
        assert len(adapter._request_timestamps) == 1
        
        await adapter._wait_for_rate_limit()
        assert len(adapter._request_timestamps) == 2
    
    @pytest.mark.asyncio
    async def test_rate_limit_cleanup(self, adapter):
        """测试过期时间戳清理"""
        adapter._request_timestamps.append(time.monotonic() - 10)
        adapter._request_timestamps.append(time.monotonic() - 10)
        
        await adapter._wait_for_rate_limit()
        assert len(adapter._request_timestamps) == 1
    
    @pytest.mark.asyncio
    async def test_request_method(self, adapter):
        """测试请求方法（模拟）"""
        import aiohttp
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='{"data": "test"}')
        
        async def mock_get(*args, **kwargs):
            return mock_response
        
        with patch.object(aiohttp, 'ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session.get = MagicMock(return_value=MagicMock(
                __aenter__=AsyncMock(return_value=mock_response),
                __aexit__=AsyncMock(return_value=None)
            ))
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_class.return_value = mock_session
            
            result = await adapter._request({"key": "value"})
            assert result == '{"data": "test"}'
    
    @pytest.mark.asyncio
    async def test_request_error(self, adapter):
        """测试请求错误"""
        import aiohttp
        
        mock_response = MagicMock()
        mock_response.status = 500
        
        with patch.object(aiohttp, 'ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session.get = MagicMock(return_value=MagicMock(
                __aenter__=AsyncMock(return_value=mock_response),
                __aexit__=AsyncMock(return_value=None)
            ))
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_class.return_value = mock_session
            
            with pytest.raises(Exception, match="HTTP 500"):
                await adapter._request({})
