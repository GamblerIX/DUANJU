# DUANJU Debug 版本 - 开发者指南

## 概述

Debug 版本用于开发和调试，包含完整的日志系统和调试功能。

## 环境配置

```bash
# 安装依赖
pip install -r requirements.txt

# 运行应用
python main.py
```

## 开发特性

### 日志系统
- 日志分级：DEBUG / INFO / WARNING / ERROR
- 日志文件保存在 `logs/` 目录
- 应用退出时自动清理缓存，仅保留日志

### 代码规范
- 保留完整代码注释和文档字符串
- 包含开发调试用辅助代码
- 模块化设计，便于开发测试

### VLC 支持
- 可选集成便携版 VLC 播放器
- 提供浏览器播放作为备选方案
- 运行时动态检测可用播放器

## 目录结构

```
Debug/
├── main.py              # 应用入口
├── requirements.txt     # Python 依赖
├── vlc/                 # 便携版 VLC（可选）
├── assets/              # 静态资源
└── src/
    ├── core/            # 核心业务逻辑
    ├── data/            # 数据模型与持久层
    ├── services/        # 业务服务层
    └── ui/              # 用户界面层
```

## 开发流程

1. 在此目录进行功能开发
2. 添加详细的代码注释
3. 包含必要的日志记录
4. 功能稳定后同步到 Release 版本

## 打包测试

使用 PyInstaller 快速打包：

```bash
# 手动触发 GitHub Actions
# 选择 PyInstaller.yml -> build_type: Debug
```

## 注意事项

- 此版本仅用于开发调试
- 不要直接发布给最终用户
- 重要功能变更需同步到 Release 版本
