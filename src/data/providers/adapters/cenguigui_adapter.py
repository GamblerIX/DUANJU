"""Cenguigui API 适配器

将现有 api.cenguigui.cn 接口适配到统一的 IDataProvider 接口。
这是默认的数据提供者实现。
"""
import re
import json
import time
from typing import List
from collections import deque
import aiohttp
import asyncio

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
from ....core.utils.log_manager import get_logger

logger = get_logger()


class CenguiguiAdapter(BaseDataProvider):
    """Cenguigui API 数据提供者"""
    
    BASE_URL = "https://api.cenguigui.cn/api/duanju/api.php"
    
    # 限流配置：10秒内最多5次请求
    RATE_LIMIT_WINDOW = 10.0  # 时间窗口（秒）
    RATE_LIMIT_MAX_REQUESTS = 5  # 窗口内最大请求数
    
    # 静态分类列表
    CATEGORIES = [
        "推荐榜", "新剧", "逆袭", "霸总", "现代言情", "打脸虐渣", 
        "豪门恩怨", "神豪", "马甲", "都市日常", "战神归来", "小人物", 
        "女性成长", "大女主", "穿越", "都市修仙", "强者回归", "亲情", 
        "古装", "重生", "闪婚", "赘婿逆袭", "虐恋", "追妻", "天下无敌", 
        "家庭伦理", "萌宝", "古风权谋", "职场", "奇幻脑洞", "异能", 
        "无敌神医", "古风言情", "传承觉醒", "现言甜宠", "奇幻爱情", 
        "乡村", "历史古代", "王妃", "高手下山", "娱乐圈", "强强联合", 
        "破镜重圆", "暗恋成真", "民国", "欢喜冤家", "系统", "真假千金", 
        "龙王", "校园", "穿书", "女帝", "团宠", "年代爱情", "玄幻仙侠", 
        "青梅竹马", "悬疑推理", "皇后", "替身", "大叔", "喜剧", "剧情"
    ]
    
    def __init__(self, timeout: int = 10000):
        super().__init__(timeout)
        self._info = ProviderInfo(
            id="cenguigui",
            name="Cenguigui API",
            description="默认短剧数据源",
            version="1.0.0",
            base_url=self.BASE_URL,
            capabilities=ProviderCapabilities(
                supports_dynamic_categories=False,
                available_qualities=["1080p", "720p", "360p"]
            )
        )
        # 限流：滑动窗口记录请求时间戳
        self._request_timestamps: deque = deque()
    
    @property
    def info(self) -> ProviderInfo:
        return self._info
    
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
    
    async def _request(self, params: dict) -> str:
        """发送 HTTP 请求（带限流）"""
        await self._wait_for_rate_limit()
        
        timeout = aiohttp.ClientTimeout(total=self._timeout / 1000)
        connector = aiohttp.TCPConnector(force_close=True)
        
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            async with session.get(self.BASE_URL, params=params) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")
                return await response.text()
    
    async def search(self, keyword: str, page: int = 1) -> SearchResult:
        """搜索短剧"""
        body = await self._request({"name": keyword, "page": str(page)})
        return self._parse_search_result(body)
    
    async def get_categories(self) -> List[str]:
        """获取分类列表（静态）"""
        return self.CATEGORIES.copy()
    
    async def get_category_dramas(self, category: str, page: int = 1) -> CategoryResult:
        """获取分类下的短剧"""
        body = await self._request({"classname": category, "offset": str(page)})
        return self._parse_category_result(body, category)
    
    async def get_recommendations(self) -> List[DramaInfo]:
        """获取推荐内容"""
        body = await self._request({"type": "recommend"})
        return self._parse_recommendations(body)
    
    async def get_episodes(self, drama_id: str) -> EpisodeList:
        """获取剧集列表"""
        body = await self._request({"book_id": drama_id})
        return self._parse_episode_list(body)
    
    async def get_video_url(self, episode_id: str, quality: str = "1080p") -> VideoInfo:
        """获取视频播放地址"""
        body = await self._request({
            "video_id": episode_id, 
            "level": quality, 
            "type": "json"
        })
        return self._parse_video_info(body)
    
    # ==================== 响应解析方法 ====================
    
    def _parse_search_result(self, json_str: str) -> SearchResult:
        data = json.loads(json_str)
        dramas = [self._parse_drama_item(item) for item in data.get("data", [])]
        page = data.get("page", 1)
        if isinstance(page, str):
            page = int(page) if page.isdigit() else 1
        return SearchResult(
            code=data.get("code", 0),
            msg=data.get("msg", ""),
            data=dramas,
            page=page
        )
    
    def _parse_category_result(self, json_str: str, category: str) -> CategoryResult:
        data = json.loads(json_str)
        dramas = []
        for item in data.get("data", []):
            dramas.append(DramaInfo(
                book_id=str(item.get("book_id", "")),
                title=item.get("title", ""),
                cover=item.get("cover", ""),
                episode_cnt=int(item.get("episode_cnt", 0)),
                intro=item.get("video_desc", ""),
                type=item.get("sub_title", category),
                author="",
                play_cnt=int(item.get("play_cnt", 0))
            ))
        return CategoryResult(
            code=data.get("code", 0),
            category=category,
            data=dramas,
            offset=1
        )
    
    def _parse_recommendations(self, json_str: str) -> List[DramaInfo]:
        data = json.loads(json_str)
        dramas = []
        for item in data.get("data", []):
            book_data = item.get("book_data", {})
            serial_count = book_data.get("serial_count", 0)
            if isinstance(serial_count, str):
                serial_count = int(serial_count) if serial_count.isdigit() else 0
            dramas.append(DramaInfo(
                book_id=str(book_data.get("book_id", "")),
                title=book_data.get("book_name", ""),
                cover=book_data.get("thumb_url", ""),
                episode_cnt=serial_count,
                intro="",
                type=book_data.get("category", ""),
                author="",
                play_cnt=int(item.get("hot", 0))
            ))
        return dramas
    
    def _parse_episode_list(self, json_str: str) -> EpisodeList:
        data = json.loads(json_str)
        episodes = []
        for item in data.get("data", []):
            title = item.get("title", "")
            episodes.append(EpisodeInfo(
                video_id=str(item.get("video_id", "")),
                title=title,
                episode_number=self._parse_episode_number(title),
                chapter_word_number=int(item.get("chapter_word_number", 0))
            ))
        total = data.get("total", 0)
        if isinstance(total, str):
            total = int(total) if total.isdigit() else 0
        return EpisodeList(
            code=data.get("code", 0),
            book_name=data.get("book_name", ""),
            episodes=episodes,
            total=total,
            book_id=str(data.get("book_id", "")),
            author=data.get("author", ""),
            category=data.get("category", ""),
            desc=data.get("desc", ""),
            duration=data.get("duration", ""),
            book_pic=data.get("book_pic", "")
        )
    
    def _parse_video_info(self, json_str: str) -> VideoInfo:
        data = json.loads(json_str)
        video_data = data.get("data", {})
        info = video_data.get("info", {})
        return VideoInfo(
            code=data.get("code", 0),
            url=video_data.get("url", ""),
            pic=video_data.get("pic", ""),
            quality=info.get("quality", ""),
            title=video_data.get("title", ""),
            duration=info.get("duration", ""),
            size_str=info.get("size_str", "")
        )
    
    def _parse_drama_item(self, item: dict) -> DramaInfo:
        return DramaInfo(
            book_id=str(item.get("book_id", "")),
            title=item.get("title", ""),
            cover=item.get("cover", ""),
            episode_cnt=int(item.get("episode_cnt", 0)),
            intro=item.get("intro", ""),
            type=item.get("type", ""),
            author=item.get("author", ""),
            play_cnt=int(item.get("play_cnt", 0))
        )
    
    @staticmethod
    def _parse_episode_number(title: str) -> int:
        match = re.search(r'第(\d+)集', title)
        if match:
            return int(match.group(1))
        match = re.search(r'(\d+)', title)
        if match:
            return int(match.group(1))
        return 0
