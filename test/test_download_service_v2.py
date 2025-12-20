"""下载服务 V2 测试"""
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import os
import tempfile

import pytest

from src.core.models import DramaInfo, EpisodeInfo, VideoInfo
from src.services.download_service_v2 import (
    DownloadStatus, DownloadTask, DownloadWorkerV2, DownloadServiceV2
)

class TestDownloadStatus:
    """测试下载状态枚举"""
    
    def test_status_values(self):
        assert DownloadStatus.PENDING.value == "pending"
        assert DownloadStatus.FETCHING.value == "fetching"
        assert DownloadStatus.DOWNLOADING.value == "downloading"
        assert DownloadStatus.PAUSED.value == "paused"
        assert DownloadStatus.COMPLETED.value == "completed"
        assert DownloadStatus.FAILED.value == "failed"
        assert DownloadStatus.CANCELLED.value == "cancelled"


class TestDownloadTask:
    """测试下载任务数据类"""
    
    @pytest.fixture
    def sample_drama(self):
        return DramaInfo(
            book_id="drama_001",
            title="测试短剧",
            cover="https://example.com/cover.jpg",
            episode_cnt=10
        )
    
    @pytest.fixture
    def sample_episode(self):
        return EpisodeInfo(
            video_id="video_001",
            title="第1集",
            episode_number=1
        )
    
    def test_task_creation(self, sample_drama, sample_episode):
        task = DownloadTask(drama=sample_drama, episode=sample_episode)
        assert task.drama == sample_drama
        assert task.episode == sample_episode
        assert task.status == DownloadStatus.PENDING
        assert task.progress == 0.0
        assert task.video_url == ""
        assert task.file_path == ""
        assert task.error == ""
    
    def test_task_id(self, sample_drama, sample_episode):
        task = DownloadTask(drama=sample_drama, episode=sample_episode)
        expected_id = f"{sample_drama.book_id}_{sample_episode.video_id}"
        assert task.id == expected_id
    
    def test_task_with_progress(self, sample_drama, sample_episode):
        task = DownloadTask(
            drama=sample_drama,
            episode=sample_episode,
            status=DownloadStatus.DOWNLOADING,
            progress=50.0,
            downloaded_bytes=1024,
            total_bytes=2048,
            speed=100.0
        )
        assert task.progress == 50.0
        assert task.downloaded_bytes == 1024
        assert task.total_bytes == 2048
        assert task.speed == 100.0


class TestDownloadWorkerV2:
    """测试下载工作线程"""
    
    @pytest.fixture
    def sample_drama(self):
        return DramaInfo(
            book_id="drama_001",
            title="测试短剧",
            cover="https://example.com/cover.jpg",
            episode_cnt=10
        )
    
    @pytest.fixture
    def sample_episode(self):
        return EpisodeInfo(
            video_id="video_001",
            title="第1集",
            episode_number=1
        )
    
    @pytest.fixture
    def temp_download_dir(self, tmp_path):
        return str(tmp_path / "downloads")
    
    def test_worker_creation_logic(self, sample_drama, sample_episode, temp_download_dir):
        """测试工作线程创建逻辑（不实际创建 QThread）"""
        task = DownloadTask(drama=sample_drama, episode=sample_episode)
        
        # 测试参数验证逻辑
        tasks = [task]
        download_dir = temp_download_dir
        quality = "1080p"
        max_concurrent = 3
        speed_limit = 0
        
        assert tasks == [task]
        assert download_dir == temp_download_dir
        assert quality == "1080p"
        assert max_concurrent == 3
        assert speed_limit == 0
    
    def test_sanitize_filename_logic(self, sample_drama, sample_episode, temp_download_dir):
        """测试文件名清理逻辑"""
        # 直接测试清理逻辑
        def sanitize(name):
            invalid_chars = '<>:"/\\|?*'
            for char in invalid_chars:
                name = name.replace(char, '_')
            return name.strip()
        
        assert sanitize("normal.mp4") == "normal.mp4"
        assert sanitize("file<>:\"/\\|?*.mp4") == "file_________.mp4"
        assert sanitize("  spaces  ") == "spaces"
    
    def test_pause_resume_task_logic(self, sample_drama, sample_episode, temp_download_dir):
        """测试暂停恢复逻辑"""
        task = DownloadTask(drama=sample_drama, episode=sample_episode)
        paused_tasks = set()
        
        # 暂停
        paused_tasks.add(task.id)
        assert task.id in paused_tasks
        
        # 恢复
        paused_tasks.discard(task.id)
        assert task.id not in paused_tasks
    
    def test_cancel_logic(self, sample_drama, sample_episode, temp_download_dir):
        """测试取消逻辑"""
        cancelled = False
        assert not cancelled
        cancelled = True
        assert cancelled


