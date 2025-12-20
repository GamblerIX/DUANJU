"""分类服务测试

测试 src/services/category_service.py 中的分类服务。
"""
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
from unittest.mock import MagicMock, patch, AsyncMock
import json
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.models import CategoryResult, DramaInfo, ApiError


class TestCategoryServiceLogic:
    """分类服务逻辑测试（不依赖 Qt）"""
    
    def test_default_categories(self):
        """测试默认分类列表"""
        # 从服务中获取默认分类
        CATEGORIES = [
            "推荐榜", "新剧", "逆袭", "霸总", "现代言情", "打脸虐渣", 
            "豪门恩怨", "神豪", "马甲", "都市日常", "战神归来", "小人物", 
            "女性成长", "大女主", "穿越", "都市修仙", "强者回归", "亲情", 
            "古装", "重生", "闪婚", "赘婿逆袭", "虐恋", "追妻", "天下无敌", 
            "家庭伦理", "萌宝", "古风权谋", "职场", "奇幻脑洞", "异能", 
            "无敌神医", "古风言情", "传承觉醒", "现言甜宠", "奇幻爱情", 
            "乡村", "历史古代", "王妃", "高手下山", "娱乐圈", "强强联合", 
            "破镜重圆", "暗恋成真", "民国", "欢喜冤家", "系统", "真假千金", 
            "龙王", "校园", "穿书", "女帝", "团宠", "年代爱情", "玄幻仙侠", 
            "青梅竹马", "悬疑推理", "皇后", "替身", "大叔", "喜剧", "剧情"
        ]
        
        assert len(CATEGORIES) > 0
        assert "推荐榜" in CATEGORIES
        assert "古装" in CATEGORIES
        assert "穿越" in CATEGORIES
    
    def test_category_result_structure(self):
        """测试分类结果结构"""
        dramas = [
            DramaInfo(book_id="1", title="Drama 1", cover="url1"),
            DramaInfo(book_id="2", title="Drama 2", cover="url2"),
        ]
        
        result = CategoryResult(
            code=200,
            category="都市",
            data=dramas,
            offset=1
        )
        
        assert result.code == 200
        assert result.category == "都市"
        assert len(result.data) == 2
        assert result.offset == 1
    
    def test_category_cache_key_generation(self):
        """测试分类缓存键生成"""
        from src.data.cache_manager import CacheManager
        
        key1 = CacheManager.generate_key("category", "都市", "1")
        key2 = CacheManager.generate_key("category", "都市", "1")
        key3 = CacheManager.generate_key("category", "古装", "1")
        
        assert key1 == key2
        assert key1 != key3
    
    def test_category_result_parsing(self):
        """测试分类结果解析"""
        from src.data.response_parser import ResponseParser
        
        json_str = json.dumps({
            "code": 200,
            "data": [
                {
                    "book_id": "123",
                    "title": "测试短剧",
                    "cover": "url",
                    "episode_cnt": 20,
                    "video_desc": "描述",
                    "sub_title": "都市",
                    "play_cnt": 1000
                }
            ]
        })
        
        result = ResponseParser.parse_category_result(json_str, "都市")
        
        assert result.code == 200
        assert result.category == "都市"
        assert len(result.data) == 1
        assert result.data[0].book_id == "123"
    
    def test_recommendations_parsing(self):
        """测试推荐内容解析"""
        from src.data.response_parser import ResponseParser
        
        json_str = json.dumps({
            "code": 200,
            "data": [
                {
                    "hot": 10000,
                    "book_data": {
                        "book_id": "123",
                        "book_name": "推荐短剧",
                        "thumb_url": "url",
                        "serial_count": 20,
                        "category": "甜宠"
                    }
                }
            ]
        })
        
        dramas = ResponseParser.parse_recommendations(json_str)
        
        assert len(dramas) == 1
        assert dramas[0].book_id == "123"
        assert dramas[0].title == "推荐短剧"
        assert dramas[0].play_cnt == 10000


