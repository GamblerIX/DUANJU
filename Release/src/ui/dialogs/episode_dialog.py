from typing import Optional, List
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtWidgets import QVBoxLayout, QWidget, QGridLayout, QHBoxLayout
from qfluentwidgets import (SubtitleLabel, BodyLabel, PushButton, ScrollArea, 
                            CheckBox, RadioButton, MessageBoxBase)
from ...core.models import EpisodeInfo, DramaInfo


class EpisodeDialog(MessageBoxBase):
    episode_selected = pyqtSignal(object)
    episodes_download = pyqtSignal(list)
    
    def __init__(self, drama: DramaInfo, episodes: List[EpisodeInfo], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._drama = drama
        self._episodes = episodes
        self._buttons: List[PushButton] = []
        self._checkboxes: List[CheckBox] = []
        self._is_download_mode = False
        self._setup_ui()
        QTimer.singleShot(50, self._create_buttons)
    
    def _setup_ui(self) -> None:
        self.widget.setFixedSize(600, 500)
        self.yesButton.hide()
        self.cancelButton.hide()
        self.buttonGroup.hide()
        layout = self.viewLayout
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(10)
        self.titleLabel = SubtitleLabel(self._drama.name)
        layout.addWidget(self.titleLabel)
        self.countLabel = BodyLabel(f"共 {len(self._episodes)} 集")
        layout.addWidget(self.countLabel)
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
        self._scroll_area = ScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setMinimumHeight(320)
        self._scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self._scroll_area.viewport().setStyleSheet("background: transparent;")
        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self._grid_layout = QGridLayout(self._container)
        self._grid_layout.setSpacing(8)
        self._scroll_area.setWidget(self._container)
        layout.addWidget(self._scroll_area)
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
        cols = 5
        for i, episode in enumerate(self._episodes):
            btn = PushButton(f"第{episode.episode_number}集")
            btn.setFixedSize(80, 36)
            btn.setToolTip(episode.title)
            btn.clicked.connect(lambda checked, ep=episode: self._on_episode_clicked(ep))
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
        self._is_download_mode = self._download_radio.isChecked()
        if self._is_download_mode:
            for btn in self._buttons:
                btn.hide()
            for cb in self._checkboxes:
                cb.show()
            self._select_all_btn.show()
            self._deselect_all_btn.show()
            self._confirm_btn.show()
        else:
            for btn in self._buttons:
                btn.show()
            for cb in self._checkboxes:
                cb.hide()
            self._select_all_btn.hide()
            self._deselect_all_btn.hide()
            self._confirm_btn.hide()
    
    def _select_all(self) -> None:
        for cb in self._checkboxes:
            cb.setChecked(True)
    
    def _toggle_selection(self) -> None:
        for cb in self._checkboxes:
            cb.setChecked(not cb.isChecked())
    
    def _on_episode_clicked(self, episode: EpisodeInfo) -> None:
        if not self._is_download_mode:
            self.episode_selected.emit(episode)
            self.close()
    
    def _on_confirm_download(self) -> None:
        selected_episodes = []
        for i, cb in enumerate(self._checkboxes):
            if cb.isChecked() and i < len(self._episodes):
                selected_episodes.append(self._episodes[i])
        if selected_episodes:
            self.episodes_download.emit(selected_episodes)
            self.close()
    
    @property
    def drama(self) -> DramaInfo:
        return self._drama
    
    @property
    def episodes(self) -> List[EpisodeInfo]:
        return self._episodes


class EpisodeListWidget(QWidget):
    episode_selected = pyqtSignal(object)
    
    def __init__(self, episodes: List[EpisodeInfo], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._episodes = episodes
        self._current_episode: Optional[int] = None
        self._buttons: List[PushButton] = []
        self._setup_ui()
    
    def _setup_ui(self) -> None:
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
        self._current_episode = episode.episode_number
        self._update_button_styles()
        self.episode_selected.emit(episode)
    
    def _update_button_styles(self) -> None:
        pass
    
    def set_current_episode(self, episode_number: int) -> None:
        self._current_episode = episode_number
        self._update_button_styles()
    
    def set_episodes(self, episodes: List[EpisodeInfo]) -> None:
        self._episodes = episodes
        for btn in self._buttons:
            btn.deleteLater()
        self._buttons.clear()
        self._setup_ui()
