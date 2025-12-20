"""下载服务 V2 - 支持并发下载、断点续传、暂停/取消

优化点:
1. 多任务并发下载
2. 断点续传支持
3. 暂停/恢复功能
4. 下载速度限制
5. 优雅的线程管理
"""
import os
import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass, field
from enum import Enum

from PySide6.QtCore import QObject, Signal, QThread

from ..core.models import EpisodeInfo, DramaInfo, VideoInfo
from ..utils.log_manager import get_logger
from ..data.providers.provider_registry import get_current_provider

logger = get_logger()


class DownloadStatus(Enum):
    PENDING = "pending"
    FETCHING = "fetching"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DownloadTask:
    """下载任务"""
    drama: DramaInfo
    episode: EpisodeInfo
    status: DownloadStatus = DownloadStatus.PENDING
    progress: float = 0.0
    video_url: str = ""
    file_path: str = ""
    temp_path: str = ""
    error: str = ""
    downloaded_bytes: int = 0
    total_bytes: int = 0
    speed: float = 0.0  # bytes/s
    
    @property
    def id(self) -> str:
        return f"{self.drama.book_id}_{self.episode.video_id}"


class DownloadWorkerV2(QThread):
    """下载工作线程 V2"""
    
    task_started = Signal(str)
    task_progress = Signal(str, float, int, int, float)  # id, progress, downloaded, total, speed
    task_completed = Signal(str)
    task_failed = Signal(str, str)
    task_paused = Signal(str)
    
    def __init__(
        self,
        tasks: List[DownloadTask],
        download_dir: str,
        quality: str = "1080p",
        max_concurrent: int = 3,
        speed_limit: int = 0,  # 0 = 无限制, bytes/s
        parent: Optional[QObject] = None
    ):
        super().__init__(parent)
        self._tasks = tasks
        self._download_dir = download_dir
        self._quality = quality
        self._max_concurrent = max_concurrent
        self._speed_limit = speed_limit
        self._cancelled = False
        self._paused_tasks: set = set()
        self._stop_event = asyncio.Event()
    
    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._process_tasks())
        finally:
            loop.close()
    
    async def _process_tasks(self):
        """并发处理任务"""
        semaphore = asyncio.Semaphore(self._max_concurrent)
        tasks = [self._process_single_task(task, semaphore) for task in self._tasks]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _process_single_task(self, task: DownloadTask, semaphore: asyncio.Semaphore):
        """处理单个任务"""
        async with semaphore:
            if self._cancelled or task.id in self._paused_tasks:
                return
            
            self.task_started.emit(task.id)
            
            try:
                # 获取视频 URL
                task.status = DownloadStatus.FETCHING
                video_url = await self._fetch_video_url(task.episode.video_id)
                
                if not video_url:
                    raise Exception("获取视频地址失败")
                
                task.video_url = video_url
                
                if self._cancelled or task.id in self._paused_tasks:
                    return
                
                # 下载视频
                task.status = DownloadStatus.DOWNLOADING
                await self._download_video(task)
                
                if task.id not in self._paused_tasks and not self._cancelled:
                    task.status = DownloadStatus.COMPLETED
                    task.progress = 100.0
                    self.task_completed.emit(task.id)
                    
            except Exception as e:
                logger.log_service_error("DownloadService", f"download_{task.id}", e)
                task.status = DownloadStatus.FAILED
                task.error = str(e)
                self.task_failed.emit(task.id, str(e))
    
    async def _fetch_video_url(self, video_id: str) -> str:
        """获取视频 URL"""
        provider = get_current_provider()
        if not provider:
            raise Exception("没有可用的数据提供者")
        
        video_info = await provider.get_video_url(video_id, self._quality)
        return video_info.url
    
    async def _download_video(self, task: DownloadTask):
        """下载视频（支持断点续传）"""
        drama_dir = Path(self._download_dir) / self._sanitize_filename(task.drama.name)
        drama_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{task.episode.title}.mp4"
        file_path = drama_dir / self._sanitize_filename(filename)
        temp_path = file_path.with_suffix('.tmp')
        
        task.file_path = str(file_path)
        task.temp_path = str(temp_path)
        
        # 检查已下载的字节数（断点续传）
        start_byte = 0
        if temp_path.exists():
            start_byte = temp_path.stat().st_size
            task.downloaded_bytes = start_byte
        
        headers = {}
        if start_byte > 0:
            headers['Range'] = f'bytes={start_byte}-'
            logger.info(f"Resuming download from byte {start_byte}")
        
        timeout = aiohttp.ClientTimeout(total=3600)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(task.video_url, headers=headers) as response:
                if response.status not in (200, 206):
                    raise Exception(f"HTTP {response.status}")
                
                # 获取总大小
                if response.status == 206:
                    content_range = response.headers.get('Content-Range', '')
                    if '/' in content_range:
                        task.total_bytes = int(content_range.split('/')[-1])
                else:
                    task.total_bytes = int(response.headers.get('Content-Length', 0))
                    start_byte = 0  # 服务器不支持断点续传
                
                downloaded = start_byte
                last_time = asyncio.get_event_loop().time()
                last_downloaded = downloaded
                
                mode = 'ab' if start_byte > 0 else 'wb'
                async with aiofiles.open(temp_path, mode) as f:
                    async for chunk in response.content.iter_chunked(65536):
                        if self._cancelled or task.id in self._paused_tasks:
                            if task.id in self._paused_tasks:
                                task.status = DownloadStatus.PAUSED
                                self.task_paused.emit(task.id)
                            break
                        
                        await f.write(chunk)
                        downloaded += len(chunk)
                        task.downloaded_bytes = downloaded
                        
                        # 计算速度
                        current_time = asyncio.get_event_loop().time()
                        time_diff = current_time - last_time
                        if time_diff >= 0.5:
                            speed = (downloaded - last_downloaded) / time_diff
                            task.speed = speed
                            last_time = current_time
                            last_downloaded = downloaded
                        
                        # 计算进度
                        if task.total_bytes > 0:
                            task.progress = (downloaded / task.total_bytes) * 100
                            self.task_progress.emit(
                                task.id, task.progress, downloaded, 
                                task.total_bytes, task.speed
                            )
                        
                        # 速度限制
                        if self._speed_limit > 0:
                            expected_time = len(chunk) / self._speed_limit
                            await asyncio.sleep(max(0, expected_time - 0.001))
        
        # 下载完成，重命名临时文件
        if task.status == DownloadStatus.DOWNLOADING and not self._cancelled:
            if temp_path.exists():
                temp_path.rename(file_path)
    
    def _sanitize_filename(self, name: str) -> str:
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name.strip()
    
    def pause_task(self, task_id: str):
        """暂停任务"""
        self._paused_tasks.add(task_id)
    
    def resume_task(self, task_id: str):
        """恢复任务"""
        self._paused_tasks.discard(task_id)
    
    def cancel(self):
        """取消所有下载"""
        self._cancelled = True


