"""剧集选择对话框实现"""
from typing import Optional, List
from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtWidgets import QVBoxLayout, QWidget, QGridLayout, QHBoxLayout
from qfluentwidgets import (
    SubtitleLabel, BodyLabel, 
    PushButton, ScrollArea, CheckBox, RadioButton,
    MessageBoxBase, isDarkTheme
)

from ...core.models import EpisodeInfo, DramaInfo
from ...utils.log_manager import get_logger

logger = get_logger()


class EpisodeDialog(MessageBoxBase):
    """
    剧集选择对话框
    
    显示剧集列表，支持选择播放或下载
    使用 MessageBoxBase 以支持主题
    """
    
    # 信号：选择剧集播放
    episode_selected = Signal(object)  # EpisodeInfo
    # 信号：下载选中的剧集
    episodes_download = Signal(list)  # List[EpisodeInfo]
    
    def __init__(
        self,
        drama: DramaInfo,
        episodes: List[EpisodeInfo],
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self._drama = drama
        self._episodes = episodes
        self._buttons: List[PushButton] = []
        self._checkboxes: List[CheckBox] = []
        self._is_download_mode = False
        self._setup_ui()
        # 延迟创建按钮，避免卡顿
        QTimer.singleShot(50, self._create_buttons)
    
    def _setup_ui(self) -> None:
        """初始化UI"""
        self.widget.setFixedSize(600, 500)
        
        # 隐藏默认按钮区域
        self.yesButton.hide()
        self.cancelButton.hide()
        self.buttonGroup.hide()
        
        # 主布局
        layout = self.viewLayout
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(10)
        
        # 标题
        self.titleLabel = SubtitleLabel(self._drama.name)
        layout.addWidget(self.titleLabel)
        
        # 剧集数量提示
        self.countLabel = BodyLabel(f"共 {len(self._episodes)} 集")
        layout.addWidget(self.countLabel)
        
        # 模式选择区域
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(20)
        
        self._play_radio = RadioButton("播放")
        self._play_radio.setChecked(True)
        self._play_radio.clicked.connect(self._on_mode_changed)
        mode_layout.addWidget(self._play_radio)
        
        self._download_radio = RadioButton("下载")
        self._download_radio.clicked.connect(self._on_mode_changed)
        mode_layout.addWidget(self._download_radio)
        
        mode_layout.addStretch()
        layout.addLayout(mode_layout)
        
        # 全选/反选按钮区域（下载模式时显示）
        self._select_btn_layout = QHBoxLayout()
        self._select_btn_layout.setSpacing(10)
        
        self._select_all_btn = PushButton("全选")
        self._select_all_btn.clicked.connect(self._select_all)
        self._select_all_btn.hide()
        self._select_btn_layout.addWidget(self._select_all_btn)
        
        self._deselect_all_btn = PushButton("反选")
        self._deselect_all_btn.clicked.connect(self._toggle_selection)
        self._deselect_all_btn.hide()
        self._select_btn_layout.addWidget(self._deselect_all_btn)
        
        self._select_btn_layout.addStretch()
        layout.addLayout(self._select_btn_layout)
        
        # 剧集列表滚动区域
        self._scroll_area = ScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setMinimumHeight(320)
        self._scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self._scroll_area.viewport().setStyleSheet("background: transparent;")
        
        # 剧集按钮容器
        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self._grid_layout = QGridLayout(self._container)
        self._grid_layout.setSpacing(8)
        
        self._scroll_area.setWidget(self._container)
        layout.addWidget(self._scroll_area)
        
        # 底部按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self._confirm_btn = PushButton("确认下载")
        self._confirm_btn.clicked.connect(self._on_confirm_download)
        self._confirm_btn.hide()
        btn_layout.addWidget(self._confirm_btn)
        
        self._close_btn = PushButton("关闭")
        self._close_btn.clicked.connect(self.close)
        btn_layout.addWidget(self._close_btn)
        layout.addLayout(btn_layout)
    
    def _create_buttons(self) -> None:
        """创建剧集按钮（延迟执行）"""
        cols = 5  # 每行5个按钮
        for i, episode in enumerate(self._episodes):
            # 创建按钮
            btn = PushButton(f"第{episode.episode_number}集")
            btn.setFixedSize(80, 36)
            btn.setToolTip(episode.title)
            btn.clicked.connect(lambda checked, ep=episode: self._on_episode_clicked(ep))
            
            # 创建复选框（下载模式用）
            checkbox = CheckBox(f"第{episode.episode_number}集")
            checkbox.setToolTip(episode.title)
            checkbox.hide()
            
            row = i // cols
            col = i % cols
            self._grid_layout.addWidget(btn, row * 2, col)
            self._grid_layout.addWidget(checkbox, row * 2 + 1, col)
            
            self._buttons.append(btn)
            self._checkboxes.append(checkbox)
    
    def _on_mode_changed(self) -> None:
        """处理模式切换"""
        self._is_download_mode = self._download_radio.isChecked()
        
        if self._is_download_mode:
            # 下载模式：显示复选框，隐藏按钮
            for btn in self._buttons:
                btn.hide()
            for cb in self._checkboxes:
                cb.show()
            self._select_all_btn.show()
            self._deselect_all_btn.show()
            self._confirm_btn.show()
        else:
            # 播放模式：显示按钮，隐藏复选框
            for btn in self._buttons:
                btn.show()
            for cb in self._checkboxes:
                cb.hide()
            self._select_all_btn.hide()
            self._deselect_all_btn.hide()
            self._confirm_btn.hide()
    
    def _select_all(self) -> None:
        """全选"""
        for cb in self._checkboxes:
            cb.setChecked(True)
    
    def _toggle_selection(self) -> None:
        """反选"""
        for cb in self._checkboxes:
            cb.setChecked(not cb.isChecked())
    
    def _on_episode_clicked(self, episode: EpisodeInfo) -> None:
        """处理剧集点击（播放模式）"""
        if not self._is_download_mode:
            logger.log_user_action("episode_click", f"drama={self._drama.name}, episode={episode.title}")
            self.episode_selected.emit(episode)
            self.close()
    
    def _on_confirm_download(self) -> None:
        """确认下载选中的剧集"""
        selected_episodes = []
        for i, cb in enumerate(self._checkboxes):
            if cb.isChecked() and i < len(self._episodes):
                selected_episodes.append(self._episodes[i])
        
        if selected_episodes:
            logger.log_user_action("download_episodes", f"drama={self._drama.name}, count={len(selected_episodes)}")
            self.episodes_download.emit(selected_episodes)
            self.close()
    
    @property
    def drama(self) -> DramaInfo:
        """获取短剧信息"""
        return self._drama
    
    @property
    def episodes(self) -> List[EpisodeInfo]:
        """获取剧集列表"""
        return self._episodes


class EpisodeListWidget(QWidget):
    """
    剧集列表控件
    
    可嵌入其他界面使用
    """
    
    episode_selected = Signal(object)  # EpisodeInfo
    
    def __init__(
        self,
        episodes: List[EpisodeInfo],
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self._episodes = episodes
        self._current_episode: Optional[int] = None
        self._buttons: List[PushButton] = []
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """初始化UI"""
        layout = QGridLayout(self)
        layout.setSpacing(8)
        
        cols = 5
        for i, episode in enumerate(self._episodes):
            btn = PushButton(f"第{episode.episode_number}集")
            btn.setFixedSize(70, 36)
            btn.setToolTip(episode.title)
            btn.clicked.connect(lambda checked, ep=episode: self._on_episode_clicked(ep))
            
            row = i // cols
            col = i % cols
            layout.addWidget(btn, row, col)
            self._buttons.append(btn)
    
    def _on_episode_clicked(self, episode: EpisodeInfo) -> None:
        """处理剧集点击"""
        self._current_episode = episode.episode_number
        self._update_button_styles()
        self.episode_selected.emit(episode)
    
    def _update_button_styles(self) -> None:
        """更新按钮样式"""
        for i, btn in enumerate(self._buttons):
            if i < len(self._episodes):
                is_current = self._episodes[i].episode_number == self._current_episode
                # 可以添加高亮样式
    
    def set_current_episode(self, episode_number: int) -> None:
        """设置当前播放的剧集"""
        self._current_episode = episode_number
        self._update_button_styles()
    
    def set_episodes(self, episodes: List[EpisodeInfo]) -> None:
        """更新剧集列表"""
        self._episodes = episodes
        # 清除旧按钮并重建
        for btn in self._buttons:
            btn.deleteLater()
        self._buttons.clear()
        self._setup_ui()
