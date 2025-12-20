"""主题管理器实现"""
from typing import Optional
from PySide6.QtCore import QObject, Signal
from qfluentwidgets import setTheme, Theme, setThemeColor, isDarkTheme

from .models import ThemeMode


class ThemeManager(QObject):
    """主题管理器 - 管理应用主题切换"""
    
    theme_changed = Signal(object)
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._current_mode = ThemeMode.AUTO
    
    def get_current_theme(self) -> ThemeMode:
        """获取当前主题模式"""
        return self._current_mode
    
    def set_theme(self, mode: ThemeMode) -> None:
        """设置主题模式"""
        self._current_mode = mode
        
        if mode == ThemeMode.LIGHT:
            setTheme(Theme.LIGHT)
        elif mode == ThemeMode.DARK:
            setTheme(Theme.DARK)
        else:
            setTheme(Theme.AUTO)
        
        self.theme_changed.emit(mode)
    
    def apply_theme(self) -> None:
        """应用当前主题"""
        self.set_theme(self._current_mode)
    
    def is_dark(self) -> bool:
        """检查当前是否为深色主题"""
        return isDarkTheme()
    
    def toggle_theme(self) -> None:
        """切换主题"""
        if self.is_dark():
            self.set_theme(ThemeMode.LIGHT)
        else:
            self.set_theme(ThemeMode.DARK)
    
    def set_theme_color(self, color: str) -> None:
        """设置主题强调色"""
        from PySide6.QtGui import QColor
        setThemeColor(QColor(color))
    
    @property
    def current_mode(self) -> ThemeMode:
        return self._current_mode
