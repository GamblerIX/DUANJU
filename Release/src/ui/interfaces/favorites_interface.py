from typing import Optional, List
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import ScrollArea, SubtitleLabel, BodyLabel, FlowLayout, PushButton, FluentIcon
from ...core.models import DramaInfo
from ...data.favorites.favorites_manager import FavoritesManager
from ..controls.drama_card import DramaCard


class FavoritesInterface(ScrollArea):
    drama_clicked = pyqtSignal(object)
    favorite_removed = pyqtSignal(object)
    
    def __init__(self, favorites_manager: FavoritesManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._favorites_manager = favorites_manager
        self._cards: List[DramaCard] = []
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        self.setObjectName("favoritesInterface")
        self.setWidgetResizable(True)
        self.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.viewport().setStyleSheet("background: transparent;")
        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self.setWidget(self._container)
        layout = QVBoxLayout(self._container)
        layout.setContentsMargins(24, 24, 36, 24)
        layout.setSpacing(16)
        header_layout = QHBoxLayout()
        self._title_label = SubtitleLabel("我的收藏")
        header_layout.addWidget(self._title_label)
        self._count_label = BodyLabel("")
        header_layout.addWidget(self._count_label)
        header_layout.addStretch()
        self._clear_btn = PushButton("清空", self, FluentIcon.DELETE)
        self._clear_btn.clicked.connect(self._on_clear_clicked)
        header_layout.addWidget(self._clear_btn)
        layout.addLayout(header_layout)
        self._empty_label = BodyLabel("暂无收藏")
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
        layout.addStretch()
    
    def refresh(self) -> None:
        dramas = self._favorites_manager.get_all()
        self._update_cards(dramas)
        self._update_count()
    
    def _update_cards(self, dramas: List[DramaInfo]) -> None:
        for card in self._cards:
            self._flow_layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()
        if not dramas:
            self._empty_label.show()
            self._flow_widget.hide()
            return
        self._empty_label.hide()
        self._flow_widget.show()
        for drama in dramas:
            card = DramaCard(drama, is_favorite=True)
            card.clicked.connect(self._on_card_clicked)
            card.favorite_clicked.connect(self._on_favorite_clicked)
            self._flow_layout.addWidget(card)
            self._cards.append(card)
    
    def _update_count(self) -> None:
        count = self._favorites_manager.count()
        self._count_label.setText(f"({count})")
        self._clear_btn.setEnabled(count > 0)
    
    def _on_card_clicked(self, drama: DramaInfo) -> None:
        self.drama_clicked.emit(drama)
    
    def _on_favorite_clicked(self, drama: DramaInfo, is_favorite: bool) -> None:
        if not is_favorite:
            self._favorites_manager.remove(drama.book_id)
            self.favorite_removed.emit(drama)
            self.refresh()
    
    def _on_clear_clicked(self) -> None:
        self._favorites_manager.clear()
        self.refresh()
    
    def load_data(self) -> None:
        self.refresh()
