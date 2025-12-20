"""主题管理器测试"""
import pytest
from unittest.mock import MagicMock, patch


class TestThemeManagerLogic:
    """主题管理器逻辑测试（不依赖 Qt）"""
    
    def test_theme_mode_enum(self):
        """测试主题模式枚举"""
        from src.core.models import ThemeMode
        
        assert ThemeMode.LIGHT.value == "light"
        assert ThemeMode.DARK.value == "dark"
        assert ThemeMode.AUTO.value == "auto"
    
    def test_theme_mode_list(self):
        """测试主题模式列表"""
        from src.core.models import ThemeMode
        
        modes = list(ThemeMode)
        assert len(modes) == 3
        assert ThemeMode.LIGHT in modes
        assert ThemeMode.DARK in modes
        assert ThemeMode.AUTO in modes


class TestThemeManagerMock:
    """主题管理器 Mock 测试"""
    
    @patch('src.core.theme_manager.setTheme')
    @patch('src.core.theme_manager.isDarkTheme')
    @patch('src.core.theme_manager.setThemeColor')
    def test_theme_manager_init(self, mock_set_color, mock_is_dark, mock_set_theme):
        """测试主题管理器初始化"""
        from src.core.theme_manager import ThemeManager
        from src.core.models import ThemeMode
        
        manager = ThemeManager()
        assert manager.get_current_theme() == ThemeMode.AUTO
        assert manager.current_mode == ThemeMode.AUTO
    
    @patch('src.core.theme_manager.setTheme')
    @patch('src.core.theme_manager.isDarkTheme')
    @patch('src.core.theme_manager.setThemeColor')
    def test_set_theme_light(self, mock_set_color, mock_is_dark, mock_set_theme):
        """测试设置浅色主题"""
        from src.core.theme_manager import ThemeManager, Theme
        from src.core.models import ThemeMode
        
        manager = ThemeManager()
        manager.set_theme(ThemeMode.LIGHT)
        
        assert manager.current_mode == ThemeMode.LIGHT
        mock_set_theme.assert_called_with(Theme.LIGHT)
    
    @patch('src.core.theme_manager.setTheme')
    @patch('src.core.theme_manager.isDarkTheme')
    @patch('src.core.theme_manager.setThemeColor')
    def test_set_theme_dark(self, mock_set_color, mock_is_dark, mock_set_theme):
        """测试设置深色主题"""
        from src.core.theme_manager import ThemeManager, Theme
        from src.core.models import ThemeMode
        
        manager = ThemeManager()
        manager.set_theme(ThemeMode.DARK)
        
        assert manager.current_mode == ThemeMode.DARK
        mock_set_theme.assert_called_with(Theme.DARK)
    
    @patch('src.core.theme_manager.setTheme')
    @patch('src.core.theme_manager.isDarkTheme')
    @patch('src.core.theme_manager.setThemeColor')
    def test_set_theme_auto(self, mock_set_color, mock_is_dark, mock_set_theme):
        """测试设置自动主题"""
        from src.core.theme_manager import ThemeManager, Theme
        from src.core.models import ThemeMode
        
        manager = ThemeManager()
        manager.set_theme(ThemeMode.AUTO)
        
        assert manager.current_mode == ThemeMode.AUTO
        mock_set_theme.assert_called_with(Theme.AUTO)
    
    @patch('src.core.theme_manager.setTheme')
    @patch('src.core.theme_manager.isDarkTheme', return_value=True)
    @patch('src.core.theme_manager.setThemeColor')
    def test_is_dark(self, mock_set_color, mock_is_dark, mock_set_theme):
        """测试检查深色主题"""
        from src.core.theme_manager import ThemeManager
        
        manager = ThemeManager()
        assert manager.is_dark() is True
        mock_is_dark.assert_called()
    
    @patch('src.core.theme_manager.setTheme')
    @patch('src.core.theme_manager.isDarkTheme', return_value=False)
    @patch('src.core.theme_manager.setThemeColor')
    def test_toggle_theme_to_dark(self, mock_set_color, mock_is_dark, mock_set_theme):
        """测试切换到深色主题"""
        from src.core.theme_manager import ThemeManager, Theme
        from src.core.models import ThemeMode
        
        manager = ThemeManager()
        manager.toggle_theme()
        
        assert manager.current_mode == ThemeMode.DARK
    
    @patch('src.core.theme_manager.setTheme')
    @patch('src.core.theme_manager.isDarkTheme', return_value=True)
    @patch('src.core.theme_manager.setThemeColor')
    def test_toggle_theme_to_light(self, mock_set_color, mock_is_dark, mock_set_theme):
        """测试切换到浅色主题"""
        from src.core.theme_manager import ThemeManager, Theme
        from src.core.models import ThemeMode
        
        manager = ThemeManager()
        manager.toggle_theme()
        
        assert manager.current_mode == ThemeMode.LIGHT
    
    @patch('src.core.theme_manager.setTheme')
    @patch('src.core.theme_manager.isDarkTheme')
    @patch('src.core.theme_manager.setThemeColor')
    def test_apply_theme(self, mock_set_color, mock_is_dark, mock_set_theme):
        """测试应用当前主题"""
        from src.core.theme_manager import ThemeManager, Theme
        from src.core.models import ThemeMode
        
        manager = ThemeManager()
        manager._current_mode = ThemeMode.DARK
        manager.apply_theme()
        
        mock_set_theme.assert_called_with(Theme.DARK)
    
    @patch('src.core.theme_manager.setTheme')
    @patch('src.core.theme_manager.isDarkTheme')
    @patch('src.core.theme_manager.setThemeColor')
    def test_set_theme_color(self, mock_set_color, mock_is_dark, mock_set_theme):
        """测试设置主题强调色"""
        from src.core.theme_manager import ThemeManager
        
        manager = ThemeManager()
        manager.set_theme_color("#FF5500")
        
        mock_set_color.assert_called_once()
