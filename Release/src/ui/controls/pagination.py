from typing import Optional
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QHBoxLayout
from qfluentwidgets import PipsPager, PipsScrollButtonDisplayMode


class Pagination(QWidget):
    page_changed = pyqtSignal(int)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._current_page = 1
        self._total_pages = 1
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._pager = PipsPager()
        self._pager.setPageNumber(1)
        self._pager.setVisibleNumber(5)
        self._pager.setNextButtonDisplayMode(PipsScrollButtonDisplayMode.ALWAYS)
        self._pager.setPreviousButtonDisplayMode(PipsScrollButtonDisplayMode.ALWAYS)
        self._pager.currentIndexChanged.connect(self._on_index_changed)
        layout.addWidget(self._pager)
        self.setVisible(False)
    
    def _on_index_changed(self, index: int) -> None:
        new_page = index + 1
        if new_page != self._current_page:
            self._current_page = new_page
            self._update_button_states()
            self.page_changed.emit(self._current_page)
    
    def _update_button_states(self) -> None:
        pass
    
    def set_page_info(self, current_page: int, total_pages: int) -> None:
        self._total_pages = max(1, total_pages)
        self._current_page = max(1, min(current_page, self._total_pages))
        self._pager.setPageNumber(self._total_pages)
        self._pager.setCurrentIndex(self._current_page - 1)
        self.setVisible(self._total_pages > 1)
    
    def go_to_page(self, page: int) -> None:
        if 1 <= page <= self._total_pages:
            self._pager.setCurrentIndex(page - 1)
    
    def next_page(self) -> None:
        if self._current_page < self._total_pages:
            self.go_to_page(self._current_page + 1)
    
    def previous_page(self) -> None:
        if self._current_page > 1:
            self.go_to_page(self._current_page - 1)
    
    @property
    def current_page(self) -> int:
        return self._current_page
    
    @property
    def total_pages(self) -> int:
        return self._total_pages
    
    def is_first_page(self) -> bool:
        return self._current_page == 1
    
    def is_last_page(self) -> bool:
        return self._current_page == self._total_pages
