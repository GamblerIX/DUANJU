"""下载服务实现"""
import os
import aiohttp
import asyncio
from typing import Optional, List
from dataclasses import dataclass, field
from enum import Enum
from PyQt6.QtCore import QObject, pyqtSignal, QThread

from ..core.models import EpisodeInfo, DramaInfo, VideoInfo
from ..core.utils.log_manager import get_logger
from ..data.api.api_client import ApiClient
from ..data.api.response_parser import ResponseParser

logger = get_logger()


class DownloadStatus(Enum):
    """下载状态"""
    PENDING = "pending"      # 等待中
    FETCHING = "fetching"    # 获取视频信息
    DOWNLOADING = "downloading"  # 下载中
    COMPLETED = "completed"  # 完成
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"  # 已取消


@dataclass
class DownloadTask:
    """下载任务"""
    drama: DramaInfo
    episode: EpisodeInfo
    status: DownloadStatus = DownloadStatus.PENDING
    progress: float = 0.0  # 0-100
    video_url: str = ""
    file_path: str = ""
    error: str = ""
    downloaded_bytes: int = 0
    total_bytes: int = 0
    
    @property
    def id(self) -> str:
        return f"{self.drama.book_id}_{self.episode.video_id}"


class DownloadWorker(QThread):
    """下载工作线程"""
    
    # 信号
    task_started = pyqtSignal(str)  # task_id
    task_progress = pyqtSignal(str, float, int, int)  # task_id, progress, downloaded, total
    task_completed = pyqtSignal(str)  # task_id
    task_failed = pyqtSignal(str, str)  # task_id, error
    video_info_fetched = pyqtSignal(str, str)  # task_id, video_url
    
    def __init__(
        self,
        api_client: ApiClient,
        tasks: List[DownloadTask],
        download_dir: str,
        quality: str = "1080p",
        parent: Optional[QObject] = None
    ):
        super().__init__(parent)
        self._api_client = api_client
        self._tasks = tasks
        self._download_dir = download_dir
        self._quality = quality
        self._cancelled = False
        self._current_task_id: Optional[str] = None
    
    def run(self):
        """执行下载任务队列"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._process_tasks())
        finally:
            loop.close()
    
    async def _process_tasks(self):
        """处理所有任务（单并发）"""
        for task in self._tasks:
            if self._cancelled:
                break
            
            self._current_task_id = task.id
            self.task_started.emit(task.id)
            
            try:
                # 1. 获取视频URL
                task.status = DownloadStatus.FETCHING
                video_url = await self._fetch_video_url(task.episode.video_id)
                
                if not video_url:
                    raise Exception("获取视频地址失败")
                
                task.video_url = video_url
                self.video_info_fetched.emit(task.id, video_url)
                
                if self._cancelled:
                    break
                
                # 2. 下载视频
                task.status = DownloadStatus.DOWNLOADING
                await self._download_video(task)
                
                if not self._cancelled:
                    task.status = DownloadStatus.COMPLETED
                    task.progress = 100.0
                    self.task_completed.emit(task.id)
                    
            except Exception as e:
                logger.error(f"Download task failed: {task.id}, error: {e}")
                task.status = DownloadStatus.FAILED
                task.error = str(e)
                self.task_failed.emit(task.id, str(e))
    
    async def _fetch_video_url(self, video_id: str) -> str:
        """获取视频URL"""
        response = await self._api_client.get(
            params={"video_id": video_id, "level": self._quality, "type": "json"}
        )
        
        if response.success:
            video_info = ResponseParser.parse_video_info(response.body)
            return video_info.url
        return ""
    
    async def _download_video(self, task: DownloadTask):
        """下载视频文件"""
        # 创建下载目录
        drama_dir = os.path.join(self._download_dir, self._sanitize_filename(task.drama.name))
        os.makedirs(drama_dir, exist_ok=True)
        
        # 文件名
        filename = f"{task.episode.title}.mp4"
        file_path = os.path.join(drama_dir, self._sanitize_filename(filename))
        task.file_path = file_path
        
        # 下载
        timeout = aiohttp.ClientTimeout(total=3600)  # 1小时超时
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
        """清理文件名中的非法字符"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name.strip()
    
    def cancel(self):
        """取消下载"""
        self._cancelled = True


class DownloadService(QObject):
    """下载服务"""
    
    # 信号
    task_added = pyqtSignal(object)  # DownloadTask
    task_started = pyqtSignal(str)  # task_id
    task_progress = pyqtSignal(str, float, int, int)  # task_id, progress, downloaded, total
    task_completed = pyqtSignal(str)  # task_id
    task_failed = pyqtSignal(str, str)  # task_id, error
    all_completed = pyqtSignal()
    
    def __init__(
        self,
        api_client: ApiClient,
        download_dir: str,
        quality: str = "1080p",
        parent: Optional[QObject] = None
    ):
        super().__init__(parent)
        self._api_client = api_client
        self._download_dir = download_dir
        self._quality = quality
        self._tasks: List[DownloadTask] = []
        self._worker: Optional[DownloadWorker] = None
        self._is_running = False
    
    def add_tasks(self, drama: DramaInfo, episodes: List[EpisodeInfo]) -> None:
        """添加下载任务"""
        for episode in episodes:
            task = DownloadTask(drama=drama, episode=episode)
            # 检查是否已存在
            if not any(t.id == task.id for t in self._tasks):
                self._tasks.append(task)
                self.task_added.emit(task)
                logger.info(f"Download task added: {task.id}")
    
    def start(self) -> None:
        """开始下载"""
        if self._is_running:
            return
        
        pending_tasks = [t for t in self._tasks if t.status == DownloadStatus.PENDING]
        if not pending_tasks:
            return
        
        self._is_running = True
        self._worker = DownloadWorker(
            self._api_client,
            pending_tasks,
            self._download_dir,
            self._quality,
            self
        )
        self._worker.task_started.connect(self._on_task_started)
        self._worker.task_progress.connect(self._on_task_progress)
        self._worker.task_completed.connect(self._on_task_completed)
        self._worker.task_failed.connect(self._on_task_failed)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()
    
    def cancel(self) -> None:
        """取消所有下载"""
        if self._worker:
            self._worker.cancel()
            self._worker.wait(3000)  # 等待最多3秒
            self._worker = None
            self._is_running = False
    
    def _on_task_started(self, task_id: str) -> None:
        self.task_started.emit(task_id)
    
    def _on_task_progress(self, task_id: str, progress: float, downloaded: int, total: int) -> None:
        # 更新任务状态
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
        """获取任务"""
        for task in self._tasks:
            if task.id == task_id:
                return task
        return None
    
    def get_all_tasks(self) -> List[DownloadTask]:
        """获取所有任务"""
        return self._tasks.copy()
    
    def clear_completed(self) -> None:
        """清除已完成的任务"""
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
