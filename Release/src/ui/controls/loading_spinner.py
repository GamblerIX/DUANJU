from typing import Optional
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import IndeterminateProgressRing, BodyLabel


class LoadingSpinner(QWidget):
    def __init__(self, text: str = "加载中...", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._text = text
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)
        self._progress_ring = IndeterminateProgressRing()
        self._progress_ring.setFixedSize(48, 48)
        self._progress_ring.setStrokeWidth(4)
        layout.addWidget(self._progress_ring, alignment=Qt.AlignmentFlag.AlignCenter)
        self._label = BodyLabel(self._text)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._label, alignment=Qt.AlignmentFlag.AlignCenter)
    
    def set_text(self, text: str) -> None:
        self._text = text
        self._label.setText(text)
    
    def start(self) -> None:
        self.show()
    
    def stop(self) -> None:
        self.hide()
    
    @property
    def text(self) -> str:
        return self._text


class OverlayLoadingSpinner(QWidget):
    def __init__(self, text: str = "加载中...", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui(text)
        self.hide()
    
    def _setup_ui(self, text: str) -> None:
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0.3);")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._spinner = LoadingSpinner(text)
        self._spinner.setStyleSheet("background-color: transparent;")
        layout.addWidget(self._spinner)
    
    def set_text(self, text: str) -> None:
        self._spinner.set_text(text)
    
    def start(self) -> None:
        if self.parent():
            self.setGeometry(self.parent().rect())
        self.show()
        self.raise_()
    
    def stop(self) -> None:
        self.hide()
    
    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self.parent():
            self.setGeometry(self.parent().rect())
