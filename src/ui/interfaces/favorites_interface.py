"""收藏界面实现"""
from typing import Optional, List
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    ScrollArea, SubtitleLabel, BodyLabel, FlowLayout,
    PushButton, FluentIcon
)

from ...core.models import DramaInfo
from ...data.favorites_manager import FavoritesManager
from ..controls.drama_card import DramaCard


class FavoritesInterface(ScrollArea):
    """
    收藏界面
    
    显示用户收藏的短剧列表
    """
    
    # 信号
    drama_clicked = Signal(object)  # DramaInfo
    favorite_removed = Signal(object)  # DramaInfo
    
    def __init__(
        self,
        favorites_manager: FavoritesManager,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self._favorites_manager = favorites_manager
        self._cards: List[DramaCard] = []
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """初始化UI"""
        self.setObjectName("favoritesInterface")
        self.setWidgetResizable(True)
        
        # 设置滚动区域背景透明，让主题正确应用
        self.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.viewport().setStyleSheet("background: transparent;")
        
        # 主容器
        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self.setWidget(self._container)
        
        layout = QVBoxLayout(self._container)
        layout.setContentsMargins(24, 24, 36, 24)
        layout.setSpacing(16)
        
        # 标题栏
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
        
        # 空状态提示
        self._empty_label = BodyLabel("暂无收藏")
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
        
        layout.addStretch()
    
    def refresh(self) -> None:
        """刷新收藏列表"""
        dramas = self._favorites_manager.get_all()
        self._update_cards(dramas)
        self._update_count()
    
    def _update_cards(self, dramas: List[DramaInfo]) -> None:
        """更新卡片显示"""
        # 清除旧卡片
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
        
        # 创建新卡片
        for drama in dramas:
            card = DramaCard(drama, is_favorite=True)
            card.clicked.connect(self._on_card_clicked)
            card.favorite_clicked.connect(self._on_favorite_clicked)
            self._flow_layout.addWidget(card)
            self._cards.append(card)
    
    def _update_count(self) -> None:
        """更新收藏数量显示"""
        count = self._favorites_manager.count()
        self._count_label.setText(f"({count})")
        self._clear_btn.setEnabled(count > 0)
    
    def _on_card_clicked(self, drama: DramaInfo) -> None:
        """处理卡片点击"""
        self.drama_clicked.emit(drama)
    
    def _on_favorite_clicked(self, drama: DramaInfo, is_favorite: bool) -> None:
        """处理收藏点击（取消收藏）"""
        if not is_favorite:
            self._favorites_manager.remove(drama.book_id)
            self.favorite_removed.emit(drama)
            self.refresh()
    
    def _on_clear_clicked(self) -> None:
        """处理清空点击"""
        self._favorites_manager.clear()
        self.refresh()
    
    def load_data(self) -> None:
        """加载数据"""
        self.refresh()
