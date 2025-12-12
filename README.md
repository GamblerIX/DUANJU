# DUANJU Debug 版本

开发调试版本，包含完整日志系统和模块化代码结构。

## 运行

```bash
pip install -r requirements.txt
python main.py
```

## 目录结构

```
DUANJU/
├── main.py              # 应用入口
├── requirements.txt     # 依赖
├── pyappify.yml         # PyAppify 打包配置
├── assets/              # 静态资源
├── docs/                # 开发文档
└── src/
    ├── core/            # 核心模型与工具
    ├── data/            # 数据访问层（API、缓存、配置）
    ├── services/        # 业务服务层
    └── ui/              # 用户界面层
```

## 开发特性

- 日志分级（DEBUG/INFO/WARNING/ERROR），保存至 logs/
- 模块化设计，便于开发测试
- 可选集成便携版 VLC 播放器

## 开发流程

1. 在此分支进行功能开发
2. 功能稳定后合并到 main 分支（代码合并为单文件）
