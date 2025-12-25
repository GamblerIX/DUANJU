"""启动画面对话框实现"""
from typing import Optional, List, Callable
from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QApplication, QDialog
from qfluentwidgets import (
    SubtitleLabel, BodyLabel, ProgressBar, PushButton
)

from ...utils.log_manager import get_logger

logger = get_logger()


class SplashDialog(QDialog):
    """
    启动画面对话框
    
    显示初始化进度
    """
    
    # 信号
    init_completed = Signal()
    init_failed = Signal(str)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._tasks: List[tuple] = []  # (name, callback)
        self._current_task = 0
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """初始化UI"""
        self.setWindowTitle("初始化")
        self.setFixedSize(400, 180)
        self.setModal(True)
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint
        )
        
        # 设置对话框背景跟随主题（使用 qfluentwidgets 的主题色）
        from qfluentwidgets import isDarkTheme, qconfig
        from qfluentwidgets.common.config import Theme
        
        def update_theme():
            if isDarkTheme():
                self.setStyleSheet("QDialog { background-color: #202020; }")
            else:
                self.setStyleSheet("QDialog { background-color: #f9f9f9; }")
        
        update_theme()
        # 监听主题变化
        qconfig.themeChanged.connect(update_theme)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)
        
        # 标题
        self.titleLabel = SubtitleLabel("短剧搜索")
        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.titleLabel)
        
        # 状态文本
        self._status_label = BodyLabel("正在初始化...")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status_label)
        
        # 进度条
        self._progress = ProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        layout.addWidget(self._progress)
        
        # 退出按钮（初始隐藏）
        self._exit_btn = PushButton("退出")
        self._exit_btn.clicked.connect(self.reject)
        self._exit_btn.hide()
        layout.addWidget(self._exit_btn, alignment=Qt.AlignmentFlag.AlignCenter)
    
    def add_task(self, name: str, callback: Callable[[], bool]) -> None:
        """
        添加初始化任务
        
        Args:
            name: 任务名称
            callback: 任务回调，返回 True 表示成功
        """
        self._tasks.append((name, callback))
    
    def start(self) -> None:
        """开始执行初始化任务"""
        logger.info("Starting initialization...")
        self._current_task = 0
        if self._tasks:
            QTimer.singleShot(100, self._run_next_task)
        else:
            self._on_completed()
    
    def _run_next_task(self) -> None:
        """执行下一个任务"""
        if self._current_task >= len(self._tasks):
            self._on_completed()
            return
        
        name, callback = self._tasks[self._current_task]
        self._status_label.setText(f"正在{name}...")
        logger.debug(f"Running init task: {name}")
        
        # 更新进度
        progress = int((self._current_task / len(self._tasks)) * 100)
        self._progress.setValue(progress)
        
        # 处理事件，保持 UI 响应
        QApplication.processEvents()
        
        try:
            success = callback()
            if success:
                logger.debug(f"Init task completed: {name}")
                self._current_task += 1
                QTimer.singleShot(50, self._run_next_task)
            else:
                logger.warning(f"初始化任务失败: {name}")
                self._on_failed(f"{name}失败")
        except Exception as e:
            logger.warning(f"初始化任务出错: {name} - {e}")
            self._on_failed(f"{name}出错: {e}")
    
    def _on_completed(self) -> None:
        """初始化完成"""
        self._progress.setValue(100)
        self._status_label.setText("初始化完成")
        logger.info("Initialization completed")
        QTimer.singleShot(300, lambda: self.init_completed.emit())
        QTimer.singleShot(500, self.accept)
    
    def _on_failed(self, error: str) -> None:
        """初始化失败"""
        self._status_label.setText(f"初始化失败: {error}")
        logger.warning(f"初始化失败: {error}")
        self.init_failed.emit(error)
        # 显示退出按钮
        self._exit_btn.show()
