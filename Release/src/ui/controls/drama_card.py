from typing import Optional
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QFrame, QLabel
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath
from qfluentwidgets import BodyLabel, CaptionLabel, ToolButton, FluentIcon
from ...core.models import DramaInfo
from ...core.utils.string_utils import truncate


class RoundedImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = None
        self._radius = (6, 6, 0, 0)
        
    def setPixmap(self, pixmap: QPixmap) -> None:
        self._pixmap = pixmap
        self.update()
        
    def setBorderRadius(self, tl: int, tr: int, br: int, bl: int) -> None:
        self._radius = (tl, tr, br, bl)
        self.update()
        
    def paintEvent(self, event) -> None:
        if self._pixmap is None:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), self._radius[0], self._radius[0])
        painter.setClipPath(path)
        scaled = self._pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                     Qt.TransformationMode.SmoothTransformation)
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)


class DramaCard(QFrame):
    clicked = pyqtSignal(object)
    favorite_clicked = pyqtSignal(object, bool)
    
    CARD_WIDTH = 170
    CARD_HEIGHT = 330
    COVER_HEIGHT = 272
    
    def __init__(self, drama: DramaInfo, is_favorite: bool = False, parent: Optional[QFrame] = None):
        super().__init__(parent)
        self._drama = drama
        self._is_favorite = is_favorite
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        self.setFixedSize(self.CARD_WIDTH, self.CARD_HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("DramaCard { background-color: transparent; border-radius: 8px; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 8)
        layout.setSpacing(4)
        self._cover_label = RoundedImageLabel()
        self._cover_label.setFixedSize(self.CARD_WIDTH, self.COVER_HEIGHT)
        layout.addWidget(self._cover_label)
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(8, 0, 8, 0)
        title_layout.setSpacing(4)
        self._title_label = BodyLabel(truncate(self._drama.name, 11))
        self._title_label.setWordWrap(False)
        title_layout.addWidget(self._title_label, 1)
        self._favorite_btn = ToolButton(FluentIcon.HEART if self._is_favorite else FluentIcon.HEART)
        self._favorite_btn.setFixedSize(24, 24)
        self._favorite_btn.clicked.connect(self._on_favorite_clicked)
        title_layout.addWidget(self._favorite_btn)
        layout.addLayout(title_layout)
        info_text = f"{self._drama.episode_count}集"
        if self._drama.category:
            info_text = f"{self._drama.category} · {info_text}"
        self._info_label = CaptionLabel(info_text)
        self._info_label.setWordWrap(False)
        self._info_label.setContentsMargins(8, 0, 8, 0)
        layout.addWidget(self._info_label)
        self._update_favorite_style()
    
    def _on_favorite_clicked(self) -> None:
        self._is_favorite = not self._is_favorite
        self._update_favorite_style()
        self.favorite_clicked.emit(self._drama, self._is_favorite)
    
    def _update_favorite_style(self) -> None:
        self._favorite_btn.setIcon(FluentIcon.HEART)
    
    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if not self._favorite_btn.geometry().contains(event.pos()):
                self.clicked.emit(self._drama)
    
    def set_cover(self, pixmap: QPixmap) -> None:
        if pixmap and not pixmap.isNull():
            self._cover_label.setPixmap(pixmap)
    
    def set_cover_from_url(self, url: str) -> None:
        pass
    
    def set_favorite(self, is_favorite: bool) -> None:
        self._is_favorite = is_favorite
        self._update_favorite_style()
    
    @property
    def drama(self) -> DramaInfo:
        return self._drama
    
    @property
    def is_favorite(self) -> bool:
        return self._is_favorite
