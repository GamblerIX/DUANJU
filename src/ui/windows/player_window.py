"""视频播放器窗口实现"""
import os
import subprocess
import webbrowser
from typing import Optional, List, Callable
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget
from qfluentwidgets import (
    PushButton, FluentIcon, BodyLabel, InfoBar, InfoBarPosition,
    isDarkTheme
)

from ...core.models import DramaInfo, EpisodeInfo
from ...utils.log_manager import get_logger

logger = get_logger()


class PlayerWindow(QWidget):
    """
    视频播放器窗口
    
    播放器优先级:
    1. 本地 VLC (相对路径 ./vlc/vlc.exe)
    2. 系统 VLC (用户安装的 VLC)
    3. 浏览器播放 (最低优先级)
    """
    
    # 信号
    episode_changed = Signal(object)  # EpisodeInfo
    closed = Signal()
    select_episode_requested = Signal()  # 请求选集
    
    # VLC 路径
    LOCAL_VLC_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "vlc", "vlc.exe")
    SYSTEM_VLC_PATHS = [
        r"C:\Program Files\VideoLAN\VLC\vlc.exe",
        r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
    ]
    
    def __init__(
        self,
        drama: DramaInfo,
        episode: EpisodeInfo,
        video_url: str,
        episodes: Optional[List[EpisodeInfo]] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self._drama = drama
        self._episode = episode
        self._video_url = video_url
        self._episodes = episodes or []
        self._vlc_process: Optional[subprocess.Popen] = None
        self._on_play_episode: Optional[Callable[[EpisodeInfo], None]] = None
        
        # 自动连播定时器
        self._check_timer = QTimer(self)
        self._check_timer.setInterval(1000)
        self._check_timer.timeout.connect(self._check_vlc_status)
        
        self._setup_ui()
        self._update_nav_buttons()
        self._play_video()
    
    def _setup_ui(self) -> None:
        """初始化UI"""
        self.setWindowTitle(f"{self._drama.name} - {self._episode.title}")
        self.setFixedSize(450, 250)
        self.setWindowFlags(Qt.WindowType.Window)
        
        # 设置背景跟随主题
        self._apply_theme()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # 标题
        self._title_label = BodyLabel(f"正在播放: {self._drama.name}")
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._title_label)
        
        # 剧集信息
        self._episode_label = BodyLabel(f"{self._episode.title}")
        self._episode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._episode_label)
        
        # 播放器状态
        self._status_label = BodyLabel("正在启动播放器...")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status_label)
        
        layout.addStretch()
        
        # 剧集导航按钮
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(10)
        
        self._prev_btn = PushButton("上一集", self, FluentIcon.LEFT_ARROW)
        self._prev_btn.clicked.connect(self._play_prev_episode)
        nav_layout.addWidget(self._prev_btn)
        
        self._select_btn = PushButton("选集", self, FluentIcon.MENU)
        self._select_btn.clicked.connect(self._on_select_episode)
        nav_layout.addWidget(self._select_btn)
        
        self._next_btn = PushButton("下一集", self, FluentIcon.RIGHT_ARROW)
        self._next_btn.clicked.connect(self._play_next_episode)
        nav_layout.addWidget(self._next_btn)
        
        layout.addLayout(nav_layout)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        
        self._browser_btn = PushButton("浏览器播放", self, FluentIcon.GLOBE)
        self._browser_btn.clicked.connect(self._play_in_browser)
        btn_layout.addWidget(self._browser_btn)
        
        self._close_btn = PushButton("关闭", self, FluentIcon.CLOSE)
        self._close_btn.clicked.connect(self.close)
        btn_layout.addWidget(self._close_btn)
        
        layout.addLayout(btn_layout)
    
    def _find_vlc(self) -> Optional[str]:
        """查找 VLC 播放器路径
        
        Returns:
            VLC 可执行文件路径，如果未找到则返回 None
        """
        # 1. 检查本地 VLC (相对路径)
        local_vlc = os.path.normpath(self.LOCAL_VLC_PATH)
        if os.path.exists(local_vlc):
            logger.debug(f"Found local VLC: {local_vlc}")
            return local_vlc
        
        # 2. 检查系统 VLC
        for path in self.SYSTEM_VLC_PATHS:
            if os.path.exists(path):
                logger.debug(f"Found system VLC: {path}")
                return path
        
        # 3. 尝试从 PATH 环境变量查找
        try:
            result = subprocess.run(
                ["where", "vlc"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            if result.returncode == 0:
                vlc_path = result.stdout.strip().split('\n')[0]
                if os.path.exists(vlc_path):
                    logger.debug(f"Found VLC in PATH: {vlc_path}")
                    return vlc_path
        except Exception as e:
            logger.debug(f"Failed to find VLC in PATH: {e}")
        
        return None
    
    def _play_video(self) -> None:
        """播放视频"""
        vlc_path = self._find_vlc()
        
        if vlc_path:
            self._play_with_vlc(vlc_path)
        else:
            logger.warning("VLC not found, falling back to browser")
            self._status_label.setText("未找到 VLC，使用浏览器播放")
            self._play_in_browser()
    
    def _play_with_vlc(self, vlc_path: str) -> None:
        """使用 VLC 播放视频"""
        try:
            logger.log_user_action("play_video_vlc", f"url={self._video_url[:50]}...")
            
            # VLC 命令行参数
            cmd = [
                vlc_path,
                self._video_url,
                f"--meta-title={self._drama.name} - {self._episode.title}",
                "--no-video-title-show",
                "--play-and-exit",
            ]
            
            # 启动 VLC 进程
            self._vlc_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            self._check_timer.start()
            
            self._status_label.setText(f"VLC 播放中...")
            logger.info(f"VLC started with PID: {self._vlc_process.pid}")
            
        except Exception as e:
            logger.warning(f"VLC 启动失败: {e}")
            self._status_label.setText(f"VLC 启动失败: {e}")
            InfoBar.error(
                title="播放失败",
                content=f"无法启动 VLC: {e}",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
    
    def _play_in_browser(self) -> None:
        """使用浏览器播放视频"""
        try:
            logger.log_user_action("play_video_browser", f"url={self._video_url[:50]}...")
            webbrowser.open(self._video_url)
            self._status_label.setText("已在浏览器中打开")
        except Exception as e:
            logger.warning(f"浏览器打开失败: {e}")
            self._status_label.setText(f"浏览器打开失败: {e}")

    def _check_vlc_status(self) -> None:
        """检查 VLC 状态"""
        if self._vlc_process and self._vlc_process.poll() is not None:
            # VLC 已退出
            logger.info("VLC process exited, checking for next episode...")
            self._check_timer.stop()
            self._vlc_process = None
            self._play_next_episode()
    
    def play(self, video_url: str, episode: Optional[EpisodeInfo] = None) -> None:
        """
        播放新视频
        
        Args:
            video_url: 视频地址
            episode: 剧集信息
        """
        # 停止当前播放
        self._stop_vlc()
        
        self._video_url = video_url
        if episode:
            self._episode = episode
            self.setWindowTitle(f"{self._drama.name} - {self._episode.title}")
        
        self._play_video()
    
    def _stop_vlc(self) -> None:
        """停止 VLC 进程"""
        self._check_timer.stop()
        if self._vlc_process:
            try:
                self._vlc_process.terminate()
                self._vlc_process.wait(timeout=2)
            except Exception as e:
                logger.warning(f"Failed to terminate VLC: {e}")
                try:
                    self._vlc_process.kill()
                except Exception:
                    pass
            self._vlc_process = None
    
    def closeEvent(self, event) -> None:
        """关闭事件"""
        self._stop_vlc()
        self.closed.emit()
        super().closeEvent(event)
    
    def _apply_theme(self) -> None:
        """应用主题样式"""
        if isDarkTheme():
            self.setStyleSheet("PlayerWindow { background-color: #202020; }")
        else:
            self.setStyleSheet("PlayerWindow { background-color: #f9f9f9; }")
    
    def keyPressEvent(self, event) -> None:
        """键盘事件"""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            return
        
        super().keyPressEvent(event)
    
    def set_episodes(self, episodes: List[EpisodeInfo]) -> None:
        """设置剧集列表"""
        self._episodes = episodes
        self._update_nav_buttons()
    
    def set_play_episode_callback(self, callback: Callable[[EpisodeInfo], None]) -> None:
        """设置播放剧集的回调函数"""
        self._on_play_episode = callback
    
    def _get_current_index(self) -> int:
        """获取当前剧集索引"""
        for i, ep in enumerate(self._episodes):
            if ep.video_id == self._episode.video_id:
                return i
        return -1
    
    def _update_nav_buttons(self) -> None:
        """更新导航按钮状态"""
        current_idx = self._get_current_index()
        has_episodes = len(self._episodes) > 0
        
        # 上一集按钮
        self._prev_btn.setEnabled(has_episodes and current_idx > 0)
        # 下一集按钮
        self._next_btn.setEnabled(has_episodes and current_idx < len(self._episodes) - 1)
        # 选集按钮
        self._select_btn.setEnabled(has_episodes)
    
    def _play_prev_episode(self) -> None:
        """播放上一集"""
        current_idx = self._get_current_index()
        if current_idx > 0:
            prev_episode = self._episodes[current_idx - 1]
            logger.log_user_action("play_prev_episode", f"episode={prev_episode.title}")
            if self._on_play_episode:
                self._on_play_episode(prev_episode)
    
    def _play_next_episode(self) -> None:
        """播放下一集"""
        current_idx = self._get_current_index()
        if current_idx < len(self._episodes) - 1:
            next_episode = self._episodes[current_idx + 1]
            logger.log_user_action("play_next_episode", f"episode={next_episode.title}")
            if self._on_play_episode:
                self._on_play_episode(next_episode)
    
    def _on_select_episode(self) -> None:
        """选集按钮点击"""
        logger.log_user_action("select_episode_from_player")
        self.select_episode_requested.emit()
    
    def update_episode(self, episode: EpisodeInfo, video_url: str) -> None:
        """更新当前播放的剧集"""
        self._stop_vlc()
        self._episode = episode
        self._video_url = video_url
        self.setWindowTitle(f"{self._drama.name} - {self._episode.title}")
        self._episode_label.setText(f"{self._episode.title}")
        self._update_nav_buttons()
        self._play_video()