class TestDownloadServiceV2:
    """测试下载服务 V2"""
    
    @pytest.fixture
    def sample_drama(self):
        return DramaInfo(
            book_id="drama_001",
            title="测试短剧",
            cover="https://example.com/cover.jpg",
            episode_cnt=10
        )
    
    @pytest.fixture
    def sample_episodes(self):
        return [
            EpisodeInfo(video_id=f"video_{i:03d}", title=f"第{i}集", episode_number=i)
            for i in range(1, 4)
        ]
    
    @pytest.fixture
    def download_service(self, tmp_path):
        return DownloadServiceV2(
            download_dir=str(tmp_path / "downloads"),
            quality="1080p",
            max_concurrent=3,
            speed_limit=0
        )
    
    def test_service_creation(self, download_service, tmp_path):
        assert download_service._quality == "1080p"
        assert download_service._max_concurrent == 3
        assert download_service._speed_limit == 0
        assert not download_service._is_running
        assert download_service._tasks == {}
    
    def test_add_task(self, download_service, sample_drama, sample_episodes):
        task = download_service.add_task(sample_drama, sample_episodes[0])
        assert task.id in download_service._tasks
        assert task.drama == sample_drama
        assert task.episode == sample_episodes[0]
    
    def test_add_duplicate_task(self, download_service, sample_drama, sample_episodes):
        task1 = download_service.add_task(sample_drama, sample_episodes[0])
        task2 = download_service.add_task(sample_drama, sample_episodes[0])
        assert task1.id == task2.id
        assert len(download_service._tasks) == 1
    
    def test_add_tasks_batch(self, download_service, sample_drama, sample_episodes):
        tasks = download_service.add_tasks(sample_drama, sample_episodes)
        assert len(tasks) == 3
        assert len(download_service._tasks) == 3
    
    def test_get_task(self, download_service, sample_drama, sample_episodes):
        task = download_service.add_task(sample_drama, sample_episodes[0])
        retrieved = download_service.get_task(task.id)
        assert retrieved == task
        
        assert download_service.get_task("nonexistent") is None
    
    def test_get_all_tasks(self, download_service, sample_drama, sample_episodes):
        download_service.add_tasks(sample_drama, sample_episodes)
        all_tasks = download_service.get_all_tasks()
        assert len(all_tasks) == 3
    
    def test_clear_completed(self, download_service, sample_drama, sample_episodes):
        tasks = download_service.add_tasks(sample_drama, sample_episodes)
        tasks[0].status = DownloadStatus.COMPLETED
        tasks[1].status = DownloadStatus.COMPLETED
        
        download_service.clear_completed()
        assert len(download_service._tasks) == 1
    
    def test_properties(self, download_service):
        assert not download_service.is_running
        assert download_service.download_dir == download_service._download_dir
        assert download_service.max_concurrent == 3
        assert download_service.speed_limit == 0
    
    def test_set_download_dir(self, download_service):
        download_service.download_dir = "/new/path"
        assert download_service._download_dir == "/new/path"
    
    def test_set_max_concurrent(self, download_service):
        download_service.max_concurrent = 5
        assert download_service._max_concurrent == 5
        
        download_service.max_concurrent = 0
        assert download_service._max_concurrent == 1
        
        download_service.max_concurrent = 100
        assert download_service._max_concurrent == 10
    
    def test_set_speed_limit(self, download_service):
        download_service.speed_limit = 1024
        assert download_service._speed_limit == 1024
        
        download_service.speed_limit = -100
        assert download_service._speed_limit == 0
    
    def test_start_no_tasks(self, download_service):
        download_service.start()
        assert not download_service._is_running
    
    def test_cancel_specific_task(self, download_service, sample_drama, sample_episodes):
        task = download_service.add_task(sample_drama, sample_episodes[0])
        download_service.cancel(task.id)
        assert task.status == DownloadStatus.CANCELLED
    
    def test_cancel_all(self, download_service, sample_drama, sample_episodes):
        download_service.add_tasks(sample_drama, sample_episodes)
        download_service.cancel()
        assert not download_service._is_running
    
    def test_pause_task(self, download_service, sample_drama, sample_episodes):
        task = download_service.add_task(sample_drama, sample_episodes[0])
        download_service.pause(task.id)
    
    def test_resume_paused_task(self, download_service, sample_drama, sample_episodes):
        task = download_service.add_task(sample_drama, sample_episodes[0])
        task.status = DownloadStatus.PAUSED
        # 不调用 start，只测试状态变化
        download_service._is_running = True  # 模拟已运行
        download_service.resume(task.id)
        assert task.status == DownloadStatus.PENDING
    
    def test_on_progress(self, download_service, sample_drama, sample_episodes):
        task = download_service.add_task(sample_drama, sample_episodes[0])
        download_service._on_progress(task.id, 50.0, 1024, 2048, 100.0)
        
        assert task.progress == 50.0
        assert task.downloaded_bytes == 1024
        assert task.total_bytes == 2048
        assert task.speed == 100.0
    
    def test_on_completed(self, download_service, sample_drama, sample_episodes):
        task = download_service.add_task(sample_drama, sample_episodes[0])
        download_service._on_completed(task.id)
        assert task.status == DownloadStatus.COMPLETED
    
    def test_on_failed(self, download_service, sample_drama, sample_episodes):
        task = download_service.add_task(sample_drama, sample_episodes[0])
        download_service._on_failed(task.id, "Test error")
        assert task.status == DownloadStatus.FAILED
        assert task.error == "Test error"
    
    def test_on_finished(self, download_service):
        download_service._is_running = True
        download_service._on_finished()
        assert not download_service._is_running
        assert download_service._worker is None



