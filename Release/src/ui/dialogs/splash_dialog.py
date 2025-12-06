from typing import Optional, List, Callable
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QApplication, QDialog
from qfluentwidgets import SubtitleLabel, BodyLabel, ProgressBar, PushButton, isDarkTheme, qconfig


class SplashDialog(QDialog):
    init_completed = pyqtSignal()
    init_failed = pyqtSignal(str)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._tasks: List[tuple] = []
        self._current_task = 0
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        self.setWindowTitle("初始化")
        self.setFixedSize(400, 180)
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        
        def update_theme():
            if isDarkTheme():
                self.setStyleSheet("QDialog { background-color: #202020; }")
            else:
                self.setStyleSheet("QDialog { background-color: #f9f9f9; }")
        update_theme()
        qconfig.themeChanged.connect(update_theme)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)
        self.titleLabel = SubtitleLabel("短剧搜索")
        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.titleLabel)
        self._status_label = BodyLabel("正在初始化...")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status_label)
        self._progress = ProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        layout.addWidget(self._progress)
        self._exit_btn = PushButton("退出")
        self._exit_btn.clicked.connect(self.reject)
        self._exit_btn.hide()
        layout.addWidget(self._exit_btn, alignment=Qt.AlignmentFlag.AlignCenter)
    
    def add_task(self, name: str, callback: Callable[[], bool]) -> None:
        self._tasks.append((name, callback))
    
    def start(self) -> None:
        self._current_task = 0
        if self._tasks:
            QTimer.singleShot(100, self._run_next_task)
        else:
            self._on_completed()
    
    def _run_next_task(self) -> None:
        if self._current_task >= len(self._tasks):
            self._on_completed()
            return
        name, callback = self._tasks[self._current_task]
        self._status_label.setText(f"正在{name}...")
        progress = int((self._current_task / len(self._tasks)) * 100)
        self._progress.setValue(progress)
        QApplication.processEvents()
        try:
            success = callback()
            if success:
                self._current_task += 1
                QTimer.singleShot(50, self._run_next_task)
            else:
                self._on_failed(f"{name}失败")
        except Exception as e:
            self._on_failed(f"{name}出错: {e}")
    
    def _on_completed(self) -> None:
        self._progress.setValue(100)
        self._status_label.setText("初始化完成")
        QTimer.singleShot(300, lambda: self.init_completed.emit())
        QTimer.singleShot(500, self.accept)
    
    def _on_failed(self, error: str) -> None:
        self._status_label.setText(f"初始化失败: {error}")
        self.init_failed.emit(error)
        self._exit_btn.show()
