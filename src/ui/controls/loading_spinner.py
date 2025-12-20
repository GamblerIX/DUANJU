"""加载指示器控件实现"""
from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import IndeterminateProgressRing, BodyLabel


class LoadingSpinner(QWidget):
    """
    加载指示器控件
    
    显示加载动画和可选的加载文本
    """
    
    def __init__(
        self, 
        text: str = "加载中...",
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self._text = text
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)
        
        # 使用不确定进度环（会自动旋转动画）
        self._progress_ring = IndeterminateProgressRing()
        self._progress_ring.setFixedSize(48, 48)
        self._progress_ring.setStrokeWidth(4)
        layout.addWidget(self._progress_ring, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 加载文本
        self._label = BodyLabel(self._text)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._label, alignment=Qt.AlignmentFlag.AlignCenter)
    
    def set_text(self, text: str) -> None:
        """设置加载文本"""
        self._text = text
        self._label.setText(text)
    
    def start(self) -> None:
        """开始加载动画"""
        self.show()
    
    def stop(self) -> None:
        """停止加载动画"""
        self.hide()
    
    @property
    def text(self) -> str:
        """获取加载文本"""
        return self._text


class OverlayLoadingSpinner(QWidget):
    """
    覆盖式加载指示器
    
    覆盖在父控件上显示加载状态
    """
    
    def __init__(
        self,
        text: str = "加载中...",
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self._setup_ui(text)
        self.hide()
    
    def _setup_ui(self, text: str) -> None:
        """初始化UI"""
        # 设置半透明背景
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0.3);")
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self._spinner = LoadingSpinner(text)
        self._spinner.setStyleSheet("background-color: transparent;")
        layout.addWidget(self._spinner)
    
    def set_text(self, text: str) -> None:
        """设置加载文本"""
        self._spinner.set_text(text)
    
    def start(self) -> None:
        """开始加载"""
        if self.parent():
            self.setGeometry(self.parent().rect())
        self.show()
        self.raise_()
    
    def stop(self) -> None:
        """停止加载"""
        self.hide()
    
    def resizeEvent(self, event) -> None:
        """调整大小时跟随父控件"""
        super().resizeEvent(event)
        if self.parent():
            self.setGeometry(self.parent().rect())
