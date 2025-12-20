"""短剧分页搜索 API 适配器

全网短剧数据源适配器，支持按日期获取、关键词搜索、每日更新和热榜。
注意：此 API 返回的是网盘链接，不提供直接的视频播放地址。
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


class DuanjuSearchAdapter(BaseDataProvider):
    """短剧分页搜索 API 数据提供者（全网短剧）"""

    # API 地址
    BASE_URL = "https://kuoapp.com"

    # 分类映射（基于 API 文档）
    CATEGORIES = {
        "今日更新": "today",
        "热门榜单": "hot",
        "全部短剧": "all",
    }

    def __init__(self, timeout: int = 10000, base_url: str = None):
        super().__init__(timeout)
        if base_url:
            self.BASE_URL = base_url
        self._info = ProviderInfo(
            id="duanju_search",
            name="全网短剧API",
            description="全网短剧数据源 - 提供短剧索引链接（网盘链接）",
            version="1.0.0",
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
            return data
        except json.JSONDecodeError as e:
            logger.error(f"DuanjuSearch API JSON 解析错误: {e}")
            raise Exception(f"响应解析错误: {e}")

    async def search(self, keyword: str, page: int = 1) -> SearchResult:
        """搜索短剧
        
        API: GET /duanju/api.php?param=1&name=关键词&page=1
        注意：搜索接口响应较慢，如果超时会使用本地数据过滤
        """
        try:
            # 尝试使用搜索 API
            data = await self._request("/duanju/api.php", {
                "param": 1,
                "name": keyword,
                "page": page
            })
            return self._parse_search_result(data, page)
        except Exception as e:
            logger.warning(f"DuanjuSearch 搜索接口失败: {e}，使用本地数据过滤")
            # 搜索接口失败时，从最近数据中过滤
            return await self._search_from_local(keyword, page)

    async def get_categories(self) -> List[str]:
        """获取分类列表"""
        return list(self.CATEGORIES.keys())

    async def get_category_dramas(self, category: str, page: int = 1) -> CategoryResult:
        """获取分类下的短剧"""
        category_type = self.CATEGORIES.get(category, "today")
        
        if category_type == "hot":
            # 热门榜单 - 使用最近日期的数据
            data = await self._get_recent_data()
            return self._parse_category_result(data, category, page)
        elif category_type == "today":
            # 今日更新
            data = await self._get_recent_data()
            return self._parse_category_result(data, category, page)
        else:
            # 全部短剧 - 也使用最近日期数据（避免超时）
            data = await self._get_recent_data()
            return self._parse_category_result(data, category, page)

    async def _search_from_local(self, keyword: str, page: int) -> SearchResult:
        """从本地数据中搜索（当搜索接口不可用时的备选方案）"""
        try:
            data = await self._get_recent_data()
            # 过滤包含关键词的数据
            filtered = [
                item for item in data
                if keyword.lower() in (item.get("name") or "").lower()
            ]
            dramas = [self._parse_item(item) for item in filtered]
            logger.info(f"DuanjuSearch: 本地搜索找到 {len(dramas)} 条结果")
            return SearchResult(
                code=0,
                msg=f"本地搜索结果（搜索接口暂不可用）",
                data=dramas,
                page=page
            )
        except Exception as e:
            logger.error(f"DuanjuSearch 本地搜索失败: {e}")
            return SearchResult(code=1, msg=f"搜索失败: {e}", data=[], page=page)

    async def _get_recent_data(self) -> list:
        """获取最近日期的数据
        
        从今天开始往前查找，直到找到有数据的日期
        """
        from datetime import date, timedelta
        
        # 从今天开始，往前查找最多30天
        for days_ago in range(30):
            check_date = date.today() - timedelta(days=days_ago)
            date_str = check_date.strftime("%Y-%m-%d")
            
            try:
                logger.debug(f"DuanjuSearch: 尝试获取 {date_str} 的数据...")
                data = await self._request("/duanju/get.php", {"day": date_str})
                if data and isinstance(data, list) and len(data) > 0:
                    logger.info(f"DuanjuSearch: 获取到 {date_str} 的 {len(data)} 条数据")
                    return data
            except Exception as e:
                logger.debug(f"DuanjuSearch: {date_str} 无数据: {e}")
                continue
        
        logger.warning("DuanjuSearch: 未找到任何数据")
        return []

    async def get_recommendations(self) -> List[DramaInfo]:
        """获取推荐内容（最近更新）"""
        logger.debug("DuanjuSearch: 获取推荐内容...")
        try:
            data = await self._get_recent_data()
            dramas = self._parse_data_list(data)
            logger.debug(f"DuanjuSearch: 获取到 {len(dramas)} 条推荐")
            return dramas[:20]  # 限制返回数量
        except Exception as e:
            logger.error(f"DuanjuSearch 获取推荐失败: {e}")
            return []

    async def get_episodes(self, drama_id: str) -> EpisodeList:
        """获取剧集列表 - 此 API 不支持在线播放
        
        此 API 只提供短剧索引链接（网盘链接），不提供剧集列表。
        drama_id 实际上是网盘链接。
        """
        source_link = drama_id
        is_valid_link = source_link.startswith("http")
        
        if is_valid_link:
            desc = f"🔗 此短剧资源存储在网盘中，请复制以下链接到浏览器打开：\n\n{source_link}\n\n提示：点击链接可能需要登录对应网盘账号"
            logger.info(f"DuanjuSearch: 返回网盘链接 - {source_link}")
        else:
            desc = "[全网短剧API] 此数据源仅提供短剧索引，不支持在线播放。"
            logger.warning(f"DuanjuSearch API: 无效的链接 - {drama_id}")
        
        return EpisodeList(
            code=0 if is_valid_link else 1,
            book_name="网盘资源" if is_valid_link else "不支持播放",
            episodes=[],
            total=0,
            book_id=drama_id,
            author="",
            category="网盘链接",
            desc=desc,
            duration="",
            book_pic=""
        )

    async def get_video_url(self, episode_id: str, quality: str = "1080p") -> VideoInfo:
        """获取视频播放地址 - 此 API 不支持"""
        error_msg = "[全网短剧API] 此数据源不支持获取视频播放地址"
        logger.warning(f"DuanjuSearch API 不支持获取视频播放地址: episode_id={episode_id}")
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

    def _parse_search_result(self, data: dict, page: int) -> SearchResult:
        """解析搜索结果
        
        API 返回格式:
        {
            "page": "1",
            "totalPages": 119,
            "data": [
                {
                    "id": "xxx",
                    "name": "短剧名称",
                    "label": 0,
                    "addtime": "2024-06-29",
                    "cover": "https://...",
                    "url": "https://pan.quark.cn/s/xxx",
                    "episodes": "90",
                    "state": 0
                }
            ]
        }
        """
        if isinstance(data, dict):
            items = data.get("data", [])
            if isinstance(items, list):
                dramas = [self._parse_item(item) for item in items]
            else:
                dramas = []
            
            return SearchResult(
                code=0,
                msg="success",
                data=dramas,
                page=page
            )
        
        return SearchResult(code=1, msg="响应格式错误", data=[], page=page)

    def _parse_category_result(self, data: dict, category: str, page: int) -> CategoryResult:
        """解析分类结果"""
        dramas = self._parse_data_list(data)
        return CategoryResult(
            code=0,
            category=category,
            data=dramas,
            offset=page
        )

    def _parse_data_list(self, data) -> List[DramaInfo]:
        """解析数据列表"""
        if isinstance(data, dict):
            items = data.get("data", [])
            if isinstance(items, list):
                return [self._parse_item(item) for item in items]
        elif isinstance(data, list):
            return [self._parse_item(item) for item in data]
        return []

    def _parse_item(self, item: dict) -> DramaInfo:
        """解析单个内容项
        
        API 返回的数据项格式:
        {
            "id": "667fb7e8e02e3",
            "name": "短剧名称（90集）",
            "label": 0,
            "addtime": "2024-06-29",
            "cover": "https://t12.baidu.com/...",
            "url": "https://pan.quark.cn/s/xxx",
            "episodes": "90",
            "state": 0
        }
        """
        # 获取标题
        title = item.get("name") or item.get("title") or "未知短剧"
        
        # 获取网盘链接（夸克网盘）
        source_link = item.get("url") or ""
        
        # 使用 source_link 作为 book_id，方便后续提取
        book_id = source_link if source_link else item.get("id") or str(hash(title))
        
        # 获取更新时间
        update_time = item.get("addtime") or ""
        
        # 获取集数
        episode_cnt = item.get("episodes") or 0
        if isinstance(episode_cnt, str):
            try:
                episode_cnt = int(episode_cnt.replace("集", "").strip())
            except Exception:
                episode_cnt = 0

        # 获取封面
        cover = item.get("cover") or ""

        intro = f"🔗 夸克网盘链接\n更新时间: {update_time}" if update_time else "🔗 夸克网盘链接"
        if source_link:
            intro += f"\n\n点击短剧后可复制链接到浏览器打开"

        return DramaInfo(
            book_id=book_id,
            title=title,
            cover=cover,
            episode_cnt=episode_cnt,
            intro=intro,
            type="短剧",
            author="",
            play_cnt=0
        )
