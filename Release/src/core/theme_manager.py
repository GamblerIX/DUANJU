from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal
from qfluentwidgets import setTheme, Theme, setThemeColor, isDarkTheme
from .models import ThemeMode


class ThemeManager(QObject):
    theme_changed = pyqtSignal(object)
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._current_mode = ThemeMode.AUTO
    
    def get_current_theme(self) -> ThemeMode:
        return self._current_mode
    
    def set_theme(self, mode: ThemeMode) -> None:
        self._current_mode = mode
        if mode == ThemeMode.LIGHT:
            setTheme(Theme.LIGHT)
        elif mode == ThemeMode.DARK:
            setTheme(Theme.DARK)
        else:
            setTheme(Theme.AUTO)
        self.theme_changed.emit(mode)
    
    def apply_theme(self) -> None:
        self.set_theme(self._current_mode)
    
    def is_dark(self) -> bool:
        return isDarkTheme()
    
    def toggle_theme(self) -> None:
        if self.is_dark():
            self.set_theme(ThemeMode.LIGHT)
        else:
            self.set_theme(ThemeMode.DARK)
    
    def set_theme_color(self, color: str) -> None:
        from PyQt6.QtGui import QColor
        setThemeColor(QColor(color))
    
    @property
    def current_mode(self) -> ThemeMode:
        return self._current_mode
