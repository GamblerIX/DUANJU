"""数据提供者基础接口定义

定义所有数据源必须实现的统一接口协议。
新数据源只需实现 IDataProvider 接口即可无缝接入。

使用方法:
1. 在 adapters/ 目录创建新适配器文件
2. 继承 BaseDataProvider 并实现所有抽象方法
3. 在 provider_registry.py 中注册
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Protocol, runtime_checkable

from ...core.models import (
    DramaInfo,
    EpisodeList,
    VideoInfo,
    SearchResult,
    CategoryResult,
)


@dataclass
class ProviderCapabilities:
    """数据提供者能力声明"""
    supports_search: bool = True
    supports_categories: bool = True
    supports_recommendations: bool = True
    supports_episodes: bool = True
    supports_video_url: bool = True
    supports_quality_selection: bool = True
    supports_pagination: bool = True
    supports_dynamic_categories: bool = False  # 是否支持动态获取分类
    available_qualities: List[str] = field(default_factory=lambda: ["1080p", "720p", "480p"])


@dataclass
class ProviderInfo:
    """数据提供者元信息"""
    id: str                    # 唯一标识符
    name: str                  # 显示名称
    description: str = ""
    version: str = "1.0.0"
    author: str = ""
    base_url: str = ""
    capabilities: ProviderCapabilities = field(default_factory=ProviderCapabilities)


@runtime_checkable
class IDataProvider(Protocol):
    """数据提供者统一接口协议
    
    所有数据源适配器必须实现此接口。
    """
    
    @property
    def info(self) -> ProviderInfo:
        """获取提供者信息"""
        ...
    
    async def search(self, keyword: str, page: int = 1) -> SearchResult:
        """搜索短剧"""
        ...
    
    async def get_categories(self) -> List[str]:
        """获取分类列表"""
        ...
    
    async def get_category_dramas(self, category: str, page: int = 1) -> CategoryResult:
        """获取分类下的短剧"""
        ...
    
    async def get_recommendations(self) -> List[DramaInfo]:
        """获取推荐内容"""
        ...
    
    async def get_episodes(self, drama_id: str) -> EpisodeList:
        """获取剧集列表"""
        ...
    
    async def get_video_url(self, episode_id: str, quality: str = "1080p") -> VideoInfo:
        """获取视频播放地址"""
        ...
    
    def set_timeout(self, milliseconds: int) -> None:
        """设置请求超时"""
        ...


class BaseDataProvider(ABC):
    """数据提供者基类，子类只需实现抽象方法"""
    
    def __init__(self, timeout: int = 10000):
        self._timeout = timeout
    
    @property
    @abstractmethod
    def info(self) -> ProviderInfo:
        pass
    
    @abstractmethod
    async def search(self, keyword: str, page: int = 1) -> SearchResult:
        pass
    
    @abstractmethod
    async def get_categories(self) -> List[str]:
        pass
    
    @abstractmethod
    async def get_category_dramas(self, category: str, page: int = 1) -> CategoryResult:
        pass
    
    @abstractmethod
    async def get_recommendations(self) -> List[DramaInfo]:
        pass
    
    @abstractmethod
    async def get_episodes(self, drama_id: str) -> EpisodeList:
        pass
    
    @abstractmethod
    async def get_video_url(self, episode_id: str, quality: str = "1080p") -> VideoInfo:
        pass
    
    def set_timeout(self, milliseconds: int) -> None:
        self._timeout = max(1000, min(60000, milliseconds))
    
    @property
    def timeout(self) -> int:
        return self._timeout
