"""搜索界面实现"""
from typing import Optional, List
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    ScrollArea, SearchLineEdit, SubtitleLabel, 
    BodyLabel, FlowLayout, InfoBar, InfoBarPosition
)

from ...core.models import DramaInfo, SearchResult
from ...utils.log_manager import get_logger
from ...services.search_service import SearchService
from ...data.config_manager import ConfigManager
from ...data.image_loader import ImageLoader

logger = get_logger()
from ..controls.drama_card import DramaCard
from ..controls.pagination import Pagination
from ..controls.loading_spinner import LoadingSpinner


class SearchInterface(ScrollArea):
    """
    搜索界面
    
    提供搜索功能和结果展示
    """
    
    # 信号
    drama_clicked = Signal(object)  # DramaInfo
    favorite_clicked = Signal(object, bool)  # DramaInfo, is_favorite
    
    def __init__(
        self,
        search_service: SearchService,
        config_manager: ConfigManager,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self._search_service = search_service
        self._config = config_manager
        self._dramas: List[DramaInfo] = []
        self._cards: List[DramaCard] = []
        self._favorites: set = set()
        self._current_page = 1
        self._total_pages = 1
        self._image_loader = ImageLoader(self)
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self) -> None:
        """初始化UI"""
        self.setObjectName("searchInterface")
        self.setWidgetResizable(True)
        
        # 设置滚动区域背景透明，让主题正确应用
        self.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.viewport().setStyleSheet("background: transparent;")
        
        # 主容器
        self._container = QWidget()
        self._container.setObjectName("searchContainer")
        self._container.setStyleSheet("background: transparent;")
        self.setWidget(self._container)
        
        layout = QVBoxLayout(self._container)
        layout.setContentsMargins(24, 24, 36, 24)  # 右边距增加，避免滚动条遮挡
        layout.setSpacing(16)
        
        # 搜索栏
        search_layout = QHBoxLayout()
        self._search_edit = SearchLineEdit()
        self._search_edit.setPlaceholderText("搜索短剧...")
        self._search_edit.setFixedWidth(400)
        self._search_edit.searchSignal.connect(self._on_search)
        self._search_edit.returnPressed.connect(
            lambda: self._on_search(self._search_edit.text())
        )
        search_layout.addWidget(self._search_edit)
        search_layout.addStretch()
        layout.addLayout(search_layout)
        
        # 结果标题
        self._result_label = SubtitleLabel("")
        self._result_label.hide()
        layout.addWidget(self._result_label)
        
        # 加载指示器
        self._loading = LoadingSpinner("正在搜索...")
        self._loading.hide()
        layout.addWidget(self._loading, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 空结果提示
        self._empty_label = BodyLabel("无搜索结果")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.hide()
        layout.addWidget(self._empty_label)
        
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
        self._search_service.search_started.connect(self._on_search_started)
        self._search_service.search_completed.connect(self._on_search_completed)
        self._search_service.search_error.connect(self._on_search_error)
        self._image_loader.image_loaded.connect(self._on_image_loaded)
    
    def _on_search(self, keyword: str) -> None:
        """执行搜索"""
        keyword = keyword.strip()
        if not keyword:
            return
        
        logger.log_user_action("search", f"keyword={keyword}, page=1")
        self._current_page = 1
        self._search_service.search(keyword, self._current_page)
        
        # 添加到搜索历史
        self._config.add_search_history(keyword)
        self._config.last_search_keyword = keyword
    
    def _on_search_started(self) -> None:
        """处理搜索开始"""
        self._loading.show()
        self._flow_widget.hide()
        self._empty_label.hide()
        self._pagination.hide()
        self._search_edit.setEnabled(False)
    
    def _on_search_completed(self, result: SearchResult) -> None:
        """处理搜索完成"""
        logger.debug(f"Search completed: {len(result.data)} results")
        self._loading.hide()
        self._search_edit.setEnabled(True)
        
        self._dramas = result.data
        self._current_page = result.current_page
        self._total_pages = result.total_pages
        
        if not self._dramas:
            self._empty_label.show()
            self._flow_widget.hide()
            self._pagination.hide()
            self._result_label.hide()
        else:
            self._empty_label.hide()
            self._flow_widget.show()
            self._result_label.setText(f"搜索结果 - {result.title}")
            self._result_label.show()
            self._update_cards()
            self._pagination.set_page_info(self._current_page, self._total_pages)
    
    def _on_search_error(self, error) -> None:
        """处理搜索错误"""
        logger.debug(f"搜索失败: {error.message}")
        self._loading.hide()
        self._search_edit.setEnabled(True)
        
        InfoBar.error(
            title="搜索失败",
            content=error.message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=3000,
            parent=self
        )
    
    def _on_page_changed(self, page: int) -> None:
        """处理页码改变"""
        keyword = self._search_service.current_keyword
        if keyword:
            logger.log_user_action("search_page_change", f"keyword={keyword}, page={page}")
            self._search_service.search(keyword, page)
    
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
    
    def focus_search(self) -> None:
        """聚焦搜索框"""
        self._search_edit.setFocus()
    
    def set_search_text(self, text: str) -> None:
        """设置搜索文本"""
        self._search_edit.setText(text)
