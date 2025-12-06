from typing import Protocol, Optional, List
from PyQt6.QtCore import QObject, pyqtSignal
from ..core.models import CategoryResult, DramaInfo, ApiError
from ..core.utils.async_worker import AsyncWorker
from ..data.api.api_client import IApiClient
from ..data.api.response_parser import ResponseParser
from ..data.cache.cache_manager import CacheManager


class ICategoryService(Protocol):
    def fetch_categories(self) -> None: ...
    def fetch_category_dramas(self, category: str, offset: int = 1) -> None: ...
    def fetch_recommendations(self) -> None: ...
    def cancel(self) -> None: ...


class CategoryService(QObject):
    categories_loaded = pyqtSignal(list)
    dramas_loaded = pyqtSignal(object)
    recommendations_loaded = pyqtSignal(list)
    error = pyqtSignal(object)
    loading_started = pyqtSignal()
    
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
    
    def __init__(self, api_client: IApiClient, cache: CacheManager, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._api_client = api_client
        self._cache = cache
        self._category_worker: Optional[AsyncWorker] = None
        self._recommendations_worker: Optional[AsyncWorker] = None
        self._is_loading_category = False
        self._is_loading_recommendations = False
    
    def fetch_categories(self) -> None:
        self.categories_loaded.emit(self.CATEGORIES)
    
    def fetch_category_dramas(self, category: str, offset: int = 1) -> None:
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
            except Exception:
                pass
        self._category_worker = AsyncWorker(self._do_fetch_category_dramas, category, offset, cache_key,
                                           parent=self, service_name="CategoryService")
        self._category_worker.finished_signal.connect(self._on_dramas_result)
        self._category_worker.error_signal.connect(self._on_dramas_error)
        self._category_worker.start()
    
    async def _do_fetch_category_dramas(self, category: str, offset: int, cache_key: str):
        response = await self._api_client.get(params={"classname": category, "offset": str(offset)})
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
        error = ApiError(code=0, message=str(e), details="")
        self.error.emit(error)
    
    def fetch_recommendations(self, force_refresh: bool = False) -> None:
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
                    self._is_loading_recommendations = False
                    self.recommendations_loaded.emit(dramas)
                    return
                except Exception:
                    pass
        self._recommendations_worker = AsyncWorker(self._do_fetch_recommendations, cache_key,
                                                   parent=self, service_name="CategoryService")
        self._recommendations_worker.finished_signal.connect(self._on_recommendations_result)
        self._recommendations_worker.error_signal.connect(self._on_recommendations_error)
        self._recommendations_worker.start()
    
    async def _do_fetch_recommendations(self, cache_key: str):
        response = await self._api_client.get(params={"type": "recommend"})
        if response.success:
            self._cache.set(cache_key, response.body, self.CACHE_TTL)
            dramas = ResponseParser.parse_recommendations(response.body)
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
        error = ApiError(code=0, message=str(e), details="")
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
        self._cancel_category_worker()
        self._cancel_recommendations_worker()
    
    @property
    def is_loading(self) -> bool:
        return self._is_loading_category or self._is_loading_recommendations
