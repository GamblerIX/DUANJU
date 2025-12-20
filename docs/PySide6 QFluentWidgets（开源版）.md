# PySide6 QFluentWidgets (开源版) 完整开发指南

## 1. 项目综述与核心价值

QFluentWidgets 是基于 PySide6 的 Fluent Design 风格组件库，旨在弥补 Qt 原生 `QStyle` 在现代化设计上的不足。本指南针对 **开源版 (GPLv3)** 进行编写，涵盖环境搭建、核心架构、全组件详解及工程化部署。

### 核心特性

- **原生体验**：复刻 WinUI 3 设计语言（光感、动效、缩放）。
- **高 DPI 适配**：支持 2K/4K 屏幕下的矢量渲染与自动缩放。
- **主题系统**：内置亮色/暗色模式，支持跟随系统与动态切换。
- **开箱即用**：封装了 100+ 现成组件，无需手写 QSS。

### 开源版 vs Pro 版边界

- **开源版包含**：完整的基础组件（按钮、输入、选择）、导航系统（FluentWindow）、基础视图（List/Table/Tree）、弹窗反馈。
- **开源版不包含**：数据可视化图表（Charts）、高级时间轴视图、复杂的 Mica/亚克力混合材质特效（开源版仅提供基础亚克力）。

## 2. 环境搭建与安装

### 2.1 依赖环境

- Python 3.6+
- PySide6 (Qt 6.x)

### 2.2 安装策略

为避免包名冲突，请严格执行以下命令安装 PySide6 专用版本。

**基础版安装：**

```
pip install PySide6-Fluent-Widgets -i [https://pypi.org/simple/](https://pypi.org/simple/)
```

**完整版安装（推荐，包含亚克力特效依赖）：**

```
pip install "PySide6-Fluent-Widgets[full]" -i [https://pypi.org/simple/](https://pypi.org/simple/)
```

> **警告**：严禁在同一环境中混装 `PyQt-Fluent-Widgets` 和 `PySide6-Fluent-Widgets`，否则会导致严重的命名空间冲突。

## 3. 核心架构与初始化

### 3.1 高 DPI 与应用启动

在创建 `QApplication` 之前，必须配置高 DPI 策略以保证界面清晰度。

```
import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from qfluentwidgets import FluentWindow

if __name__ == '__main__':
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    w = FluentWindow()
    w.show()
    app.exec()
```

### 3.2 主题管理 (Theme)

支持全局切换亮色与暗色主题。

```
from qfluentwidgets import setTheme, Theme, setThemeColor

setTheme(Theme.DARK)
setTheme(Theme.LIGHT)
setTheme(Theme.AUTO)

setThemeColor('#0078d4')
```

### 3.3 图标系统 (FluentIcon)

使用枚举类 `FluentIcon` (FIF) 调用矢量图标，自动适配当前主题颜色。

```
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import IconWidget

icon = IconWidget(FIF.GITHUB)
icon.setFixedSize(24, 24)
```

## 4. 窗口与导航系统 (Window & Navigation)

`FluentWindow` 是构建应用程序的骨架，集成了侧边栏导航和页面堆叠管理。

### 4.1 构建主窗口

```
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout
from qfluentwidgets import FluentWindow, NavigationItemPosition, FluentIcon as FIF

class HomeInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("homeInterface")
        layout = QHBoxLayout(self)
        layout.addWidget(QLabel("Home Interface", self))

class SettingInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("settingInterface")
        layout = QHBoxLayout(self)
        layout.addWidget(QLabel("Settings Interface", self))

class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.homeInterface = HomeInterface(self)
        self.settingInterface = SettingInterface(self)
        
        self.initNavigation()
        self.setWindowTitle("PySide6 Fluent App")
        self.resize(900, 700)

    def initNavigation(self):
        self.addSubInterface(
            interface=self.homeInterface,
            icon=FIF.HOME,
            text='Home',
            position=NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            interface=self.settingInterface,
            icon=FIF.SETTING,
            text='Settings',
            position=NavigationItemPosition.BOTTOM
        )
```

### 4.2 路由跳转

在应用内部跳转页面并同步侧边栏状态。

```
self.switchTo(self.settingInterface)
```

## 5. 基础交互组件 (Basic Input)

### 5.1 按钮 (Buttons)

包含标准按钮、主色按钮、超链接按钮和开关按钮。

```
from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import PushButton, PrimaryPushButton, HyperlinkButton, SwitchButton, FluentIcon

class ButtonDemo(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        
        self.btn1 = PushButton('Standard Button')
        self.btn1.setIcon(FluentIcon.ACCEPT)
        
        self.btn2 = PrimaryPushButton('Primary Button')
        
        self.btn3 = HyperlinkButton('[https://qfluentwidgets.com](https://qfluentwidgets.com)', 'Link Button')
        
        self.switchBtn = SwitchButton()
        self.switchBtn.setOnText('On')
        self.switchBtn.setOffText('Off')
        
        self.layout.addWidget(self.btn1)
        self.layout.addWidget(self.btn2)
        self.layout.addWidget(self.btn3)
        self.layout.addWidget(self.switchBtn)
```

