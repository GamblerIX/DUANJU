from typing import Optional, List
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import ScrollArea, SubtitleLabel, FlowLayout, PushButton, FluentIcon
from ...core.models import DramaInfo
from ...services.category_service import CategoryService
from ...data.image.image_loader import ImageLoader
from ..controls.drama_card import DramaCard
from ..controls.loading_spinner import LoadingSpinner


class HomeInterface(ScrollArea):
    drama_clicked = pyqtSignal(object)
    favorite_clicked = pyqtSignal(object, bool)
    
    def __init__(self, category_service: CategoryService, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._category_service = category_service
        self._dramas: List[DramaInfo] = []
        self._cards: List[DramaCard] = []
        self._favorites: set = set()
        self._image_loader = ImageLoader(self)
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self) -> None:
        self.setObjectName("homeInterface")
        self.setWidgetResizable(True)
        self.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.viewport().setStyleSheet("background: transparent;")
        self._container = QWidget()
        self._container.setObjectName("homeContainer")
        self._container.setStyleSheet("background: transparent;")
        self.setWidget(self._container)
        layout = QVBoxLayout(self._container)
        layout.setContentsMargins(24, 24, 36, 24)
        layout.setSpacing(16)
        header_layout = QHBoxLayout()
        self._title_label = SubtitleLabel("推荐短剧")
        header_layout.addWidget(self._title_label)
        header_layout.addStretch()
        self._refresh_btn = PushButton("刷新", self, FluentIcon.SYNC)
        self._refresh_btn.clicked.connect(self.refresh)
        header_layout.addWidget(self._refresh_btn)
        layout.addLayout(header_layout)
        self._loading = LoadingSpinner("正在加载推荐...")
        self._loading.show()
        layout.addWidget(self._loading, alignment=Qt.AlignmentFlag.AlignCenter)
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
        self._category_service.recommendations_loaded.connect(self._on_recommendations_loaded)
        self._category_service.error.connect(self._on_error)
        self._image_loader.image_loaded.connect(self._on_image_loaded)
    
    def _on_recommendations_loaded(self, dramas: List[DramaInfo]) -> None:
        self._loading.hide()
        self._flow_widget.show()
        self._dramas = dramas
        self._update_cards()
    
    def _on_error(self, error) -> None:
        self._loading.hide()
        self._flow_widget.show()
    
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
    
    def refresh(self) -> None:
        self._loading.show()
        self._flow_widget.hide()
        self._category_service.fetch_recommendations(force_refresh=True)
    
    def set_favorites(self, favorites: set) -> None:
        self._favorites = favorites
        for card in self._cards:
            card.set_favorite(card.drama.book_id in self._favorites)
    
    def load_data(self) -> None:
        self.refresh()
