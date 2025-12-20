"""数据提供者基础接口定义

定义所有数据源必须实现的统一接口协议。
新数据源只需实现 IDataProvider 接口即可无缝接入。

使用方法:
1. 在 adapters/ 目录创建新适配器文件
2. 继承 BaseDataProvider 并实现所有抽象方法
3. 在 provider_registry.py 中注册
"""
import time
import asyncio
import aiohttp
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from collections import deque
from typing import List, Optional, Protocol, runtime_checkable

from ...core.models import (
    DramaInfo,
    EpisodeList,
    VideoInfo,
    SearchResult,
    CategoryResult,
)
from ...utils.log_manager import get_logger

logger = get_logger()


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
    
    # 默认限流配置：10秒内最多5次请求
    RATE_LIMIT_WINDOW = 10.0
    RATE_LIMIT_MAX_REQUESTS = 5
    
    def __init__(self, timeout: int = 10000):
        self._timeout = timeout
        # 限流：滑动窗口记录请求时间戳
        self._request_timestamps: deque = deque()
    
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

    async def _wait_for_rate_limit(self) -> None:
        """等待直到满足限流条件（滑动窗口算法）"""
        now = time.monotonic()
        window_start = now - self.RATE_LIMIT_WINDOW
        
        # 清理过期的时间戳
        while self._request_timestamps and self._request_timestamps[0] < window_start:
            self._request_timestamps.popleft()
        
        # 如果窗口内请求数已达上限，等待最早的请求过期
        if len(self._request_timestamps) >= self.RATE_LIMIT_MAX_REQUESTS:
            wait_time = self._request_timestamps[0] - window_start
            if wait_time > 0:
                logger.debug(f"限流等待 {wait_time:.2f} 秒")
                await asyncio.sleep(wait_time)
                # 等待后重新清理
                now = time.monotonic()
                window_start = now - self.RATE_LIMIT_WINDOW
                while self._request_timestamps and self._request_timestamps[0] < window_start:
                    self._request_timestamps.popleft()
        
        # 记录本次请求时间
        self._request_timestamps.append(time.monotonic())
    
    async def _request(self, params: dict, url: Optional[str] = None) -> str:
        """发送 HTTP 请求（带限流）"""
        await self._wait_for_rate_limit()
        
        target_url = url or self.info.base_url
        if not target_url:
            raise ValueError("未设置基础 URL")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    target_url, 
                    params=params, 
                    timeout=aiohttp.ClientTimeout(total=self._timeout / 1000),
                    headers={"User-Agent": "Mozilla/5.0"}
                ) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP Error: {response.status}")
                    return await response.text()
        except Exception as e:
            logger.error(f"API 请求失败: {e}")
            raise
