import os
import aiohttp
import asyncio
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from ..core.models import EpisodeInfo, DramaInfo
from ..data.api.api_client import ApiClient
from ..data.api.response_parser import ResponseParser


class DownloadStatus(Enum):
    PENDING = "pending"
    FETCHING = "fetching"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DownloadTask:
    drama: DramaInfo
    episode: EpisodeInfo
    status: DownloadStatus = DownloadStatus.PENDING
    progress: float = 0.0
    video_url: str = ""
    file_path: str = ""
    error: str = ""
    downloaded_bytes: int = 0
    total_bytes: int = 0
    
    @property
    def id(self) -> str:
        return f"{self.drama.book_id}_{self.episode.video_id}"


class DownloadWorker(QThread):
    task_started = pyqtSignal(str)
    task_progress = pyqtSignal(str, float, int, int)
    task_completed = pyqtSignal(str)
    task_failed = pyqtSignal(str, str)
    video_info_fetched = pyqtSignal(str, str)
    
    def __init__(self, api_client: ApiClient, tasks: List[DownloadTask], download_dir: str,
                 quality: str = "1080p", parent: Optional[QObject] = None):
        super().__init__(parent)
        self._api_client = api_client
        self._tasks = tasks
        self._download_dir = download_dir
        self._quality = quality
        self._cancelled = False
        self._current_task_id: Optional[str] = None
    
    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._process_tasks())
        finally:
            loop.close()
    
    async def _process_tasks(self):
        for task in self._tasks:
            if self._cancelled:
                break
            self._current_task_id = task.id
            self.task_started.emit(task.id)
            try:
                task.status = DownloadStatus.FETCHING
                video_url = await self._fetch_video_url(task.episode.video_id)
                if not video_url:
                    raise Exception("获取视频地址失败")
                task.video_url = video_url
                self.video_info_fetched.emit(task.id, video_url)
                if self._cancelled:
                    break
                task.status = DownloadStatus.DOWNLOADING
                await self._download_video(task)
                if not self._cancelled:
                    task.status = DownloadStatus.COMPLETED
                    task.progress = 100.0
                    self.task_completed.emit(task.id)
            except Exception as e:
                task.status = DownloadStatus.FAILED
                task.error = str(e)
                self.task_failed.emit(task.id, str(e))
    
    async def _fetch_video_url(self, video_id: str) -> str:
        response = await self._api_client.get(
            params={"video_id": video_id, "level": self._quality, "type": "json"})
        if response.success:
            video_info = ResponseParser.parse_video_info(response.body)
            return video_info.url
        return ""
    
    async def _download_video(self, task: DownloadTask):
        drama_dir = os.path.join(self._download_dir, self._sanitize_filename(task.drama.name))
        os.makedirs(drama_dir, exist_ok=True)
        filename = f"{task.episode.title}.mp4"
        file_path = os.path.join(drama_dir, self._sanitize_filename(filename))
        task.file_path = file_path
        timeout = aiohttp.ClientTimeout(total=3600)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(task.video_url) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")
                total_size = int(response.headers.get('content-length', 0))
                task.total_bytes = total_size
                downloaded = 0
                with open(file_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        if self._cancelled:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        task.downloaded_bytes = downloaded
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            task.progress = progress
                            self.task_progress.emit(task.id, progress, downloaded, total_size)
    
    def _sanitize_filename(self, name: str) -> str:
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name.strip()
    
    def cancel(self):
        self._cancelled = True


class DownloadService(QObject):
    task_added = pyqtSignal(object)
    task_started = pyqtSignal(str)
    task_progress = pyqtSignal(str, float, int, int)
    task_completed = pyqtSignal(str)
    task_failed = pyqtSignal(str, str)
    all_completed = pyqtSignal()
    
    def __init__(self, api_client: ApiClient, download_dir: str, quality: str = "1080p",
                 parent: Optional[QObject] = None):
        super().__init__(parent)
        self._api_client = api_client
        self._download_dir = download_dir
        self._quality = quality
        self._tasks: List[DownloadTask] = []
        self._worker: Optional[DownloadWorker] = None
        self._is_running = False
    
    def add_tasks(self, drama: DramaInfo, episodes: List[EpisodeInfo]) -> None:
        for episode in episodes:
            task = DownloadTask(drama=drama, episode=episode)
            if not any(t.id == task.id for t in self._tasks):
                self._tasks.append(task)
                self.task_added.emit(task)
    
    def start(self) -> None:
        if self._is_running:
            return
        pending_tasks = [t for t in self._tasks if t.status == DownloadStatus.PENDING]
        if not pending_tasks:
            return
        self._is_running = True
        self._worker = DownloadWorker(self._api_client, pending_tasks, self._download_dir, self._quality, self)
        self._worker.task_started.connect(self._on_task_started)
        self._worker.task_progress.connect(self._on_task_progress)
        self._worker.task_completed.connect(self._on_task_completed)
        self._worker.task_failed.connect(self._on_task_failed)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()
    
    def cancel(self) -> None:
        if self._worker:
            self._worker.cancel()
            self._worker.wait(3000)
            self._worker = None
            self._is_running = False
    
    def _on_task_started(self, task_id: str) -> None:
        self.task_started.emit(task_id)
    
    def _on_task_progress(self, task_id: str, progress: float, downloaded: int, total: int) -> None:
        for task in self._tasks:
            if task.id == task_id:
                task.progress = progress
                task.downloaded_bytes = downloaded
                task.total_bytes = total
                break
        self.task_progress.emit(task_id, progress, downloaded, total)
    
    def _on_task_completed(self, task_id: str) -> None:
        for task in self._tasks:
            if task.id == task_id:
                task.status = DownloadStatus.COMPLETED
                break
        self.task_completed.emit(task_id)
    
    def _on_task_failed(self, task_id: str, error: str) -> None:
        for task in self._tasks:
            if task.id == task_id:
                task.status = DownloadStatus.FAILED
                task.error = error
                break
        self.task_failed.emit(task_id, error)
    
    def _on_worker_finished(self) -> None:
        self._is_running = False
        self._worker = None
        self.all_completed.emit()
    
    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        for task in self._tasks:
            if task.id == task_id:
                return task
        return None
    
    def get_all_tasks(self) -> List[DownloadTask]:
        return self._tasks.copy()
    
    def clear_completed(self) -> None:
        self._tasks = [t for t in self._tasks if t.status != DownloadStatus.COMPLETED]
    
    @property
    def is_running(self) -> bool:
        return self._is_running
    
    @property
    def download_dir(self) -> str:
        return self._download_dir
    
    @download_dir.setter
    def download_dir(self, value: str) -> None:
        self._download_dir = value
