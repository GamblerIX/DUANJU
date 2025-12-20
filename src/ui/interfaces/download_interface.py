"""下载管理界面实现"""
from typing import Optional, Dict
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
    QListWidgetItem, QProgressBar, QFileDialog
)
from qfluentwidgets import (
    ScrollArea, SubtitleLabel, BodyLabel, CaptionLabel,
    PushButton, FluentIcon, ProgressBar
)

from ...utils.log_manager import get_logger
from ...services.download_service_v2 import DownloadServiceV2, DownloadTask, DownloadStatus

logger = get_logger()


class DownloadItemWidget(QWidget):
    """下载项控件"""
    
    def __init__(self, task: DownloadTask, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._task = task
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # 标题行
        title_layout = QHBoxLayout()
        self._title_label = BodyLabel(f"{self._task.drama.name}")
        self._title_label.setWordWrap(True)
        title_layout.addWidget(self._title_label, 1)
        
        self._status_label = CaptionLabel(self._get_status_text())
        title_layout.addWidget(self._status_label)
        layout.addLayout(title_layout)
        
        # 剧集信息
        self._episode_label = CaptionLabel(self._task.episode.title)
        layout.addWidget(self._episode_label)
        
        # 进度条
        self._progress_bar = ProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(int(self._task.progress))
        layout.addWidget(self._progress_bar)
        
        # 进度文本
        self._progress_label = CaptionLabel(self._get_progress_text())
        layout.addWidget(self._progress_label)
    
    def _get_status_text(self) -> str:
        status_map = {
            DownloadStatus.PENDING: "等待中",
            DownloadStatus.FETCHING: "获取信息...",
            DownloadStatus.DOWNLOADING: "下载中",
            DownloadStatus.PAUSED: "已暂停",
            DownloadStatus.COMPLETED: "已完成",
            DownloadStatus.FAILED: "失败",
            DownloadStatus.CANCELLED: "已取消",
        }
        return status_map.get(self._task.status, "未知")
    
    def _get_progress_text(self) -> str:
        text = ""
        if self._task.total_bytes > 0:
            downloaded_mb = self._task.downloaded_bytes / (1024 * 1024)
            total_mb = self._task.total_bytes / (1024 * 1024)
            text = f"{downloaded_mb:.1f} MB / {total_mb:.1f} MB"
        
        if self._task.status == DownloadStatus.DOWNLOADING and self._task.speed > 0:
            speed_mb = self._task.speed / (1024 * 1024)
            text += f" ({speed_mb:.1f} MB/s)"
            
        return text
    
    def update_progress(self, progress: float, downloaded: int, total: int, speed: float) -> None:
        """更新进度"""
        self._task.progress = progress
        self._task.downloaded_bytes = downloaded
        self._task.total_bytes = total
        self._task.speed = speed
        
        self._progress_bar.setValue(int(progress))
        self._progress_label.setText(self._get_progress_text())
        self._status_label.setText("下载中")
    
    def update_status(self, status: DownloadStatus, error: str = "") -> None:
        """更新状态"""
        self._task.status = status
        self._task.error = error
        self._status_label.setText(self._get_status_text())
        
        if status == DownloadStatus.COMPLETED:
            self._progress_bar.setValue(100)
            self._progress_label.setText("下载完成")
        elif status == DownloadStatus.FAILED:
            self._progress_label.setText(f"错误: {error}")
    
    @property
    def task_id(self) -> str:
        return self._task.id


class DownloadInterface(ScrollArea):
    """下载管理界面"""
    
    def __init__(
        self,
        download_service: DownloadServiceV2,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self._download_service = download_service
        self._item_widgets: Dict[str, DownloadItemWidget] = {}
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self) -> None:
        self.setObjectName("downloadInterface")
        self.setWidgetResizable(True)
        
        # 设置滚动区域背景透明，让主题正确应用
        self.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.viewport().setStyleSheet("background: transparent;")
        
        # 主容器
        self._container = QWidget()
        self._container.setObjectName("downloadContainer")
        self._container.setStyleSheet("background: transparent;")
        self.setWidget(self._container)
        
        layout = QVBoxLayout(self._container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # 标题栏
        header_layout = QHBoxLayout()
        self._title_label = SubtitleLabel("下载管理")
        header_layout.addWidget(self._title_label)
        header_layout.addStretch()
        
        # 打开下载目录按钮
        self._open_dir_btn = PushButton("打开目录", self, FluentIcon.FOLDER)
        self._open_dir_btn.clicked.connect(self._open_download_dir)
        header_layout.addWidget(self._open_dir_btn)
        
        # 清除已完成按钮
        self._clear_btn = PushButton("清除已完成", self, FluentIcon.DELETE)
        self._clear_btn.clicked.connect(self._clear_completed)
        header_layout.addWidget(self._clear_btn)
        
        layout.addLayout(header_layout)
        
        # 空状态提示（居中显示）
        self._empty_label = BodyLabel("暂无下载任务")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._empty_label, 1)
        
        # 下载列表容器（有任务时显示）
        self._list_container = QWidget()
        self._list_container.hide()
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(8)
        self._list_layout.addStretch()
        
        layout.addWidget(self._list_container, 1)
    
    def _connect_signals(self) -> None:
        self._download_service.task_added.connect(self._on_task_added)
        self._download_service.task_started.connect(self._on_task_started)
        self._download_service.task_progress.connect(self._on_task_progress)
        self._download_service.task_completed.connect(self._on_task_completed)
        self._download_service.task_failed.connect(self._on_task_failed)
    
    def _on_task_added(self, task: DownloadTask) -> None:
        """处理任务添加"""
        self._empty_label.hide()
        self._list_container.show()
        
        item_widget = DownloadItemWidget(task)
        self._item_widgets[task.id] = item_widget
        
        # 插入到列表顶部（stretch之前）
        self._list_layout.insertWidget(0, item_widget)
    
    def _on_task_started(self, task_id: str) -> None:
        """处理任务开始"""
        if task_id in self._item_widgets:
            self._item_widgets[task_id].update_status(DownloadStatus.FETCHING)
    
    def _on_task_progress(self, task_id: str, progress: float, downloaded: int, total: int, speed: float) -> None:
        """处理进度更新"""
        if task_id in self._item_widgets:
            self._item_widgets[task_id].update_progress(progress, downloaded, total, speed)
    
    def _on_task_completed(self, task_id: str) -> None:
        """处理任务完成"""
        if task_id in self._item_widgets:
            self._item_widgets[task_id].update_status(DownloadStatus.COMPLETED)
    
    def _on_task_failed(self, task_id: str, error: str) -> None:
        """处理任务失败"""
        if task_id in self._item_widgets:
            self._item_widgets[task_id].update_status(DownloadStatus.FAILED, error)
    
    def _open_download_dir(self) -> None:
        """打开下载目录"""
        import os
        import subprocess
        download_dir = self._download_service.download_dir
        if os.path.exists(download_dir):
            subprocess.run(['explorer', download_dir])
        else:
            os.makedirs(download_dir, exist_ok=True)
            subprocess.run(['explorer', download_dir])
    
    def _clear_completed(self) -> None:
        """清除已完成的任务"""
        completed_ids = [
            task_id for task_id, widget in self._item_widgets.items()
            if widget._task.status == DownloadStatus.COMPLETED
        ]
        
        for task_id in completed_ids:
            widget = self._item_widgets.pop(task_id)
            self._list_layout.removeWidget(widget)
            widget.deleteLater()
        
        self._download_service.clear_completed()
        
        # 检查是否为空
        if not self._item_widgets:
            self._list_container.hide()
            self._empty_label.show()
