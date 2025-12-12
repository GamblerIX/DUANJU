"""Core data models - 核心数据模型

This module defines all data models used throughout the application.
Models are implemented as dataclasses for clean, type-safe data structures.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Callable


class ThemeMode(Enum):
    """主题模式枚举"""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class PlaybackState(Enum):
    """播放状态枚举"""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    BUFFERING = "buffering"
    ERROR = "error"


class ErrorType(Enum):
    """错误类型枚举"""
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    PARSE_ERROR = "parse_error"
    API_ERROR = "api_error"
    VIDEO_ERROR = "video_error"
    CONFIG_ERROR = "config_error"


@dataclass
class DramaInfo:
    """短剧信息数据模型
    
    字段映射 (API 字段 -> 模型字段):
        - book_id -> book_id
        - title -> title
        - cover -> cover
        - episode_cnt -> episode_cnt
        - intro -> intro
        - type -> type
        - author -> author
        - play_cnt -> play_cnt
    """
    book_id: str
    title: str
    cover: str
    episode_cnt: int = 0
    intro: str = ""
    type: str = ""
    author: str = ""
    play_cnt: int = 0
    
    @property
    def name(self) -> str:
        """向后兼容: 返回 title"""
        return self.title
    
    @property
    def cover_url(self) -> str:
        """向后兼容: 返回 cover"""
        return self.cover
    
    @property
    def episode_count(self) -> int:
        """向后兼容: 返回 episode_cnt"""
        return self.episode_cnt
    
    @property
    def description(self) -> str:
        """向后兼容: 返回 intro"""
        return self.intro
    
    @property
    def category(self) -> str:
        """向后兼容: 返回 type"""
        return self.type

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DramaInfo):
            return NotImplemented
        return (self.book_id == other.book_id and
                self.title == other.title and
                self.cover == other.cover and
                self.episode_cnt == other.episode_cnt and
                self.intro == other.intro and
                self.type == other.type and
                self.author == other.author and
                self.play_cnt == other.play_cnt)


@dataclass
class EpisodeInfo:
    """剧集信息数据模型
    
    字段映射 (API 字段 -> 模型字段):
        - video_id -> video_id
        - title -> title
        - chapter_word_number -> chapter_word_number
    """
    video_id: str
    title: str
    episode_number: int = 0
    chapter_word_number: int = 0

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EpisodeInfo):
            return NotImplemented
        return (self.video_id == other.video_id and
                self.title == other.title and
                self.episode_number == other.episode_number and
                self.chapter_word_number == other.chapter_word_number)


@dataclass
class VideoInfo:
    """视频信息数据模型
    
    字段映射 (API 字段 -> 模型字段):
        - data.url -> url
        - data.pic -> pic
        - data.info.quality -> quality
        - data.title -> title
        - data.info.duration -> duration
        - data.info.size_str -> size_str
    """
    code: int
    url: str
    pic: str = ""
    quality: str = ""
    title: str = ""
    duration: str = ""
    size_str: str = ""
    
    @property
    def video_url(self) -> str:
        """向后兼容: 返回 url"""
        return self.url
    
    @property
    def cover_url(self) -> str:
        """向后兼容: 返回 pic"""
        return self.pic


@dataclass
class SearchResult:
    """搜索结果数据模型"""
    code: int
    msg: str = ""
    data: List[DramaInfo] = field(default_factory=list)
    page: int = 1
    
    @property
    def title(self) -> str:
        """向后兼容: 返回 msg"""
        return self.msg
    
    @property
    def current_page(self) -> int:
        """向后兼容: 返回 page"""
        return self.page
    
    @property
    def total_pages(self) -> int:
        """向后兼容: API 不返回总页数，返回 1"""
        return 1


@dataclass
class EpisodeList:
    """剧集列表数据模型"""
    code: int
    book_name: str
    episodes: List[EpisodeInfo] = field(default_factory=list)
    total: int = 0
    book_id: str = ""
    author: str = ""
    category: str = ""
    desc: str = ""
    duration: str = ""
    book_pic: str = ""
    
    @property
    def drama_name(self) -> str:
        """向后兼容: 返回 book_name"""
        return self.book_name


@dataclass
class CategoryResult:
    """分类结果数据模型"""
    code: int
    category: str
    data: List[DramaInfo] = field(default_factory=list)
    offset: int = 1


@dataclass
class ApiError:
    """API错误数据模型"""
    code: int
    message: str
    details: str = ""

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ApiError):
            return NotImplemented
        return (self.code == other.code and
                self.message == other.message and
                self.details == other.details)


@dataclass
class AppConfig:
    """应用配置数据模型"""
    api_timeout: int = 10000
    default_quality: str = "1080p"
    theme_mode: ThemeMode = ThemeMode.AUTO
    last_search_keyword: str = ""
    search_history: List[str] = field(default_factory=list)
    max_search_history: int = 20
    # 新增配置项
    current_provider: str = "cenguigui"
    enable_cache: bool = True
    cache_ttl: int = 300000
    max_retries: int = 3
    retry_delay: int = 1000

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AppConfig):
            return NotImplemented
        return (self.api_timeout == other.api_timeout and
                self.default_quality == other.default_quality and
                self.theme_mode == other.theme_mode and
                self.last_search_keyword == other.last_search_keyword and
                self.search_history == other.search_history and
                self.max_search_history == other.max_search_history and
                self.current_provider == other.current_provider and
                self.enable_cache == other.enable_cache and
                self.cache_ttl == other.cache_ttl and
                self.max_retries == other.max_retries and
                self.retry_delay == other.retry_delay)


@dataclass
class ErrorItem:
    """错误队列项"""
    error_type: ErrorType
    message: str
    timestamp: float
    retryable: bool = False
    retry_callback: Optional[Callable[[], None]] = None


@dataclass
class CacheEntry:
    """缓存条目"""
    data: str
    timestamp: float
    ttl: int

    def is_expired(self, current_time: float) -> bool:
        """检查缓存是否过期"""
        elapsed = (current_time - self.timestamp) * 1000
        return elapsed > self.ttl


@dataclass
class ApiResponse:
    """API 响应数据结构"""
    status_code: int
    body: str
    error: str = ""
    success: bool = False


@dataclass
class FavoriteItem:
    """收藏项"""
    drama: DramaInfo
    added_time: float

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FavoriteItem):
            return NotImplemented
        return (self.drama == other.drama and
                self.added_time == other.added_time)


@dataclass
class HistoryItem:
    """观看历史项"""
    drama: DramaInfo
    episode_number: int
    position_ms: int
    watch_time: float

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, HistoryItem):
            return NotImplemented
        return (self.drama == other.drama and
                self.episode_number == other.episode_number and
                self.position_ms == other.position_ms and
                self.watch_time == other.watch_time)
