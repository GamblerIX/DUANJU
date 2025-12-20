"""短剧卡片控件实现"""
from typing import Optional
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QFrame, QLabel, QApplication
from PySide6.QtGui import QPixmap, QPainter, QPainterPath, QBrush, QPalette
from qfluentwidgets import (
    BodyLabel, CaptionLabel,
    ToolButton, FluentIcon, isDarkTheme
)

from ...core.models import DramaInfo
from ...utils.string_utils import truncate


class RoundedImageLabel(QLabel):
    """圆角图片标签"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = None
        self._radius = (6, 6, 0, 0)  # 左上、右上、右下、左下
        
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
        
        # 创建圆角路径
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), self._radius[0], self._radius[0])
        painter.setClipPath(path)
        
        # 缩放图片填充整个区域，裁剪超出部分
        scaled = self._pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # 居中绘制
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)


class DramaCard(QFrame):
    """
    短剧卡片控件
    
    显示短剧封面、标题、简介，支持点击和收藏
    """
    
    # 信号
    clicked = Signal(object)  # DramaInfo
    favorite_clicked = Signal(object, bool)  # DramaInfo, is_favorite
    
    CARD_WIDTH = 170
    CARD_HEIGHT = 330
    COVER_HEIGHT = 272  # 保持 5:8 比例
    
    def __init__(
        self, 
        drama: DramaInfo,
        is_favorite: bool = False,
        parent: Optional[QFrame] = None
    ):
        super().__init__(parent)
        self._drama = drama
        self._is_favorite = is_favorite
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """初始化UI"""
        self.setFixedSize(self.CARD_WIDTH, self.CARD_HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFrameShape(QFrame.Shape.NoFrame)
        
        # 设置卡片样式 - 不使用固定颜色，让其跟随主题
        self.setStyleSheet("""
            DramaCard {
                background-color: transparent;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 8)
        layout.setSpacing(4)
        
        # 封面图 - 使用自定义圆角图片标签
        self._cover_label = RoundedImageLabel()
        self._cover_label.setFixedSize(self.CARD_WIDTH, self.COVER_HEIGHT)
        layout.addWidget(self._cover_label)
        
        # 标题行（标题 + 收藏按钮）
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(8, 0, 8, 0)
        title_layout.setSpacing(4)
        
        self._title_label = BodyLabel(truncate(self._drama.name, 11))
        self._title_label.setWordWrap(False)
        title_layout.addWidget(self._title_label, 1)
        
        self._favorite_btn = ToolButton(
            FluentIcon.HEART if self._is_favorite else FluentIcon.HEART
        )
        self._favorite_btn.setFixedSize(24, 24)
        self._favorite_btn.clicked.connect(self._on_favorite_clicked)
        title_layout.addWidget(self._favorite_btn)
        
        layout.addLayout(title_layout)
        
        # 简介/集数
        info_text = f"{self._drama.episode_count}集"
        if self._drama.category:
            info_text = f"{self._drama.category} · {info_text}"
        self._info_label = CaptionLabel(info_text)
        self._info_label.setWordWrap(False)
        self._info_label.setContentsMargins(8, 0, 8, 0)
        layout.addWidget(self._info_label)
        
        # 更新收藏按钮样式
        self._update_favorite_style()
    

    
    def _on_favorite_clicked(self) -> None:
        """处理收藏按钮点击"""
        self._is_favorite = not self._is_favorite
        self._update_favorite_style()
        self.favorite_clicked.emit(self._drama, self._is_favorite)
    
    def _update_favorite_style(self) -> None:
        """更新收藏按钮样式"""
        if self._is_favorite:
            self._favorite_btn.setIcon(FluentIcon.HEART)
            # 可以添加颜色变化
        else:
            self._favorite_btn.setIcon(FluentIcon.HEART)
    
    def mouseReleaseEvent(self, event) -> None:
        """处理鼠标点击"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 检查是否点击在收藏按钮上
            if not self._favorite_btn.geometry().contains(event.pos()):
                self.clicked.emit(self._drama)
        # 不调用 super().mouseReleaseEvent(event)
        # 因为父类 CardWidget 会触发无参数的 clicked.emit()
        # 而我们重新定义的 clicked 信号需要一个参数
    
    def set_cover(self, pixmap: QPixmap) -> None:
        """设置封面图"""
        if pixmap and not pixmap.isNull():
            self._cover_label.setPixmap(pixmap)
    
    def set_cover_from_url(self, url: str) -> None:
        """从URL设置封面图（需要外部加载器）"""
        # 这里只是占位，实际加载由 ImageLoader 处理
        pass
    
    def set_favorite(self, is_favorite: bool) -> None:
        """设置收藏状态"""
        self._is_favorite = is_favorite
        self._update_favorite_style()
    
    @property
    def drama(self) -> DramaInfo:
        """获取短剧信息"""
        return self._drama
    
    @property
    def is_favorite(self) -> bool:
        """获取收藏状态"""
        return self._is_favorite
