"""搜索服务实现"""
from typing import Protocol, Optional

from PySide6.QtCore import QObject, Signal

from ..core.models import SearchResult, ApiError
from ..utils.string_utils import is_blank
from ..utils.log_manager import get_logger
from ..utils.async_worker import AsyncWorker
from ..data.api_client import IApiClient
from ..data.response_parser import ResponseParser
from ..data.cache_manager import CacheManager
from ..data.providers.provider_registry import get_current_provider

logger = get_logger()


class ISearchService(Protocol):
    """搜索服务接口协议"""
    
    def search(self, keyword: str, page: int = 1) -> None: ...
    def cancel_search(self) -> None: ...
    def is_searching(self) -> bool: ...
    @property
    def current_keyword(self) -> str: ...


class SearchService(QObject):
    """搜索服务实现"""
    
    search_started = Signal()
    search_completed = Signal(object)
    search_error = Signal(object)
    
    CACHE_TTL = 300000
    
    def __init__(
        self, 
        api_client: IApiClient, 
        cache: CacheManager,
        parent: Optional[QObject] = None
    ):
        super().__init__(parent)
        self._api_client = api_client
        self._cache = cache
        self._is_searching = False
        self._current_keyword = ""
        self._current_worker: Optional[AsyncWorker] = None
    
    def search(self, keyword: str, page: int = 1) -> None:
        """执行搜索"""
        if is_blank(keyword):
            logger.debug(f"SearchService: blank keyword rejected")
            return
        
        logger.log_user_action("search", f"keyword={keyword}, page={page}")
        self.cancel_search()
        
        self._current_keyword = keyword.strip()
        self._is_searching = True
        self.search_started.emit()
        
        cache_key = CacheManager.generate_key("search", self._current_keyword, str(page))
        cached = self._cache.get(cache_key)
        if cached:
            try:
                result = ResponseParser.parse_search_result(cached)
                logger.log_cache_operation("GET", cache_key, hit=True)
                self._is_searching = False
                self.search_completed.emit(result)
                return
            except Exception as e:
                logger.warning(f"Cache parse error for {cache_key}: {e}")
        
        logger.log_cache_operation("GET", cache_key, hit=False)
        
        self._current_worker = AsyncWorker(
            self._do_search,
            self._current_keyword,
            page,
            cache_key,
            parent=self,
            service_name="SearchService"
        )
        self._current_worker.finished_signal.connect(self._on_search_result)
        self._current_worker.error_signal.connect(self._on_search_error)
        self._current_worker.start()
    
    async def _do_search(self, keyword: str, page: int, cache_key: str):
        """执行实际的搜索请求"""
        provider = get_current_provider()
        if provider:
            # 使用 Provider 搜索
            logger.debug(f"Searching via Provider: {provider.info.id}")
            result = await provider.search(keyword, page)
            logger.debug(f"Search returned {len(result.data)} results via Provider")
            return result
        else:
            # 回退到旧的 API 调用方式
            logger.log_api_request("search", {"name": keyword, "page": page})
            response = await self._api_client.get(
                params={"name": keyword, "page": str(page)}
            )
            logger.log_api_response("search", response.status_code, response.success)
            
            if response.success:
                self._cache.set(cache_key, response.body, self.CACHE_TTL)
                result = ResponseParser.parse_search_result(response.body)
                logger.debug(f"Search returned {len(result.data)} results")
                return result
            else:
                raise Exception(response.error or "搜索失败")
    
    def _on_search_result(self, result: SearchResult) -> None:
        """处理搜索结果"""
        if not self._is_searching:
            return
        self._is_searching = False
        self.search_completed.emit(result)
    
    def _on_search_error(self, e: Exception) -> None:
        """处理搜索错误"""
        self._is_searching = False
        friendly_msg = logger.get_friendly_error_message(e)
        error = ApiError(code=0, message=friendly_msg, details=str(e))
        self.search_error.emit(error)
    
    def cancel_search(self) -> None:
        """取消搜索"""
        self._is_searching = False
        if self._current_worker and self._current_worker.isRunning():
            self._current_worker.terminate()
            self._current_worker.wait()
        self._current_worker = None
    
    def is_searching(self) -> bool:
        """检查是否正在搜索"""
        return self._is_searching
    
    @property
    def current_keyword(self) -> str:
        """获取当前搜索关键词"""
        return self._current_keyword
