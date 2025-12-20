"""历史界面实现"""
from typing import Optional, List
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    ScrollArea, SubtitleLabel, BodyLabel, CaptionLabel,
    CardWidget, PushButton, FluentIcon
)

from ...core.models import DramaInfo, HistoryItem
from ...utils.time_utils import format_duration
from ...data.history_manager import HistoryManager


class HistoryCard(CardWidget):
    """历史记录卡片"""
    
    clicked = Signal(object)  # HistoryItem
    remove_clicked = Signal(object)  # HistoryItem
    
    def __init__(self, item: HistoryItem, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._item = item
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """初始化UI"""
        self.setFixedHeight(80)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        # 信息区域
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        self._title_label = BodyLabel(self._item.drama.name)
        info_layout.addWidget(self._title_label)
        
        # 观看进度
        progress_text = f"第{self._item.episode_number}集"
        if self._item.position_ms > 0:
            progress_text += f" · {format_duration(self._item.position_ms)}"
        self._progress_label = CaptionLabel(progress_text)
        info_layout.addWidget(self._progress_label)
        
        layout.addLayout(info_layout, 1)
        
        # 删除按钮
        self._remove_btn = PushButton("删除", self, FluentIcon.DELETE)
        self._remove_btn.setFixedWidth(60)
        self._remove_btn.clicked.connect(self._on_remove_clicked)
        layout.addWidget(self._remove_btn)
    
    def _on_remove_clicked(self) -> None:
        """处理删除点击"""
        self.remove_clicked.emit(self._item)
    
    def mouseReleaseEvent(self, event) -> None:
        """处理鼠标点击"""
        super().mouseReleaseEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            if not self._remove_btn.geometry().contains(event.pos()):
                self.clicked.emit(self._item)
    
    @property
    def item(self) -> HistoryItem:
        return self._item


class HistoryInterface(ScrollArea):
    """
    历史界面
    
    显示用户的观看历史
    """
    
    # 信号
    history_clicked = Signal(object)  # HistoryItem
    
    def __init__(
        self,
        history_manager: HistoryManager,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self._history_manager = history_manager
        self._cards: List[HistoryCard] = []
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """初始化UI"""
        self.setObjectName("historyInterface")
        self.setWidgetResizable(True)
        
        # 主容器
        self._container = QWidget()
        self.setWidget(self._container)
        
        layout = QVBoxLayout(self._container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # 标题栏
        header_layout = QHBoxLayout()
        self._title_label = SubtitleLabel("观看历史")
        header_layout.addWidget(self._title_label)
        
        self._count_label = BodyLabel("")
        header_layout.addWidget(self._count_label)
        header_layout.addStretch()
        
        self._clear_btn = PushButton("清空", self, FluentIcon.DELETE)
        self._clear_btn.clicked.connect(self._on_clear_clicked)
        header_layout.addWidget(self._clear_btn)
        
        layout.addLayout(header_layout)
        
        # 空状态提示
        self._empty_label = BodyLabel("暂无观看历史")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.hide()
        layout.addWidget(self._empty_label)
        
        # 历史列表容器
        self._list_widget = QWidget()
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(8)
        layout.addWidget(self._list_widget)
        
        layout.addStretch()
    
    def refresh(self) -> None:
        """刷新历史列表"""
        history = self._history_manager.get_all()
        self._update_cards(history)
        self._update_count()
    
    def _update_cards(self, history: List[HistoryItem]) -> None:
        """更新卡片显示"""
        # 清除旧卡片
        for card in self._cards:
            self._list_layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()
        
        if not history:
            self._empty_label.show()
            self._list_widget.hide()
            return
        
        self._empty_label.hide()
        self._list_widget.show()
        
        # 创建新卡片
        for item in history:
            card = HistoryCard(item)
            card.clicked.connect(self._on_card_clicked)
            card.remove_clicked.connect(self._on_remove_clicked)
            self._list_layout.addWidget(card)
            self._cards.append(card)
    
    def _update_count(self) -> None:
        """更新历史数量显示"""
        count = self._history_manager.count()
        self._count_label.setText(f"({count})")
        self._clear_btn.setEnabled(count > 0)
    
    def _on_card_clicked(self, item: HistoryItem) -> None:
        """处理卡片点击"""
        self.history_clicked.emit(item)
    
    def _on_remove_clicked(self, item: HistoryItem) -> None:
        """处理删除点击"""
        self._history_manager.remove(item.drama.book_id)
        self.refresh()
    
    def _on_clear_clicked(self) -> None:
        """处理清空点击"""
        self._history_manager.clear()
        self.refresh()
    
    def load_data(self) -> None:
        """加载数据"""
        self.refresh()