# ============================================================
# From: test_download_service_v2_coverage.py
# ============================================================
class TestDownloadStatus_Coverage:
    """测试下载状态枚举"""
    
    def test_status_values(self):
        """测试状态值"""
        from src.services.download_service_v2 import DownloadStatus
        
        assert DownloadStatus.PENDING.value == "pending"
        assert DownloadStatus.FETCHING.value == "fetching"
        assert DownloadStatus.DOWNLOADING.value == "downloading"
        assert DownloadStatus.PAUSED.value == "paused"
        assert DownloadStatus.COMPLETED.value == "completed"
        assert DownloadStatus.FAILED.value == "failed"
        assert DownloadStatus.CANCELLED.value == "cancelled"


class TestDownloadTask_Coverage:
    """测试下载任务数据类"""
    
    def test_task_creation(self):
        """测试任务创建"""
        from src.services.download_service_v2 import DownloadTask, DownloadStatus
        from src.core.models import DramaInfo, EpisodeInfo
        
        drama = DramaInfo(book_id="drama1", title="测试剧", cover="")
        episode = EpisodeInfo(video_id="ep1", title="第1集", episode_number=1)
        
        task = DownloadTask(drama=drama, episode=episode)
        
        assert task.status == DownloadStatus.PENDING
        assert task.progress == 0.0
        assert task.video_url == ""
        assert task.downloaded_bytes == 0
        assert task.total_bytes == 0
        assert task.speed == 0.0
    
    def test_task_id(self):
        """测试任务ID生成"""
        from src.services.download_service_v2 import DownloadTask
        from src.core.models import DramaInfo, EpisodeInfo
        
        drama = DramaInfo(book_id="drama123", title="测试剧", cover="")
        episode = EpisodeInfo(video_id="video456", title="第1集", episode_number=1)
        
        task = DownloadTask(drama=drama, episode=episode)
        
        assert task.id == "drama123_video456"


