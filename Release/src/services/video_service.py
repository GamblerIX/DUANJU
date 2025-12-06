from typing import Protocol, Optional
from PyQt6.QtCore import QObject, pyqtSignal
from ..core.models import EpisodeList, VideoInfo, ApiError
from ..core.utils.async_worker import AsyncWorker
from ..data.api.api_client import IApiClient
from ..data.api.response_parser import ResponseParser


class IVideoService(Protocol):
    def fetch_episodes(self, book_id: str) -> None: ...
    def fetch_video_url(self, video_id: str, quality: str = "1080p") -> None: ...
    def cancel(self) -> None: ...


class VideoService(QObject):
    episodes_loaded = pyqtSignal(object)
    video_url_loaded = pyqtSignal(object)
    error = pyqtSignal(object)
    loading_started = pyqtSignal()
    
    def __init__(self, api_client: IApiClient, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._api_client = api_client
        self._current_worker: Optional[AsyncWorker] = None
        self._is_loading = False
    
    def fetch_episodes(self, book_id: str) -> None:
        self.cancel()
        self._is_loading = True
        self.loading_started.emit()
        self._current_worker = AsyncWorker(self._do_fetch_episodes, book_id,
                                          parent=self, service_name="VideoService")
        self._current_worker.finished_signal.connect(self._on_episodes_result)
        self._current_worker.error_signal.connect(self._on_error)
        self._current_worker.start()
    
    async def _do_fetch_episodes(self, book_id: str):
        response = await self._api_client.get(params={"book_id": book_id})
        if response.success:
            result = ResponseParser.parse_episode_list(response.body)
            return ("episodes", result)
        else:
            raise Exception(response.error or "获取剧集失败")
    
    def _on_episodes_result(self, result) -> None:
        if not self._is_loading:
            return
        self._is_loading = False
        result_type, data = result
        if result_type == "episodes":
            self.episodes_loaded.emit(data)
    
    def fetch_video_url(self, video_id: str, quality: str = "1080p") -> None:
        self.cancel()
        self._is_loading = True
        self.loading_started.emit()
        self._current_worker = AsyncWorker(self._do_fetch_video_url, video_id, quality,
                                          parent=self, service_name="VideoService")
        self._current_worker.finished_signal.connect(self._on_video_url_result)
        self._current_worker.error_signal.connect(self._on_error)
        self._current_worker.start()
    
    async def _do_fetch_video_url(self, video_id: str, quality: str):
        response = await self._api_client.get(
            params={"video_id": video_id, "level": quality, "type": "json"})
        if response.success:
            result = ResponseParser.parse_video_info(response.body)
            return ("video_url", result)
        else:
            raise Exception(response.error or "获取视频地址失败")
    
    def _on_video_url_result(self, result) -> None:
        if not self._is_loading:
            return
        self._is_loading = False
        result_type, data = result
        if result_type == "video_url":
            self.video_url_loaded.emit(data)
    
    def _on_error(self, e: Exception) -> None:
        self._is_loading = False
        error = ApiError(code=0, message=str(e), details="")
        self.error.emit(error)
    
    def cancel(self) -> None:
        self._is_loading = False
        if self._current_worker and self._current_worker.isRunning():
            self._current_worker.terminate()
            self._current_worker.wait()
        self._current_worker = None
    
    @property
    def is_loading(self) -> bool:
        return self._is_loading
