"""分类服务实现"""
from typing import Protocol, Optional, List
import json

from PySide6.QtCore import QObject, Signal

from ..core.models import CategoryResult, DramaInfo, ApiError
from ..utils.log_manager import get_logger
from ..utils.async_worker import AsyncWorker
from ..data.api_client import IApiClient
from ..data.response_parser import ResponseParser
from ..data.cache_manager import CacheManager
from ..data.providers.provider_registry import get_current_provider

logger = get_logger()


class ICategoryService(Protocol):
    """分类服务接口协议"""
    def fetch_categories(self) -> None: ...
    def fetch_category_dramas(self, category: str, offset: int = 1) -> None: ...
    def fetch_recommendations(self) -> None: ...
    def cancel(self) -> None: ...


class CategoryService(QObject):
    """分类服务实现"""
    
    categories_loaded = Signal(list)
    dramas_loaded = Signal(object)
    recommendations_loaded = Signal(list)
    error = Signal(object)
    loading_started = Signal()
    
    CACHE_TTL = 300000
    
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
    
    def __init__(
        self, 
        api_client: IApiClient,
        cache: CacheManager,
        parent: Optional[QObject] = None
    ):
        super().__init__(parent)
        self._api_client = api_client
        self._cache = cache
        self._category_worker: Optional[AsyncWorker] = None
        self._recommendations_worker: Optional[AsyncWorker] = None
        self._is_loading_category = False
        self._is_loading_recommendations = False
    
    def fetch_categories(self) -> None:
        """获取分类列表"""
        logger.debug("CategoryService: fetch_categories called")
        provider = get_current_provider()
        if provider:
            # 使用 Provider 的分类（异步获取）
            self._cancel_category_worker()
            self._category_worker = AsyncWorker(
                self._do_fetch_categories,
                parent=self, service_name="CategoryService"
            )
            self._category_worker.finished_signal.connect(
                lambda cats: self.categories_loaded.emit(cats)
            )
            self._category_worker.error_signal.connect(
                lambda e: self.categories_loaded.emit(self.CATEGORIES)  # 失败时使用默认分类
            )
            self._category_worker.start()
        else:
            self.categories_loaded.emit(self.CATEGORIES)
    
    async def _do_fetch_categories(self) -> List[str]:
        """异步获取分类列表"""
        provider = get_current_provider()
        if provider:
            return await provider.get_categories()
        return self.CATEGORIES
    
    def fetch_category_dramas(self, category: str, offset: int = 1) -> None:
        """获取分类下的短剧列表"""
        logger.debug(f"fetch_category_dramas: category={category}, offset={offset}")
        self._cancel_category_worker()
        self._is_loading_category = True
        self.loading_started.emit()
        
        cache_key = CacheManager.generate_key("category", category, str(offset))
        cached = self._cache.get(cache_key)
        if cached:
            try:
                result = ResponseParser.parse_category_result(cached, category)
                self._is_loading_category = False
                self.dramas_loaded.emit(result)
                return
            except Exception as e:
                logger.warning(f"Category cache parse error: {e}")
        
        self._category_worker = AsyncWorker(
            self._do_fetch_category_dramas, category, offset, cache_key,
            parent=self, service_name="CategoryService"
        )
        self._category_worker.finished_signal.connect(self._on_dramas_result)
        self._category_worker.error_signal.connect(self._on_dramas_error)
        self._category_worker.start()
    
    async def _do_fetch_category_dramas(self, category: str, offset: int, cache_key: str):
        """执行获取分类短剧请求"""
        provider = get_current_provider()
        if provider:
            # 使用 Provider 获取数据
            result = await provider.get_category_dramas(category, offset)
            return ("dramas", result)
        else:
            # 回退到旧的 API 调用方式
            response = await self._api_client.get(
                params={"classname": category, "offset": str(offset)}
            )
            
            if response.success:
                self._cache.set(cache_key, response.body, self.CACHE_TTL)
                result = ResponseParser.parse_category_result(response.body, category)
                return ("dramas", result)
            else:
                raise Exception(response.error or "获取分类内容失败")
    
    def _on_dramas_result(self, result) -> None:
        if not self._is_loading_category:
            return
        self._is_loading_category = False
        result_type, data = result
        if result_type == "dramas":
            self.dramas_loaded.emit(data)
    
    def _on_dramas_error(self, e: Exception) -> None:
        self._is_loading_category = False
        friendly_msg = logger.get_friendly_error_message(e)
        error = ApiError(code=0, message=friendly_msg, details=str(e))
        self.error.emit(error)
    
    def fetch_recommendations(self, force_refresh: bool = False) -> None:
        """获取推荐内容"""
        logger.debug(f"CategoryService: fetch_recommendations, force_refresh={force_refresh}")
        self._cancel_recommendations_worker()
        self._is_loading_recommendations = True
        
        cache_key = "recommendations"
        
        if force_refresh:
            self._cache.remove(cache_key)
        else:
            cached = self._cache.get(cache_key)
            if cached:
                try:
                    dramas = ResponseParser.parse_recommendations(cached)
                    logger.log_cache_operation("GET", cache_key, hit=True)
                    self._is_loading_recommendations = False
                    self.recommendations_loaded.emit(dramas)
                    return
                except Exception as e:
                    logger.warning(f"Cache parse error for {cache_key}: {e}")
        
        logger.log_cache_operation("GET", cache_key, hit=False)
        self._recommendations_worker = AsyncWorker(
            self._do_fetch_recommendations, cache_key,
            parent=self, service_name="CategoryService"
        )
        self._recommendations_worker.finished_signal.connect(self._on_recommendations_result)
        self._recommendations_worker.error_signal.connect(self._on_recommendations_error)
        self._recommendations_worker.start()
    
    async def _do_fetch_recommendations(self, cache_key: str):
        """执行获取推荐内容请求"""
        provider = get_current_provider()
        if provider:
            # 使用 Provider 获取数据
            dramas = await provider.get_recommendations()
            logger.debug(f"Fetched {len(dramas)} recommendations via Provider")
            return ("recommendations", dramas)
        else:
            # 回退到旧的 API 调用方式
            logger.log_api_request("recommendations", {"type": "recommend"})
            response = await self._api_client.get(params={"type": "recommend"})
            logger.log_api_response("recommendations", response.status_code, response.success)
            
            if response.success:
                self._cache.set(cache_key, response.body, self.CACHE_TTL)
                dramas = ResponseParser.parse_recommendations(response.body)
                logger.debug(f"Fetched {len(dramas)} recommendations")
                return ("recommendations", dramas)
            else:
                raise Exception(response.error or "获取推荐失败")
    
    def _on_recommendations_result(self, result) -> None:
        if not self._is_loading_recommendations:
            return
        self._is_loading_recommendations = False
        result_type, data = result
        if result_type == "recommendations":
            self.recommendations_loaded.emit(data)
    
    def _on_recommendations_error(self, e: Exception) -> None:
        self._is_loading_recommendations = False
        friendly_msg = logger.get_friendly_error_message(e)
        error = ApiError(code=0, message=friendly_msg, details=str(e))
        self.error.emit(error)
    
    def _cancel_category_worker(self) -> None:
        self._is_loading_category = False
        if self._category_worker and self._category_worker.isRunning():
            self._category_worker.terminate()
            self._category_worker.wait()
        self._category_worker = None
    
    def _cancel_recommendations_worker(self) -> None:
        self._is_loading_recommendations = False
        if self._recommendations_worker and self._recommendations_worker.isRunning():
            self._recommendations_worker.terminate()
            self._recommendations_worker.wait()
        self._recommendations_worker = None
    
    def cancel(self) -> None:
        """取消所有请求"""
        self._cancel_category_worker()
        self._cancel_recommendations_worker()
    
    @property
    def is_loading(self) -> bool:
        return self._is_loading_category or self._is_loading_recommendations