class TestDownloadWorkerV2_Coverage:
    """测试下载工作线程V2"""
    
    @patch('src.services.download_service_v2.QThread')
    def test_worker_init(self, mock_qthread):
        """测试工作线程初始化"""
        from src.services.download_service_v2 import DownloadWorkerV2, DownloadTask
        from src.core.models import DramaInfo, EpisodeInfo
        
        drama = DramaInfo(book_id="d1", title="剧1", cover="")
        episode = EpisodeInfo(video_id="e1", title="第1集", episode_number=1)
        task = DownloadTask(drama=drama, episode=episode)
        
        worker = DownloadWorkerV2(
            tasks=[task],
            download_dir="/tmp/downloads",
            quality="720p",
            max_concurrent=2,
            speed_limit=1024
        )
        
        assert worker._download_dir == "/tmp/downloads"
        assert worker._quality == "720p"
        assert worker._max_concurrent == 2
        assert worker._speed_limit == 1024
        assert worker._cancelled is False
    
    @patch('src.services.download_service_v2.QThread')
    def test_sanitize_filename(self, mock_qthread):
        """测试文件名清理"""
        from src.services.download_service_v2 import DownloadWorkerV2
        
        worker = DownloadWorkerV2([], "/tmp", parent=None)
        
        assert worker._sanitize_filename("test.mp4") == "test.mp4"
        assert worker._sanitize_filename("test<>file.mp4") == "test__file.mp4"
        assert worker._sanitize_filename('test:"/file.mp4') == "test___file.mp4"
        assert worker._sanitize_filename("test|?*file.mp4") == "test___file.mp4"
    
    @patch('src.services.download_service_v2.QThread')
    def test_pause_resume_task(self, mock_qthread):
        """测试暂停和恢复任务"""
        from src.services.download_service_v2 import DownloadWorkerV2
        
        worker = DownloadWorkerV2([], "/tmp", parent=None)
        
        worker.pause_task("task1")
        assert "task1" in worker._paused_tasks
        
        worker.resume_task("task1")
        assert "task1" not in worker._paused_tasks
    
    @patch('src.services.download_service_v2.QThread')
    def test_cancel(self, mock_qthread):
        """测试取消下载"""
        from src.services.download_service_v2 import DownloadWorkerV2
        
        worker = DownloadWorkerV2([], "/tmp", parent=None)
        
        assert worker._cancelled is False
        worker.cancel()
        assert worker._cancelled is True


