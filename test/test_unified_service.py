"""统一服务测试"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import json


class TestUnifiedServiceMock:
    """统一服务 Mock 测试"""
    
    @patch('src.services.unified_service.get_current_provider')
    @patch('src.services.unified_service.get_registry')
    @patch('src.services.unified_service.AsyncWorker')
    def test_unified_service_init(self, mock_worker, mock_registry, mock_provider):
        """测试统一服务初始化"""
        from src.services.unified_service import UnifiedService
        from src.data.cache_manager import CacheManager
        
        cache = MagicMock(spec=CacheManager)
        
        service = UnifiedService(cache)
        
        assert service._is_loading is False
        assert service._current_worker is None
    
    @patch('src.services.unified_service.get_current_provider')
    @patch('src.services.unified_service.get_registry')
    @patch('src.services.unified_service.AsyncWorker')
    def test_search_blank_keyword(self, mock_worker, mock_registry, mock_provider):
        """测试空白关键词搜索"""
        from src.services.unified_service import UnifiedService
        from src.data.cache_manager import CacheManager
        
        cache = MagicMock(spec=CacheManager)
        
        service = UnifiedService(cache)
        service.search_started = MagicMock()
        
        service.search("")
        
        service.search_started.emit.assert_not_called()
    
    @patch('src.services.unified_service.get_current_provider')
    @patch('src.services.unified_service.get_registry')
    @patch('src.services.unified_service.AsyncWorker')
    def test_search_with_cache_miss(self, mock_worker_class, mock_registry, mock_provider):
        """测试搜索缓存未命中"""
        from src.services.unified_service import UnifiedService
        from src.data.cache_manager import CacheManager
        
        cache = MagicMock(spec=CacheManager)
        cache.get.return_value = None
        
        mock_worker = MagicMock()
        mock_worker_class.return_value = mock_worker
        
        service = UnifiedService(cache)
        service.search_started = MagicMock()
        
        service.search("测试")
        
        assert service._is_loading is True
        mock_worker_class.assert_called_once()
        mock_worker.start.assert_called_once()
    
    @patch('src.services.unified_service.get_current_provider')
    @patch('src.services.unified_service.get_registry')
    @patch('src.services.unified_service.AsyncWorker')
    def test_fetch_categories(self, mock_worker_class, mock_registry, mock_provider):
        """测试获取分类"""
        from src.services.unified_service import UnifiedService
        from src.data.cache_manager import CacheManager
        
        cache = MagicMock(spec=CacheManager)
        
        mock_worker = MagicMock()
        mock_worker_class.return_value = mock_worker
        
        service = UnifiedService(cache)
        
        service.fetch_categories()
        
        mock_worker_class.assert_called_once()
        mock_worker.start.assert_called_once()
    
    @patch('src.services.unified_service.get_current_provider')
    @patch('src.services.unified_service.get_registry')
    @patch('src.services.unified_service.AsyncWorker')
    def test_fetch_category_dramas(self, mock_worker_class, mock_registry, mock_provider):
        """测试获取分类短剧"""
        from src.services.unified_service import UnifiedService
        from src.data.cache_manager import CacheManager
        
        cache = MagicMock(spec=CacheManager)
        
        mock_worker = MagicMock()
        mock_worker_class.return_value = mock_worker
        
        service = UnifiedService(cache)
        service.loading_started = MagicMock()
        
        service.fetch_category_dramas("霸总", 1)
        
        assert service._is_loading is True
        service.loading_started.emit.assert_called_once()
        mock_worker.start.assert_called_once()
    
    @patch('src.services.unified_service.get_current_provider')
    @patch('src.services.unified_service.get_registry')
    @patch('src.services.unified_service.AsyncWorker')
    def test_fetch_recommendations(self, mock_worker_class, mock_registry, mock_provider):
        """测试获取推荐"""
        from src.services.unified_service import UnifiedService
        from src.data.cache_manager import CacheManager
        
        cache = MagicMock(spec=CacheManager)
        
        mock_worker = MagicMock()
        mock_worker_class.return_value = mock_worker
        
        service = UnifiedService(cache)
        
        service.fetch_recommendations()
        
        assert service._is_loading is True
        mock_worker.start.assert_called_once()
    
    @patch('src.services.unified_service.get_current_provider')
    @patch('src.services.unified_service.get_registry')
    @patch('src.services.unified_service.AsyncWorker')
    def test_fetch_episodes(self, mock_worker_class, mock_registry, mock_provider):
        """测试获取剧集"""
        from src.services.unified_service import UnifiedService
        from src.data.cache_manager import CacheManager
        
        cache = MagicMock(spec=CacheManager)
        
        mock_worker = MagicMock()
        mock_worker_class.return_value = mock_worker
        
        service = UnifiedService(cache)
        service.loading_started = MagicMock()
        
        service.fetch_episodes("drama_123")
        
        assert service._is_loading is True
        service.loading_started.emit.assert_called_once()
        mock_worker.start.assert_called_once()
    
    @patch('src.services.unified_service.get_current_provider')
    @patch('src.services.unified_service.get_registry')
    @patch('src.services.unified_service.AsyncWorker')
    def test_fetch_video_url(self, mock_worker_class, mock_registry, mock_provider):
        """测试获取视频地址"""
        from src.services.unified_service import UnifiedService
        from src.data.cache_manager import CacheManager
        
        cache = MagicMock(spec=CacheManager)
        
        mock_worker = MagicMock()
        mock_worker_class.return_value = mock_worker
        
        service = UnifiedService(cache)
        service.loading_started = MagicMock()
        
        service.fetch_video_url("episode_123", "1080p")
        
        assert service._is_loading is True
        service.loading_started.emit.assert_called_once()
        mock_worker.start.assert_called_once()
    
    @patch('src.services.unified_service.get_current_provider')
    @patch('src.services.unified_service.get_registry')
    @patch('src.services.unified_service.AsyncWorker')
    def test_switch_provider_success(self, mock_worker, mock_registry_func, mock_provider):
        """测试切换提供者成功"""
        from src.services.unified_service import UnifiedService
        from src.data.cache_manager import CacheManager
        
        mock_registry = MagicMock()
        mock_registry.set_current.return_value = True
        mock_registry_func.return_value = mock_registry
        
        cache = MagicMock(spec=CacheManager)
        
        service = UnifiedService(cache)
        service.provider_changed = MagicMock()
        
        result = service.switch_provider("new_provider")
        
        assert result is True
        cache.clear.assert_called_once()
        service.provider_changed.emit.assert_called_once_with("new_provider")
    
    @patch('src.services.unified_service.get_current_provider')
    @patch('src.services.unified_service.get_registry')
    @patch('src.services.unified_service.AsyncWorker')
    def test_switch_provider_failure(self, mock_worker, mock_registry_func, mock_provider):
        """测试切换提供者失败"""
        from src.services.unified_service import UnifiedService
        from src.data.cache_manager import CacheManager
        
        mock_registry = MagicMock()
        mock_registry.set_current.return_value = False
        mock_registry_func.return_value = mock_registry
        
        cache = MagicMock(spec=CacheManager)
        
        service = UnifiedService(cache)
        service.provider_changed = MagicMock()
        
        result = service.switch_provider("invalid_provider")
        
        assert result is False
        cache.clear.assert_not_called()
        service.provider_changed.emit.assert_not_called()
    
    @patch('src.services.unified_service.get_current_provider')
    @patch('src.services.unified_service.get_registry')
    @patch('src.services.unified_service.AsyncWorker')
    def test_get_available_providers(self, mock_worker, mock_registry_func, mock_provider):
        """测试获取可用提供者"""
        from src.services.unified_service import UnifiedService
        from src.data.cache_manager import CacheManager
        
        mock_registry = MagicMock()
        mock_registry.list_provider_ids.return_value = ["provider1", "provider2"]
        mock_registry_func.return_value = mock_registry
        
        cache = MagicMock(spec=CacheManager)
        
        service = UnifiedService(cache)
        
        result = service.get_available_providers()
        
        assert result == ["provider1", "provider2"]
    
    @patch('src.services.unified_service.get_current_provider')
    @patch('src.services.unified_service.get_registry')
    @patch('src.services.unified_service.AsyncWorker')
    def test_cancel(self, mock_worker_class, mock_registry, mock_provider):
        """测试取消操作"""
        from src.services.unified_service import UnifiedService
        from src.data.cache_manager import CacheManager
        
        cache = MagicMock(spec=CacheManager)
        cache.get.return_value = None
        
        mock_worker = MagicMock()
        mock_worker.isRunning.return_value = True
        mock_worker_class.return_value = mock_worker
        
        service = UnifiedService(cache)
        service.search("测试")
        
        service.cancel()
        
        assert service._is_loading is False
        mock_worker.terminate.assert_called_once()
    
    @patch('src.services.unified_service.get_current_provider')
    @patch('src.services.unified_service.get_registry')
    @patch('src.services.unified_service.AsyncWorker')
    def test_is_loading_property(self, mock_worker, mock_registry, mock_provider):
        """测试加载状态属性"""
        from src.services.unified_service import UnifiedService
        from src.data.cache_manager import CacheManager
        
        cache = MagicMock(spec=CacheManager)
        
        service = UnifiedService(cache)
        
        assert service.is_loading is False
        
        service._is_loading = True
        assert service.is_loading is True
    
    @patch('src.services.unified_service.get_current_provider')
    @patch('src.services.unified_service.get_registry')
    @patch('src.services.unified_service.AsyncWorker')
    def test_current_provider_id(self, mock_worker, mock_registry_func, mock_provider):
        """测试当前提供者 ID"""
        from src.services.unified_service import UnifiedService
        from src.data.cache_manager import CacheManager
        
        mock_registry = MagicMock()
        mock_registry.current_id = "test_provider"
        mock_registry_func.return_value = mock_registry
        
        cache = MagicMock(spec=CacheManager)
        
        service = UnifiedService(cache)
        
        assert service.current_provider_id == "test_provider"
    
    @patch('src.services.unified_service.get_current_provider')
    @patch('src.services.unified_service.get_registry')
    @patch('src.services.unified_service.AsyncWorker')
    def test_on_search_result(self, mock_worker, mock_registry, mock_provider):
        """测试搜索结果处理"""
        from src.services.unified_service import UnifiedService
        from src.data.cache_manager import CacheManager
        from src.core.models import SearchResult
        
        cache = MagicMock(spec=CacheManager)
        
        service = UnifiedService(cache)
        service._is_loading = True
        service.search_completed = MagicMock()
        
        result = SearchResult(code=200, msg="success", data=[], page=1)
        service._on_search_result(result)
        
        assert service._is_loading is False
        service.search_completed.emit.assert_called_once_with(result)
    
    @patch('src.services.unified_service.get_current_provider')
    @patch('src.services.unified_service.get_registry')
    @patch('src.services.unified_service.AsyncWorker')
    def test_on_search_error(self, mock_worker, mock_registry, mock_provider):
        """测试搜索错误处理"""
        from src.services.unified_service import UnifiedService
        from src.data.cache_manager import CacheManager
        
        cache = MagicMock(spec=CacheManager)
        
        service = UnifiedService(cache)
        service._is_loading = True
        service.search_error = MagicMock()
        
        error = Exception("搜索失败")
        service._on_search_error(error)
        
        assert service._is_loading is False
        service.search_error.emit.assert_called_once()
    
    @patch('src.services.unified_service.get_current_provider')
    @patch('src.services.unified_service.get_registry')
    @patch('src.services.unified_service.AsyncWorker')
    def test_on_error(self, mock_worker, mock_registry, mock_provider):
        """测试通用错误处理"""
        from src.services.unified_service import UnifiedService
        from src.data.cache_manager import CacheManager
        
        cache = MagicMock(spec=CacheManager)
        
        service = UnifiedService(cache)
        service._is_loading = True
        service.error = MagicMock()
        
        error = Exception("操作失败")
        service._on_error(error)
        
        assert service._is_loading is False
        service.error.emit.assert_called_once()


class TestUnifiedServiceAsync:
    """统一服务异步测试"""
    
    @pytest.mark.asyncio
    @patch('src.services.unified_service.get_current_provider')
    @patch('src.services.unified_service.get_registry')
    async def test_do_search(self, mock_registry, mock_get_provider):
        """测试异步搜索"""
        from src.services.unified_service import UnifiedService
        from src.data.cache_manager import CacheManager
        from src.core.models import SearchResult
        
        mock_provider = MagicMock()
        mock_provider.search = AsyncMock(return_value=SearchResult(
            code=200, msg="success", data=[], page=1
        ))
        mock_get_provider.return_value = mock_provider
        
        cache = MagicMock(spec=CacheManager)
        
        service = UnifiedService(cache)
        result = await service._do_search("测试", 1, "cache_key")
        
        assert result.code == 200
        mock_provider.search.assert_called_once_with("测试", 1)
    
    @pytest.mark.asyncio
    @patch('src.services.unified_service.get_current_provider')
    @patch('src.services.unified_service.get_registry')
    async def test_do_fetch_categories(self, mock_registry, mock_get_provider):
        """测试异步获取分类"""
        from src.services.unified_service import UnifiedService
        from src.data.cache_manager import CacheManager
        
        mock_provider = MagicMock()
        mock_provider.get_categories = AsyncMock(return_value=["分类1", "分类2"])
        mock_get_provider.return_value = mock_provider
        
        cache = MagicMock(spec=CacheManager)
        
        service = UnifiedService(cache)
        result = await service._do_fetch_categories()
        
        assert result == ["分类1", "分类2"]
    
    @pytest.mark.asyncio
    @patch('src.services.unified_service.get_current_provider')
    @patch('src.services.unified_service.get_registry')
    async def test_do_fetch_category_dramas(self, mock_registry, mock_get_provider):
        """测试异步获取分类短剧"""
        from src.services.unified_service import UnifiedService
        from src.data.cache_manager import CacheManager
        from src.core.models import CategoryResult
        
        mock_provider = MagicMock()
        mock_provider.get_category_dramas = AsyncMock(return_value=CategoryResult(
            code=200, category="霸总", data=[], offset=1
        ))
        mock_get_provider.return_value = mock_provider
        
        cache = MagicMock(spec=CacheManager)
        
        service = UnifiedService(cache)
        result = await service._do_fetch_category_dramas("霸总", 1)
        
        assert result.code == 200
    
    @pytest.mark.asyncio
    @patch('src.services.unified_service.get_current_provider')
    @patch('src.services.unified_service.get_registry')
    async def test_do_fetch_recommendations(self, mock_registry, mock_get_provider):
        """测试异步获取推荐"""
        from src.services.unified_service import UnifiedService
        from src.data.cache_manager import CacheManager
        
        mock_provider = MagicMock()
        mock_provider.get_recommendations = AsyncMock(return_value=[])
        mock_get_provider.return_value = mock_provider
        
        cache = MagicMock(spec=CacheManager)
        
        service = UnifiedService(cache)
        result = await service._do_fetch_recommendations()
        
        assert result == []
    
    @pytest.mark.asyncio
    @patch('src.services.unified_service.get_current_provider')
    @patch('src.services.unified_service.get_registry')
    async def test_do_fetch_episodes(self, mock_registry, mock_get_provider):
        """测试异步获取剧集"""
        from src.services.unified_service import UnifiedService
        from src.data.cache_manager import CacheManager
        from src.core.models import EpisodeList
        
        mock_provider = MagicMock()
        mock_provider.get_episodes = AsyncMock(return_value=EpisodeList(
            code=200, book_name="测试", episodes=[], total=0
        ))
        mock_get_provider.return_value = mock_provider
        
        cache = MagicMock(spec=CacheManager)
        
        service = UnifiedService(cache)
        result = await service._do_fetch_episodes("drama_123")
        
        assert result.code == 200
    
    @pytest.mark.asyncio
    @patch('src.services.unified_service.get_current_provider')
    @patch('src.services.unified_service.get_registry')
    async def test_do_fetch_video_url(self, mock_registry, mock_get_provider):
        """测试异步获取视频地址"""
        from src.services.unified_service import UnifiedService
        from src.data.cache_manager import CacheManager
        from src.core.models import VideoInfo
        
        mock_provider = MagicMock()
        mock_provider.get_video_url = AsyncMock(return_value=VideoInfo(
            code=200, url="http://example.com/video.m3u8"
        ))
        mock_get_provider.return_value = mock_provider
        
        cache = MagicMock(spec=CacheManager)
        
        service = UnifiedService(cache)
        result = await service._do_fetch_video_url("episode_123", "1080p")
        
        assert result.code == 200
    
    @pytest.mark.asyncio
    @patch('src.services.unified_service.get_current_provider')
    @patch('src.services.unified_service.get_registry')
    async def test_get_provider_raises_error(self, mock_registry, mock_get_provider):
        """测试无提供者时抛出错误"""
        from src.services.unified_service import UnifiedService
        from src.data.cache_manager import CacheManager
        
        mock_get_provider.return_value = None
        
        cache = MagicMock(spec=CacheManager)
        
        service = UnifiedService(cache)
        
        with pytest.raises(RuntimeError, match="没有可用的数据提供者"):
            service._get_provider()
