"""首页界面实现"""
from typing import Optional, List
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    ScrollArea, SubtitleLabel, FlowLayout, 
    PushButton, FluentIcon, InfoBar, InfoBarPosition
)

from ...core.models import DramaInfo
from ...utils.log_manager import get_logger
from ...services.category_service import CategoryService
from ...data.image_loader import ImageLoader

logger = get_logger()
from ..controls.drama_card import DramaCard
from ..controls.loading_spinner import LoadingSpinner


class HomeInterface(ScrollArea):
    """
    首页界面
    
    显示推荐短剧列表
    """
    
    # 信号
    drama_clicked = Signal(object)  # DramaInfo
    favorite_clicked = Signal(object, bool)  # DramaInfo, is_favorite
    
    def __init__(
        self,
        category_service: CategoryService,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self._category_service = category_service
        self._dramas: List[DramaInfo] = []
        self._cards: List[DramaCard] = []
        self._favorites: set = set()
        self._image_loader = ImageLoader(self)
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self) -> None:
        """初始化UI"""
        self.setObjectName("homeInterface")
        self.setWidgetResizable(True)
        
        # 设置滚动区域背景透明，让主题正确应用
        self.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.viewport().setStyleSheet("background: transparent;")
        
        # 主容器
        self._container = QWidget()
        self._container.setObjectName("homeContainer")
        self._container.setStyleSheet("background: transparent;")
        self.setWidget(self._container)
        
        layout = QVBoxLayout(self._container)
        layout.setContentsMargins(24, 24, 36, 24)  # 右边距增加，避免滚动条遮挡
        layout.setSpacing(16)
        
        # 标题栏
        header_layout = QHBoxLayout()
        self._title_label = SubtitleLabel("推荐短剧")
        header_layout.addWidget(self._title_label)
        header_layout.addStretch()
        
        self._refresh_btn = PushButton("刷新", self, FluentIcon.SYNC)
        self._refresh_btn.clicked.connect(self.refresh)
        header_layout.addWidget(self._refresh_btn)
        
        layout.addLayout(header_layout)
        
        # 加载指示器 - 初始显示
        self._loading = LoadingSpinner("正在加载推荐...")
        self._loading.show()
        layout.addWidget(self._loading, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 短剧卡片流式布局 - 初始隐藏，禁用动画避免卡顿
        self._flow_widget = QWidget()
        self._flow_widget.hide()
        self._flow_widget.setStyleSheet("background: transparent;")
        self._flow_layout = FlowLayout(self._flow_widget, needAni=False)
        self._flow_layout.setContentsMargins(0, 0, 0, 0)
        self._flow_layout.setHorizontalSpacing(16)
        self._flow_layout.setVerticalSpacing(16)
        layout.addWidget(self._flow_widget)
        
        layout.addStretch()
    
    def _connect_signals(self) -> None:
        """连接信号"""
        self._category_service.recommendations_loaded.connect(self._on_recommendations_loaded)
        self._category_service.error.connect(self._on_error)
        # 不连接 loading_started，手动控制加载状态
        self._image_loader.image_loaded.connect(self._on_image_loaded)
    
    def _on_recommendations_loaded(self, dramas: List[DramaInfo]) -> None:
        """处理推荐加载完成"""
        logger.debug(f"HomeInterface: Recommendations loaded callback, {len(dramas)} dramas")
        self._loading.hide()
        self._flow_widget.show()
        self._dramas = dramas
        logger.debug("HomeInterface: Updating cards...")
        self._update_cards()
        logger.debug("HomeInterface: Cards updated")
    
    def _on_error(self, error) -> None:
        """处理错误"""
        self._loading.hide()
        self._flow_widget.show()
        
        # 显示错误提示
        error_msg = error.message if hasattr(error, 'message') else str(error)
        InfoBar.error(
            title="加载失败",
            content=error_msg,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )
    
    def _update_cards(self) -> None:
        """更新卡片显示"""
        # 清除旧卡片
        for card in self._cards:
            self._flow_layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()
        
        # 创建新卡片
        for drama in self._dramas:
            is_fav = drama.book_id in self._favorites
            card = DramaCard(drama, is_fav)
            card.clicked.connect(self._on_card_clicked)
            card.favorite_clicked.connect(self._on_favorite_clicked)
            self._flow_layout.addWidget(card)
            self._cards.append(card)
            
            # 加载封面图片
            if drama.cover_url:
                self._image_loader.load(drama.cover_url)
    
    def _on_image_loaded(self, url: str, pixmap) -> None:
        """处理图片加载完成"""
        for card in self._cards:
            if card.drama.cover_url == url:
                card.set_cover(pixmap)
                break
    
    def _on_card_clicked(self, drama: DramaInfo) -> None:
        """处理卡片点击"""
        self.drama_clicked.emit(drama)
    
    def _on_favorite_clicked(self, drama: DramaInfo, is_favorite: bool) -> None:
        """处理收藏点击"""
        if is_favorite:
            self._favorites.add(drama.book_id)
        else:
            self._favorites.discard(drama.book_id)
        self.favorite_clicked.emit(drama, is_favorite)
    
    def refresh(self) -> None:
        """刷新推荐"""
        logger.log_user_action("refresh_recommendations")
        # 手动显示加载状态
        self._loading.show()
        self._flow_widget.hide()
        # 强制刷新，忽略缓存
        self._category_service.fetch_recommendations(force_refresh=True)
    
    def set_favorites(self, favorites: set) -> None:
        """设置收藏集合"""
        self._favorites = favorites
        # 更新卡片状态
        for card in self._cards:
            card.set_favorite(card.drama.book_id in self._favorites)
    
    def load_data(self) -> None:
        """加载数据"""
        self.refresh()
