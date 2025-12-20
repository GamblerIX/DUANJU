"""视频服务实现"""
from typing import Protocol, Optional

from PySide6.QtCore import QObject, Signal

from ..core.models import EpisodeList, VideoInfo, ApiError
from ..utils.log_manager import get_logger
from ..utils.async_worker import AsyncWorker
from ..data.api_client import IApiClient
from ..data.response_parser import ResponseParser
from ..data.providers.provider_registry import get_current_provider

logger = get_logger()


class IVideoService(Protocol):
    """视频服务接口协议"""
    def fetch_episodes(self, book_id: str) -> None: ...
    def fetch_video_url(self, video_id: str, quality: str = "1080p") -> None: ...
    def cancel(self) -> None: ...


class VideoService(QObject):
    """视频服务实现"""
    
    episodes_loaded = Signal(object)
    video_url_loaded = Signal(object)
    error = Signal(object)
    loading_started = Signal()
    
    def __init__(self, api_client: IApiClient, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._api_client = api_client
        self._current_worker: Optional[AsyncWorker] = None
        self._is_loading = False
    
    def fetch_episodes(self, book_id: str) -> None:
        """获取剧集列表"""
        logger.debug(f"VideoService: fetch_episodes called for book_id={book_id}")
        self.cancel()
        self._is_loading = True
        self.loading_started.emit()
        
        self._current_worker = AsyncWorker(
            self._do_fetch_episodes,
            book_id,
            parent=self,
            service_name="VideoService"
        )
        self._current_worker.finished_signal.connect(self._on_episodes_result)
        self._current_worker.error_signal.connect(self._on_error)
        self._current_worker.start()
    
    async def _do_fetch_episodes(self, book_id: str):
        """执行获取剧集列表请求"""
        provider = get_current_provider()
        if provider:
            # 使用 Provider 获取剧集
            logger.debug(f"Fetching episodes via Provider: {provider.info.id}")
            result = await provider.get_episodes(book_id)
            logger.debug(f"Fetched {len(result.episodes)} episodes via Provider")
            return ("episodes", result)
        else:
            # 回退到旧的 API 调用方式
            logger.log_api_request("episodes", {"book_id": book_id})
            response = await self._api_client.get(params={"book_id": book_id})
            logger.log_api_response("episodes", response.status_code, response.success)
            
            if response.success:
                result = ResponseParser.parse_episode_list(response.body)
                logger.debug(f"Fetched {len(result.episodes)} episodes")
                return ("episodes", result)
            else:
                raise Exception(response.error or "获取剧集失败")
    
    def _on_episodes_result(self, result) -> None:
        """处理剧集结果"""
        if not self._is_loading:
            return
        self._is_loading = False
        result_type, data = result
        if result_type == "episodes":
            self.episodes_loaded.emit(data)
    
    def fetch_video_url(self, video_id: str, quality: str = "1080p") -> None:
        """获取视频播放地址"""
        self.cancel()
        self._is_loading = True
        self.loading_started.emit()
        
        self._current_worker = AsyncWorker(
            self._do_fetch_video_url,
            video_id,
            quality,
            parent=self,
            service_name="VideoService"
        )
        self._current_worker.finished_signal.connect(self._on_video_url_result)
        self._current_worker.error_signal.connect(self._on_error)
        self._current_worker.start()
    
    async def _do_fetch_video_url(self, video_id: str, quality: str):
        """执行获取视频地址请求"""
        provider = get_current_provider()
        if provider:
            # 使用 Provider 获取视频地址
            logger.debug(f"Fetching video URL via Provider: {provider.info.id}")
            result = await provider.get_video_url(video_id, quality)
            logger.debug(f"Got video URL via Provider: {result.url[:50] if result.url else 'empty'}...")
            return ("video_url", result)
        else:
            # 回退到旧的 API 调用方式
            logger.log_api_request("video", {"video_id": video_id, "level": quality})
            response = await self._api_client.get(
                params={"video_id": video_id, "level": quality, "type": "json"}
            )
            logger.log_api_response("video", response.status_code, response.success)
            
            if response.success:
                result = ResponseParser.parse_video_info(response.body)
                logger.debug(f"Got video URL: {result.url[:50] if result.url else 'empty'}...")
                return ("video_url", result)
            else:
                raise Exception(response.error or "获取视频地址失败")
    
    def _on_video_url_result(self, result) -> None:
        """处理视频地址结果"""
        if not self._is_loading:
            return
        self._is_loading = False
        result_type, data = result
        if result_type == "video_url":
            self.video_url_loaded.emit(data)
    
    def _on_error(self, e: Exception) -> None:
        """处理错误"""
        self._is_loading = False
        friendly_msg = logger.get_friendly_error_message(e)
        error = ApiError(code=0, message=friendly_msg, details=str(e))
        self.error.emit(error)
    
    def cancel(self) -> None:
        """取消当前请求"""
        self._is_loading = False
        if self._current_worker and self._current_worker.isRunning():
            self._current_worker.terminate()
            self._current_worker.wait()
        self._current_worker = None
    
    @property
    def is_loading(self) -> bool:
        return self._is_loading