class TestCategoryServiceMock:
    """分类服务 Mock 测试"""
    
    @pytest.fixture
    def mock_api_client(self):
        """模拟 API 客户端"""
        client = MagicMock()
        client.get = AsyncMock()
        return client
    
    @pytest.fixture
    def mock_cache(self):
        """模拟缓存管理器"""
        cache = MagicMock()
        cache.get = MagicMock(return_value=None)
        cache.set = MagicMock()
        return cache
    
    @pytest.fixture
    def mock_provider(self):
        """模拟数据提供者"""
        provider = MagicMock()
        provider.get_categories = AsyncMock(return_value=["都市", "甜宠", "古装"])
        provider.get_category_dramas = AsyncMock(return_value=CategoryResult(
            code=200, category="都市", data=[], offset=1
        ))
        provider.get_recommendations = AsyncMock(return_value=[])
        return provider
    
    @pytest.mark.asyncio
    async def test_fetch_categories_from_provider(self, mock_provider):
        """测试从提供者获取分类"""
        categories = await mock_provider.get_categories()
        
        assert len(categories) == 3
        assert "都市" in categories
        mock_provider.get_categories.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fetch_category_dramas_from_provider(self, mock_provider):
        """测试从提供者获取分类短剧"""
        result = await mock_provider.get_category_dramas("都市", 1)
        
        assert result.code == 200
        assert result.category == "都市"
        mock_provider.get_category_dramas.assert_called_once_with("都市", 1)
    
    @pytest.mark.asyncio
    async def test_fetch_recommendations_from_provider(self, mock_provider):
        """测试从提供者获取推荐"""
        dramas = await mock_provider.get_recommendations()
        
        assert isinstance(dramas, list)
        mock_provider.get_recommendations.assert_called_once()
    
    def test_cache_hit_for_category(self, mock_cache):
        """测试分类缓存命中"""
        cached_data = json.dumps({
            "code": 200,
            "data": [{"book_id": "1", "title": "Test", "cover": "url", "episode_cnt": 10}]
        })
        mock_cache.get.return_value = cached_data
        
        # 验证缓存返回数据
        result = mock_cache.get("category_key")
        assert result == cached_data
    
    def test_cache_miss_for_category(self, mock_cache):
        """测试分类缓存未命中"""
        mock_cache.get.return_value = None
        
        result = mock_cache.get("category_key")
        assert result is None


class TestCategoryPagination:
    """分类分页测试"""
    
    def test_pagination_offset(self):
        """测试分页偏移"""
        offsets = [1, 2, 3, 4, 5]
        
        for offset in offsets:
            result = CategoryResult(
                code=200,
                category="都市",
                data=[],
                offset=offset
            )
            assert result.offset == offset
    
    def test_pagination_cache_keys(self):
        """测试分页缓存键不同"""
        from src.data.cache_manager import CacheManager
        
        keys = [
            CacheManager.generate_key("category", "都市", str(i))
            for i in range(1, 6)
        ]
        
        # 所有键应该不同
        assert len(set(keys)) == 5




