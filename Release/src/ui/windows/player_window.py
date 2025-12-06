import os
import subprocess
import webbrowser
from typing import Optional, List, Callable
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget
from qfluentwidgets import PushButton, FluentIcon, BodyLabel, InfoBar, InfoBarPosition, isDarkTheme
from ...core.models import DramaInfo, EpisodeInfo


class PlayerWindow(QWidget):
    episode_changed = pyqtSignal(object)
    closed = pyqtSignal()
    select_episode_requested = pyqtSignal()
    
    LOCAL_VLC_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "vlc", "vlc.exe")
    SYSTEM_VLC_PATHS = [r"C:\Program Files\VideoLAN\VLC\vlc.exe", r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"]
    
    def __init__(self, drama: DramaInfo, episode: EpisodeInfo, video_url: str,
                 episodes: Optional[List[EpisodeInfo]] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._drama = drama
        self._episode = episode
        self._video_url = video_url
        self._episodes = episodes or []
        self._vlc_process: Optional[subprocess.Popen] = None
        self._on_play_episode: Optional[Callable[[EpisodeInfo], None]] = None
        self._setup_ui()
        self._update_nav_buttons()
        self._play_video()
    
    def _setup_ui(self) -> None:
        self.setWindowTitle(f"{self._drama.name} - {self._episode.title}")
        self.setFixedSize(450, 250)
        self.setWindowFlags(Qt.WindowType.Window)
        self._apply_theme()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        self._title_label = BodyLabel(f"正在播放: {self._drama.name}")
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._title_label)
        self._episode_label = BodyLabel(f"{self._episode.title}")
        self._episode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._episode_label)
        self._status_label = BodyLabel("正在启动播放器...")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status_label)
        layout.addStretch()
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
        btn_layout = QHBoxLayout()
        self._browser_btn = PushButton("浏览器播放", self, FluentIcon.GLOBE)
        self._browser_btn.clicked.connect(self._play_in_browser)
        btn_layout.addWidget(self._browser_btn)
        self._close_btn = PushButton("关闭", self, FluentIcon.CLOSE)
        self._close_btn.clicked.connect(self.close)
        btn_layout.addWidget(self._close_btn)
        layout.addLayout(btn_layout)
    
    def _find_vlc(self) -> Optional[str]:
        local_vlc = os.path.normpath(self.LOCAL_VLC_PATH)
        if os.path.exists(local_vlc):
            return local_vlc
        for path in self.SYSTEM_VLC_PATHS:
            if os.path.exists(path):
                return path
        try:
            result = subprocess.run(["where", "vlc"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                vlc_path = result.stdout.strip().split('\n')[0]
                if os.path.exists(vlc_path):
                    return vlc_path
        except Exception:
            pass
        return None
    
    def _play_video(self) -> None:
        vlc_path = self._find_vlc()
        if vlc_path:
            self._play_with_vlc(vlc_path)
        else:
            self._status_label.setText("未找到 VLC，使用浏览器播放")
            self._play_in_browser()
    
    def _play_with_vlc(self, vlc_path: str) -> None:
        try:
            cmd = [vlc_path, self._video_url, f"--meta-title={self._drama.name} - {self._episode.title}",
                   "--no-video-title-show"]
            self._vlc_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self._status_label.setText(f"VLC 播放中...")
        except Exception as e:
            self._status_label.setText(f"VLC 启动失败")
            InfoBar.error(title="播放失败", content=f"无法启动 VLC", orient=Qt.Orientation.Horizontal,
                         isClosable=True, position=InfoBarPosition.TOP, duration=3000, parent=self)
    
    def _play_in_browser(self) -> None:
        try:
            webbrowser.open(self._video_url)
            self._status_label.setText("已在浏览器中打开")
        except Exception:
            self._status_label.setText(f"浏览器打开失败")
    
    def play(self, video_url: str, episode: Optional[EpisodeInfo] = None) -> None:
        self._stop_vlc()
        self._video_url = video_url
        if episode:
            self._episode = episode
            self.setWindowTitle(f"{self._drama.name} - {self._episode.title}")
        self._play_video()
    
    def _stop_vlc(self) -> None:
        if self._vlc_process:
            try:
                self._vlc_process.terminate()
                self._vlc_process.wait(timeout=2)
            except Exception:
                try:
                    self._vlc_process.kill()
                except Exception:
                    pass
            self._vlc_process = None
    
    def closeEvent(self, event) -> None:
        self._stop_vlc()
        self.closed.emit()
        super().closeEvent(event)
    
    def _apply_theme(self) -> None:
        if isDarkTheme():
            self.setStyleSheet("PlayerWindow { background-color: #202020; }")
        else:
            self.setStyleSheet("PlayerWindow { background-color: #f9f9f9; }")
    
    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)
    
    def set_episodes(self, episodes: List[EpisodeInfo]) -> None:
        self._episodes = episodes
        self._update_nav_buttons()
    
    def set_play_episode_callback(self, callback: Callable[[EpisodeInfo], None]) -> None:
        self._on_play_episode = callback
    
    def _get_current_index(self) -> int:
        for i, ep in enumerate(self._episodes):
            if ep.video_id == self._episode.video_id:
                return i
        return -1
    
    def _update_nav_buttons(self) -> None:
        current_idx = self._get_current_index()
        has_episodes = len(self._episodes) > 0
        self._prev_btn.setEnabled(has_episodes and current_idx > 0)
        self._next_btn.setEnabled(has_episodes and current_idx < len(self._episodes) - 1)
        self._select_btn.setEnabled(has_episodes)
    
    def _play_prev_episode(self) -> None:
        current_idx = self._get_current_index()
        if current_idx > 0:
            prev_episode = self._episodes[current_idx - 1]
            if self._on_play_episode:
                self._on_play_episode(prev_episode)
    
    def _play_next_episode(self) -> None:
        current_idx = self._get_current_index()
        if current_idx < len(self._episodes) - 1:
            next_episode = self._episodes[current_idx + 1]
            if self._on_play_episode:
                self._on_play_episode(next_episode)
    
    def _on_select_episode(self) -> None:
        self.select_episode_requested.emit()
    
    def update_episode(self, episode: EpisodeInfo, video_url: str) -> None:
        self._stop_vlc()
        self._episode = episode
        self._video_url = video_url
        self.setWindowTitle(f"{self._drama.name} - {self._episode.title}")
        self._episode_label.setText(f"{self._episode.title}")
        self._update_nav_buttons()
        self._play_video()
