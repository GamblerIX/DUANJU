"""分页控件实现"""
from typing import Optional
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout
from qfluentwidgets import PipsPager, PipsScrollButtonDisplayMode


class Pagination(QWidget):
    """
    分页控件
    
    基于 QFluentWidgets PipsPager 实现
    """
    
    # 信号：页码改变
    page_changed = Signal(int)  # 新页码（从1开始）
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._current_page = 1
        self._total_pages = 1
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """初始化UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self._pager = PipsPager()
        self._pager.setPageNumber(1)
        self._pager.setVisibleNumber(5)
        self._pager.setNextButtonDisplayMode(PipsScrollButtonDisplayMode.ALWAYS)
        self._pager.setPreviousButtonDisplayMode(PipsScrollButtonDisplayMode.ALWAYS)
        
        # 连接信号
        self._pager.currentIndexChanged.connect(self._on_index_changed)
        
        layout.addWidget(self._pager)
        
        # 初始隐藏（总页数<=1时）
        self.setVisible(False)
    
    def _on_index_changed(self, index: int) -> None:
        """处理页码改变"""
        new_page = index + 1  # PipsPager 索引从0开始
        if new_page != self._current_page:
            self._current_page = new_page
            self._update_button_states()
            self.page_changed.emit(self._current_page)
    
    def _update_button_states(self) -> None:
        """更新按钮状态"""
        # PipsPager 会自动处理边界状态
        pass
    
    def set_page_info(self, current_page: int, total_pages: int) -> None:
        """
        设置分页信息
        
        Args:
            current_page: 当前页码（从1开始）
            total_pages: 总页数
        """
        self._total_pages = max(1, total_pages)
        self._current_page = max(1, min(current_page, self._total_pages))
        
        # 更新 PipsPager
        self._pager.setPageNumber(self._total_pages)
        self._pager.setCurrentIndex(self._current_page - 1)
        
        # 控制可见性
        self.setVisible(self._total_pages > 1)
    
    def go_to_page(self, page: int) -> None:
        """
        跳转到指定页
        
        Args:
            page: 目标页码（从1开始）
        """
        if 1 <= page <= self._total_pages:
            self._pager.setCurrentIndex(page - 1)
    
    def next_page(self) -> None:
        """下一页"""
        if self._current_page < self._total_pages:
            self.go_to_page(self._current_page + 1)
    
    def previous_page(self) -> None:
        """上一页"""
        if self._current_page > 1:
            self.go_to_page(self._current_page - 1)
    
    @property
    def current_page(self) -> int:
        """获取当前页码"""
        return self._current_page
    
    @property
    def total_pages(self) -> int:
        """获取总页数"""
        return self._total_pages
    
    def is_first_page(self) -> bool:
        """是否为第一页"""
        return self._current_page == 1
    
    def is_last_page(self) -> bool:
        """是否为最后一页"""
        return self._current_page == self._total_pages