### 5.2 文本输入 (Text Input)

支持圆角、动效及搜索模式的输入框。

```
from qfluentwidgets import LineEdit, SearchLineEdit, PasswordLineEdit

line_edit = LineEdit()
line_edit.setPlaceholderText('Enter text')
line_edit.setClearButtonEnabled(True)

search_edit = SearchLineEdit()
search_edit.searchSignal.connect(print)

password_edit = PasswordLineEdit()
```

### 5.3 选择控件 (Selection)

复选框、下拉框与滑动条。

```
from PySide6.QtCore import Qt
from qfluentwidgets import CheckBox, ComboBox, Slider

checkbox = CheckBox('Option 1')
checkbox.setChecked(True)

combo = ComboBox()
combo.addItems(['Item 1', 'Item 2', 'Item 3'])
combo.setCurrentIndex(0)

slider = Slider(Qt.Horizontal)
slider.setRange(0, 100)
slider.setValue(30)
```

### 5.4 日期与时间 (Pickers)

```
from qfluentwidgets import DatePicker, TimePicker, CalendarPicker

date_picker = DatePicker()
time_picker = TimePicker()
calendar = CalendarPicker()
```

## 6. 反馈与状态 (Feedback & Status)

### 6.1 消息条 (InfoBar)

非模态消息提示，推荐替代原生 MessageBox。

```
from qfluentwidgets import InfoBar, InfoBarPosition

InfoBar.success(
    title='Success',
    content='Operation completed successfully.',
    orient=Qt.Horizontal,
    isClosable=True,
    position=InfoBarPosition.TOP_RIGHT,
    duration=2000,
    parent=window
)
```

### 6.2 对话框 (Dialog/MessageBox)

带有背景遮罩的模态对话框。

```
from qfluentwidgets import MessageBox

msg_box = MessageBox(
    'Confirmation',
    'Are you sure you want to delete this file?',
    parent=window
)
if msg_box.exec():
    print('Confirmed')
else:
    print('Canceled')
```

### 6.3 进度指示 (Progress)

```
from qfluentwidgets import ProgressBar, ProgressRing

bar = ProgressBar()
bar.setValue(50)

ring = ProgressRing()
ring.setValue(75)
ring.setTextVisible(True)
```

## 7. 配置与设置界面 (Configuration)

利用 `QConfig` 和 `SettingCard` 快速构建标准的设置页面。

### 7.1 定义配置类

```
from qfluentwidgets import QConfig, ConfigItem

class Config(QConfig):
    enableAcrylic = ConfigItem('General', 'EnableAcrylic', False)
    themeMode = ConfigItem('General', 'ThemeMode', 'Auto')

cfg = Config()
```

### 7.2 构建设置页面

```
from qfluentwidgets import SettingCardGroup, SwitchSettingCard, ScrollArea, ExpandLayout
from PySide6.QtWidgets import QWidget

class SettingInterface(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.view = QWidget(self)
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        
        self.layout = ExpandLayout(self.view)
        
        self.generalGroup = SettingCardGroup('General Settings', self.view)
        
        self.acrylicCard = SwitchSettingCard(
            FIF.BRUSH,
            'Acrylic Effect',
            'Enable acrylic effect in window',
            configItem=cfg.enableAcrylic,
            parent=self.generalGroup
        )
        
        self.generalGroup.addSettingCard(self.acrylicCard)
        self.layout.addWidget(self.generalGroup)
```

## 8. 工程化打包 (PyInstaller)

PySide6 QFluentWidgets 包含大量非 Python 资源（QSS、SVG），打包时需特殊处理。

### 8.1 命令行打包

使用以下参数确保资源被正确收集：

```
pyinstaller --noconfirm --onedir --windowed --name "FluentApp" \
    --hidden-import qfluentwidgets \
    --collect-all qfluentwidgets \
    main.py
```

### 8.2 关键参数解析

- `--collect-all qfluentwidgets`：强制收集库中的所有资源文件（解决图标丢失、样式失效问题）。
- `--hidden-import qfluentwidgets`：防止动态导入机制导致的 `ModuleNotFoundError`。

### 8.3 常见问题排查

1. **SystemError**: 检查是否混装了 PyQt5 版本库。
2. **图标黑块**: 确认使用了 `--collect-all` 参数。
3. **特效缺失**: 若使用了 `[full]` 版本特性，需确保目标机器安装了 VC++ 运行库。