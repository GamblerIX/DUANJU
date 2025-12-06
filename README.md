# DUANJU 短剧播放器

基于 PyQt6 和 QFluentWidgets 的桌面短剧播放应用。

## 功能特性

- 🔍 短剧搜索与浏览
- 📂 分类筛选与推荐
- ▶️ VLC/浏览器双播放模式
- ⬇️ 视频下载与离线观看
- ⭐ 收藏夹管理
- 📜 观看历史记录
- 🎨 明暗主题切换

## 项目结构

```
DUANJU/
├── .github/        # CI/CD 配置
├── Debug/          # 开发版本（含日志、调试功能）
├── Release/        # 生产版本（优化、精简）
├── README.md       # 说明文档
└── LICENSE         # 开源许可证
```

## 快速开始

### 开发版本

```bash
cd Debug
pip install -r requirements.txt
python main.py
```

### 生产版本

```bash
cd Release
pip install -r requirements.txt
python main.py
```

## 依赖要求

- Python 3.10+
- PyQt6
- QFluentWidgets
- aiohttp
- VLC（可选）

## 许可证

GNU General Public License v3.0