class DownloadServiceV2(QObject):
    """下载服务 V2"""
    
    task_added = Signal(object)
    task_started = Signal(str)
    task_progress = Signal(str, float, int, int, float)
    task_completed = Signal(str)
    task_failed = Signal(str, str)
    task_paused = Signal(str)
    all_completed = Signal()
    
    def __init__(
        self,
        download_dir: str,
        quality: str = "1080p",
        max_concurrent: int = 3,
        speed_limit: int = 0,
        parent: Optional[QObject] = None
    ):
        super().__init__(parent)
        self._download_dir = download_dir
        self._quality = quality
        self._max_concurrent = max_concurrent
        self._speed_limit = speed_limit
        self._tasks: Dict[str, DownloadTask] = {}
        self._worker: Optional[DownloadWorkerV2] = None
        self._is_running = False
    
    def add_task(self, drama: DramaInfo, episode: EpisodeInfo) -> DownloadTask:
        """添加单个任务"""
        task = DownloadTask(drama=drama, episode=episode)
        if task.id not in self._tasks:
            self._tasks[task.id] = task
            self.task_added.emit(task)
        return task
    
    def add_tasks(self, drama: DramaInfo, episodes: List[EpisodeInfo]) -> List[DownloadTask]:
        """批量添加任务"""
        return [self.add_task(drama, ep) for ep in episodes]
    
    def start(self) -> None:
        """开始下载"""
        if self._is_running:
            return
        
        pending = [t for t in self._tasks.values() 
                   if t.status in (DownloadStatus.PENDING, DownloadStatus.PAUSED)]
        if not pending:
            return
        
        self._is_running = True
        self._worker = DownloadWorkerV2(
            pending, self._download_dir, self._quality,
            self._max_concurrent, self._speed_limit, self
        )
        self._connect_signals()
        self._worker.start()
    
    def _connect_signals(self):
        self._worker.task_started.connect(self.task_started)
        self._worker.task_progress.connect(self._on_progress)
        self._worker.task_completed.connect(self._on_completed)
        self._worker.task_failed.connect(self._on_failed)
        self._worker.task_paused.connect(self.task_paused)
        self._worker.finished.connect(self._on_finished)
    
    def _on_progress(self, task_id: str, progress: float, downloaded: int, total: int, speed: float):
        if task_id in self._tasks:
            task = self._tasks[task_id]
            task.progress = progress
            task.downloaded_bytes = downloaded
            task.total_bytes = total
            task.speed = speed
        self.task_progress.emit(task_id, progress, downloaded, total, speed)
    
    def _on_completed(self, task_id: str):
        if task_id in self._tasks:
            self._tasks[task_id].status = DownloadStatus.COMPLETED
        self.task_completed.emit(task_id)
    
    def _on_failed(self, task_id: str, error: str):
        if task_id in self._tasks:
            self._tasks[task_id].status = DownloadStatus.FAILED
            self._tasks[task_id].error = error
        self.task_failed.emit(task_id, error)
    
    def _on_finished(self):
        self._is_running = False
        self._worker = None
        self.all_completed.emit()
    
    def pause(self, task_id: str) -> None:
        """暂停任务"""
        if self._worker and task_id in self._tasks:
            self._worker.pause_task(task_id)
    
    def resume(self, task_id: str) -> None:
        """恢复任务"""
        if task_id in self._tasks:
            task = self._tasks[task_id]
            if task.status == DownloadStatus.PAUSED:
                task.status = DownloadStatus.PENDING
                if not self._is_running:
                    self.start()
                elif self._worker:
                    self._worker.resume_task(task_id)
    
    def cancel(self, task_id: Optional[str] = None) -> None:
        """取消任务"""
        if task_id:
            if task_id in self._tasks:
                self._tasks[task_id].status = DownloadStatus.CANCELLED
                if self._worker:
                    self._worker.pause_task(task_id)
        else:
            # 取消所有
            if self._worker:
                self._worker.cancel()
                self._worker.wait(5000)
                self._worker = None
            self._is_running = False
    
    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        return self._tasks.get(task_id)
    
    def get_all_tasks(self) -> List[DownloadTask]:
        return list(self._tasks.values())
    
    def clear_completed(self) -> None:
        self._tasks = {k: v for k, v in self._tasks.items() 
                       if v.status != DownloadStatus.COMPLETED}
    
    @property
    def is_running(self) -> bool:
        return self._is_running
    
    @property
    def download_dir(self) -> str:
        return self._download_dir
    
    @download_dir.setter
    def download_dir(self, value: str) -> None:
        self._download_dir = value
    
    @property
    def max_concurrent(self) -> int:
        return self._max_concurrent
    
    @max_concurrent.setter
    def max_concurrent(self, value: int) -> None:
        self._max_concurrent = max(1, min(10, value))
    
    @property
    def speed_limit(self) -> int:
        return self._speed_limit
    
    @speed_limit.setter
    def speed_limit(self, value: int) -> None:
        self._speed_limit = max(0, value)
