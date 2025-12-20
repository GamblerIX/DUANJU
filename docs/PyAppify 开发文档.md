# PyAppify 开发文档

## 1. 项目概述

**PyAppify** 是一个现代化的 Python 打包和分发工具，基于 **Rust (Tauri)** 和 **React** 构建。它打破了传统打包工具（如 PyInstaller）将解释器和源码打包成大文件的模式，采用“轻量级启动器 + 动态环境构建”的策略。

### 核心设计理念

- **分离式架构**: 启动器（约 3MB）与 Python 环境分离，首次运行时按需下载。
- **Git 驱动更新**: 利用 Git 的增量更新特性，仅拉取变动代码，实现秒级更新。
- **环境隔离**: 每个应用或 Profile 可拥有独立的依赖环境，互不干扰。
- **原生体验**: 使用系统级 WebView (WebView2) 渲染 UI，通过 NSIS 生成标准的 Windows 安装包。

## 2. 技术栈架构

### 前端 (Frontend)

- **框架**: React 18, TypeScript。
- **构建工具**: Vite 6。
- **UI 组件库**: Material UI (MUI) v7，使用 `@emotion/styled` 进行样式定制。
- **状态管理**: React Hooks (`useState`, `useEffect`, `useRef`)。
- **国际化**: `i18next` + `react-i18next`，支持浏览器语言自动检测。
- **通信机制**:
  - **Invoke**: 主动调用 Rust 后端命令。
  - **Event**: 监听后端推送的日志流和状态变更。

### 后端 (Backend / Core)

- **框架**: Rust (Tauri 2.0)。
- **异步运行时**: `tokio` (用于并发下载、Git 操作、进程管理)。
- **Git 操作**: `git2` (libgit2 的 Rust 绑定)，提供高性能的 Git 仓库管理。
- **HTTP 客户端**: `reqwest` (支持 HTTPS, 代理, 流式下载)。
- **压缩解压**: `tar`, `zip`, `flate2` (处理 Python 环境包)。
- **系统交互**:
  - `tauri-plugin-opener`: 打开外部链接/目录。
  - `tauri-plugin-single-instance`: 保证单例运行，处理重复启动参数。
- **日志系统**: `tracing` + `tracing-appender` + `tracing-subscriber` (实现结构化日志和文件轮转)。

## 3. 项目目录结构深度解析

```
pyappify/
├── .github/workflows/build.yml # GitHub Actions 自动构建流程
├── src/                        # 前端源代码
│   ├── App.tsx                 # 主入口，处理全局路由状态和应用列表渲染
│   ├── ConsolePage.tsx         # 通用控制台组件，用于显示安装、更新、运行时的实时日志
│   ├── SettingsPage.tsx        # 设置页面，管理全局 Pip 源、缓存路径、主题等
│   ├── UpdateLogPage.tsx       # 版本切换页面，计算版本差异
│   ├── i18n.ts                 # 前端国际化配置 (资源文件内嵌)
│   └── utils.ts                # 工具函数 (Command 包装器, 错误处理)
├── src-tauri/                  # Rust 后端源代码
│   ├── assets/pyappify.yml     # 默认的应用配置文件模板
│   ├── locales/                # 后端多语言文件 (YAML 格式)
│   ├── nsis/installer.nsi      # NSIS 安装脚本，定义安装向导界面和逻辑
│   ├── src/
│   │   ├── app_service.rs      # [核心] 应用逻辑：安装、启动、停止、删除、版本控制
│   │   ├── config_manager.rs   # [核心] 全局配置管理：读写 config.json，管理 Pip 源
│   │   ├── execute_python.rs   # [核心] 进程管理：环境注入、隐藏窗口、输出流捕获
│   │   ├── python_env.rs       # [核心] 环境构建：版本判定、下载、解压、瘦身
│   │   ├── git.rs              # Git 操作封装：Clone, Fetch, Checkout, Tags 解析
│   │   ├── lib.rs              # Tauri 入口：插件注册、菜单系统、CLI 参数解析
│   │   ├── main.rs             # Rust 程序入口
│   │   └── utils/              # 通用工具模块
│   │       ├── defender.rs     # Windows Defender 排除项添加逻辑
│   │       ├── logger.rs       # 日志配置，设置文件轮转
│   │       ├── path.rs         # 路径帮助函数 (获取 AppData, Python 目录等)
│   │       └── window.rs       # 窗口管理 (系统托盘, 窗口事件)
│   ├── Cargo.toml              # Rust 依赖定义
│   └── tauri.conf.json         # Tauri 配置文件 (权限, 图标, 插件配置)
└── pyappify.yml                # 用户项目配置示例
```

