"""数据源适配器模板

复制此文件并实现所有方法即可对接新的 API 数据源。

使用步骤:
1. 复制此文件，重命名为 xxx_adapter.py
2. 修改类名和 ProviderInfo
3. 根据 API 限流要求调整 RATE_LIMIT_WINDOW 和 RATE_LIMIT_MAX_REQUESTS
4. 实现所有 async 方法，将 API 响应转换为标准数据模型
5. 在 provider_init.py 中注册到 ProviderRegistry

限流说明:
- 默认配置: 10秒内最多5次请求
- 使用滑动窗口算法自动控制请求频率
- 超限时会自动等待，无需手动处理
"""
import json
import time
from typing import List
from collections import deque
import aiohttp
import asyncio

from ..provider_base import BaseDataProvider, ProviderInfo, ProviderCapabilities
from ....core.models import (
    DramaInfo,
    EpisodeInfo,
    EpisodeList,
    VideoInfo,
    SearchResult,
    CategoryResult,
)
from ....utils.log_manager import get_logger

logger = get_logger()


class TemplateAdapter(BaseDataProvider):
    """模板适配器 - 复制并修改此类"""

    # TODO: 修改为你的 API 地址
    BASE_URL = "https://your-api.example.com/api"

    # 限流配置 - 根据 API 要求调整
    RATE_LIMIT_WINDOW = 10.0  # 时间窗口（秒）
    RATE_LIMIT_MAX_REQUESTS = 5  # 窗口内最大请求数

    # 静态分类列表（如果 API 不支持动态获取）
    CATEGORIES: List[str] = [
        # TODO: 填写分类列表，或设置 supports_dynamic_categories=True 动态获取
        "分类1",
        "分类2",
        "分类3",
    ]

    def __init__(self, timeout: int = 10000):
        super().__init__(timeout)
        # TODO: 修改提供者信息
        self._info = ProviderInfo(
            id="your_provider_id",
            name="Your Provider Name",
            description="数据源描述",
            version="1.0.0",
            base_url=self.BASE_URL,
            capabilities=ProviderCapabilities(
                supports_search=True,
                supports_categories=True,
                supports_recommendations=True,
                supports_episodes=True,
                supports_video_url=True,
                supports_quality_selection=True,
                supports_pagination=True,
                supports_dynamic_categories=False,
                available_qualities=["1080p", "720p", "480p"],
            ),
        )
        # 限流：滑动窗口记录请求时间戳
        self._request_timestamps: deque = deque()

    @property
    def info(self) -> ProviderInfo:
        return self._info


    # ==================== 网络请求（带限流） ====================

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
                while (
                    self._request_timestamps
                    and self._request_timestamps[0] < window_start
                ):
                    self._request_timestamps.popleft()

        # 记录本次请求时间
        self._request_timestamps.append(time.monotonic())

    async def _request(self, params: dict, endpoint: str = "") -> str:
        """发送 HTTP 请求（带限流）

        Args:
            params: 请求参数
            endpoint: API 端点路径（可选，拼接到 BASE_URL 后）

        Returns:
            响应文本内容
        """
        await self._wait_for_rate_limit()

        timeout = aiohttp.ClientTimeout(total=self._timeout / 1000)
        connector = aiohttp.TCPConnector(force_close=True)
        url = f"{self.BASE_URL}/{endpoint}" if endpoint else self.BASE_URL

        async with aiohttp.ClientSession(
            timeout=timeout, connector=connector
        ) as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")
                return await response.text()


    # ==================== 接口实现 ====================

    async def search(self, keyword: str, page: int = 1) -> SearchResult:
        """搜索短剧

        TODO: 实现搜索逻辑，将 API 响应转换为 SearchResult

        示例:
            body = await self._request({"q": keyword, "page": page}, "search")
            data = json.loads(body)
            dramas = [self._convert_to_drama(item) for item in data["results"]]
            return SearchResult(code=200, data=dramas, page=page)
        """
        raise NotImplementedError("请实现 search 方法")

    async def get_categories(self) -> List[str]:
        """获取分类列表

        TODO: 返回分类列表，可以是静态列表或从 API 动态获取

        静态分类:
            return self.CATEGORIES.copy()

        动态获取:
            body = await self._request({}, "categories")
            data = json.loads(body)
            return [item["name"] for item in data["categories"]]
        """
        return self.CATEGORIES.copy()

    async def get_category_dramas(self, category: str, page: int = 1) -> CategoryResult:
        """获取分类下的短剧

        TODO: 实现分类查询，将 API 响应转换为 CategoryResult

        示例:
            body = await self._request({"category": category, "page": page})
            data = json.loads(body)
            dramas = [self._convert_to_drama(item) for item in data["list"]]
            return CategoryResult(code=200, category=category, data=dramas, offset=page)
        """
        raise NotImplementedError("请实现 get_category_dramas 方法")

    async def get_recommendations(self) -> List[DramaInfo]:
        """获取推荐内容

        TODO: 实现推荐获取，返回 DramaInfo 列表

        示例:
            body = await self._request({"type": "recommend"})
            data = json.loads(body)
            return [self._convert_to_drama(item) for item in data["list"]]
        """
        raise NotImplementedError("请实现 get_recommendations 方法")

    async def get_episodes(self, drama_id: str) -> EpisodeList:
        """获取剧集列表

        TODO: 实现剧集获取，将 API 响应转换为 EpisodeList

        示例:
            body = await self._request({"drama_id": drama_id})
            data = json.loads(body)
            episodes = [self._convert_to_episode(item, i) for i, item in enumerate(data["episodes"])]
            return EpisodeList(
                code=200,
                book_name=data["title"],
                episodes=episodes,
                total=len(episodes),
                book_id=drama_id,
            )
        """
        raise NotImplementedError("请实现 get_episodes 方法")

    async def get_video_url(self, episode_id: str, quality: str = "1080p") -> VideoInfo:
        """获取视频播放地址

        TODO: 实现视频地址获取，将 API 响应转换为 VideoInfo

        示例:
            body = await self._request({"video_id": episode_id, "quality": quality})
            data = json.loads(body)
            return VideoInfo(
                code=200,
                url=data["url"],
                pic=data.get("cover", ""),
                quality=quality,
                title=data.get("title", ""),
                duration=data.get("duration", ""),
                size_str=data.get("size", ""),
            )
        """
        raise NotImplementedError("请实现 get_video_url 方法")


    # ==================== 辅助转换方法 ====================

    def _convert_to_drama(self, item: dict) -> DramaInfo:
        """将 API 响应项转换为 DramaInfo

        TODO: 根据你的 API 响应格式修改字段映射
        """
        return DramaInfo(
            book_id=str(item.get("id", "")),
            title=item.get("name", ""),
            cover=item.get("cover_url", ""),
            episode_cnt=int(item.get("episode_count", 0)),
            intro=item.get("description", ""),
            type=item.get("category", ""),
            author=item.get("author", ""),
            play_cnt=int(item.get("views", 0)),
        )

    def _convert_to_episode(self, item: dict, index: int = 0) -> EpisodeInfo:
        """将 API 响应项转换为 EpisodeInfo

        TODO: 根据你的 API 响应格式修改字段映射

        Args:
            item: API 响应中的单个剧集数据
            index: 剧集索引（用于生成 episode_number）
        """
        return EpisodeInfo(
            video_id=str(item.get("id", "")),
            title=item.get("title", f"第{index + 1}集"),
            episode_number=int(item.get("number", index + 1)),
            chapter_word_number=int(item.get("word_count", 0)),
        )
