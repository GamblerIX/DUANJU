# DUANJU Release 版本

生产环境版本，代码合并为单文件，优化性能。

## 快速开始

### 方式一：直接运行

从 [Releases](../../releases) 下载最新版本，双击运行。

### 方式二：源码运行

```bash
pip install -r requirements.txt
python main.py
```

## 功能

- 🔍 短剧搜索与浏览
- 📂 分类筛选与推荐
- ▶️ VLC / 浏览器双播放模式
- ⬇️ 视频下载
- ⭐ 收藏夹管理
- 📜 观看历史记录
- 🎨 明暗主题切换

## 系统要求

- Windows 10/11
- Python 3.10+（源码运行）

## 目录结构

```
Release/
├── main.py              # 应用入口（单文件，含所有模块）
├── requirements.txt     # 依赖
└── assets/              # 静态资源
```

## 依赖

| 依赖 | 版本 | 说明 |
|------|------|------|
| PySide6 | ≥6.4.0 | GUI 框架 |
| PySide6-Fluent-Widgets | ≥1.5.0 | Fluent 风格组件 |
| aiohttp | ≥3.9.0 | 异步 HTTP 客户端 |
| pydantic | ≥2.0.0 | 数据验证 |

## 许可证

GNU General Public License v3.0