## 4. 详细功能设计与实现

### 4.1 全局配置管理系统 (`config_manager.rs` & `SettingsPage.tsx`)

除了项目级别的 `pyappify.yml`，PyAppify 还维护一个用户级别的全局配置文件。

- **存储位置**: 系统应用配置目录下的 `config.json` (例如: `%APPDATA%\pyappify\config.json`)。
- **配置项**:
  - `locale`: 界面语言设置。
  - `pip_index_url`: 全局 Pip 镜像源（如阿里云、清华源），用于加速依赖安装。
  - `pip_cache_dir`: 自定义 Pip 缓存目录，避免重复下载依赖。
  - `theme_mode`: 主题设置 (跟随系统/亮色/暗色)。
- **实现逻辑**:
  - 后端使用 `lazy_static` 和 `Mutex` 维护全局配置单例 `GLOBAL_CONFIG_STATE`。
  - 前端通过 `get_config_payload` 获取配置，`save_configuration` 保存配置。
  - `app_service.rs` 在执行 `pip install` 时会读取此全局配置，动态注入 `--index-url` 和 `--cache-dir` 参数。

### 4.2 智能 Python 环境构建 (`python_env.rs`)

- **版本映射策略**:
  - 代码中硬编码了 `KNOWN_PATCHES` 常量，将主版本 (如 "3.12") 映射到特定的稳定 Patch 版本 (如 "3.12.10")。
  - **双源策略**: 针对不同的网络环境，内置了两套下载源：
    - **默认/海外**: Python 官网 FTP 或 GitHub Releases (Astral 构建版)。
    - **中国大陆**: 华为云镜像 或 ModelScope 镜像 (根据 `rust-i18n` 获取的系统语言自动判定)。
- **环境瘦身 (`clean_python_install`)**:
  - 下载并解压后，会自动删除 `Doc`, `include`, `share`, `libs` 等运行时不必须的目录。
  - 删除 `site-packages` 中的临时文件。
  - 此步骤显著减小了最终占用的磁盘空间。

### 4.3 实时日志与状态监控 (`utils/logger.rs` & `app_service.rs`)

- **日志系统**:
  - 使用 `tracing_appender` 实现了**按日轮转**的文件日志。
  - 日志文件存放于 `logs/` 目录下，文件名前缀为 `app` (如 `app.2023-10-27.log`)。
  - 同时也支持向标准输出 (stdout) 打印日志。
- **状态轮询**:
  - `app_service.rs` 中启动了一个异步任务 `periodically_update_all_apps_running_status`。
  - 每隔 **2秒** 检查一次所有应用的运行状态 (PID 存活检测)。
  - 状态变更通过 Tauri Event `apps` 推送到前端，实现 UI 的实时刷新（如“运行中”状态的自动切换）。

### 4.4 进程执行与控制台交互 (`execute_python.rs`)

- **环境注入**:
  - 使用 `RemovePythonEnvsExt` trait 清除父进程的 `PYTHONHOME`, `PYTHONPATH` 等环境变量，防止环境污染。
  - 手动设置子进程的环境变量，确保其使用刚才下载的独立 Python 环境。
- **静默运行**:
  - Windows 平台下，通过 `creation_flags(0x08000000)` (CREATE_NO_WINDOW) 启动子进程，避免弹出黑框。
- **实时流传输**:
  - 使用 `tokio::process::Command` 捕获 `stdout` 和 `stderr`。
  - 通过 `run_command_and_stream_output` 函数，将每一行输出实时 emit 到前端，前端 `ConsolePage` 组件接收并展示，实现类似 IDE 的控制台体验。

### 4.5 Windows Defender 白名单机制 (`utils/defender.rs`)

