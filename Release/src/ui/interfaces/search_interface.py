from typing import Optional, List
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import ScrollArea, SearchLineEdit, SubtitleLabel, BodyLabel, FlowLayout, InfoBar, InfoBarPosition
from ...core.models import DramaInfo, SearchResult
from ...services.search_service import SearchService
from ...data.config.config_manager import ConfigManager
from ...data.image.image_loader import ImageLoader
from ..controls.drama_card import DramaCard
from ..controls.pagination import Pagination
from ..controls.loading_spinner import LoadingSpinner


class SearchInterface(ScrollArea):
    drama_clicked = pyqtSignal(object)
    favorite_clicked = pyqtSignal(object, bool)
    
    def __init__(self, search_service: SearchService, config_manager: ConfigManager, 
                 parent: Optional[QWidget] = None):
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
        self.setObjectName("searchInterface")
        self.setWidgetResizable(True)
        self.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.viewport().setStyleSheet("background: transparent;")
        self._container = QWidget()
        self._container.setObjectName("searchContainer")
        self._container.setStyleSheet("background: transparent;")
        self.setWidget(self._container)
        layout = QVBoxLayout(self._container)
        layout.setContentsMargins(24, 24, 36, 24)
        layout.setSpacing(16)
        search_layout = QHBoxLayout()
        self._search_edit = SearchLineEdit()
        self._search_edit.setPlaceholderText("搜索短剧...")
        self._search_edit.setFixedWidth(400)
        self._search_edit.searchSignal.connect(self._on_search)
        self._search_edit.returnPressed.connect(lambda: self._on_search(self._search_edit.text()))
        search_layout.addWidget(self._search_edit)
        search_layout.addStretch()
        layout.addLayout(search_layout)
        self._result_label = SubtitleLabel("")
        self._result_label.hide()
        layout.addWidget(self._result_label)
        self._loading = LoadingSpinner("正在搜索...")
        self._loading.hide()
        layout.addWidget(self._loading, alignment=Qt.AlignmentFlag.AlignCenter)
        self._empty_label = BodyLabel("无搜索结果")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.hide()
        layout.addWidget(self._empty_label)
        self._flow_widget = QWidget()
        self._flow_widget.setStyleSheet("background: transparent;")
        self._flow_layout = FlowLayout(self._flow_widget, needAni=False)
        self._flow_layout.setContentsMargins(0, 0, 0, 0)
        self._flow_layout.setHorizontalSpacing(16)
        self._flow_layout.setVerticalSpacing(16)
        layout.addWidget(self._flow_widget)
        self._pagination = Pagination()
        self._pagination.page_changed.connect(self._on_page_changed)
        layout.addWidget(self._pagination, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
    
    def _connect_signals(self) -> None:
        self._search_service.search_started.connect(self._on_search_started)
        self._search_service.search_completed.connect(self._on_search_completed)
        self._search_service.search_error.connect(self._on_search_error)
        self._image_loader.image_loaded.connect(self._on_image_loaded)
    
    def _on_search(self, keyword: str) -> None:
        keyword = keyword.strip()
        if not keyword:
            return
        self._current_page = 1
        self._search_service.search(keyword, self._current_page)
        self._config.add_search_history(keyword)
        self._config.last_search_keyword = keyword
    
    def _on_search_started(self) -> None:
        self._loading.show()
        self._flow_widget.hide()
        self._empty_label.hide()
        self._pagination.hide()
        self._search_edit.setEnabled(False)
    
    def _on_search_completed(self, result: SearchResult) -> None:
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
        self._loading.hide()
        self._search_edit.setEnabled(True)
        InfoBar.error(title="搜索失败", content=error.message, orient=Qt.Orientation.Horizontal,
                     isClosable=True, position=InfoBarPosition.TOP_RIGHT, duration=3000, parent=self)
    
    def _on_page_changed(self, page: int) -> None:
        keyword = self._search_service.current_keyword
        if keyword:
            self._search_service.search(keyword, page)
    
    def _update_cards(self) -> None:
        for card in self._cards:
            self._flow_layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()
        for drama in self._dramas:
            is_fav = drama.book_id in self._favorites
            card = DramaCard(drama, is_fav)
            card.clicked.connect(self._on_card_clicked)
            card.favorite_clicked.connect(self._on_favorite_clicked)
            self._flow_layout.addWidget(card)
            self._cards.append(card)
            if drama.cover_url:
                self._image_loader.load(drama.cover_url)
    
    def _on_image_loaded(self, url: str, pixmap) -> None:
        for card in self._cards:
            if card.drama.cover_url == url:
                card.set_cover(pixmap)
                break
    
    def _on_card_clicked(self, drama: DramaInfo) -> None:
        self.drama_clicked.emit(drama)
    
    def _on_favorite_clicked(self, drama: DramaInfo, is_favorite: bool) -> None:
        if is_favorite:
            self._favorites.add(drama.book_id)
        else:
            self._favorites.discard(drama.book_id)
        self.favorite_clicked.emit(drama, is_favorite)
    
    def set_favorites(self, favorites: set) -> None:
        self._favorites = favorites
        for card in self._cards:
            card.set_favorite(card.drama.book_id in self._favorites)
    
    def focus_search(self) -> None:
        self._search_edit.setFocus()
    
    def set_search_text(self, text: str) -> None:
        self._search_edit.setText(text)
