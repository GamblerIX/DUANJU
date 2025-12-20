# AI 自动开发规范

本文档定义了 AI 辅助开发 DuanjuApp 时应遵循的规范和约定。

## 项目结构

```
DUANJU/
├── main.py                 # 应用入口
├── config/
│   └── config.json         # 应用配置
├── docs/                   # 文档目录
├── logs/                   # 日志目录（自动生成）
├── src/
│   ├── core/               # 核心模块
│   │   ├── models.py       # 数据模型定义
│   │   ├── theme_manager.py
│   │   └── utils/          # 工具类
│   ├── data/               # 数据层
│   │   ├── api/            # API 客户端
│   │   ├── cache/          # 缓存管理
│   │   ├── config/         # 配置管理
│   │   ├── providers/      # 数据提供者
│   │   │   └── adapters/   # API 适配器
│   │   ├── favorites/      # 收藏管理
│   │   ├── history/        # 历史记录
│   │   └── image/          # 图片加载
│   ├── services/           # 服务层
│   └── ui/                 # UI 层
│       ├── controls/       # 自定义控件
│       ├── dialogs/        # 对话框
│       ├── interfaces/     # 界面页面
│       └── windows/        # 窗口
└── requirements.txt
```

## 代码规范

### 1. 导入规范

使用相对导入，不使用绝对导入 `from src.xxx`：

```python
# ✅ 正确
from ..core.models import DramaInfo
from ...core.utils.log_manager import get_logger

# ❌ 错误
from src.core.models import DramaInfo
```

### 2. 类型注解

所有函数和方法必须有类型注解：

```python
from typing import List, Optional

async def search(self, keyword: str, page: int = 1) -> SearchResult:
    ...

def get_item(self, item_id: str) -> Optional[DramaInfo]:
    ...
```

### 3. 文档字符串

所有公开类和方法必须有文档字符串：

```python
class CategoryService(QObject):
    """分类服务实现
    
    负责获取分类列表和分类下的短剧内容。
    """
    
    def fetch_categories(self) -> None:
        """获取分类列表，结果通过 categories_loaded 信号发出"""
        ...
```

### 4. 日志规范

使用统一的日志管理器：

```python
from ..core.utils.log_manager import get_logger

logger = get_logger()

# 日志级别使用
logger.debug("调试信息")           # 开发调试
logger.info("普通信息")            # 正常流程
logger.warning("警告信息")         # 潜在问题
logger.error("错误信息")           # 错误但可恢复
logger.critical("严重错误")        # 致命错误

# 专用日志方法
logger.log_user_action("search", f"keyword={keyword}")
logger.log_service_error("ServiceName", "operation", exception)
logger.log_api_request("url", params)
```

### 5. 错误处理

- 服务层抛出异常，由 AsyncWorker 统一捕获
- 不要在服务层重复记录错误日志
- 使用友好的中文错误消息

```python
# ✅ 正确
async def _do_search(self, keyword: str) -> SearchResult:
    response = await self._api_client.get(params={"name": keyword})
    if not response.success:
        raise Exception(response.error or "搜索失败")
    return self._parse_result(response.body)

# ❌ 错误 - 重复记录日志
async def _do_search(self, keyword: str) -> SearchResult:
    response = await self._api_client.get(params={"name": keyword})
    if not response.success:
        logger.error(f"Search failed: {response.error}")  # 不需要
        raise Exception(response.error or "搜索失败")
```

### 6. 异步编程

- 网络请求使用 `async/await`
- 使用 `AsyncWorker` 在 Qt 线程中执行异步任务
- 不要在主线程执行阻塞操作

```python
class MyService(QObject):
    result_ready = Signal(object)
    
    def fetch_data(self) -> None:
        self._worker = AsyncWorker(
            self._do_fetch,
            parent=self,
            service_name="MyService"
        )
        self._worker.finished_signal.connect(self._on_result)
        self._worker.error_signal.connect(self._on_error)
        self._worker.start()
    
    async def _do_fetch(self):
        # 异步操作
        return await self._api_client.get(...)
```

### 7. Qt 信号槽

- 使用 PySide6 的信号槽机制
- 信号命名使用过去式或状态描述

```python
class MyService(QObject):
    # 信号命名规范
    loading_started = Signal()           # 开始加载
    data_loaded = Signal(object)         # 数据加载完成
    error_occurred = Signal(object)      # 发生错误
    
    # 槽方法命名
    def _on_data_loaded(self, data):
        ...
```

## 数据模型

### 1. 使用 dataclass

```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class DramaInfo:
    book_id: str
    title: str
    cover: str
    episode_cnt: int = 0
    intro: str = ""
```

### 2. 模型位置

所有数据模型定义在 `src/core/models.py`

### 3. 序列化

使用 `src/core/utils/json_serializer.py` 中的函数

## UI 开发

### 1. 使用 QFluentWidgets

项目使用 PySide6-Fluent-Widgets 组件库：

```python
from qfluentwidgets import (
    PushButton, LineEdit, InfoBar, 
    FluentIcon, CardWidget
)
```

### 2. 界面结构

- `windows/` - 主窗口和独立窗口
- `interfaces/` - 导航页面
- `dialogs/` - 弹出对话框
- `controls/` - 自定义控件

### 3. 样式

使用主题管理器，不要硬编码颜色：

```python
from ..core.theme_manager import ThemeManager

theme = ThemeManager()
theme.set_theme(ThemeMode.DARK)
```

## 配置管理

### 1. 配置文件

`config/config.json` 存储应用配置

### 2. 新增配置项

1. 在 `src/core/models.py` 的 `AppConfig` 添加字段
2. 在 `src/core/utils/json_serializer.py` 更新序列化
3. 在 `config/config.json` 添加默认值

## 测试

### 1. 导入测试

```bash
python -c "import sys; sys.path.insert(0, '.'); from src.xxx import Xxx; print('OK')"
```

### 2. 运行应用

```bash
python main.py
```

### 3. 检查语法

使用 IDE 的诊断功能检查语法错误

## 提交规范

### 1. 文件命名

- Python 文件：`snake_case.py`
- 类名：`PascalCase`
- 函数/变量：`snake_case`
- 常量：`UPPER_SNAKE_CASE`

### 2. 新增功能

1. 先在 `models.py` 定义数据模型
2. 在 `services/` 实现业务逻辑
3. 在 `ui/` 实现界面
4. 更新文档

### 3. 新增 API 适配器

参考 `docs/api-adapter-guide.md`

## 禁止事项

1. ❌ 不要使用 `print()` 输出，使用 `logger`
2. ❌ 不要在主线程执行网络请求
3. ❌ 不要硬编码 API 地址，使用配置
4. ❌ 不要忽略异常，至少记录日志
5. ❌ 不要使用绝对导入 `from src.xxx`
6. ❌ 不要在服务层重复记录错误日志