为了防止杀毒软件误删 Python 脚本或 DLL，提供了白名单添加功能。

- **实现原理**: 调用 PowerShell 执行管理员命令。

- **核心命令**:

  ```
  Add-MpPreference -ExclusionPath "应用所在绝对路径"
  ```

- **用户体验**: 前端提供按钮，用户点击后需确认 UAC 权限请求，成功后该路径将不再被 Defender 扫描。

### 4.6 Git 操作细节 (`git.rs`)

- **克隆与拉取**:
  - 封装了 `git2` 的 `Repository::clone` 和 `find_remote`, `fetch`。
  - 支持解析 Tag 列表，用于前端的版本选择下拉框。
- **进度反馈**:
  - 实现了 `RemoteCallbacks` 的 `transfer_progress`，将下载进度实时推送到前端（显示为百分比进度条）。

## 5. 前后端通信 API 参考

### Commands (前端 -> 后端)

| **命令名**               | **参数类型 (TS Interface)**                                  | **返回值**      | **描述**                                                     |
| ------------------------ | ------------------------------------------------------------ | --------------- | ------------------------------------------------------------ |
| `load_apps`              | `void`                                                       | `App[]`         | 读取 `pyappify.yml` 并结合运行时状态返回应用列表。           |
| `setup_app`              | `{ appName: string, profileName: string }`                   | `void`          | 根据指定 Profile 初始化应用环境（下载 Python, Clone 代码, 安装依赖）。 |
| `start_app`              | `{ appName: string }`                                        | `void`          | 启动应用主脚本。                                             |
| `stop_app`               | `{ appName: string }`                                        | `void`          | 终止应用进程。                                               |
| `delete_app`             | `{ appName: string }`                                        | `void`          | 删除应用的所有文件和数据。                                   |
| `update_to_version`      | `{ appName: string, version: string, requirements: string }` | `void`          | `git checkout` 到指定 tag 并重新安装依赖。                   |
| `add_defender_exclusion` | `{ appName: string }`                                        | `void`          | 将应用目录加入 Windows Defender 排除项。                     |
| `save_configuration`     | `{ payload: ConfigPayload }`                                 | `void`          | 保存全局设置 (Pip 源, 语言, 主题)。                          |
| `get_config_payload`     | `void`                                                       | `ConfigPayload` | 获取当前全局设置。                                           |

### Events (后端 -> 前端)

| **事件名**            | **Payload 类型** | **触发时机**                                        |
| --------------------- | ---------------- | --------------------------------------------------- |
| `apps`                | `App[]`          | 应用列表加载完成或状态发生变化（每2秒轮询）。       |
| `choose_app_profile`  | `App`            | 点击安装且存在多个 Profile 时触发，前端弹出选择框。 |
| `app_log:{appName}`   | `string`         | 应用安装、更新或运行时的标准日志输出。              |
| `app_error:{appName}` | `string`         | 应用运行时的错误日志输出。                          |

## 6. 构建与部署流程

### 6.1 开发环境

1. **依赖安装**:

   ```
   pnpm install
   ```

2. **启动调试**:

   ```
   pnpm tauri dev
   ```

   - 此时会创建一个虚拟工作目录 `src-tauri/dev_cwd` 模拟用户环境。

### 6.2 生产构建

1. **版本号管理**: 修改 `src-tauri/tauri.conf.json` 中的 `version` 字段。

2. **构建命令**:

   ```
   pnpm tauri build
   ```

3. **产物**:

   - 生成位置: `src-tauri/target/release/bundle/nsis/`。
   - 文件名: `pyappify_{version}_x64-setup.exe`。
   - **注意**: 这是一个安装包，安装后会包含 `pyappify.exe` 和资源文件。

### 6.3 NSIS 安装脚本 (`src-tauri/nsis/installer.nsi`)

项目自定义了 NSIS 模板，主要配置了：

- **多语言支持**: 包含 SimpChinese, TradChinese, English, Korean, Japanese。
- **安装路径**: 默认安装到 `%LOCALAPPDATA%\Programs\pyappify` (用户级安装，无需管理员权限)。
- **卸载逻辑**: 清理注册表和文件。