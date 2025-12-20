"""设置对话框实现"""
from typing import Optional, List
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDialog
)
from qfluentwidgets import (
    SubtitleLabel, SettingCardGroup,
    SettingCard, ComboBox, Slider,
    FluentIcon, BodyLabel, PrimaryPushButton, PushButton,
    isDarkTheme, qconfig
)
from enum import Enum

from ...core.models import ThemeMode
from ...utils.log_manager import get_logger
from ...data.config_manager import ConfigManager, QualityOption
from ...data.providers.provider_registry import get_registry
from ...data.providers.provider_init import set_current_provider

logger = get_logger()


class ThemeModeOption(Enum):
    """主题模式选项（用于设置卡片）"""
    LIGHT = "浅色"
    DARK = "深色"
    AUTO = "跟随系统"


class CustomSettingCard(SettingCard):
    """自定义设置卡片，支持自定义控件"""
    
    def __init__(self, icon, title, content, widget, parent=None):
        super().__init__(icon, title, content, parent)
        self.hBoxLayout.addWidget(widget, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)


class SettingsDialog(QDialog):
    """
    设置对话框
    
    使用 QDialog 替代 MessageBoxBase 以获得更好的尺寸控制
    """
    
    # 信号
    theme_changed = Signal(object)  # ThemeMode
    timeout_changed = Signal(int)
    quality_changed = Signal(str)
    provider_changed = Signal(str)  # provider_id
    settings_saved = Signal()
    
    def __init__(
        self,
        config_manager: ConfigManager,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self._config = config_manager
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """初始化UI"""
        self.setWindowTitle("设置")
        self.setFixedSize(600, 580)
        self.setModal(True)
        
        # 设置对话框背景跟随主题
        self._update_dialog_theme()
        # 监听主题变化
        qconfig.themeChanged.connect(self._update_dialog_theme)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # 外观设置组 - 设置透明背景让其跟随对话框主题
        self._appearance_group = SettingCardGroup("外观", self)
        self._appearance_group.setStyleSheet("SettingCardGroup { background: transparent; }")
        
        # 主题设置 - 使用 ComboBox
        self._theme_combo = ComboBox()
        self._theme_combo.addItems(["浅色", "深色", "跟随系统"])
        theme_index = {
            ThemeMode.LIGHT: 0,
            ThemeMode.DARK: 1,
            ThemeMode.AUTO: 2
        }.get(self._config.theme_mode, 2)
        self._theme_combo.setCurrentIndex(theme_index)
        self._theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        
        self._theme_card = CustomSettingCard(
            FluentIcon.BRUSH,
            "主题模式",
            "选择应用的主题外观",
            self._theme_combo,
            self._appearance_group
        )
        self._appearance_group.addSettingCard(self._theme_card)
        
        layout.addWidget(self._appearance_group)
        
        # 数据源设置组
        self._provider_group = SettingCardGroup("数据源", self)
        self._provider_group.setStyleSheet("SettingCardGroup { background: transparent; }")
        
        # 数据源选择
        self._provider_combo = ComboBox()
        self._provider_ids: List[str] = []
        self._load_providers()
        self._provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        
        self._provider_card = CustomSettingCard(
            FluentIcon.CLOUD,
            "数据源",
            "选择短剧数据来源（切换后需重启生效）",
            self._provider_combo,
            self._provider_group
        )
        self._provider_group.addSettingCard(self._provider_card)
        
        layout.addWidget(self._provider_group)
        
        # 播放设置组
        self._playback_group = SettingCardGroup("播放", self)
        self._playback_group.setStyleSheet("SettingCardGroup { background: transparent; }")
        
        # 默认清晰度 - 使用 ComboBox (API支持: 360p/480p/720p/1080p/2160p)
        self._quality_combo = ComboBox()
        self._quality_combo.addItems(["360p", "480p", "720p", "1080p", "2160p"])
        quality_index = {"360p": 0, "480p": 1, "720p": 2, "1080p": 3, "2160p": 4}.get(
            self._config.default_quality, 3  # 默认 1080p
        )
        self._quality_combo.setCurrentIndex(quality_index)
        self._quality_combo.currentTextChanged.connect(self._on_quality_changed)
        
        self._quality_card = CustomSettingCard(
            FluentIcon.VIDEO,
            "默认清晰度",
            "选择视频播放的默认清晰度 (2160p不是所有视频都支持)",
            self._quality_combo,
            self._playback_group
        )
        self._playback_group.addSettingCard(self._quality_card)
        
        layout.addWidget(self._playback_group)
        
        # 网络设置组
        self._network_group = SettingCardGroup("网络", self)
        self._network_group.setStyleSheet("SettingCardGroup { background: transparent; }")
        
        # API 超时设置 - 使用 Slider
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
        
        self._timeout_card = CustomSettingCard(
            FluentIcon.SPEED_HIGH,
            "API 超时时间",
            "设置网络请求的超时时间",
            timeout_widget,
            self._network_group
        )
        self._network_group.addSettingCard(self._timeout_card)
        
        layout.addWidget(self._network_group)
        
        layout.addStretch()
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self._cancel_btn = PushButton("取消")
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)
        
        self._save_btn = PrimaryPushButton("保存")
        self._save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self._save_btn)
        
        layout.addLayout(btn_layout)
    
    def _update_dialog_theme(self) -> None:
        """更新对话框主题"""
        if isDarkTheme():
            self.setStyleSheet("""
                QDialog { background-color: #202020; }
                QLabel { color: #ffffff; }
            """)
        else:
            self.setStyleSheet("""
                QDialog { background-color: #f9f9f9; }
                QLabel { color: #000000; }
            """)
    
    def _load_providers(self) -> None:
        """加载可用的数据源列表"""
        registry = get_registry()
        providers = registry.list_providers()
        
        self._provider_ids.clear()
        self._provider_combo.clear()
        
        current_provider = self._config.config.current_provider
        current_index = 0
        
        for i, info in enumerate(providers):
            self._provider_ids.append(info.id)
            self._provider_combo.addItem(f"{info.name}")
            if info.id == current_provider:
                current_index = i
        
        if self._provider_ids:
            self._provider_combo.setCurrentIndex(current_index)
    
    def _on_provider_changed(self, index: int) -> None:
        """处理数据源改变"""
        if 0 <= index < len(self._provider_ids):
            provider_id = self._provider_ids[index]
            self.provider_changed.emit(provider_id)
    
    def _on_theme_changed(self, index: int) -> None:
        """处理主题改变"""
        theme_map = {0: ThemeMode.LIGHT, 1: ThemeMode.DARK, 2: ThemeMode.AUTO}
        theme = theme_map.get(index, ThemeMode.AUTO)
        self.theme_changed.emit(theme)
    
    def _on_quality_changed(self, text: str) -> None:
        """处理清晰度改变"""
        self.quality_changed.emit(text)
    
    def _on_timeout_changed(self, value: int) -> None:
        """处理超时改变"""
        self._timeout_label.setText(f"{value}秒")
        self.timeout_changed.emit(value * 1000)  # 转换为毫秒
    
    def _on_save(self) -> None:
        """保存设置"""
        # 保存主题
        theme_index = self._theme_combo.currentIndex()
        theme_map = {0: ThemeMode.LIGHT, 1: ThemeMode.DARK, 2: ThemeMode.AUTO}
        new_theme = theme_map.get(theme_index, ThemeMode.AUTO)
        logger.log_config_change("theme_mode", self._config.theme_mode.value, new_theme.value)
        self._config.theme_mode = new_theme
        
        # 保存数据源
        provider_index = self._provider_combo.currentIndex()
        if 0 <= provider_index < len(self._provider_ids):
            new_provider = self._provider_ids[provider_index]
            old_provider = self._config.config.current_provider
            if new_provider != old_provider:
                logger.log_config_change("current_provider", old_provider, new_provider)
                self._config.set("current_provider", new_provider)
                # 切换当前活动的数据提供者
                set_current_provider(new_provider)
                logger.info(f"Provider switched to: {new_provider}")
        
        # 保存清晰度
        new_quality = self._quality_combo.currentText()
        logger.log_config_change("default_quality", self._config.default_quality, new_quality)
        self._config.default_quality = new_quality
        
        # 保存超时
        new_timeout = self._timeout_slider.value() * 1000
        logger.log_config_change("api_timeout", self._config.api_timeout, new_timeout)
        self._config.api_timeout = new_timeout
        
        self._config.save()
        logger.log_user_action("settings_save")
        self.settings_saved.emit()
        self.accept()
