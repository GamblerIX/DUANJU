"""分类界面实现"""
from typing import Optional, List
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import (
    ScrollArea, Pivot, FlowLayout, InfoBar, InfoBarPosition
)

from ...core.models import DramaInfo, CategoryResult
from ...utils.log_manager import get_logger
from ...services.category_service import CategoryService
from ...data.image_loader import ImageLoader

logger = get_logger()
from ..controls.drama_card import DramaCard
from ..controls.pagination import Pagination
from ..controls.loading_spinner import LoadingSpinner


class CategoryInterface(ScrollArea):
    """
    分类界面
    
    按分类浏览短剧
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
        self._categories: List[str] = []
        self._current_category = ""
        self._dramas: List[DramaInfo] = []
        self._cards: List[DramaCard] = []
        self._favorites: set = set()
        self._current_offset = 1
        self._image_loader = ImageLoader(self)
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self) -> None:
        """初始化UI"""
        self.setObjectName("categoryInterface")
        self.setWidgetResizable(True)
        
        # 设置滚动区域背景透明，让主题正确应用
        self.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.viewport().setStyleSheet("background: transparent;")
        
        # 主容器
        self._container = QWidget()
        self._container.setObjectName("categoryContainer")
        self._container.setStyleSheet("background: transparent;")
        self.setWidget(self._container)
        
        layout = QVBoxLayout(self._container)
        layout.setContentsMargins(24, 24, 36, 24)  # 右边距增加，避免滚动条遮挡
        layout.setSpacing(16)
        
        # 分类标签导航
        self._pivot = Pivot()
        self._pivot.currentItemChanged.connect(self._on_category_changed)
        layout.addWidget(self._pivot)
        
        # 加载指示器
        self._loading = LoadingSpinner("正在加载...")
        self._loading.hide()
        layout.addWidget(self._loading, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 短剧卡片流式布局 - 禁用动画避免卡顿
        self._flow_widget = QWidget()
        self._flow_widget.setStyleSheet("background: transparent;")
        self._flow_layout = FlowLayout(self._flow_widget, needAni=False)
        self._flow_layout.setContentsMargins(0, 0, 0, 0)
        self._flow_layout.setHorizontalSpacing(16)
        self._flow_layout.setVerticalSpacing(16)
        layout.addWidget(self._flow_widget)
        
        # 分页控件
        self._pagination = Pagination()
        self._pagination.page_changed.connect(self._on_page_changed)
        layout.addWidget(self._pagination, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addStretch()
    
    def _connect_signals(self) -> None:
        """连接信号"""
        self._category_service.categories_loaded.connect(self._on_categories_loaded)
        self._category_service.dramas_loaded.connect(self._on_dramas_loaded)
        self._category_service.error.connect(self._on_error)
        # 不连接 loading_started，手动控制加载状态
        self._image_loader.image_loaded.connect(self._on_image_loaded)
    
    def _on_categories_loaded(self, categories: List[str]) -> None:
        """处理分类列表加载完成"""
        logger.debug(f"Categories loaded: {len(categories)} categories")
        self._categories = categories
        
        # 清除旧的 Pivot 项
        # Pivot 没有 clear 方法，需要重新创建
        
        # 只添加前15个分类，避免 Pivot 过长
        display_categories = categories[:15]
        logger.debug(f"Adding {len(display_categories)} categories to Pivot")
        
        # 添加新标签
        for i, category in enumerate(display_categories):
            logger.debug(f"Adding Pivot item: {category}")
            self._pivot.addItem(
                routeKey=f"cat_{i}_{category}",
                text=category,
                onClick=lambda checked=False, c=category: self._load_category(c)
            )
        
        # 选择第一个分类
        if display_categories:
            first_key = f"cat_0_{display_categories[0]}"
            logger.debug(f"Setting current item to: {first_key}")
            self._pivot.setCurrentItem(first_key)
            self._load_category(display_categories[0])
    
    def _on_category_changed(self, route_key: str) -> None:
        """处理分类切换"""
        # 从 route_key 提取分类名称 (格式: cat_index_name)
        parts = route_key.split("_", 2)
        category = parts[2] if len(parts) >= 3 else route_key
        if category != self._current_category:
            self._current_offset = 1
            self._load_category(category)
    
    def _load_category(self, category: str) -> None:
        """加载分类内容"""
        logger.log_user_action("category_select", f"category={category}, offset={self._current_offset}")
        self._current_category = category
        # 手动显示加载状态
        self._loading.show()
        self._flow_widget.hide()
        self._pagination.hide()
        self._category_service.fetch_category_dramas(category, self._current_offset)
    
    def _on_loading_started(self) -> None:
        """处理加载开始（保留但不使用）"""
        pass
    
    def _on_dramas_loaded(self, result: CategoryResult) -> None:
        """处理短剧列表加载完成"""
        logger.debug(f"Category dramas loaded: {len(result.data)} dramas for {result.category}")
        self._loading.hide()
        self._flow_widget.show()
        
        self._dramas = result.data
        self._current_offset = result.offset
        
        self._update_cards()
        
        # 假设每页20条，计算总页数
        # 实际应该从API返回
        has_more = len(result.data) >= 20
        total_pages = self._current_offset + (1 if has_more else 0)
        self._pagination.set_page_info(self._current_offset, total_pages)
    
    def _on_error(self, error) -> None:
        """处理错误"""
        logger.debug(f"分类加载失败: {error.message}")
        self._loading.hide()
        self._flow_widget.show()
        
        InfoBar.error(
            title="加载失败",
            content=error.message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=3000,
            parent=self
        )
    
    def _on_page_changed(self, page: int) -> None:
        """处理页码改变"""
        logger.log_user_action("category_page_change", f"category={self._current_category}, page={page}")
        self._current_offset = page
        if self._current_category:
            self._load_category(self._current_category)
    
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
    
    def set_favorites(self, favorites: set) -> None:
        """设置收藏集合"""
        self._favorites = favorites
        for card in self._cards:
            card.set_favorite(card.drama.book_id in self._favorites)
    
    def load_data(self) -> None:
        """加载数据"""
        self._category_service.fetch_categories()