# ============================================================
# From: test_category_service_full.py
# ============================================================
class TestCategoryServiceMock_Full:
    """分类服务 Mock 测试"""
    
    @patch('src.services.category_service.get_current_provider')
    @patch('src.services.category_service.AsyncWorker')
    def test_category_service_init(self, mock_worker, mock_provider):
        """测试分类服务初始化"""
        from src.services.category_service import CategoryService
        from src.data.api_client import ApiClient
        from src.data.cache_manager import CacheManager
        
        api_client = MagicMock(spec=ApiClient)
        cache = MagicMock(spec=CacheManager)
        
        service = CategoryService(api_client, cache)
        
        assert service._is_loading_category is False
        assert service._is_loading_recommendations is False
        assert service._category_worker is None
        assert service._recommendations_worker is None
    
    @patch('src.services.category_service.get_current_provider')
    @patch('src.services.category_service.AsyncWorker')
    def test_fetch_categories_no_provider(self, mock_worker, mock_get_provider):
        """测试无 Provider 时获取分类"""
        from src.services.category_service import CategoryService
        from src.data.api_client import ApiClient
        from src.data.cache_manager import CacheManager
        
        mock_get_provider.return_value = None
        
        api_client = MagicMock(spec=ApiClient)
        cache = MagicMock(spec=CacheManager)
        
        service = CategoryService(api_client, cache)
        service.categories_loaded = MagicMock()
        
        service.fetch_categories()
        
        service.categories_loaded.emit.assert_called_once()
        args = service.categories_loaded.emit.call_args[0][0]
        assert "推荐榜" in args
    
    @patch('src.services.category_service.get_current_provider')
    @patch('src.services.category_service.AsyncWorker')
    def test_fetch_categories_with_provider(self, mock_worker_class, mock_get_provider):
        """测试有 Provider 时获取分类"""
        from src.services.category_service import CategoryService
        from src.data.api_client import ApiClient
        from src.data.cache_manager import CacheManager
        
        mock_provider = MagicMock()
        mock_get_provider.return_value = mock_provider
        
        mock_worker = MagicMock()
        mock_worker_class.return_value = mock_worker
        
        api_client = MagicMock(spec=ApiClient)
        cache = MagicMock(spec=CacheManager)
        
        service = CategoryService(api_client, cache)
        
        service.fetch_categories()
        
        mock_worker_class.assert_called_once()
        mock_worker.start.assert_called_once()
    
    @patch('src.services.category_service.get_current_provider')
    @patch('src.services.category_service.AsyncWorker')
    def test_fetch_category_dramas_cache_hit(self, mock_worker, mock_provider):
        """测试分类短剧缓存命中"""
        from src.services.category_service import CategoryService
        from src.data.api_client import ApiClient
        from src.data.cache_manager import CacheManager
        
        api_client = MagicMock(spec=ApiClient)
        cache = MagicMock(spec=CacheManager)
        cache.get.return_value = json.dumps({
            "code": 200,
            "data": []
        })
        
        service = CategoryService(api_client, cache)
        service.loading_started = MagicMock()
        service.dramas_loaded = MagicMock()
        
        service.fetch_category_dramas("霸总", 1)
        
        # 缓存命中时不应创建 worker
        mock_worker.assert_not_called()
        service.dramas_loaded.emit.assert_called_once()
    
    @patch('src.services.category_service.get_current_provider')
    @patch('src.services.category_service.AsyncWorker')
    def test_fetch_category_dramas_cache_miss(self, mock_worker_class, mock_provider):
        """测试分类短剧缓存未命中"""
        from src.services.category_service import CategoryService
        from src.data.api_client import ApiClient
        from src.data.cache_manager import CacheManager
        
        api_client = MagicMock(spec=ApiClient)
        cache = MagicMock(spec=CacheManager)
        cache.get.return_value = None
        
        mock_worker = MagicMock()
        mock_worker_class.return_value = mock_worker
        
        service = CategoryService(api_client, cache)
        service.loading_started = MagicMock()
        
        service.fetch_category_dramas("霸总", 1)
        
        assert service._is_loading_category is True
        mock_worker_class.assert_called_once()
        mock_worker.start.assert_called_once()
    
    @patch('src.services.category_service.get_current_provider')
    @patch('src.services.category_service.AsyncWorker')
    def test_fetch_recommendations_cache_hit(self, mock_worker, mock_provider):
        """测试推荐内容缓存命中"""
        from src.services.category_service import CategoryService
        from src.data.api_client import ApiClient
        from src.data.cache_manager import CacheManager
        
        api_client = MagicMock(spec=ApiClient)
        cache = MagicMock(spec=CacheManager)
        cache.get.return_value = json.dumps({
            "code": 200,
            "data": []
        })
        
        service = CategoryService(api_client, cache)
        service.recommendations_loaded = MagicMock()
        
        service.fetch_recommendations()
        
        # 缓存命中时不应创建 worker
        mock_worker.assert_not_called()
        service.recommendations_loaded.emit.assert_called_once()
    
    @patch('src.services.category_service.get_current_provider')
    @patch('src.services.category_service.AsyncWorker')
    def test_fetch_recommendations_force_refresh(self, mock_worker_class, mock_provider):
        """测试强制刷新推荐内容"""
        from src.services.category_service import CategoryService
        from src.data.api_client import ApiClient
        from src.data.cache_manager import CacheManager
        
        api_client = MagicMock(spec=ApiClient)
        cache = MagicMock(spec=CacheManager)
        
        mock_worker = MagicMock()
        mock_worker_class.return_value = mock_worker
        
        service = CategoryService(api_client, cache)
        
        service.fetch_recommendations(force_refresh=True)
        
        cache.remove.assert_called_once_with("recommendations")
        mock_worker_class.assert_called_once()
    
    @patch('src.services.category_service.get_current_provider')
    @patch('src.services.category_service.AsyncWorker')
    def test_cancel(self, mock_worker_class, mock_provider):
        """测试取消所有请求"""
        from src.services.category_service import CategoryService
        from src.data.api_client import ApiClient
        from src.data.cache_manager import CacheManager
        
        api_client = MagicMock(spec=ApiClient)
        cache = MagicMock(spec=CacheManager)
        cache.get.return_value = None
        
        mock_worker = MagicMock()
        mock_worker.isRunning.return_value = True
        mock_worker_class.return_value = mock_worker
        
        service = CategoryService(api_client, cache)
        service.fetch_category_dramas("霸总", 1)
        
        service.cancel()
        
        assert service._is_loading_category is False
        mock_worker.terminate.assert_called()
    
    @patch('src.services.category_service.get_current_provider')
    @patch('src.services.category_service.AsyncWorker')
    def test_is_loading_property(self, mock_worker, mock_provider):
        """测试加载状态属性"""
        from src.services.category_service import CategoryService
        from src.data.api_client import ApiClient
        from src.data.cache_manager import CacheManager
        
        api_client = MagicMock(spec=ApiClient)
        cache = MagicMock(spec=CacheManager)
        
        service = CategoryService(api_client, cache)
        
        assert service.is_loading is False
        
        service._is_loading_category = True
        assert service.is_loading is True
        
        service._is_loading_category = False
        service._is_loading_recommendations = True
        assert service.is_loading is True
    
    @patch('src.services.category_service.get_current_provider')
    @patch('src.services.category_service.AsyncWorker')
    def test_on_dramas_result(self, mock_worker, mock_provider):
        """测试分类短剧结果处理"""
        from src.services.category_service import CategoryService
        from src.data.api_client import ApiClient
        from src.data.cache_manager import CacheManager
        from src.core.models import CategoryResult
        
        api_client = MagicMock(spec=ApiClient)
        cache = MagicMock(spec=CacheManager)
        
        service = CategoryService(api_client, cache)
        service._is_loading_category = True
        service.dramas_loaded = MagicMock()
        
        result = CategoryResult(code=200, category="霸总", data=[], offset=1)
        service._on_dramas_result(("dramas", result))
        
        assert service._is_loading_category is False
        service.dramas_loaded.emit.assert_called_once_with(result)
    
    @patch('src.services.category_service.get_current_provider')
    @patch('src.services.category_service.AsyncWorker')
    def test_on_dramas_error(self, mock_worker, mock_provider):
        """测试分类短剧错误处理"""
        from src.services.category_service import CategoryService
        from src.data.api_client import ApiClient
        from src.data.cache_manager import CacheManager
        
        api_client = MagicMock(spec=ApiClient)
        cache = MagicMock(spec=CacheManager)
        
        service = CategoryService(api_client, cache)
        service._is_loading_category = True
        service.error = MagicMock()
        
        error = Exception("获取失败")
        service._on_dramas_error(error)
        
        assert service._is_loading_category is False
        service.error.emit.assert_called_once()
    
    @patch('src.services.category_service.get_current_provider')
    @patch('src.services.category_service.AsyncWorker')
    def test_on_recommendations_result(self, mock_worker, mock_provider):
        """测试推荐内容结果处理"""
        from src.services.category_service import CategoryService
        from src.data.api_client import ApiClient
        from src.data.cache_manager import CacheManager
        
        api_client = MagicMock(spec=ApiClient)
        cache = MagicMock(spec=CacheManager)
        
        service = CategoryService(api_client, cache)
        service._is_loading_recommendations = True
        service.recommendations_loaded = MagicMock()
        
        dramas = []
        service._on_recommendations_result(("recommendations", dramas))
        
        assert service._is_loading_recommendations is False
        service.recommendations_loaded.emit.assert_called_once_with(dramas)


