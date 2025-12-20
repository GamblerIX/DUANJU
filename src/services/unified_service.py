"""统一服务层

基于 IDataProvider 接口的统一服务实现。
自动使用当前活动的数据提供者，支持缓存和错误处理。
"""
import json
from typing import Optional, List

from PySide6.QtCore import QObject, Signal

from ..core.models import (
    DramaInfo, 
    EpisodeList, 
    VideoInfo, 
    SearchResult, 
    CategoryResult,
    ApiError
)
from ..utils.log_manager import get_logger
from ..utils.async_worker import AsyncWorker
from ..data.providers.provider_registry import get_current_provider, get_registry
from ..data.providers.provider_base import IDataProvider
from ..data.cache_manager import CacheManager

logger = get_logger()


class UnifiedService(QObject):
    """统一数据服务
    
    整合搜索、分类、视频等功能，自动使用当前数据提供者。
    """
    
    # 搜索信号
    search_started = Signal()
    search_completed = Signal(object)  # SearchResult
    search_error = Signal(object)  # ApiError
    
    # 分类信号
    categories_loaded = Signal(list)  # List[str]
    dramas_loaded = Signal(object)  # CategoryResult
    recommendations_loaded = Signal(list)  # List[DramaInfo]
    
    # 视频信号
    episodes_loaded = Signal(object)  # EpisodeList
    video_url_loaded = Signal(object)  # VideoInfo
    
    # 通用信号
    loading_started = Signal()
    error = Signal(object)  # ApiError
    provider_changed = Signal(str)  # provider_id
    
    CACHE_TTL = 300000  # 5 分钟
    
    def __init__(
        self, 
        cache: Optional[CacheManager] = None,
        parent: Optional[QObject] = None
    ):
        super().__init__(parent)
        self._cache = cache or CacheManager()
        self._current_worker: Optional[AsyncWorker] = None
        self._is_loading = False
    
    def _get_provider(self) -> IDataProvider:
        """获取当前数据提供者"""
        provider = get_current_provider()
        if not provider:
            raise RuntimeError("没有可用的数据提供者")
        return provider
    
    def _cancel_worker(self) -> None:
        """取消当前工作线程"""
        self._is_loading = False
        if self._current_worker and self._current_worker.isRunning():
            self._current_worker.terminate()
            self._current_worker.wait()
        self._current_worker = None
    
    # ==================== 搜索功能 ====================
    
    def search(self, keyword: str, page: int = 1) -> None:
        """搜索短剧"""
        if not keyword.strip():
            return
        
        self._cancel_worker()
        self._is_loading = True
        self.search_started.emit()
        
        # 检查缓存 (加入 provider_id 防止冲突)
        provider_id = self.current_provider_id or "unknown"
        cache_key = CacheManager.generate_key(f"search:{provider_id}", keyword, str(page))
        cached = self._cache.get(cache_key)
        if cached:
            try:
                result = self._deserialize_search_result(cached)
                self._is_loading = False
                self.search_completed.emit(result)
                return
            except Exception as e:
                logger.warning(f"Cache parse failed: {e}")
                # 缓存解析失败，继续网络请求
        
        self._current_worker = AsyncWorker(
            self._do_search, keyword, page, cache_key,
            parent=self, service_name="UnifiedService"
        )
        self._current_worker.finished_signal.connect(self._on_search_result)
        self._current_worker.error_signal.connect(self._on_search_error)
        self._current_worker.start()
    
    def _deserialize_search_result(self, json_str: str) -> SearchResult:
        """反序列化缓存的搜索结果"""
        data = json.loads(json_str)
        dramas = []
        for item in data.get("data", []):
            dramas.append(DramaInfo(
                book_id=item.get("book_id", ""),
                title=item.get("title", ""),
                cover=item.get("cover", ""),
                episode_cnt=item.get("episode_cnt", 0),
                intro=item.get("intro", ""),
                type=item.get("type", ""),
                author=item.get("author", ""),
                play_cnt=item.get("play_cnt", 0)
            ))
        
        return SearchResult(
            code=data.get("code", 0),
            msg=data.get("msg", ""),
            data=dramas,
            page=data.get("page", 1)
        )

    async def _do_search(self, keyword: str, page: int, cache_key: str) -> SearchResult:
        provider = self._get_provider()
        result = await provider.search(keyword, page)
        # 缓存原始结果
        try:
            cache_data = {
                "code": result.code,
                "msg": result.msg,
                "page": result.page,
                "data": [{
                    "book_id": d.book_id, 
                    "title": d.title, 
                    "cover": d.cover,
                    "episode_cnt": d.episode_cnt, 
                    "intro": d.intro, 
                    "type": d.type,
                    "author": d.author, 
                    "play_cnt": d.play_cnt
                } for d in result.data]
            }
            self._cache.set(cache_key, json.dumps(cache_data), self.CACHE_TTL)
        except Exception as e:
            logger.warning(f"Failed to cache search result: {e}")
            
        return result
    
    def _on_search_result(self, result: SearchResult) -> None:
        if not self._is_loading:
            return
        self._is_loading = False
        self.search_completed.emit(result)
    
    def _on_search_error(self, e: Exception) -> None:
        self._is_loading = False
        self.search_error.emit(ApiError(code=0, message=str(e)))
    
    # ==================== 分类功能 ====================
    
    def fetch_categories(self) -> None:
        """获取分类列表"""
        self._cancel_worker()
        self._current_worker = AsyncWorker(
            self._do_fetch_categories,
            parent=self, service_name="UnifiedService"
        )
        self._current_worker.finished_signal.connect(
            lambda cats: self.categories_loaded.emit(cats)
        )
        self._current_worker.error_signal.connect(self._on_error)
        self._current_worker.start()
    
    async def _do_fetch_categories(self) -> List[str]:
        provider = self._get_provider()
        return await provider.get_categories()
    
    def fetch_category_dramas(self, category: str, page: int = 1) -> None:
        """获取分类下的短剧"""
        self._cancel_worker()
        self._is_loading = True
        self.loading_started.emit()
        
        self._current_worker = AsyncWorker(
            self._do_fetch_category_dramas, category, page,
            parent=self, service_name="UnifiedService"
        )
        self._current_worker.finished_signal.connect(
            lambda r: self._emit_if_loading(self.dramas_loaded, r)
        )
        self._current_worker.error_signal.connect(self._on_error)
        self._current_worker.start()
    
    async def _do_fetch_category_dramas(self, category: str, page: int) -> CategoryResult:
        provider = self._get_provider()
        return await provider.get_category_dramas(category, page)
    
    def fetch_recommendations(self) -> None:
        """获取推荐内容"""
        self._cancel_worker()
        self._is_loading = True
        
        self._current_worker = AsyncWorker(
            self._do_fetch_recommendations,
            parent=self, service_name="UnifiedService"
        )
        self._current_worker.finished_signal.connect(
            lambda r: self._emit_if_loading(self.recommendations_loaded, r)
        )
        self._current_worker.error_signal.connect(self._on_error)
        self._current_worker.start()
    
    async def _do_fetch_recommendations(self) -> List[DramaInfo]:
        provider = self._get_provider()
        return await provider.get_recommendations()
    
    # ==================== 视频功能 ====================
    
    def fetch_episodes(self, drama_id: str) -> None:
        """获取剧集列表"""
        self._cancel_worker()
        self._is_loading = True
        self.loading_started.emit()
        
        self._current_worker = AsyncWorker(
            self._do_fetch_episodes, drama_id,
            parent=self, service_name="UnifiedService"
        )
        self._current_worker.finished_signal.connect(
            lambda r: self._emit_if_loading(self.episodes_loaded, r)
        )
        self._current_worker.error_signal.connect(self._on_error)
        self._current_worker.start()
    
    async def _do_fetch_episodes(self, drama_id: str) -> EpisodeList:
        provider = self._get_provider()
        return await provider.get_episodes(drama_id)
    
    def fetch_video_url(self, episode_id: str, quality: str = "1080p") -> None:
        """获取视频播放地址"""
        self._cancel_worker()
        self._is_loading = True
        self.loading_started.emit()
        
        self._current_worker = AsyncWorker(
            self._do_fetch_video_url, episode_id, quality,
            parent=self, service_name="UnifiedService"
        )
        self._current_worker.finished_signal.connect(
            lambda r: self._emit_if_loading(self.video_url_loaded, r)
        )
        self._current_worker.error_signal.connect(self._on_error)
        self._current_worker.start()
    
    async def _do_fetch_video_url(self, episode_id: str, quality: str) -> VideoInfo:
        provider = self._get_provider()
        return await provider.get_video_url(episode_id, quality)
    
    # ==================== 提供者管理 ====================
    
    def switch_provider(self, provider_id: str) -> bool:
        """切换数据提供者"""
        registry = get_registry()
        if registry.set_current(provider_id):
            self._cache.clear()  # 清空缓存
            self.provider_changed.emit(provider_id)
            return True
        return False
    
    def get_available_providers(self) -> List[str]:
        """获取可用的提供者列表"""
        return get_registry().list_provider_ids()
    
    # ==================== 辅助方法 ====================
    
    def _emit_if_loading(self, signal: Signal, data) -> None:
        if self._is_loading:
            self._is_loading = False
            signal.emit(data)
    
    def _on_error(self, e: Exception) -> None:
        self._is_loading = False
        self.error.emit(ApiError(code=0, message=str(e)))
    
    def cancel(self) -> None:
        """取消当前操作"""
        self._cancel_worker()
    
    @property
    def is_loading(self) -> bool:
        return self._is_loading
    
    @property
    def current_provider_id(self) -> Optional[str]:
        return get_registry().current_id
