from typing import Optional
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QDialog
from qfluentwidgets import (SubtitleLabel, SettingCardGroup, SettingCard, ComboBox, Slider,
                            FluentIcon, BodyLabel, PrimaryPushButton, PushButton, isDarkTheme, qconfig)
from ...core.models import ThemeMode
from ...data.config.config_manager import ConfigManager


class CustomSettingCard(SettingCard):
    def __init__(self, icon, title, content, widget, parent=None):
        super().__init__(icon, title, content, parent)
        self.hBoxLayout.addWidget(widget, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)


class SettingsDialog(QDialog):
    theme_changed = pyqtSignal(object)
    timeout_changed = pyqtSignal(int)
    quality_changed = pyqtSignal(str)
    settings_saved = pyqtSignal()
    
    def __init__(self, config_manager: ConfigManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._config = config_manager
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        self.setWindowTitle("设置")
        self.setFixedSize(600, 500)
        self.setModal(True)
        
        def update_theme():
            if isDarkTheme():
                self.setStyleSheet("QDialog { background-color: #202020; }")
            else:
                self.setStyleSheet("QDialog { background-color: #f9f9f9; }")
        update_theme()
        qconfig.themeChanged.connect(update_theme)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        self._appearance_group = SettingCardGroup("外观", self)
        self._appearance_group.setStyleSheet("SettingCardGroup { background: transparent; }")
        self._theme_combo = ComboBox()
        self._theme_combo.addItems(["浅色", "深色", "跟随系统"])
        theme_index = {ThemeMode.LIGHT: 0, ThemeMode.DARK: 1, ThemeMode.AUTO: 2}.get(self._config.theme_mode, 2)
        self._theme_combo.setCurrentIndex(theme_index)
        self._theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        self._theme_card = CustomSettingCard(FluentIcon.BRUSH, "主题模式", "选择应用的主题外观",
                                            self._theme_combo, self._appearance_group)
        self._appearance_group.addSettingCard(self._theme_card)
        layout.addWidget(self._appearance_group)
        self._playback_group = SettingCardGroup("播放", self)
        self._playback_group.setStyleSheet("SettingCardGroup { background: transparent; }")
        self._quality_combo = ComboBox()
        self._quality_combo.addItems(["360p", "480p", "720p", "1080p", "2160p"])
        quality_index = {"360p": 0, "480p": 1, "720p": 2, "1080p": 3, "2160p": 4}.get(self._config.default_quality, 3)
        self._quality_combo.setCurrentIndex(quality_index)
        self._quality_combo.currentTextChanged.connect(self._on_quality_changed)
        self._quality_card = CustomSettingCard(FluentIcon.VIDEO, "默认清晰度", 
                                              "选择视频播放的默认清晰度 (2160p不是所有视频都支持)",
                                              self._quality_combo, self._playback_group)
        self._playback_group.addSettingCard(self._quality_card)
        layout.addWidget(self._playback_group)
        self._network_group = SettingCardGroup("网络", self)
        self._network_group.setStyleSheet("SettingCardGroup { background: transparent; }")
        timeout_widget = QWidget()
        timeout_layout = QHBoxLayout(timeout_widget)
        timeout_layout.setContentsMargins(0, 0, 0, 0)
        self._timeout_slider = Slider(Qt.Orientation.Horizontal)
        self._timeout_slider.setRange(1, 60)
        self._timeout_slider.setValue(self._config.api_timeout // 1000)
        self._timeout_slider.setFixedWidth(200)
        self._timeout_slider.valueChanged.connect(self._on_timeout_changed)
        self._timeout_label = BodyLabel(f"{self._config.api_timeout // 1000}秒")
        self._timeout_label.setFixedWidth(40)
        timeout_layout.addWidget(self._timeout_slider)
        timeout_layout.addWidget(self._timeout_label)
        self._timeout_card = CustomSettingCard(FluentIcon.SPEED_HIGH, "API 超时时间", "设置网络请求的超时时间",
                                              timeout_widget, self._network_group)
        self._network_group.addSettingCard(self._timeout_card)
        layout.addWidget(self._network_group)
        layout.addStretch()
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self._cancel_btn = PushButton("取消")
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)
        self._save_btn = PrimaryPushButton("保存")
        self._save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self._save_btn)
        layout.addLayout(btn_layout)
    
    def _on_theme_changed(self, index: int) -> None:
        theme_map = {0: ThemeMode.LIGHT, 1: ThemeMode.DARK, 2: ThemeMode.AUTO}
        theme = theme_map.get(index, ThemeMode.AUTO)
        self.theme_changed.emit(theme)
    
    def _on_quality_changed(self, text: str) -> None:
        self.quality_changed.emit(text)
    
    def _on_timeout_changed(self, value: int) -> None:
        self._timeout_label.setText(f"{value}秒")
        self.timeout_changed.emit(value * 1000)
    
    def _on_save(self) -> None:
        theme_index = self._theme_combo.currentIndex()
        theme_map = {0: ThemeMode.LIGHT, 1: ThemeMode.DARK, 2: ThemeMode.AUTO}
        new_theme = theme_map.get(theme_index, ThemeMode.AUTO)
        self._config.theme_mode = new_theme
        new_quality = self._quality_combo.currentText()
        self._config.default_quality = new_quality
        new_timeout = self._timeout_slider.value() * 1000
        self._config.api_timeout = new_timeout
        self._config.save()
        self.settings_saved.emit()