class TestCategoryServiceAsync:
    """分类服务异步测试"""
    
    @pytest.mark.asyncio
    @patch('src.services.category_service.get_current_provider')
    async def test_do_fetch_categories_with_provider(self, mock_get_provider):
        """测试使用 Provider 获取分类"""
        from src.services.category_service import CategoryService
        from src.data.api_client import ApiClient
        from src.data.cache_manager import CacheManager
        
        mock_provider = MagicMock()
        mock_provider.get_categories = AsyncMock(return_value=["分类1", "分类2"])
        mock_get_provider.return_value = mock_provider
        
        api_client = MagicMock(spec=ApiClient)
        cache = MagicMock(spec=CacheManager)
        
        service = CategoryService(api_client, cache)
        result = await service._do_fetch_categories()
        
        assert result == ["分类1", "分类2"]
        mock_provider.get_categories.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.category_service.get_current_provider')
    async def test_do_fetch_categories_without_provider(self, mock_get_provider):
        """测试无 Provider 时获取分类"""
        from src.services.category_service import CategoryService
        from src.data.api_client import ApiClient
        from src.data.cache_manager import CacheManager
        
        mock_get_provider.return_value = None
        
        api_client = MagicMock(spec=ApiClient)
        cache = MagicMock(spec=CacheManager)
        
        service = CategoryService(api_client, cache)
        result = await service._do_fetch_categories()
        
        assert "推荐榜" in result
    
    @pytest.mark.asyncio
    @patch('src.services.category_service.get_current_provider')
    async def test_do_fetch_category_dramas_with_provider(self, mock_get_provider):
        """测试使用 Provider 获取分类短剧"""
        from src.services.category_service import CategoryService
        from src.data.api_client import ApiClient
        from src.data.cache_manager import CacheManager
        from src.core.models import CategoryResult
        
        mock_provider = MagicMock()
        mock_provider.get_category_dramas = AsyncMock(return_value=CategoryResult(
            code=200, category="霸总", data=[], offset=1
        ))
        mock_get_provider.return_value = mock_provider
        
        api_client = MagicMock(spec=ApiClient)
        cache = MagicMock(spec=CacheManager)
        
        service = CategoryService(api_client, cache)
        result = await service._do_fetch_category_dramas("霸总", 1, "cache_key")
        
        assert result[0] == "dramas"
        assert result[1].code == 200
        mock_provider.get_category_dramas.assert_called_once_with("霸总", 1)
    
    @pytest.mark.asyncio
    @patch('src.services.category_service.get_current_provider')
    async def test_do_fetch_recommendations_with_provider(self, mock_get_provider):
        """测试使用 Provider 获取推荐"""
        from src.services.category_service import CategoryService
        from src.data.api_client import ApiClient
        from src.data.cache_manager import CacheManager
        
        mock_provider = MagicMock()
        mock_provider.get_recommendations = AsyncMock(return_value=[])
        mock_get_provider.return_value = mock_provider
        
        api_client = MagicMock(spec=ApiClient)
        cache = MagicMock(spec=CacheManager)
        
        service = CategoryService(api_client, cache)
        result = await service._do_fetch_recommendations("cache_key")
        
        assert result[0] == "recommendations"
        mock_provider.get_recommendations.assert_called_once()
