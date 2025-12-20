"""UuuKa API 适配器

即刻短剧 API (api.uuuka.com) 数据源适配器。
注意：此 API 返回的是外部链接 (source_link)，不提供直接的视频播放地址。
"""
import json
from typing import List

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
from ....utils.log_manager import get_logger

logger = get_logger()


class UuukaAdapter(BaseDataProvider):
    """UuuKa API 数据提供者（即刻短剧）"""

    BASE_URL = "https://api.uuuka.com"

    # 内容类型映射
    CONTENT_TYPES = {
        "短剧": "post",
        "动漫": "dongman",
        "电影": "movie",
        "电视剧": "tv",
        "学习资源": "xuexi",
        "百度短剧": "baidu",
    }

    def __init__(self, timeout: int = 10000):
        super().__init__(timeout)
        self._info = ProviderInfo(
            id="uuuka",
            name="即刻短剧API",
            description="即刻短剧数据源 (api.uuuka.com) - 提供短剧索引链接",
            version="2.2.1",
            base_url=self.BASE_URL,
            capabilities=ProviderCapabilities(
                supports_search=True,
                supports_categories=True,
                supports_recommendations=True,
                supports_episodes=False,  # 此 API 不提供剧集列表
                supports_video_url=False,  # 此 API 不提供视频播放地址
                supports_quality_selection=False,
                supports_pagination=True,
                supports_dynamic_categories=False,
                available_qualities=[]
            )
        )

    @property
    def info(self) -> ProviderInfo:
        return self._info

    async def _request(self, endpoint: str, params: dict = None) -> dict:
        """发送 HTTP 请求"""
        url = f"{self.BASE_URL}{endpoint}"
        text = await super()._request(params=params, url=url)
        
        try:
            data = json.loads(text)
            if not data.get("success"):
                logger.warning(f"UuuKa API 返回失败: {data.get('message', 'Unknown error')}")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"UuuKa API JSON 解析错误: {e}")
            raise Exception(f"响应解析错误: {e}")

    async def search(self, keyword: str, page: int = 1) -> SearchResult:
        """搜索短剧"""
        data = await self._request("/api/search", {
            "keyword": keyword,
            "content_type": "post",  # 默认搜索短剧
            "page": page,
            "limit": 20
        })
        return self._parse_search_result(data)

    async def get_categories(self) -> List[str]:
        """获取分类列表"""
        return list(self.CONTENT_TYPES.keys())

    async def get_category_dramas(self, category: str, page: int = 1) -> CategoryResult:
        """获取分类下的短剧"""
        content_type = self.CONTENT_TYPES.get(category, "post")
        data = await self._request(f"/api/contents/{content_type}", {
            "page": page,
            "limit": 20
        })
        return self._parse_category_result(data, category)

    async def get_recommendations(self) -> List[DramaInfo]:
        """获取推荐内容（优先今日更新，否则获取最新列表）"""
        # 先尝试获取今日更新
        logger.debug("UuuKa: 尝试获取今日更新...")
        data = await self._request("/api/contents/post", {
            "today": "today",
            "page": 1,
            "limit": 20
        })
        dramas = self._parse_recommendations(data)
        
        # 如果今日更新为空，获取最新短剧列表
        if not dramas:
            logger.debug("UuuKa: 今日更新为空，获取最新短剧列表...")
            data = await self._request("/api/contents/post", {
                "page": 1,
                "limit": 20
            })
            dramas = self._parse_recommendations(data)
            logger.debug(f"UuuKa: 获取到 {len(dramas)} 条最新短剧")
        else:
            logger.debug(f"UuuKa: 获取到 {len(dramas)} 条今日更新")
        
        return dramas

    async def get_episodes(self, drama_id: str) -> EpisodeList:
        """获取剧集列表 - 此 API 不支持在线播放
        
        即刻短剧 API 只提供短剧索引链接（网盘链接），不提供剧集列表。
        drama_id 实际上是 source_link（网盘链接）。
        """
        # drama_id 就是 source_link
        source_link = drama_id
        
        # 判断是否是有效的链接
        is_valid_link = source_link.startswith("http")
        
        if is_valid_link:
            desc = f"🔗 此短剧资源存储在网盘中，请复制以下链接到浏览器打开：\n\n{source_link}\n\n提示：点击链接可能需要登录对应网盘账号"
            logger.info(f"UuuKa: 返回网盘链接 - {source_link}")
        else:
            desc = "[即刻短剧API] 此数据源仅提供短剧索引，不支持在线播放。"
            logger.warning(f"UuuKa API: 无效的链接 - {drama_id}")
        
        return EpisodeList(
            code=0 if is_valid_link else 1,
            book_name="网盘资源" if is_valid_link else "不支持播放",
            episodes=[],  # 没有剧集列表
            total=0,
            book_id=drama_id,
            author="",
            category="网盘链接",
            desc=desc,
            duration="",
            book_pic=""
        )

    async def get_video_url(self, episode_id: str, quality: str = "1080p") -> VideoInfo:
        """获取视频播放地址 - 此 API 不支持
        
        即刻短剧 API 只提供短剧索引链接，不提供视频播放地址。
        """
        error_msg = "[即刻短剧API] 此数据源不支持获取视频播放地址"
        logger.warning(f"UuuKa API 不支持获取视频播放地址: episode_id={episode_id}")
        logger.info(error_msg)
        return VideoInfo(
            code=1,
            url="",
            pic="",
            quality="",
            title=error_msg,
            duration="",
            size_str=""
        )

    # ==================== 响应解析方法 ====================

    def _parse_search_result(self, data: dict) -> SearchResult:
        """解析搜索结果"""
        if not data.get("success"):
            return SearchResult(code=1, msg=data.get("message", "搜索失败"), data=[], page=1)

        items = data.get("data", {}).get("items", [])
        dramas = [self._parse_item(item) for item in items]
        page = data.get("data", {}).get("page", 1)

        return SearchResult(
            code=0,
            msg=data.get("message", ""),
            data=dramas,
            page=page
        )

    def _parse_category_result(self, data: dict, category: str) -> CategoryResult:
        """解析分类结果"""
        if not data.get("success"):
            return CategoryResult(code=1, category=category, data=[], offset=1)

        items = data.get("data", {}).get("items", [])
        dramas = [self._parse_item(item) for item in items]
        page = data.get("data", {}).get("page", 1)

        return CategoryResult(
            code=0,
            category=category,
            data=dramas,
            offset=page
        )

    def _parse_recommendations(self, data: dict) -> List[DramaInfo]:
        """解析推荐内容"""
        if not data.get("success"):
            return []

        items = data.get("data", {}).get("items", [])
        return [self._parse_item(item) for item in items]

    def _parse_item(self, item: dict) -> DramaInfo:
        """解析单个内容项"""
        # 使用 source_link 的 hash 作为 book_id，同时保存原始链接
        source_link = item.get("source_link", "")
        # 使用 source_link 作为 book_id，方便后续提取
        book_id = source_link if source_link else str(hash(item.get("title", "")))

        return DramaInfo(
            book_id=book_id,
            title=item.get("title", ""),
            cover="",  # 此 API 不提供封面
            episode_cnt=0,  # 此 API 不提供集数
            intro=f"🔗 网盘链接: {source_link}\n\n点击短剧后可复制链接到浏览器打开",
            type=item.get("type", "post"),
            author="",
            play_cnt=0
        )
