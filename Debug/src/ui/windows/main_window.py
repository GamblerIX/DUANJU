"""主窗口实现"""
from typing import Optional
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from qfluentwidgets import (
    FluentWindow, NavigationItemPosition, FluentIcon,
    InfoBar, InfoBarPosition
)
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl

from ...core.models import DramaInfo, ThemeMode
from ...core.theme_manager import ThemeManager
from ...core.utils.log_manager import get_logger

logger = get_logger()

from ...data.api.api_client import ApiClient
from ...data.cache.cache_manager import CacheManager
from ...data.config.config_manager import ConfigManager
from ...services.search_service import SearchService
from ...services.video_service import VideoService
from ...services.category_service import CategoryService
from ...services.download_service import DownloadService


class MainWindow(FluentWindow):
    """主窗口 - 使用 QFluentWidgets FluentWindow 实现侧边栏导航"""
    
    initialization_completed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self._initialized = False
        self._init_services()
        self._setup_ui()
        self._connect_signals()
        self._set_ui_enabled(False)
    
    def _init_services(self) -> None:
        """初始化服务"""
        self._config = ConfigManager()
        self._theme_manager = ThemeManager(self)
        self._theme_manager.set_theme(self._config.theme_mode)
        self._api_client = ApiClient(timeout=self._config.api_timeout)
        self._cache = CacheManager()
        
        self._search_service = SearchService(self._api_client, self._cache, self)
        self._video_service = VideoService(self._api_client, self)
        self._category_service = CategoryService(self._api_client, self._cache, self)
        
        import os
        download_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "downloads")
        self._download_service = DownloadService(
            self._api_client, download_dir, self._config.default_quality, self
        )
        
        self._favorites: set = set()
        self._player_window = None
    
    def _setup_ui(self) -> None:
        """初始化UI"""
        self.setWindowTitle("短剧搜索")
        self.setMinimumSize(900, 650)
        self.resize(1025, 750)  # 默认窗口大小
        self.navigationInterface.setExpandWidth(120)
        
        # 导入界面组件
        from ..interfaces.home_interface import HomeInterface
        from ..interfaces.search_interface import SearchInterface
        from ..interfaces.category_interface import CategoryInterface
        from ..interfaces.download_interface import DownloadInterface
        
        self._home_interface = HomeInterface(self._category_service, self)
        self._search_interface = SearchInterface(self._search_service, self._config, self)
        self._category_interface = CategoryInterface(self._category_service, self)
        self._download_interface = DownloadInterface(self._download_service, self)
        
        self.addSubInterface(self._home_interface, FluentIcon.HOME, "首页", NavigationItemPosition.TOP)
        self.addSubInterface(self._search_interface, FluentIcon.SEARCH, "搜索", NavigationItemPosition.TOP)
        self.addSubInterface(self._category_interface, FluentIcon.FOLDER, "分类", NavigationItemPosition.TOP)
        self.addSubInterface(self._download_interface, FluentIcon.DOWNLOAD, "下载", NavigationItemPosition.TOP)
        
        self.navigationInterface.addSeparator()
        
        self.navigationInterface.addItem(
            routeKey="github", icon=FluentIcon.GITHUB, text="GitHub",
            onClick=lambda: QDesktopServices.openUrl(QUrl("https://github.com/GamblerIX/DUANJU")),
            position=NavigationItemPosition.BOTTOM
        )
        
        import os
        gitee_icon_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "assets", "gitee.ico")
        self.navigationInterface.addItem(
            routeKey="gitee", icon=QIcon(gitee_icon_path), text="Gitee",
            onClick=lambda: QDesktopServices.openUrl(QUrl("https://gitee.com/GamblerIX/DUANJU")),
            position=NavigationItemPosition.BOTTOM
        )
        
        self.navigationInterface.addItem(
            routeKey="settings", icon=FluentIcon.SETTING, text="设置",
            onClick=self._show_settings, position=NavigationItemPosition.BOTTOM
        )
        
        self.navigationInterface.setCurrentItem(self._home_interface.objectName())
    
    def _connect_signals(self) -> None:
        """连接信号"""
        self._home_interface.drama_clicked.connect(self._on_drama_clicked)
        self._search_interface.drama_clicked.connect(self._on_drama_clicked)
        self._category_interface.drama_clicked.connect(self._on_drama_clicked)
        
        self._home_interface.favorite_clicked.connect(self._on_favorite_clicked)
        self._search_interface.favorite_clicked.connect(self._on_favorite_clicked)
        self._category_interface.favorite_clicked.connect(self._on_favorite_clicked)
        
        self._video_service.episodes_loaded.connect(self._on_episodes_loaded)
        self._video_service.video_url_loaded.connect(self._on_video_url_loaded)
        self._video_service.error.connect(self._on_error)
        
        self._theme_manager.theme_changed.connect(self._on_theme_changed)
    
    def _set_ui_enabled(self, enabled: bool) -> None:
        """设置 UI 是否可用"""
        self._home_interface.setEnabled(enabled)
        self._search_interface.setEnabled(enabled)
        self._category_interface.setEnabled(enabled)
        self.navigationInterface.setEnabled(enabled)
    
    def start_initialization(self) -> None:
        """启动初始化流程"""
        logger.info("Starting application initialization...")
        
        from ..dialogs.splash_dialog import SplashDialog
        self._splash = SplashDialog(self)
        self._splash.add_task("加载配置", self._init_task_config)
        self._splash.add_task("预加载数据", self._init_task_preload)
        self._splash.init_completed.connect(self._on_init_completed)
        self._splash.init_failed.connect(self._on_init_failed)
        self._splash.show()
        QTimer.singleShot(100, self._splash.start)
    
    def _init_task_config(self) -> bool:
        try:
            logger.debug("Config loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Config load failed: {e}")
            return False
    
    def _init_task_preload(self) -> bool:
        try:
            self._home_interface.load_data()
            self._category_interface.load_data()
            logger.debug("Preload started")
            return True
        except Exception as e:
            logger.error(f"Preload failed: {e}")
            return False
    
    def _on_init_completed(self) -> None:
        logger.info("Application initialization completed")
        self._initialized = True
        self._set_ui_enabled(True)
        self.initialization_completed.emit()
    
    def _on_init_failed(self, error: str) -> None:
        logger.error(f"Application initialization failed: {error}")
        InfoBar.error(title="初始化失败", content=error, orient=Qt.Orientation.Horizontal,
                      isClosable=True, position=InfoBarPosition.TOP, duration=-1, parent=self)
    
    def _on_drama_clicked(self, drama: DramaInfo) -> None:
        logger.log_user_action("drama_click", f"drama={drama.name}, book_id={drama.book_id}")
        self._current_drama = drama
        self._video_service.fetch_episodes(drama.book_id)
    
    def _on_episodes_loaded(self, episode_list) -> None:
        logger.debug(f"Episodes loaded: {len(episode_list.episodes)} episodes")
        if hasattr(self, '_current_drama'):
            self._current_episodes = episode_list.episodes
            self._show_episode_dialog()
    
    def _show_episode_dialog(self) -> None:
        from ..dialogs.episode_dialog import EpisodeDialog
        dialog = EpisodeDialog(self._current_drama, self._current_episodes, self)
        dialog.episode_selected.connect(self._on_episode_selected)
        dialog.episodes_download.connect(self._on_episodes_download)
        dialog.exec()
    
    def _on_episode_selected(self, episode) -> None:
        logger.log_user_action("episode_select", f"episode={episode.title}")
        self._current_episode = episode
        self._video_service.fetch_video_url(episode.video_id, self._config.default_quality)
    
    def _on_episodes_download(self, episodes) -> None:
        logger.log_user_action("episodes_download", f"count={len(episodes)}")
        if hasattr(self, '_current_drama'):
            self._download_service.add_tasks(self._current_drama, episodes)
            self._download_service.start()
            self.navigationInterface.setCurrentItem(self._download_interface.objectName())
            InfoBar.success(title="已添加下载", content=f"已添加 {len(episodes)} 集到下载队列",
                           orient=Qt.Orientation.Horizontal, isClosable=True,
                           position=InfoBarPosition.TOP_RIGHT, duration=3000, parent=self)
    
    def _on_video_url_loaded(self, video_info) -> None:
        logger.debug(f"Video URL loaded: {video_info.quality}")
        if video_info.url and hasattr(self, '_current_drama') and hasattr(self, '_current_episode'):
            from .player_window import PlayerWindow
            episodes = getattr(self, '_current_episodes', [])
            if self._player_window is None:
                self._player_window = PlayerWindow(
                    self._current_drama, self._current_episode, video_info.url, episodes
                )
                self._player_window.closed.connect(self._on_player_closed)
                self._player_window.select_episode_requested.connect(self._on_player_select_episode)
                self._player_window.set_play_episode_callback(self._on_episode_selected)
                self._player_window.show()
            else:
                self._player_window.set_episodes(episodes)
                self._player_window.set_play_episode_callback(self._on_episode_selected)
                self._player_window.update_episode(self._current_episode, video_info.url)
                self._player_window.show()
                self._player_window.activateWindow()
    
    def _on_player_closed(self) -> None:
        logger.log_user_action("player_close")
        self._player_window = None
    
    def _on_player_select_episode(self) -> None:
        if hasattr(self, '_current_drama') and hasattr(self, '_current_episodes'):
            self._show_episode_dialog()
    
    def _on_favorite_clicked(self, drama: DramaInfo, is_favorite: bool) -> None:
        action = "add_favorite" if is_favorite else "remove_favorite"
        logger.log_user_action(action, f"drama={drama.name}")
        if is_favorite:
            self._favorites.add(drama.book_id)
        else:
            self._favorites.discard(drama.book_id)
        
        self._home_interface.set_favorites(self._favorites)
        self._search_interface.set_favorites(self._favorites)
        self._category_interface.set_favorites(self._favorites)
    
    def _on_error(self, error) -> None:
        logger.error(f"Service error: {error.message}")
        InfoBar.error(title="错误", content=error.message, orient=Qt.Orientation.Horizontal,
                      isClosable=True, position=InfoBarPosition.TOP_RIGHT, duration=3000, parent=self)
    
    def _on_theme_changed(self, mode: ThemeMode) -> None:
        logger.log_user_action("theme_change", f"mode={mode.value}")
        self._config.theme_mode = mode
    
    def _show_settings(self) -> None:
        logger.log_user_action("open_settings")
        from ..dialogs.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self._config, self)
        dialog.theme_changed.connect(self._theme_manager.set_theme)
        dialog.exec()
    
    def keyPressEvent(self, event) -> None:
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_F:
                self.navigationInterface.setCurrentItem(self._search_interface.objectName())
                self._search_interface.focus_search()
                return
        if event.key() == Qt.Key.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
            return
        super().keyPressEvent(event)
    
    def closeEvent(self, event) -> None:
        """关闭事件 - 清理资源"""
        # 取消下载任务
        if self._download_service.is_running:
            self._download_service.cancel()
        
        # 关闭播放器窗口
        if self._player_window:
            self._player_window.close()
        
        super().closeEvent(event)
