"""视频播放器控件实现"""
from typing import Optional
from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QSizePolicy
)
from qfluentwidgets import (
    Slider, ToolButton, FluentIcon, BodyLabel, ProgressRing
)

from ...core.models import PlaybackState
from ...utils.time_utils import format_duration


class VideoPlayer(QWidget):
    """
    视频播放器控件
    
    集成 VLC 播放器，提供播放控制界面
    """
    
    # 信号
    state_changed = Signal(object)  # PlaybackState
    position_changed = Signal(int)  # 毫秒
    duration_changed = Signal(int)  # 毫秒
    error_occurred = Signal(str)
    playback_finished = Signal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._state = PlaybackState.STOPPED
        self._duration = 0
        self._position = 0
        self._volume = 100
        self._is_muted = False
        self._vlc_instance = None
        self._player = None
        self._setup_ui()
        self._setup_vlc()
        self._setup_timer()
    
    def _setup_ui(self) -> None:
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 视频显示区域
        self._video_frame = QFrame()
        self._video_frame.setStyleSheet("background-color: black;")
        self._video_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self._video_frame)
        
        # 加载指示器（覆盖在视频上）
        self._loading = ProgressRing(self._video_frame)
        self._loading.setFixedSize(48, 48)
        self._loading.hide()
        
        # 控制栏
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.setContentsMargins(8, 4, 8, 8)
        controls_layout.setSpacing(4)
        
        # 进度条
        progress_layout = QHBoxLayout()
        self._time_label = BodyLabel("00:00")
        self._progress_slider = Slider(Qt.Orientation.Horizontal)
        self._progress_slider.setRange(0, 1000)
        self._progress_slider.sliderPressed.connect(self._on_slider_pressed)
        self._progress_slider.sliderReleased.connect(self._on_slider_released)
        self._duration_label = BodyLabel("00:00")
        
        progress_layout.addWidget(self._time_label)
        progress_layout.addWidget(self._progress_slider, 1)
        progress_layout.addWidget(self._duration_label)
        controls_layout.addLayout(progress_layout)
        
        # 控制按钮
        buttons_layout = QHBoxLayout()
        
        self._play_btn = ToolButton(FluentIcon.PLAY)
        self._play_btn.clicked.connect(self.toggle_play)
        buttons_layout.addWidget(self._play_btn)
        
        self._stop_btn = ToolButton(FluentIcon.CLOSE)
        self._stop_btn.clicked.connect(self.stop)
        buttons_layout.addWidget(self._stop_btn)
        
        buttons_layout.addStretch()
        
        # 音量控制
        self._mute_btn = ToolButton(FluentIcon.VOLUME)
        self._mute_btn.clicked.connect(self.toggle_mute)
        buttons_layout.addWidget(self._mute_btn)
        
        self._volume_slider = Slider(Qt.Orientation.Horizontal)
        self._volume_slider.setRange(0, 100)
        self._volume_slider.setValue(100)
        self._volume_slider.setFixedWidth(100)
        self._volume_slider.valueChanged.connect(self._on_volume_changed)
        buttons_layout.addWidget(self._volume_slider)
        
        # 全屏按钮
        self._fullscreen_btn = ToolButton(FluentIcon.FULL_SCREEN)
        self._fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        buttons_layout.addWidget(self._fullscreen_btn)
        
        controls_layout.addLayout(buttons_layout)
        layout.addWidget(controls_widget)
        
        self._slider_pressed = False
    
    def _setup_vlc(self) -> None:
        """初始化 VLC 播放器"""
        try:
            import vlc
            self._vlc_instance = vlc.Instance()
            self._player = self._vlc_instance.media_player_new()
            
            # 设置视频输出窗口
            if sys.platform.startswith('linux'):
                self._player.set_xwindow(self._video_frame.winId())
            elif sys.platform == 'win32':
                self._player.set_hwnd(self._video_frame.winId())
            elif sys.platform == 'darwin':
                self._player.set_nsobject(int(self._video_frame.winId()))
        except ImportError:
            self._vlc_instance = None
            self._player = None
    
    def _setup_timer(self) -> None:
        """设置更新定时器"""
        self._update_timer = QTimer(self)
        self._update_timer.setInterval(100)  # 100ms 更新一次
        self._update_timer.timeout.connect(self._update_position)
    
    def _update_position(self) -> None:
        """更新播放位置"""
        if self._player and not self._slider_pressed:
            try:
                pos = self._player.get_time()
                if pos >= 0:
                    self._position = pos
                    self._time_label.setText(format_duration(pos))
                    
                    if self._duration > 0:
                        slider_pos = int(pos * 1000 / self._duration)
                        self._progress_slider.setValue(slider_pos)
                    
                    self.position_changed.emit(pos)
                
                # 检查播放状态
                import vlc
                state = self._player.get_state()
                if state == vlc.State.Ended:
                    self._set_state(PlaybackState.STOPPED)
                    self.playback_finished.emit()
                elif state == vlc.State.Buffering:
                    self._set_state(PlaybackState.BUFFERING)
            except Exception:
                pass
    
    def play(self, url: str) -> None:
        """
        播放视频
        
        Args:
            url: 视频地址
        """
        if not self._player:
            self.error_occurred.emit("VLC 播放器未初始化")
            return
        
        try:
            import vlc
            media = self._vlc_instance.media_new(url)
            self._player.set_media(media)
            self._player.play()
            self._set_state(PlaybackState.PLAYING)
            self._update_timer.start()
            
            # 获取时长（延迟获取）
            QTimer.singleShot(1000, self._update_duration)
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def _update_duration(self) -> None:
        """更新视频时长"""
        if self._player:
            duration = self._player.get_length()
            if duration > 0:
                self._duration = duration
                self._duration_label.setText(format_duration(duration))
                self.duration_changed.emit(duration)
    
    def pause(self) -> None:
        """暂停播放"""
        if self._player:
            self._player.pause()
            self._set_state(PlaybackState.PAUSED)
    
    def resume(self) -> None:
        """继续播放"""
        if self._player:
            self._player.play()
            self._set_state(PlaybackState.PLAYING)
    
    def stop(self) -> None:
        """停止播放"""
        if self._player:
            self._player.stop()
            self._set_state(PlaybackState.STOPPED)
            self._update_timer.stop()
            self._position = 0
            self._time_label.setText("00:00")
            self._progress_slider.setValue(0)
    
    def toggle_play(self) -> None:
        """切换播放/暂停"""
        if self._state == PlaybackState.PLAYING:
            self.pause()
        elif self._state == PlaybackState.PAUSED:
            self.resume()
    
    def seek(self, position_ms: int) -> None:
        """
        跳转到指定位置
        
        Args:
            position_ms: 位置（毫秒）
        """
        if self._player:
            self._player.set_time(position_ms)
    
    def set_volume(self, volume: int) -> None:
        """
        设置音量
        
        Args:
            volume: 音量（0-100）
        """
        self._volume = max(0, min(100, volume))
        if self._player:
            self._player.audio_set_volume(self._volume)
        self._volume_slider.setValue(self._volume)
        self._update_mute_icon()
    
    def toggle_mute(self) -> None:
        """切换静音"""
        self._is_muted = not self._is_muted
        if self._player:
            self._player.audio_set_mute(self._is_muted)
        self._update_mute_icon()
    
    def _update_mute_icon(self) -> None:
        """更新静音图标"""
        if self._is_muted or self._volume == 0:
            self._mute_btn.setIcon(FluentIcon.MUTE)
        else:
            self._mute_btn.setIcon(FluentIcon.VOLUME)
    
    def toggle_fullscreen(self) -> None:
        """切换全屏"""
        parent = self.window()
        if parent:
            if parent.isFullScreen():
                parent.showNormal()
            else:
                parent.showFullScreen()
    
    def _set_state(self, state: PlaybackState) -> None:
        """设置播放状态"""
        if state != self._state:
            self._state = state
            self._update_play_button()
            self._loading.setVisible(state == PlaybackState.BUFFERING)
            self.state_changed.emit(state)
    
    def _update_play_button(self) -> None:
        """更新播放按钮图标"""
        if self._state == PlaybackState.PLAYING:
            self._play_btn.setIcon(FluentIcon.PAUSE)
        else:
            self._play_btn.setIcon(FluentIcon.PLAY)
    
    def _on_slider_pressed(self) -> None:
        """进度条按下"""
        self._slider_pressed = True
    
    def _on_slider_released(self) -> None:
        """进度条释放"""
        self._slider_pressed = False
        if self._duration > 0:
            pos = self._progress_slider.value() * self._duration // 1000
            self.seek(pos)
    
    def _on_volume_changed(self, value: int) -> None:
        """音量改变"""
        self.set_volume(value)
    
    @property
    def state(self) -> PlaybackState:
        """获取播放状态"""
        return self._state
    
    @property
    def position(self) -> int:
        """获取当前位置（毫秒）"""
        return self._position
    
    @property
    def duration(self) -> int:
        """获取总时长（毫秒）"""
        return self._duration
    
    @property
    def volume(self) -> int:
        """获取音量"""
        return self._volume
    
    def keyPressEvent(self, event) -> None:
        """处理键盘事件"""
        key = event.key()
        
        # 空格键：播放/暂停
        if key == Qt.Key.Key_Space:
            self.toggle_play()
            return
        
        # 左右方向键：快退/快进 5 秒
        if key == Qt.Key.Key_Left:
            self.seek(max(0, self._position - 5000))
            return
        if key == Qt.Key.Key_Right:
            self.seek(min(self._duration, self._position + 5000))
            return
        
        # 上下方向键：调整音量
        if key == Qt.Key.Key_Up:
            self.set_volume(self._volume + 10)
            return
        if key == Qt.Key.Key_Down:
            self.set_volume(self._volume - 10)
            return
        
        super().keyPressEvent(event)


# 需要导入 sys
import sys
