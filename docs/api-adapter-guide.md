# API 数据源对接开发指南

本文档说明如何为 DuanjuApp 对接新的数据源 API。

## 架构概述

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   UI Layer      │────▶│  Service Layer   │────▶│  Provider Layer │
│  (界面组件)      │     │  (业务逻辑)       │     │  (数据适配器)    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                          │
                                                          ▼
                                                 ┌─────────────────┐
                                                 │   External API  │
                                                 │   (外部接口)     │
                                                 └─────────────────┘
```

## 快速开始

### 1. 复制模板文件

```bash
cp src/data/providers/adapters/adapter_template.py src/data/providers/adapters/your_adapter.py
```

### 2. 实现适配器

```python
from ..provider_base import BaseDataProvider, ProviderInfo, ProviderCapabilities
from ....core.models import DramaInfo, EpisodeList, VideoInfo, SearchResult, CategoryResult

class YourAdapter(BaseDataProvider):
    BASE_URL = "https://your-api.example.com"
    
    def __init__(self, timeout: int = 10000):
        super().__init__(timeout)
        self._info = ProviderInfo(
            id="your_provider",           # 唯一标识符
            name="Your Provider",         # 显示名称
            description="数据源描述",
            base_url=self.BASE_URL,
            capabilities=ProviderCapabilities(
                supports_search=True,
                supports_categories=True,
                # ... 声明支持的功能
            )
        )
    
    @property
    def info(self) -> ProviderInfo:
        return self._info
    
    async def search(self, keyword: str, page: int = 1) -> SearchResult:
        # 实现搜索逻辑
        pass
    
    # ... 实现其他方法
```

### 3. 注册适配器

编辑 `src/data/providers/provider_init.py`:

```python
from .adapters.your_adapter import YourAdapter

def init_providers(timeout: int = 10000) -> None:
    registry = get_registry()
    registry.register(CenguiguiAdapter(timeout=timeout))
    registry.register(YourAdapter(timeout=timeout))  # 新增
```

### 4. 配置默认数据源（可选）

编辑 `config/config.json`:

```json
{
  "currentProvider": "your_provider"
}
```

## 接口定义

### IDataProvider 接口

所有适配器必须实现以下方法：

| 方法 | 说明 | 返回类型 |
|------|------|----------|
| `search(keyword, page)` | 搜索短剧 | `SearchResult` |
| `get_categories()` | 获取分类列表 | `List[str]` |
| `get_category_dramas(category, page)` | 获取分类下的短剧 | `CategoryResult` |
| `get_recommendations()` | 获取推荐内容 | `List[DramaInfo]` |
| `get_episodes(drama_id)` | 获取剧集列表 | `EpisodeList` |
| `get_video_url(episode_id, quality)` | 获取视频播放地址 | `VideoInfo` |

### 数据模型

#### DramaInfo - 短剧信息

```python
@dataclass
class DramaInfo:
    book_id: str      # 短剧唯一ID
    title: str        # 标题
    cover: str        # 封面图URL
    episode_cnt: int  # 集数
    intro: str        # 简介
    type: str         # 分类/类型
    author: str       # 作者
    play_cnt: int     # 播放量
```

#### EpisodeInfo - 剧集信息

```python
@dataclass
class EpisodeInfo:
    video_id: str        # 剧集唯一ID
    title: str           # 标题
    episode_number: int  # 集数编号
```

#### VideoInfo - 视频信息

```python
@dataclass
class VideoInfo:
    code: int       # 状态码
    url: str        # 视频播放地址
    pic: str        # 封面图
    quality: str    # 清晰度
    title: str      # 标题
    duration: str   # 时长
    size_str: str   # 文件大小
```

#### SearchResult - 搜索结果

```python
@dataclass
class SearchResult:
    code: int              # 状态码
    msg: str               # 消息
    data: List[DramaInfo]  # 结果列表
    page: int              # 当前页码
```

#### CategoryResult - 分类结果

```python
@dataclass
class CategoryResult:
    code: int              # 状态码
    category: str          # 分类名称
    data: List[DramaInfo]  # 结果列表
    offset: int            # 偏移量/页码
```

## 能力声明

通过 `ProviderCapabilities` 声明适配器支持的功能：

```python
ProviderCapabilities(
    supports_search=True,              # 支持搜索
    supports_categories=True,          # 支持分类浏览
    supports_recommendations=True,     # 支持推荐
    supports_episodes=True,            # 支持获取剧集
    supports_video_url=True,           # 支持获取播放地址
    supports_quality_selection=True,   # 支持清晰度选择
    supports_pagination=True,          # 支持分页
    supports_dynamic_categories=False, # 是否动态获取分类
    available_qualities=["1080p", "720p", "480p"]  # 可用清晰度
)
```

## 示例：字段映射

假设你的 API 返回格式如下：

```json
{
  "status": 0,
  "results": [
    {
      "id": "12345",
      "name": "短剧名称",
      "poster": "https://...",
      "episodes": 20,
      "desc": "简介..."
    }
  ]
}
```

转换为标准模型：

```python
def _parse_search_result(self, json_str: str) -> SearchResult:
    data = json.loads(json_str)
    dramas = []
    for item in data.get("results", []):
        dramas.append(DramaInfo(
            book_id=str(item["id"]),
            title=item["name"],
            cover=item["poster"],
            episode_cnt=item["episodes"],
            intro=item.get("desc", ""),
            type="",
            author="",
            play_cnt=0
        ))
    return SearchResult(
        code=200 if data["status"] == 0 else data["status"],
        data=dramas,
        page=1
    )
```

## 错误处理

适配器中的异常会被上层自动捕获并显示友好提示：

```python
async def search(self, keyword: str, page: int = 1) -> SearchResult:
    try:
        body = await self._request({"q": keyword, "page": page})
        return self._parse_search_result(body)
    except aiohttp.ClientError:
        raise Exception("网络请求失败")
    except json.JSONDecodeError:
        raise Exception("数据解析失败")
```

## 测试适配器

```python
import asyncio
from src.data.providers.adapters.your_adapter import YourAdapter

async def test():
    adapter = YourAdapter()
    
    # 测试搜索
    result = await adapter.search("测试")
    print(f"搜索结果: {len(result.data)} 条")
    
    # 测试分类
    categories = await adapter.get_categories()
    print(f"分类: {categories}")

asyncio.run(test())
```

## 文件结构

```
src/data/providers/
├── provider_base.py          # 接口定义
├── provider_registry.py      # 注册中心
├── provider_init.py          # 初始化
└── adapters/
    ├── cenguigui_adapter.py  # 默认适配器
    ├── adapter_template.py   # 模板文件
    └── your_adapter.py       # 你的适配器
```
