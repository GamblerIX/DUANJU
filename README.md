# DuanjuGUI - 短剧搜索应用

一个基于 C++ 和 Qt 6 的短剧搜索与播放桌面应用程序。

## 功能特性

- 🔍 **短剧搜索** - 通过关键词搜索短剧资源
- 📂 **分类浏览** - 按分类（穿越/虐恋/甜宠等）浏览短剧
- 🎬 **视频播放** - 内置播放器，支持多种清晰度
- 🌙 **主题切换** - 支持浅色/深色/跟随系统三种主题模式
- 📝 **实时日志** - 查看应用运行日志，支持导出
- ⚙️ **可配置** - API 超时、默认清晰度等设置

## 技术栈

- **语言**: C++17
- **GUI 框架**: Qt 6.x
- **HTTP 客户端**: Qt Network
- **视频播放**: Qt Multimedia
- **构建系统**: CMake
- **测试框架**: Google Test + RapidCheck

## 构建要求

- CMake 3.20+
- Qt 6.x (Core, Gui, Widgets, Network, Multimedia)
- C++17 兼容编译器

## 构建步骤

```bash
# 配置
cmake -B build -DCMAKE_BUILD_TYPE=Release

# 编译
cmake --build build --config Release

# 运行测试
ctest --test-dir build --build-config Release
```

## 项目结构

```
├── include/           # 头文件
│   ├── api/          # API 客户端
│   ├── models/       # 数据模型
│   ├── services/     # 业务服务
│   ├── utils/        # 工具类
│   └── widgets/      # UI 组件
├── src/              # 源文件
├── tests/            # 测试文件
├── resources/        # 资源文件
└── .github/workflows/ # CI/CD 配置
```

## API 接口

基于 api.cenguigui.cn 的短剧 API：

- 搜索接口: `?name=关键词&page=1`
- 剧集列表: `?book_id=ID`
- 视频解析: `?video_id=ID&level=1080p`
- 分类接口: `?classname=分类名`
- 推荐接口: `?type=recommend`

## 许可证

MIT License
