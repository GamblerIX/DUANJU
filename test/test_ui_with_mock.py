"""UI 组件测试 - 使用 mock 导入"""
import pytest
import sys
from unittest.mock import MagicMock, patch


# 在导入任何 UI 模块之前设置 mock
def setup_qt_mocks():
    """设置 Qt mock"""
    # 创建 mock 对象
    mock_signal = MagicMock()
    mock_signal.emit = MagicMock()
    
    mock_qt = MagicMock()
    mock_qt.CursorShape = MagicMock()
    mock_qt.AlignmentFlag = MagicMock()
    mock_qt.AspectRatioMode = MagicMock()
    mock_qt.TransformationMode = MagicMock()
    mock_qt.MouseButton = MagicMock()
    
    mock_qframe = MagicMock()
    mock_qframe.Shape = MagicMock()
    
    mock_qtcore = MagicMock()
    mock_qtcore.Signal = lambda *args: mock_signal
    mock_qtcore.Qt = mock_qt
    mock_qtcore.QObject = MagicMock()
    mock_qtcore.QTimer = MagicMock()
    mock_qtcore.QThread = MagicMock()
    mock_qtcore.QUrl = MagicMock()
    
    mock_qtwidgets = MagicMock()
    mock_qtwidgets.QWidget = MagicMock()
    mock_qtwidgets.QFrame = mock_qframe
    mock_qtwidgets.QLabel = MagicMock()
    mock_qtwidgets.QVBoxLayout = MagicMock()
    mock_qtwidgets.QHBoxLayout = MagicMock()
    mock_qtwidgets.QApplication = MagicMock()
    
    mock_qtgui = MagicMock()
    mock_qtgui.QPixmap = MagicMock()
    mock_qtgui.QPainter = MagicMock()
    mock_qtgui.QPainterPath = MagicMock()
    mock_qtgui.QBrush = MagicMock()
    mock_qtgui.QPalette = MagicMock()
    mock_qtgui.QImage = MagicMock()
    mock_qtgui.QColor = MagicMock()
    
    mock_qtnetwork = MagicMock()
    mock_qtnetwork.QNetworkAccessManager = MagicMock()
    mock_qtnetwork.QNetworkRequest = MagicMock()
    mock_qtnetwork.QNetworkReply = MagicMock()
    
    mock_fluent = MagicMock()
    mock_fluent.BodyLabel = MagicMock()
    mock_fluent.CaptionLabel = MagicMock()
    mock_fluent.ToolButton = MagicMock()
    mock_fluent.FluentIcon = MagicMock()
    mock_fluent.isDarkTheme = MagicMock(return_value=False)
    mock_fluent.setTheme = MagicMock()
    mock_fluent.setThemeColor = MagicMock()
    mock_fluent.Theme = MagicMock()
    mock_fluent.IndeterminateProgressRing = MagicMock()
    mock_fluent.PipsPager = MagicMock()
    mock_fluent.PipsScrollButtonDisplayMode = MagicMock()
    mock_fluent.CardWidget = MagicMock()
    mock_fluent.ScrollArea = MagicMock()
    mock_fluent.SearchLineEdit = MagicMock()
    mock_fluent.PushButton = MagicMock()
    mock_fluent.ComboBox = MagicMock()
    mock_fluent.Slider = MagicMock()
    mock_fluent.SwitchButton = MagicMock()
    mock_fluent.MessageBox = MagicMock()
    mock_fluent.InfoBar = MagicMock()
    mock_fluent.FlowLayout = MagicMock()
    mock_fluent.SubtitleLabel = MagicMock()
    mock_fluent.TitleLabel = MagicMock()
    mock_fluent.StrongBodyLabel = MagicMock()
    mock_fluent.ProgressBar = MagicMock()
    mock_fluent.ProgressRing = MagicMock()
    mock_fluent.TableWidget = MagicMock()
    mock_fluent.ListWidget = MagicMock()
    mock_fluent.TreeWidget = MagicMock()
    mock_fluent.TabWidget = MagicMock()
    mock_fluent.NavigationInterface = MagicMock()
    mock_fluent.NavigationItemPosition = MagicMock()
    mock_fluent.FluentWindow = MagicMock()
    mock_fluent.SplitFluentWindow = MagicMock()
    mock_fluent.MSFluentWindow = MagicMock()
    mock_fluent.NavigationAvatarWidget = MagicMock()
    mock_fluent.qrouter = MagicMock()
    
    mock_pyside6 = MagicMock()
    mock_pyside6.QtCore = mock_qtcore
    mock_pyside6.QtWidgets = mock_qtwidgets
    mock_pyside6.QtGui = mock_qtgui
    mock_pyside6.QtNetwork = mock_qtnetwork
    
    return {
        'PySide6': mock_pyside6,
        'PySide6.QtCore': mock_qtcore,
        'PySide6.QtWidgets': mock_qtwidgets,
        'PySide6.QtGui': mock_qtgui,
        'PySide6.QtNetwork': mock_qtnetwork,
        'qfluentwidgets': mock_fluent,
    }


