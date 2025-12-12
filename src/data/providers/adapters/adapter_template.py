"""数据源适配器模板

复制此文件并实现所有方法即可对接新的 API 数据源。

使用步骤:
1. 复制此文件，重命名为 xxx_adapter.py
2. 修改类名和 ProviderInfo
3. 实现所有 async 方法，将 API 响应转换为标准数据模型
4. 在应用启动时注册到 ProviderRegistry
"""
import json
from typing import List
import aiohttp

from ..provider_base import (
    BaseDataProvider, 
    ProviderInfo, 
    ProviderCapabilities
)
from ....core.models import (
    DramaInfo,
    EpisodeInfo,
    EpisodeList,
    VideoInfo,
    SearchResult,
    CategoryResult,
)


class TemplateAdapter(BaseDataProvider):
    """模板适配器 - 复制并修改此类"""
    
    # TODO: 修改为你的 API 地址
    BASE_URL = "https://your-api.example.com/api"
    
    def __init__(self, timeout: int = 10000):
        super().__init__(timeout)
        # TODO: 修改提供者信息
        self._info = ProviderInfo(
            id="your_provider_id",           # 唯一标识
            name="Your Provider Name",        # 显示名称
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
                supports_dynamic_categories=False,  # 是否支持动态获取分类
                available_qualities=["1080p", "720p", "480p"]
            )
        )
    
    @property
    def info(self) -> ProviderInfo:
        return self._info
    
    async def _request(self, endpoint: str, params: dict = None) -> str:
        """发送 HTTP 请求 - 根据需要修改"""
        timeout = aiohttp.ClientTimeout(total=self._timeout / 1000)
        url = f"{self.BASE_URL}/{endpoint}" if endpoint else self.BASE_URL
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")
                return await response.text()
    
    async def search(self, keyword: str, page: int = 1) -> SearchResult:
        """搜索短剧
        
        TODO: 实现搜索逻辑，将 API 响应转换为 SearchResult
        """
        # 示例:
        # body = await self._request("search", {"q": keyword, "page": page})
        # data = json.loads(body)
        # dramas = [self._convert_to_drama(item) for item in data["results"]]
        # return SearchResult(code=200, data=dramas, page=page)
        raise NotImplementedError("请实现 search 方法")
    
    async def get_categories(self) -> List[str]:
        """获取分类列表
        
        TODO: 返回分类列表，可以是静态列表或从 API 动态获取
        """
        # 静态分类示例:
        # return ["分类1", "分类2", "分类3"]
        
        # 动态获取示例:
        # body = await self._request("categories")
        # data = json.loads(body)
        # return [item["name"] for item in data["categories"]]
        raise NotImplementedError("请实现 get_categories 方法")
    
    async def get_category_dramas(self, category: str, page: int = 1) -> CategoryResult:
        """获取分类下的短剧
        
        TODO: 实现分类查询，将 API 响应转换为 CategoryResult
        """
        raise NotImplementedError("请实现 get_category_dramas 方法")
    
    async def get_recommendations(self) -> List[DramaInfo]:
        """获取推荐内容
        
        TODO: 实现推荐获取，返回 DramaInfo 列表
        """
        raise NotImplementedError("请实现 get_recommendations 方法")
    
    async def get_episodes(self, drama_id: str) -> EpisodeList:
        """获取剧集列表
        
        TODO: 实现剧集获取，将 API 响应转换为 EpisodeList
        """
        raise NotImplementedError("请实现 get_episodes 方法")
    
    async def get_video_url(self, episode_id: str, quality: str = "1080p") -> VideoInfo:
        """获取视频播放地址
        
        TODO: 实现视频地址获取，将 API 响应转换为 VideoInfo
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
            play_cnt=int(item.get("views", 0))
        )
    
    def _convert_to_episode(self, item: dict) -> EpisodeInfo:
        """将 API 响应项转换为 EpisodeInfo
        
        TODO: 根据你的 API 响应格式修改字段映射
        """
        return EpisodeInfo(
            video_id=str(item.get("id", "")),
            title=item.get("title", ""),
            episode_number=int(item.get("number", 0)),
            chapter_word_number=0
        )
