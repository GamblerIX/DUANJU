# DuanjuApp (沉浸式短剧播放器)

<p align="center">
  <img src="assets/icon.ico" alt="Logo" width="128" height="128">
</p>

DuanjuApp 是一个基于 Python (PySide6) 开发的现代化桌面端短剧播放器。它聚合了多个短剧源，提供沉浸式的观看体验、历史记录管理和收藏功能。

## ✨ 核心功能

*   **海量资源**: 聚合全网短剧资源，实时更新。
*   **高清播放**: 内置高性能视频播放器，支持流式播放。
*   **沉浸体验**: 现代化 Fluent UI 设计，支持深色/浅色主题自动切换。
*   **便捷管理**:
    *   📂 **收藏夹**: 一键收藏喜欢的短剧。
    *   🕒 **历史记录**: 自动记录观看进度，随时续播。
    *   🔍 **智能搜索**: 快速定位想看的内容。
*   **多源切换**: 内置多种 API 适配器（Cenguigui, Duanju Search, Uuuka），保障资源稳定性。

## 🚀 快速开始

### 方式一：下载安装包 (推荐)

前往 [Releases](../../releases) 页面下载最新版本：

*   **DuanjuApp-Setup.exe**: (推荐) PyAppify 安装包，体积小，支持自动增量更新。
*   **DuanjuApp-PyInstaller.zip**: 绿色免安装版，解压即用。
*   **DuanjuApp-Nuitka.zip**: 极致性能编译版。

### 方式二：源码运行

确保您的系统已安装 Python 3.12+。

1.  **克隆仓库**
    ```bash
    git clone https://github.com/GamblerIX/DUANJU.git
    cd DUANJU
    ```

2.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    ```

3.  **运行**
    ```bash
    python main.py
    ```

## 🛠️ 开发构建

本项目支持多种打包方式，均已集成至 GitHub Actions。

| 方式 | 描述 | 触发方式 |
| :--- | :--- | :--- |
| **PyAppify** | 生成带有在线更新功能的轻量级安装器 | GitHub Actions / Release |
| **PyInstaller** | 标准单文件夹打包 | GitHub Actions |
| **Nuitka** | 编译为原生机器码，性能更优 | GitHub Actions |

## 📄 许可证

本项目仅供学习交流使用。

---
*Built with ❤️ using PySide6 & Fluent Widgets*