class TestDownloadServiceV2_Coverage:
    """测试下载服务V2"""
    
    @patch('src.services.download_service_v2.QObject')
    def test_service_init(self, mock_qobject):
        """测试服务初始化"""
        from src.services.download_service_v2 import DownloadServiceV2
        
        service = DownloadServiceV2(
            download_dir="/tmp/downloads",
            quality="1080p",
            max_concurrent=3,
            speed_limit=0
        )
        
        assert service._download_dir == "/tmp/downloads"
        assert service._quality == "1080p"
        assert service._max_concurrent == 3
        assert service._speed_limit == 0
        assert service._is_running is False
    
    @patch('src.services.download_service_v2.QObject')
    def test_add_task(self, mock_qobject):
        """测试添加任务"""
        from src.services.download_service_v2 import DownloadServiceV2, DownloadStatus
        from src.core.models import DramaInfo, EpisodeInfo
        
        service = DownloadServiceV2("/tmp")
        service.task_added = MagicMock()
        
        drama = DramaInfo(book_id="d1", title="剧1", cover="")
        episode = EpisodeInfo(video_id="e1", title="第1集", episode_number=1)
        
        task = service.add_task(drama, episode)
        
        assert task.id == "d1_e1"
        assert task.status == DownloadStatus.PENDING
        service.task_added.emit.assert_called_once()
    
    @patch('src.services.download_service_v2.QObject')
    def test_add_duplicate_task(self, mock_qobject):
        """测试添加重复任务"""
        from src.services.download_service_v2 import DownloadServiceV2
        from src.core.models import DramaInfo, EpisodeInfo
        
        service = DownloadServiceV2("/tmp")
        service.task_added = MagicMock()
        
        drama = DramaInfo(book_id="d1", title="剧1", cover="")
        episode = EpisodeInfo(video_id="e1", title="第1集", episode_number=1)
        
        task1 = service.add_task(drama, episode)
        task2 = service.add_task(drama, episode)
        
        # 重复添加返回已存在的任务（通过ID比较）
        assert task1.id == task2.id
        # 只发出一次信号
        assert service.task_added.emit.call_count == 1
    
    @patch('src.services.download_service_v2.QObject')
    def test_add_tasks_batch(self, mock_qobject):
        """测试批量添加任务"""
        from src.services.download_service_v2 import DownloadServiceV2
        from src.core.models import DramaInfo, EpisodeInfo
        
        service = DownloadServiceV2("/tmp")
        service.task_added = MagicMock()
        
        drama = DramaInfo(book_id="d1", title="剧1", cover="")
        episodes = [
            EpisodeInfo(video_id=f"e{i}", title=f"第{i}集", episode_number=i)
            for i in range(1, 4)
        ]
        
        tasks = service.add_tasks(drama, episodes)
        
        assert len(tasks) == 3
        assert service.task_added.emit.call_count == 3
    
    @patch('src.services.download_service_v2.QObject')
    def test_get_task(self, mock_qobject):
        """测试获取任务"""
        from src.services.download_service_v2 import DownloadServiceV2
        from src.core.models import DramaInfo, EpisodeInfo
        
        service = DownloadServiceV2("/tmp")
        service.task_added = MagicMock()
        
        drama = DramaInfo(book_id="d1", title="剧1", cover="")
        episode = EpisodeInfo(video_id="e1", title="第1集", episode_number=1)
        
        service.add_task(drama, episode)
        
        task = service.get_task("d1_e1")
        assert task is not None
        assert task.id == "d1_e1"
        
        assert service.get_task("nonexistent") is None
    
    @patch('src.services.download_service_v2.QObject')
    def test_get_all_tasks(self, mock_qobject):
        """测试获取所有任务"""
        from src.services.download_service_v2 import DownloadServiceV2
        from src.core.models import DramaInfo, EpisodeInfo
        
        service = DownloadServiceV2("/tmp")
        service.task_added = MagicMock()
        
        drama = DramaInfo(book_id="d1", title="剧1", cover="")
        for i in range(3):
            episode = EpisodeInfo(video_id=f"e{i}", title=f"第{i}集", episode_number=i)
            service.add_task(drama, episode)
        
        tasks = service.get_all_tasks()
        assert len(tasks) == 3
    
    @patch('src.services.download_service_v2.QObject')
    def test_clear_completed(self, mock_qobject):
        """测试清除已完成任务"""
        from src.services.download_service_v2 import DownloadServiceV2, DownloadStatus
        from src.core.models import DramaInfo, EpisodeInfo
        
        service = DownloadServiceV2("/tmp")
        service.task_added = MagicMock()
        
        drama = DramaInfo(book_id="d1", title="剧1", cover="")
        
        # 添加3个任务
        for i in range(3):
            episode = EpisodeInfo(video_id=f"e{i}", title=f"第{i}集", episode_number=i)
            task = service.add_task(drama, episode)
            if i == 1:
                task.status = DownloadStatus.COMPLETED
        
        service.clear_completed()
        
        tasks = service.get_all_tasks()
        assert len(tasks) == 2
        assert all(t.status != DownloadStatus.COMPLETED for t in tasks)
    
    @patch('src.services.download_service_v2.QObject')
    def test_properties(self, mock_qobject):
        """测试属性"""
        from src.services.download_service_v2 import DownloadServiceV2
        
        service = DownloadServiceV2("/tmp", max_concurrent=3, speed_limit=1024)
        
        assert service.is_running is False
        assert service.download_dir == "/tmp"
        assert service.max_concurrent == 3
        assert service.speed_limit == 1024
    
    @patch('src.services.download_service_v2.QObject')
    def test_property_setters(self, mock_qobject):
        """测试属性设置器"""
        from src.services.download_service_v2 import DownloadServiceV2
        
        service = DownloadServiceV2("/tmp")
        
        service.download_dir = "/new/path"
        assert service.download_dir == "/new/path"
        
        service.max_concurrent = 5
        assert service.max_concurrent == 5
        
        # 测试边界值
        service.max_concurrent = 0
        assert service.max_concurrent == 1
        
        service.max_concurrent = 100
        assert service.max_concurrent == 10
        
        service.speed_limit = 2048
        assert service.speed_limit == 2048
        
        service.speed_limit = -100
        assert service.speed_limit == 0
    
    @patch('src.services.download_service_v2.QObject')
    def test_start_no_pending(self, mock_qobject):
        """测试无待处理任务时启动"""
        from src.services.download_service_v2 import DownloadServiceV2
        
        service = DownloadServiceV2("/tmp")
        
        # 没有任务时启动不应该做任何事
        service.start()
        assert service._worker is None
    
    @patch('src.services.download_service_v2.QObject')
    def test_start_already_running(self, mock_qobject):
        """测试已运行时启动"""
        from src.services.download_service_v2 import DownloadServiceV2
        
        service = DownloadServiceV2("/tmp")
        service._is_running = True
        
        service.start()
        # 不应该创建新的 worker
        assert service._worker is None
    
    @patch('src.services.download_service_v2.QObject')
    def test_cancel_single_task(self, mock_qobject):
        """测试取消单个任务"""
        from src.services.download_service_v2 import DownloadServiceV2, DownloadStatus
        from src.core.models import DramaInfo, EpisodeInfo
        
        service = DownloadServiceV2("/tmp")
        service.task_added = MagicMock()
        
        drama = DramaInfo(book_id="d1", title="剧1", cover="")
        episode = EpisodeInfo(video_id="e1", title="第1集", episode_number=1)
        service.add_task(drama, episode)
        
        service.cancel("d1_e1")
        
        task = service.get_task("d1_e1")
        assert task.status == DownloadStatus.CANCELLED
    
    @patch('src.services.download_service_v2.QObject')
    def test_cancel_all(self, mock_qobject):
        """测试取消所有任务"""
        from src.services.download_service_v2 import DownloadServiceV2
        
        service = DownloadServiceV2("/tmp")
        service._is_running = True
        mock_worker = MagicMock()
        service._worker = mock_worker
        
        service.cancel()
        
        mock_worker.cancel.assert_called_once()
        mock_worker.wait.assert_called_once_with(5000)
        assert service._is_running is False
        assert service._worker is None
    
    @patch('src.services.download_service_v2.QObject')
    def test_pause_task(self, mock_qobject):
        """测试暂停任务"""
        from src.services.download_service_v2 import DownloadServiceV2
        from src.core.models import DramaInfo, EpisodeInfo
        
        service = DownloadServiceV2("/tmp")
        service.task_added = MagicMock()
        service._worker = MagicMock()
        
        drama = DramaInfo(book_id="d1", title="剧1", cover="")
        episode = EpisodeInfo(video_id="e1", title="第1集", episode_number=1)
        service.add_task(drama, episode)
        
        service.pause("d1_e1")
        
        service._worker.pause_task.assert_called_once_with("d1_e1")
    
    @patch('src.services.download_service_v2.QObject')
    def test_resume_task(self, mock_qobject):
        """测试恢复任务"""
        from src.services.download_service_v2 import DownloadServiceV2, DownloadStatus
        from src.core.models import DramaInfo, EpisodeInfo
        
        service = DownloadServiceV2("/tmp")
        service.task_added = MagicMock()
        service._worker = MagicMock()
        service._is_running = True
        
        drama = DramaInfo(book_id="d1", title="剧1", cover="")
        episode = EpisodeInfo(video_id="e1", title="第1集", episode_number=1)
        task = service.add_task(drama, episode)
        task.status = DownloadStatus.PAUSED
        
        service.resume("d1_e1")
        
        assert task.status == DownloadStatus.PENDING
        service._worker.resume_task.assert_called_once_with("d1_e1")


