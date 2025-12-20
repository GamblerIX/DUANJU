"""搜索服务完整测试"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock


class TestSearchServiceLogicFull:
    """搜索服务逻辑测试"""
    
    def test_blank_keyword_detection(self):
        """测试空白关键词检测"""
        from src.utils.string_utils import is_blank
        
        assert is_blank("") is True
        assert is_blank("   ") is True
        assert is_blank(None) is True
        assert is_blank("test") is False
    
    def test_cache_key_generation(self):
        """测试缓存键生成"""
        from src.data.cache_manager import CacheManager
        
        key = CacheManager.generate_key("search", "测试", "1")
        # 缓存键是 MD5 哈希值
        assert len(key) == 32  # MD5 哈希长度
        
        # 相同参数应生成相同的键
        key2 = CacheManager.generate_key("search", "测试", "1")
        assert key == key2
        
        # 不同参数应生成不同的键
        key3 = CacheManager.generate_key("search", "测试", "2")
        assert key != key3


class TestSearchServiceMock:
    """搜索服务 Mock 测试"""
    
    @patch('src.services.search_service.get_current_provider')
    @patch('src.services.search_service.AsyncWorker')
    def test_search_service_init(self, mock_worker, mock_provider):
        """测试搜索服务初始化"""
        from src.services.search_service import SearchService
        from src.data.api_client import ApiClient
        from src.data.cache_manager import CacheManager
        
        api_client = MagicMock(spec=ApiClient)
        cache = MagicMock(spec=CacheManager)
        
        service = SearchService(api_client, cache)
        
        assert service._is_searching is False
        assert service._current_keyword == ""
        assert service._current_worker is None
    
    @patch('src.services.search_service.get_current_provider')
    @patch('src.services.search_service.AsyncWorker')
    def test_search_blank_keyword(self, mock_worker, mock_provider):
        """测试空白关键词搜索"""
        from src.services.search_service import SearchService
        from src.data.api_client import ApiClient
        from src.data.cache_manager import CacheManager
        
        api_client = MagicMock(spec=ApiClient)
        cache = MagicMock(spec=CacheManager)
        
        service = SearchService(api_client, cache)
        service.search_started = MagicMock()
        
        service.search("")
        
        # 空白关键词不应触发搜索
        service.search_started.emit.assert_not_called()
    
    @patch('src.services.search_service.get_current_provider')
    @patch('src.services.search_service.AsyncWorker')
    def test_search_with_cache_hit(self, mock_worker, mock_provider):
        """测试缓存命中"""
        from src.services.search_service import SearchService
        from src.data.api_client import ApiClient
        from src.data.cache_manager import CacheManager
        import json
        
        api_client = MagicMock(spec=ApiClient)
        cache = MagicMock(spec=CacheManager)
        cache.get.return_value = json.dumps({
            "code": 200,
            "msg": "success",
            "page": 1,
            "data": []
        })
        
        service = SearchService(api_client, cache)
        service.search_started = MagicMock()
        service.search_completed = MagicMock()
        
        service.search("测试")
        
        # 缓存命中时不应创建 worker
        mock_worker.assert_not_called()
        service.search_completed.emit.assert_called_once()
    
    @patch('src.services.search_service.get_current_provider')
    @patch('src.services.search_service.AsyncWorker')
    def test_search_with_cache_miss(self, mock_worker_class, mock_provider):
        """测试缓存未命中"""
        from src.services.search_service import SearchService
        from src.data.api_client import ApiClient
        from src.data.cache_manager import CacheManager
        
        api_client = MagicMock(spec=ApiClient)
        cache = MagicMock(spec=CacheManager)
        cache.get.return_value = None
        
        mock_worker = MagicMock()
        mock_worker_class.return_value = mock_worker
        
        service = SearchService(api_client, cache)
        service.search_started = MagicMock()
        
        service.search("测试")
        
        # 缓存未命中时应创建 worker
        mock_worker_class.assert_called_once()
        mock_worker.start.assert_called_once()
    
    @patch('src.services.search_service.get_current_provider')
    @patch('src.services.search_service.AsyncWorker')
    def test_is_searching(self, mock_worker, mock_provider):
        """测试搜索状态"""
        from src.services.search_service import SearchService
        from src.data.api_client import ApiClient
        from src.data.cache_manager import CacheManager
        
        api_client = MagicMock(spec=ApiClient)
        cache = MagicMock(spec=CacheManager)
        cache.get.return_value = None
        
        service = SearchService(api_client, cache)
        
        assert service.is_searching() is False
        
        service.search("测试")
        
        assert service.is_searching() is True
    
    @patch('src.services.search_service.get_current_provider')
    @patch('src.services.search_service.AsyncWorker')
    def test_current_keyword(self, mock_worker, mock_provider):
        """测试当前关键词"""
        from src.services.search_service import SearchService
        from src.data.api_client import ApiClient
        from src.data.cache_manager import CacheManager
        
        api_client = MagicMock(spec=ApiClient)
        cache = MagicMock(spec=CacheManager)
        cache.get.return_value = None
        
        service = SearchService(api_client, cache)
        
        assert service.current_keyword == ""
        
        service.search("  测试关键词  ")
        
        assert service.current_keyword == "测试关键词"
    
    @patch('src.services.search_service.get_current_provider')
    @patch('src.services.search_service.AsyncWorker')
    def test_cancel_search(self, mock_worker_class, mock_provider):
        """测试取消搜索"""
        from src.services.search_service import SearchService
        from src.data.api_client import ApiClient
        from src.data.cache_manager import CacheManager
        
        api_client = MagicMock(spec=ApiClient)
        cache = MagicMock(spec=CacheManager)
        cache.get.return_value = None
        
        mock_worker = MagicMock()
        mock_worker.isRunning.return_value = True
        mock_worker_class.return_value = mock_worker
        
        service = SearchService(api_client, cache)
        service.search("测试")
        
        service.cancel_search()
        
        assert service._is_searching is False
        mock_worker.terminate.assert_called_once()
        mock_worker.wait.assert_called_once()
    
    @patch('src.services.search_service.get_current_provider')
    @patch('src.services.search_service.AsyncWorker')
    def test_on_search_result(self, mock_worker, mock_provider):
        """测试搜索结果处理"""
        from src.services.search_service import SearchService
        from src.data.api_client import ApiClient
        from src.data.cache_manager import CacheManager
        from src.core.models import SearchResult
        
        api_client = MagicMock(spec=ApiClient)
        cache = MagicMock(spec=CacheManager)
        
        service = SearchService(api_client, cache)
        service._is_searching = True
        service.search_completed = MagicMock()
        
        result = SearchResult(code=200, msg="success", data=[], page=1)
        service._on_search_result(result)
        
        assert service._is_searching is False
        service.search_completed.emit.assert_called_once_with(result)
    
    @patch('src.services.search_service.get_current_provider')
    @patch('src.services.search_service.AsyncWorker')
    def test_on_search_result_not_searching(self, mock_worker, mock_provider):
        """测试非搜索状态下的结果处理"""
        from src.services.search_service import SearchService
        from src.data.api_client import ApiClient
        from src.data.cache_manager import CacheManager
        from src.core.models import SearchResult
        
        api_client = MagicMock(spec=ApiClient)
        cache = MagicMock(spec=CacheManager)
        
        service = SearchService(api_client, cache)
        service._is_searching = False
        service.search_completed = MagicMock()
        
        result = SearchResult(code=200, msg="success", data=[], page=1)
        service._on_search_result(result)
        
        # 非搜索状态下不应发送信号
        service.search_completed.emit.assert_not_called()
    
    @patch('src.services.search_service.get_current_provider')
    @patch('src.services.search_service.AsyncWorker')
    def test_on_search_error(self, mock_worker, mock_provider):
        """测试搜索错误处理"""
        from src.services.search_service import SearchService
        from src.data.api_client import ApiClient
        from src.data.cache_manager import CacheManager
        
        api_client = MagicMock(spec=ApiClient)
        cache = MagicMock(spec=CacheManager)
        
        service = SearchService(api_client, cache)
        service._is_searching = True
        service.search_error = MagicMock()
        
        error = Exception("搜索失败")
        service._on_search_error(error)
        
        assert service._is_searching is False
        service.search_error.emit.assert_called_once()


class TestSearchServiceAsync:
    """搜索服务异步测试"""
    
    @pytest.mark.asyncio
    @patch('src.services.search_service.get_current_provider')
    async def test_do_search_with_provider(self, mock_get_provider):
        """测试使用 Provider 搜索"""
        from src.services.search_service import SearchService
        from src.data.api_client import ApiClient
        from src.data.cache_manager import CacheManager
        from src.core.models import SearchResult
        
        mock_provider = MagicMock()
        mock_provider.info.id = "test"
        mock_provider.search = AsyncMock(return_value=SearchResult(
            code=200, msg="success", data=[], page=1
        ))
        mock_get_provider.return_value = mock_provider
        
        api_client = MagicMock(spec=ApiClient)
        cache = MagicMock(spec=CacheManager)
        
        service = SearchService(api_client, cache)
        result = await service._do_search("测试", 1, "cache_key")
        
        assert result.code == 200
        mock_provider.search.assert_called_once_with("测试", 1)
    
    @pytest.mark.asyncio
    @patch('src.services.search_service.get_current_provider')
    async def test_do_search_without_provider(self, mock_get_provider):
        """测试无 Provider 时的搜索"""
        from src.services.search_service import SearchService
        from src.data.api_client import ApiClient
        from src.data.cache_manager import CacheManager
        from src.core.models import ApiResponse
        import json
        
        mock_get_provider.return_value = None
        
        api_client = MagicMock(spec=ApiClient)
        api_client.get = AsyncMock(return_value=ApiResponse(
            success=True,
            status_code=200,
            body=json.dumps({
                "code": 200,
                "msg": "success",
                "page": 1,
                "data": []
            })
        ))
        
        cache = MagicMock(spec=CacheManager)
        
        service = SearchService(api_client, cache)
        result = await service._do_search("测试", 1, "cache_key")
        
        assert result.code == 200
        api_client.get.assert_called_once()
