# DUANJU Release 版本 - 用户使用手册

## 概述

Release 版本为生产环境优化，提供最佳用户体验。

## 快速开始

### 方式一：直接运行

从 [Releases](../../releases) 下载最新版本，双击运行即可。

### 方式二：源码运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行应用
python main.py
```

## 功能特性

- 🔍 短剧搜索与浏览
- 📂 分类筛选与推荐
- ▶️ VLC / 浏览器双播放模式
- ⬇️ 视频下载与离线观看
- ⭐ 收藏夹管理
- 📜 观看历史记录
- 🎨 明暗主题切换

## 系统要求

- Windows 10/11
- Python 3.10+（源码运行）

## 依赖说明

| 依赖 | 版本 | 说明 |
|------|------|------|
| PyQt6 | ≥6.4.0 | GUI 框架 |
| PyQt6-Fluent-Widgets | ≥1.5.0 | Fluent 风格组件 |
| aiohttp | ≥3.9.0 | 异步 HTTP 客户端 |
| pydantic | ≥2.0.0 | 数据验证 |

## 目录结构

```
Release/
├── main.py              # 应用入口
├── requirements.txt     # Python 依赖
├── vlc/                 # 便携版 VLC（默认包含）
├── assets/              # 静态资源
└── src/
    ├── core/            # 核心业务逻辑
    ├── data/            # 数据层
    ├── services/        # 服务层
    └── ui/              # UI 层
```

## 常见问题

### Q: 视频无法播放？
A: 确保 VLC 目录存在，或使用浏览器播放模式。

### Q: 如何清理缓存？
A: 应用退出时会询问是否清理缓存，选择"是"即可。

### Q: 如何切换主题？
A: 在设置中选择明/暗主题。

## 更新日志

查看 [Releases](../../releases) 获取版本更新信息。

## 许可证

GNU General Public License v3.0