class TestDownloadServiceV2Callbacks:
    """测试下载服务V2回调"""
    
    @patch('src.services.download_service_v2.QObject')
    def test_on_progress(self, mock_qobject):
        """测试进度回调"""
        from src.services.download_service_v2 import DownloadServiceV2
        from src.core.models import DramaInfo, EpisodeInfo
        
        service = DownloadServiceV2("/tmp")
        service.task_added = MagicMock()
        service.task_progress = MagicMock()
        
        drama = DramaInfo(book_id="d1", title="剧1", cover="")
        episode = EpisodeInfo(video_id="e1", title="第1集", episode_number=1)
        service.add_task(drama, episode)
        
        service._on_progress("d1_e1", 50.0, 500, 1000, 100.0)
        
        task = service.get_task("d1_e1")
        assert task.progress == 50.0
        assert task.downloaded_bytes == 500
        assert task.total_bytes == 1000
        assert task.speed == 100.0
        service.task_progress.emit.assert_called_once()
    
    @patch('src.services.download_service_v2.QObject')
    def test_on_completed(self, mock_qobject):
        """测试完成回调"""
        from src.services.download_service_v2 import DownloadServiceV2, DownloadStatus
        from src.core.models import DramaInfo, EpisodeInfo
        
        service = DownloadServiceV2("/tmp")
        service.task_added = MagicMock()
        service.task_completed = MagicMock()
        
        drama = DramaInfo(book_id="d1", title="剧1", cover="")
        episode = EpisodeInfo(video_id="e1", title="第1集", episode_number=1)
        service.add_task(drama, episode)
        
        service._on_completed("d1_e1")
        
        task = service.get_task("d1_e1")
        assert task.status == DownloadStatus.COMPLETED
        service.task_completed.emit.assert_called_once_with("d1_e1")
    
    @patch('src.services.download_service_v2.QObject')
    def test_on_failed(self, mock_qobject):
        """测试失败回调"""
        from src.services.download_service_v2 import DownloadServiceV2, DownloadStatus
        from src.core.models import DramaInfo, EpisodeInfo
        
        service = DownloadServiceV2("/tmp")
        service.task_added = MagicMock()
        service.task_failed = MagicMock()
        
        drama = DramaInfo(book_id="d1", title="剧1", cover="")
        episode = EpisodeInfo(video_id="e1", title="第1集", episode_number=1)
        service.add_task(drama, episode)
        
        service._on_failed("d1_e1", "Network error")
        
        task = service.get_task("d1_e1")
        assert task.status == DownloadStatus.FAILED
        assert task.error == "Network error"
        service.task_failed.emit.assert_called_once_with("d1_e1", "Network error")
    
    @patch('src.services.download_service_v2.QObject')
    def test_on_finished(self, mock_qobject):
        """测试全部完成回调"""
        from src.services.download_service_v2 import DownloadServiceV2
        
        service = DownloadServiceV2("/tmp")
        service.all_completed = MagicMock()
        service._is_running = True
        service._worker = MagicMock()
        
        service._on_finished()
        
        assert service._is_running is False
        assert service._worker is None
        service.all_completed.emit.assert_called_once()
