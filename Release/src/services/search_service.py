from typing import Protocol, Optional
from PyQt6.QtCore import QObject, pyqtSignal
from ..core.models import SearchResult, ApiError
from ..core.utils.string_utils import is_blank
from ..core.utils.async_worker import AsyncWorker
from ..data.api.api_client import IApiClient
from ..data.api.response_parser import ResponseParser
from ..data.cache.cache_manager import CacheManager


class ISearchService(Protocol):
    def search(self, keyword: str, page: int = 1) -> None: ...
    def cancel_search(self) -> None: ...
    def is_searching(self) -> bool: ...
    @property
    def current_keyword(self) -> str: ...


class SearchService(QObject):
    search_started = pyqtSignal()
    search_completed = pyqtSignal(object)
    search_error = pyqtSignal(object)
    
    CACHE_TTL = 300000
    
    def __init__(self, api_client: IApiClient, cache: CacheManager, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._api_client = api_client
        self._cache = cache
        self._is_searching = False
        self._current_keyword = ""
        self._current_worker: Optional[AsyncWorker] = None
    
    def search(self, keyword: str, page: int = 1) -> None:
        if is_blank(keyword):
            return
        self.cancel_search()
        self._current_keyword = keyword.strip()
        self._is_searching = True
        self.search_started.emit()
        cache_key = CacheManager.generate_key("search", self._current_keyword, str(page))
        cached = self._cache.get(cache_key)
        if cached:
            try:
                result = ResponseParser.parse_search_result(cached)
                self._is_searching = False
                self.search_completed.emit(result)
                return
            except Exception:
                pass
        self._current_worker = AsyncWorker(self._do_search, self._current_keyword, page, cache_key,
                                          parent=self, service_name="SearchService")
        self._current_worker.finished_signal.connect(self._on_search_result)
        self._current_worker.error_signal.connect(self._on_search_error)
        self._current_worker.start()
    
    async def _do_search(self, keyword: str, page: int, cache_key: str):
        response = await self._api_client.get(params={"name": keyword, "page": str(page)})
        if response.success:
            self._cache.set(cache_key, response.body, self.CACHE_TTL)
            result = ResponseParser.parse_search_result(response.body)
            return result
        else:
            raise Exception(response.error or "搜索失败")
    
    def _on_search_result(self, result: SearchResult) -> None:
        if not self._is_searching:
            return
        self._is_searching = False
        self.search_completed.emit(result)
    
    def _on_search_error(self, e: Exception) -> None:
        self._is_searching = False
        error = ApiError(code=0, message=str(e), details="")
        self.search_error.emit(error)
    
    def cancel_search(self) -> None:
        self._is_searching = False
        if self._current_worker and self._current_worker.isRunning():
            self._current_worker.terminate()
            self._current_worker.wait()
        self._current_worker = None
    
    def is_searching(self) -> bool:
        return self._is_searching
    
    @property
    def current_keyword(self) -> str:
        return self._current_keyword