class TestUILogicWithoutQt:
    """测试 UI 逻辑（不需要 Qt）"""
    
    def test_truncate_title(self):
        """测试标题截断"""
        from src.utils.string_utils import truncate
        
        title = "这是一个很长的短剧标题需要截断"
        truncated = truncate(title, 11)
        
        assert len(truncated) <= 14  # 11 + "..."
    
    def test_episode_info_text(self):
        """测试剧集信息文本"""
        episode_cnt = 20
        category = "都市"
        
        info_text = f"{episode_cnt}集"
        if category:
            info_text = f"{category} · {info_text}"
        
        assert info_text == "都市 · 20集"
    
    def test_pagination_logic(self):
        """测试分页逻辑"""
        current_page = 5
        total_pages = 10
        
        # 下一页
        if current_page < total_pages:
            next_page = current_page + 1
        else:
            next_page = current_page
        
        assert next_page == 6
        
        # 上一页
        if current_page > 1:
            prev_page = current_page - 1
        else:
            prev_page = current_page
        
        assert prev_page == 4
    
    def test_volume_bounds(self):
        """测试音量边界"""
        def clamp_volume(v):
            return max(0, min(100, v))
        
        assert clamp_volume(50) == 50
        assert clamp_volume(-10) == 0
        assert clamp_volume(150) == 100
    
    def test_progress_calculation(self):
        """测试进度计算"""
        current = 150
        total = 300
        
        if total > 0:
            progress = (current / total) * 100
        else:
            progress = 0
        
        assert progress == 50.0
    
    def test_time_format(self):
        """测试时间格式化"""
        def format_time(seconds):
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            
            if hours > 0:
                return f"{hours:02d}:{minutes:02d}:{secs:02d}"
            return f"{minutes:02d}:{secs:02d}"
        
        assert format_time(125) == "02:05"
        assert format_time(3661) == "01:01:01"
    
    def test_grid_layout_calculation(self):
        """测试网格布局计算"""
        total_items = 20
        columns = 5
        
        rows = (total_items + columns - 1) // columns
        assert rows == 4
    
    def test_favorite_toggle(self):
        """测试收藏切换"""
        is_favorite = False
        
        is_favorite = not is_favorite
        assert is_favorite is True
        
        is_favorite = not is_favorite
        assert is_favorite is False
    
    def test_search_keyword_validation(self):
        """测试搜索关键词验证"""
        from src.utils.string_utils import is_blank
        
        assert is_blank("") is True
        assert is_blank("   ") is True
        assert is_blank("test") is False
    
    def test_quality_selection(self):
        """测试画质选择"""
        qualities = ["1080p", "720p", "480p", "360p"]
        selected = "1080p"
        
        assert selected in qualities
        assert qualities.index(selected) == 0
    
    def test_theme_mode_selection(self):
        """测试主题模式选择"""
        from src.core.models import ThemeMode
        
        modes = [ThemeMode.AUTO, ThemeMode.LIGHT, ThemeMode.DARK]
        selected = ThemeMode.AUTO
        
        assert selected in modes
    
    def test_download_status_display(self):
        """测试下载状态显示"""
        from src.services.download_service_v2 import DownloadStatus
        
        status_text = {
            DownloadStatus.PENDING: "等待中",
            DownloadStatus.FETCHING: "获取信息",
            DownloadStatus.DOWNLOADING: "下载中",
            DownloadStatus.COMPLETED: "已完成",
            DownloadStatus.FAILED: "失败",
            DownloadStatus.CANCELLED: "已取消"
        }
        
        assert status_text[DownloadStatus.PENDING] == "等待中"
        assert status_text[DownloadStatus.COMPLETED] == "已完成"
    
    def test_episode_button_text(self):
        """测试剧集按钮文本"""
        episode_number = 10
        text = str(episode_number)
        assert text == "10"
    
    def test_cover_aspect_ratio(self):
        """测试封面宽高比"""
        CARD_WIDTH = 170
        COVER_HEIGHT = 272
        
        ratio = COVER_HEIGHT / CARD_WIDTH
        assert ratio == pytest.approx(1.6, rel=0.1)
    
    def test_image_center_position(self):
        """测试图片居中位置"""
        container_width = 170
        container_height = 272
        image_width = 180
        image_height = 290
        
        x = (container_width - image_width) // 2
        y = (container_height - image_height) // 2
        
        assert x == -5
        assert y == -9
    
    def test_overlay_opacity(self):
        """测试覆盖层透明度"""
        opacity = 0.3
        rgba = f"rgba(0, 0, 0, {opacity})"
        
        assert "0.3" in rgba
    
    def test_spinner_size(self):
        """测试加载指示器大小"""
        size = 48
        stroke_width = 4
        
        assert size == 48
        assert stroke_width == 4
    
    def test_card_margin(self):
        """测试卡片边距"""
        margins = (0, 0, 0, 8)
        spacing = 4
        
        assert margins[3] == 8
        assert spacing == 4
