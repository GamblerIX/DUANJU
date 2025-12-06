from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Callable


class ThemeMode(Enum):
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class PlaybackState(Enum):
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    BUFFERING = "buffering"
    ERROR = "error"


class ErrorType(Enum):
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    PARSE_ERROR = "parse_error"
    API_ERROR = "api_error"
    VIDEO_ERROR = "video_error"
    CONFIG_ERROR = "config_error"


@dataclass
class DramaInfo:
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
        return self.title
    
    @property
    def cover_url(self) -> str:
        return self.cover
    
    @property
    def episode_count(self) -> int:
        return self.episode_cnt
    
    @property
    def description(self) -> str:
        return self.intro
    
    @property
    def category(self) -> str:
        return self.type

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DramaInfo):
            return NotImplemented
        return (self.book_id == other.book_id and self.title == other.title and
                self.cover == other.cover and self.episode_cnt == other.episode_cnt and
                self.intro == other.intro and self.type == other.type and
                self.author == other.author and self.play_cnt == other.play_cnt)


@dataclass
class EpisodeInfo:
    video_id: str
    title: str
    episode_number: int = 0
    chapter_word_number: int = 0

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EpisodeInfo):
            return NotImplemented
        return (self.video_id == other.video_id and self.title == other.title and
                self.episode_number == other.episode_number and
                self.chapter_word_number == other.chapter_word_number)


@dataclass
class VideoInfo:
    code: int
    url: str
    pic: str = ""
    quality: str = ""
    title: str = ""
    duration: str = ""
    size_str: str = ""
    
    @property
    def video_url(self) -> str:
        return self.url
    
    @property
    def cover_url(self) -> str:
        return self.pic


@dataclass
class SearchResult:
    code: int
    msg: str = ""
    data: List[DramaInfo] = field(default_factory=list)
    page: int = 1
    
    @property
    def title(self) -> str:
        return self.msg
    
    @property
    def current_page(self) -> int:
        return self.page
    
    @property
    def total_pages(self) -> int:
        return 1


@dataclass
class EpisodeList:
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
        return self.book_name


@dataclass
class CategoryResult:
    code: int
    category: str
    data: List[DramaInfo] = field(default_factory=list)
    offset: int = 1


@dataclass
class ApiError:
    code: int
    message: str
    details: str = ""

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ApiError):
            return NotImplemented
        return (self.code == other.code and self.message == other.message and
                self.details == other.details)


@dataclass
class AppConfig:
    api_timeout: int = 10000
    default_quality: str = "1080p"
    theme_mode: ThemeMode = ThemeMode.AUTO
    last_search_keyword: str = ""
    search_history: List[str] = field(default_factory=list)
    max_search_history: int = 20

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AppConfig):
            return NotImplemented
        return (self.api_timeout == other.api_timeout and
                self.default_quality == other.default_quality and
                self.theme_mode == other.theme_mode and
                self.last_search_keyword == other.last_search_keyword and
                self.search_history == other.search_history and
                self.max_search_history == other.max_search_history)


@dataclass
class ErrorItem:
    error_type: ErrorType
    message: str
    timestamp: float
    retryable: bool = False
    retry_callback: Optional[Callable[[], None]] = None


@dataclass
class CacheEntry:
    data: str
    timestamp: float
    ttl: int

    def is_expired(self, current_time: float) -> bool:
        elapsed = (current_time - self.timestamp) * 1000
        return elapsed > self.ttl


@dataclass
class ApiResponse:
    status_code: int
    body: str
    error: str = ""
    success: bool = False


@dataclass
class FavoriteItem:
    drama: DramaInfo
    added_time: float

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FavoriteItem):
            return NotImplemented
        return self.drama == other.drama and self.added_time == other.added_time


@dataclass
class HistoryItem:
    drama: DramaInfo
    episode_number: int
    position_ms: int
    watch_time: float

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, HistoryItem):
            return NotImplemented
        return (self.drama == other.drama and self.episode_number == other.episode_number and
                self.position_ms == other.position_ms and self.watch_time == other.watch_time)
