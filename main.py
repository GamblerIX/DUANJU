import sys
import os
import re
import json
import time
import hashlib
import threading
import subprocess
import webbrowser
import asyncio
import aiohttp
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum

# 修复 PyAppify 打包后 PATH 环境变量缺失的问题
if 'PATH' not in os.environ:
    os.environ['PATH'] = ''


def get_base_path() -> str:
    """获取应用程序基础路径，兼容打包和开发环境"""
    if getattr(sys, 'frozen', False):
        # PyInstaller/PyAppify 打包后
        return os.path.dirname(sys.executable)
    else:
        # 开发环境
        return os.path.dirname(os.path.abspath(__file__))


BASE_PATH = get_base_path()

from PySide6.QtCore import (
    Qt, QObject, Signal, QTimer, QThread, QUrl
)
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QGridLayout, QFileDialog, QMessageBox, QDialog, QListWidget, QListWidgetItem
)
from PySide6.QtGui import (
    QFont, QPixmap, QImage, QPainter, QPainterPath, QIcon, QDesktopServices
)
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from qfluentwidgets import (
    FluentWindow, NavigationItemPosition, FluentIcon, setTheme, Theme, isDarkTheme,
    BodyLabel, CaptionLabel, SubtitleLabel, ToolButton, PushButton, PrimaryPushButton,
    ScrollArea, SearchLineEdit, FlowLayout, Pivot, InfoBar, InfoBarPosition,
    Slider, ProgressBar, IndeterminateProgressRing, PipsPager, PipsScrollButtonDisplayMode,
    CardWidget, SettingCardGroup, SettingCard, ComboBox, CheckBox, RadioButton,
    MessageBoxBase, qconfig
)


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


class DownloadStatus(Enum):
    PENDING = "pending"
    FETCHING = "fetching"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


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
                self.cover == other.cover and self.episode_cnt == other.episode_cnt)


@dataclass
class EpisodeInfo:
    video_id: str
    title: str
    episode_number: int = 0
    chapter_word_number: int = 0

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EpisodeInfo):
            return NotImplemented
        return self.video_id == other.video_id and self.title == other.title


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


@dataclass
class AppConfig:
    api_timeout: int = 10000
    default_quality: str = "1080p"
    theme_mode: ThemeMode = ThemeMode.AUTO
    last_search_keyword: str = ""
    search_history: List[str] = field(default_factory=list)
    max_search_history: int = 20


@dataclass
class CacheEntry:
    data: str
    timestamp: float
    ttl: int

    def is_expired(self, current_time: float) -> bool:
        return (current_time - self.timestamp) * 1000 > self.ttl


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


@dataclass
class HistoryItem:
    drama: DramaInfo
    episode_number: int
    position_ms: int
    watch_time: float


@dataclass
class DownloadTask:
    drama: DramaInfo
    episode: EpisodeInfo
    status: DownloadStatus = DownloadStatus.PENDING
    progress: float = 0.0
    video_url: str = ""
    file_path: str = ""
    error: str = ""
    downloaded_bytes: int = 0
    total_bytes: int = 0

    @property
    def id(self) -> str:
        return f"{self.drama.book_id}_{self.episode.video_id}"


class ThemeManager(QObject):
    theme_changed = Signal(object)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._current_mode = ThemeMode.AUTO

    def get_current_theme(self) -> ThemeMode:
        return self._current_mode

    def set_theme(self, mode: ThemeMode) -> None:
        self._current_mode = mode
        if mode == ThemeMode.LIGHT:
            setTheme(Theme.LIGHT)
        elif mode == ThemeMode.DARK:
            setTheme(Theme.DARK)
        else:
            setTheme(Theme.AUTO)
        self.theme_changed.emit(mode)

    def is_dark(self) -> bool:
        return isDarkTheme()

    @property
    def current_mode(self) -> ThemeMode:
        return self._current_mode


def format_duration(milliseconds: int) -> str:
    if milliseconds < 0:
        milliseconds = 0
    total_seconds = milliseconds // 1000
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def truncate(s: str, max_length: int, suffix: str = "...") -> str:
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix


def sanitize_filename(filename: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '_', filename)


class AsyncWorker(QThread):
    finished_signal = Signal(object)
    error_signal = Signal(object)

    def __init__(self, coro_func: Callable[..., Any], *args, parent: Optional[QObject] = None, **kwargs):
        super().__init__(parent)
        self._coro_func = coro_func
        self._args = args
        self._kwargs = kwargs

    def run(self) -> None:
        loop: Optional[asyncio.AbstractEventLoop] = None
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            coro = self._coro_func(*self._args, **self._kwargs)
            result = loop.run_until_complete(coro)
            self.finished_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(e)
        finally:
            if loop is not None:
                try:
                    pending = asyncio.all_tasks(loop)
                    for task in pending:
                        task.cancel()
                    if pending:
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    loop.run_until_complete(loop.shutdown_asyncgens())
                except Exception:
                    pass
                finally:
                    loop.close()
                    asyncio.set_event_loop(None)


class ApiClient:
    DEFAULT_BASE_URL = "https://api.cenguigui.cn/api/duanju/api.php"
    DEFAULT_TIMEOUT = 10000

    def __init__(self, base_url: Optional[str] = None, timeout: int = DEFAULT_TIMEOUT):
        self._base_url = base_url or self.DEFAULT_BASE_URL
        self._timeout = timeout

    def _create_session(self, loop: asyncio.AbstractEventLoop) -> aiohttp.ClientSession:
        timeout = aiohttp.ClientTimeout(total=self._timeout / 1000)
        connector = aiohttp.TCPConnector(force_close=True)
        return aiohttp.ClientSession(timeout=timeout, connector=connector, connector_owner=True)

    async def get(self, endpoint: str = "", params: Optional[Dict[str, str]] = None) -> ApiResponse:
        url = self._base_url
        loop = asyncio.get_running_loop()
        session = self._create_session(loop)
        try:
            async with session:
                try:
                    async with session.get(url, params=params) as response:
                        body = await response.text()
                        success = 200 <= response.status < 300
                        return ApiResponse(status_code=response.status, body=body, success=success)
                except asyncio.TimeoutError:
                    return ApiResponse(status_code=0, body="", error="请求超时", success=False)
                except aiohttp.ClientError as e:
                    return ApiResponse(status_code=0, body="", error=str(e), success=False)
        except Exception as e:
            return ApiResponse(status_code=0, body="", error=str(e), success=False)

    def set_timeout(self, milliseconds: int) -> None:
        self._timeout = max(1000, min(60000, milliseconds))

    @property
    def timeout(self) -> int:
        return self._timeout


class ResponseParser:
    @staticmethod
    def parse_search_result(json_str: str) -> SearchResult:
        data = json.loads(json_str)
        dramas = []
        for item in data.get("data", []):
            dramas.append(DramaInfo(
                book_id=str(item.get("book_id", "")), title=item.get("title", ""),
                cover=item.get("cover", ""), episode_cnt=int(item.get("episode_cnt", 0)),
                intro=item.get("intro", ""), type=item.get("type", ""),
                author=item.get("author", ""), play_cnt=int(item.get("play_cnt", 0))
            ))
        page = data.get("page", 1)
        if isinstance(page, str):
            page = int(page) if page.isdigit() else 1
        return SearchResult(code=data.get("code", 0), msg=data.get("msg", ""), data=dramas, page=page)

    @staticmethod
    def parse_episode_number(title: str) -> int:
        match = re.search(r'第(\d+)集', title)
        if match:
            return int(match.group(1))
        match = re.search(r'(\d+)', title)
        if match:
            return int(match.group(1))
        return 0

    @staticmethod
    def parse_episode_list(json_str: str) -> EpisodeList:
        data = json.loads(json_str)
        episodes = []
        for item in data.get("data", []):
            title = item.get("title", "")
            episodes.append(EpisodeInfo(
                video_id=str(item.get("video_id", "")), title=title,
                episode_number=ResponseParser.parse_episode_number(title),
                chapter_word_number=int(item.get("chapter_word_number", 0))
            ))
        total = data.get("total", 0)
        if isinstance(total, str):
            total = int(total) if total.isdigit() else 0
        return EpisodeList(
            code=data.get("code", 0), book_name=data.get("book_name", ""),
            episodes=episodes, total=total, book_id=str(data.get("book_id", "")),
            author=data.get("author", ""), category=data.get("category", ""),
            desc=data.get("desc", ""), duration=data.get("duration", ""),
            book_pic=data.get("book_pic", "")
        )

    @staticmethod
    def parse_video_info(json_str: str) -> VideoInfo:
        data = json.loads(json_str)
        video_data = data.get("data", {})
        info = video_data.get("info", {})
        return VideoInfo(
            code=data.get("code", 0), url=video_data.get("url", ""),
            pic=video_data.get("pic", ""), quality=info.get("quality", ""),
            title=video_data.get("title", ""), duration=info.get("duration", ""),
            size_str=info.get("size_str", "")
        )

    @staticmethod
    def parse_category_result(json_str: str, category: str = "") -> CategoryResult:
        data = json.loads(json_str)
        dramas = []
        for item in data.get("data", []):
            dramas.append(DramaInfo(
                book_id=str(item.get("book_id", "")), title=item.get("title", ""),
                cover=item.get("cover", ""), episode_cnt=int(item.get("episode_cnt", 0)),
                intro=item.get("video_desc", ""), type=item.get("sub_title", category),
                author="", play_cnt=int(item.get("play_cnt", 0))
            ))
        return CategoryResult(code=data.get("code", 0), category=category, data=dramas, offset=1)

    @staticmethod
    def parse_recommendations(json_str: str) -> List[DramaInfo]:
        data = json.loads(json_str)
        dramas = []
        for item in data.get("data", []):
            book_data = item.get("book_data", {})
            serial_count = book_data.get("serial_count", 0)
            if isinstance(serial_count, str):
                serial_count = int(serial_count) if serial_count.isdigit() else 0
            dramas.append(DramaInfo(
                book_id=str(book_data.get("book_id", "")), title=book_data.get("book_name", ""),
                cover=book_data.get("thumb_url", ""), episode_cnt=serial_count,
                intro="", type=book_data.get("category", ""),
                author="", play_cnt=int(item.get("hot", 0))
            ))
        return dramas


class CacheManager:
    DEFAULT_TTL = 300000

    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()

    def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        with self._lock:
            self._cache[key] = CacheEntry(data=value, timestamp=time.time(), ttl=ttl or self.DEFAULT_TTL)

    def get(self, key: str) -> Optional[str]:
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            if entry.is_expired(time.time()):
                del self._cache[key]
                return None
            return entry.data

    def remove(self, key: str) -> None:
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    @staticmethod
    def generate_key(*args: str) -> str:
        key_str = ":".join(str(arg) for arg in args)
        return hashlib.md5(key_str.encode()).hexdigest()


def serialize_config(config: AppConfig) -> str:
    data = {
        "apiTimeout": config.api_timeout, "defaultQuality": config.default_quality,
        "themeMode": config.theme_mode.value, "lastSearchKeyword": config.last_search_keyword,
        "searchHistory": config.search_history, "maxSearchHistory": config.max_search_history
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def deserialize_config(json_str: str) -> AppConfig:
    data = json.loads(json_str)
    return AppConfig(
        api_timeout=data.get("apiTimeout", 10000), default_quality=data.get("defaultQuality", "1080p"),
        theme_mode=ThemeMode(data.get("themeMode", "auto")), last_search_keyword=data.get("lastSearchKeyword", ""),
        search_history=data.get("searchHistory", []), max_search_history=data.get("maxSearchHistory", 20)
    )


def serialize_drama(drama: DramaInfo) -> Dict[str, Any]:
    return {"book_id": drama.book_id, "title": drama.title, "cover": drama.cover,
            "episode_cnt": drama.episode_cnt, "intro": drama.intro, "type": drama.type,
            "author": drama.author, "play_cnt": drama.play_cnt}


def deserialize_drama(data: Dict[str, Any]) -> DramaInfo:
    return DramaInfo(
        book_id=data.get("book_id", data.get("bookId", "")), title=data.get("title", data.get("name", "")),
        cover=data.get("cover", data.get("coverUrl", "")), episode_cnt=data.get("episode_cnt", data.get("episodeCount", 0)),
        intro=data.get("intro", data.get("description", "")), type=data.get("type", data.get("category", "")),
        author=data.get("author", ""), play_cnt=data.get("play_cnt", 0)
    )


class ConfigManager:
    DEFAULT_CONFIG_PATH = os.path.join(BASE_PATH, "config", "config.json")

    def __init__(self, config_path: Optional[str] = None):
        self._config_path = Path(config_path or self.DEFAULT_CONFIG_PATH)
        self._config: AppConfig = AppConfig()
        self._load_config()

    def _load_config(self) -> None:
        try:
            if self._config_path.exists():
                json_str = self._config_path.read_text(encoding='utf-8')
                self._config = deserialize_config(json_str)
            else:
                self._config = AppConfig()
                self._save_config()
        except (json.JSONDecodeError, ValueError):
            self._config = AppConfig()
            self._save_config()

    def _save_config(self) -> None:
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        json_str = serialize_config(self._config)
        self._config_path.write_text(json_str, encoding='utf-8')

    def save(self, config: Optional[AppConfig] = None) -> None:
        if config:
            self._config = config
        self._save_config()

    @property
    def config(self) -> AppConfig:
        return self._config

    @property
    def api_timeout(self) -> int:
        return self._config.api_timeout

    @api_timeout.setter
    def api_timeout(self, value: int) -> None:
        self._config.api_timeout = max(1000, min(60000, value))
        self._save_config()

    @property
    def default_quality(self) -> str:
        return self._config.default_quality

    @default_quality.setter
    def default_quality(self, value: str) -> None:
        if value in ["360p", "480p", "720p", "1080p", "2160p"]:
            self._config.default_quality = value
            self._save_config()

    @property
    def theme_mode(self) -> ThemeMode:
        return self._config.theme_mode

    @theme_mode.setter
    def theme_mode(self, value: ThemeMode) -> None:
        self._config.theme_mode = value
        self._save_config()

    @property
    def last_search_keyword(self) -> str:
        return self._config.last_search_keyword

    @last_search_keyword.setter
    def last_search_keyword(self, value: str) -> None:
        self._config.last_search_keyword = value
        self._save_config()

    @property
    def search_history(self) -> List[str]:
        return self._config.search_history.copy()

    def add_search_history(self, keyword: str) -> None:
        history = self._config.search_history
        if keyword in history:
            history.remove(keyword)
        history.insert(0, keyword)
        self._config.search_history = history[:self._config.max_search_history]
        self._save_config()


class FavoritesManager:
    DEFAULT_PATH = os.path.join(BASE_PATH, "data", "favorites.json")

    def __init__(self, file_path: Optional[str] = None):
        self._file_path = Path(file_path or self.DEFAULT_PATH)
        self._favorites: List[FavoriteItem] = []
        self._load()

    def _load(self) -> None:
        try:
            if self._file_path.exists():
                data = json.loads(self._file_path.read_text(encoding='utf-8'))
                self._favorites = []
                for item in data.get("favorites", []):
                    drama = deserialize_drama(item.get("drama", {}))
                    added_time = item.get("addedTime", time.time())
                    self._favorites.append(FavoriteItem(drama, added_time))
        except (json.JSONDecodeError, KeyError):
            self._favorites = []

    def _save(self) -> None:
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        data = {"favorites": [{"drama": serialize_drama(item.drama), "addedTime": item.added_time} for item in self._favorites]}
        self._file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    def add(self, drama: DramaInfo) -> bool:
        if self.is_favorite(drama.book_id):
            return False
        self._favorites.append(FavoriteItem(drama, time.time()))
        self._save()
        return True

    def remove(self, book_id: str) -> bool:
        for i, item in enumerate(self._favorites):
            if item.drama.book_id == book_id:
                del self._favorites[i]
                self._save()
                return True
        return False

    def is_favorite(self, book_id: str) -> bool:
        return any(item.drama.book_id == book_id for item in self._favorites)

    def get_all(self) -> List[DramaInfo]:
        return [item.drama for item in self._favorites]

    def get_ids(self) -> Set[str]:
        return {item.drama.book_id for item in self._favorites}

    def clear(self) -> None:
        self._favorites.clear()
        self._save()

    def count(self) -> int:
        return len(self._favorites)


class HistoryManager:
    DEFAULT_PATH = os.path.join(BASE_PATH, "data", "history.json")
    MAX_HISTORY = 100

    def __init__(self, file_path: Optional[str] = None, max_items: int = MAX_HISTORY):
        self._file_path = Path(file_path or self.DEFAULT_PATH)
        self._max_items = max_items
        self._history: List[HistoryItem] = []
        self._load()

    def _load(self) -> None:
        try:
            if self._file_path.exists():
                data = json.loads(self._file_path.read_text(encoding='utf-8'))
                self._history = []
                for item in data.get("history", []):
                    drama = deserialize_drama(item.get("drama", {}))
                    self._history.append(HistoryItem(
                        drama=drama, episode_number=item.get("episodeNumber", 1),
                        position_ms=item.get("positionMs", 0), watch_time=item.get("watchTime", time.time())
                    ))
        except (json.JSONDecodeError, KeyError):
            self._history = []

    def _save(self) -> None:
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        data = {"history": [{"drama": serialize_drama(item.drama), "episodeNumber": item.episode_number,
                            "positionMs": item.position_ms, "watchTime": item.watch_time} for item in self._history]}
        self._file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    def add(self, drama: DramaInfo, episode_number: int, position_ms: int = 0) -> None:
        for i, item in enumerate(self._history):
            if item.drama.book_id == drama.book_id:
                self._history[i] = HistoryItem(drama=drama, episode_number=episode_number, position_ms=position_ms, watch_time=time.time())
                self._history.insert(0, self._history.pop(i))
                self._save()
                return
        self._history.insert(0, HistoryItem(drama=drama, episode_number=episode_number, position_ms=position_ms, watch_time=time.time()))
        if len(self._history) > self._max_items:
            self._history = self._history[:self._max_items]
        self._save()

    def get_all(self) -> List[HistoryItem]:
        return self._history.copy()

    def remove(self, book_id: str) -> bool:
        for i, item in enumerate(self._history):
            if item.drama.book_id == book_id:
                del self._history[i]
                self._save()
                return True
        return False

    def clear(self) -> None:
        self._history.clear()
        self._save()

    def count(self) -> int:
        return len(self._history)


class ImageLoader(QObject):
    image_loaded = Signal(str, QPixmap)
    image_failed = Signal(str, str)
    CACHE_DIR = os.path.join(BASE_PATH, "cache", "images")
    MEMORY_CACHE_SIZE = 50

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._memory_cache: Dict[str, QPixmap] = {}
        self._cache_order: list = []
        self._cache_dir = Path(self.CACHE_DIR)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._loading: set = set()
        self._pending_callbacks: Dict[str, list] = {}
        self._network_manager = QNetworkAccessManager(self)
        self._network_manager.finished.connect(self._on_network_finished)

    def load(self, url: str, callback: Optional[Callable[[QPixmap], None]] = None) -> Optional[QPixmap]:
        if not url:
            return None
        if url in self._memory_cache:
            self._update_lru(url)
            pixmap = self._memory_cache[url]
            if callback:
                callback(pixmap)
            return pixmap
        cache_path = self._get_cache_path(url)
        if cache_path.exists():
            pixmap = QPixmap(str(cache_path))
            if not pixmap.isNull():
                self._add_to_memory_cache(url, pixmap)
                if callback:
                    callback(pixmap)
                return pixmap
        if url not in self._loading:
            self._loading.add(url)
            self._pending_callbacks[url] = []
            if callback:
                self._pending_callbacks[url].append(callback)
            request = QNetworkRequest(QUrl(url))
            request.setRawHeader(b"User-Agent", b"Mozilla/5.0")
            reply = self._network_manager.get(request)
            reply.setProperty("url", url)
        elif callback:
            if url in self._pending_callbacks:
                self._pending_callbacks[url].append(callback)
        return None

    def _on_network_finished(self, reply: QNetworkReply) -> None:
        url = reply.property("url")
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll()
            image = QImage()
            image.loadFromData(data.data())
            pixmap = QPixmap.fromImage(image)
            if not pixmap.isNull():
                cache_path = self._get_cache_path(url)
                pixmap.save(str(cache_path))
                self._add_to_memory_cache(url, pixmap)
                self.image_loaded.emit(url, pixmap)
                for callback in self._pending_callbacks.get(url, []):
                    callback(pixmap)
            else:
                self.image_failed.emit(url, "Invalid image data")
        else:
            self.image_failed.emit(url, reply.errorString())
        self._loading.discard(url)
        self._pending_callbacks.pop(url, None)
        reply.deleteLater()

    def _get_cache_path(self, url: str) -> Path:
        url_hash = hashlib.md5(url.encode()).hexdigest()
        ext = url.split('.')[-1].split('?')[0]
        if ext not in ('jpg', 'jpeg', 'png', 'gif', 'webp'):
            ext = 'jpg'
        return self._cache_dir / f"{url_hash}.{ext}"

    def _add_to_memory_cache(self, url: str, pixmap: QPixmap) -> None:
        if url in self._memory_cache:
            self._update_lru(url)
            return
        while len(self._memory_cache) >= self.MEMORY_CACHE_SIZE:
            if self._cache_order:
                old_url = self._cache_order.pop(0)
                self._memory_cache.pop(old_url, None)
        self._memory_cache[url] = pixmap
        self._cache_order.append(url)

    def _update_lru(self, url: str) -> None:
        if url in self._cache_order:
            self._cache_order.remove(url)
            self._cache_order.append(url)

    def clear_memory_cache(self) -> None:
        self._memory_cache.clear()
        self._cache_order.clear()

    def clear_disk_cache(self) -> None:
        for file in self._cache_dir.glob("*"):
            try:
                file.unlink()
            except:
                pass


class SearchService(QObject):
    search_started = Signal()
    search_completed = Signal(object)
    search_error = Signal(object)
    CACHE_TTL = 300000

    def __init__(self, api_client: ApiClient, cache: CacheManager, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._api_client = api_client
        self._cache = cache
        self._is_searching = False
        self._current_keyword = ""
        self._current_worker: Optional[AsyncWorker] = None

    def search(self, keyword: str, page: int = 1) -> None:
        if not keyword or not keyword.strip():
            return
        self.cancel_search()
        self._current_keyword = keyword.strip()
        self._is_searching = True
        self.search_started.emit()
        cache_key = CacheManager.generate_key("search", self._current_keyword, str(page))
        cached = self._cache.get(cache_key)
        if cached:
            try:
                result = ResponseParser.parse_search_result(cached)
                self._is_searching = False
                self.search_completed.emit(result)
                return
            except Exception:
                pass
        self._current_worker = AsyncWorker(self._do_search, self._current_keyword, page, cache_key, parent=self)
        self._current_worker.finished_signal.connect(self._on_search_result)
        self._current_worker.error_signal.connect(self._on_search_error)
        self._current_worker.start()

    async def _do_search(self, keyword: str, page: int, cache_key: str):
        response = await self._api_client.get(params={"name": keyword, "page": str(page)})
        if response.success:
            self._cache.set(cache_key, response.body, self.CACHE_TTL)
            return ResponseParser.parse_search_result(response.body)
        else:
            raise Exception(response.error or "搜索失败")

    def _on_search_result(self, result: SearchResult) -> None:
        if not self._is_searching:
            return
        self._is_searching = False
        self.search_completed.emit(result)

    def _on_search_error(self, e: Exception) -> None:
        self._is_searching = False
        self.search_error.emit(ApiError(code=0, message=str(e), details=""))

    def cancel_search(self) -> None:
        self._is_searching = False
        if self._current_worker and self._current_worker.isRunning():
            self._current_worker.terminate()
            self._current_worker.wait()
        self._current_worker = None

    @property
    def current_keyword(self) -> str:
        return self._current_keyword


class VideoService(QObject):
    episodes_loaded = Signal(object)
    video_url_loaded = Signal(object)
    error = Signal(object)
    loading_started = Signal()

    def __init__(self, api_client: ApiClient, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._api_client = api_client
        self._current_worker: Optional[AsyncWorker] = None
        self._is_loading = False

    def fetch_episodes(self, book_id: str) -> None:
        self.cancel()
        self._is_loading = True
        self.loading_started.emit()
        self._current_worker = AsyncWorker(self._do_fetch_episodes, book_id, parent=self)
        self._current_worker.finished_signal.connect(self._on_episodes_result)
        self._current_worker.error_signal.connect(self._on_error)
        self._current_worker.start()

    async def _do_fetch_episodes(self, book_id: str):
        response = await self._api_client.get(params={"book_id": book_id})
        if response.success:
            return ("episodes", ResponseParser.parse_episode_list(response.body))
        else:
            raise Exception(response.error or "获取剧集失败")

    def _on_episodes_result(self, result) -> None:
        if not self._is_loading:
            return
        self._is_loading = False
        result_type, data = result
        if result_type == "episodes":
            self.episodes_loaded.emit(data)

    def fetch_video_url(self, video_id: str, quality: str = "1080p") -> None:
        self.cancel()
        self._is_loading = True
        self.loading_started.emit()
        self._current_worker = AsyncWorker(self._do_fetch_video_url, video_id, quality, parent=self)
        self._current_worker.finished_signal.connect(self._on_video_url_result)
        self._current_worker.error_signal.connect(self._on_error)
        self._current_worker.start()

    async def _do_fetch_video_url(self, video_id: str, quality: str):
        response = await self._api_client.get(params={"video_id": video_id, "level": quality, "type": "json"})
        if response.success:
            return ("video_url", ResponseParser.parse_video_info(response.body))
        else:
            raise Exception(response.error or "获取视频地址失败")

    def _on_video_url_result(self, result) -> None:
        if not self._is_loading:
            return
        self._is_loading = False
        result_type, data = result
        if result_type == "video_url":
            self.video_url_loaded.emit(data)

    def _on_error(self, e: Exception) -> None:
        self._is_loading = False
        self.error.emit(ApiError(code=0, message=str(e), details=""))

    def cancel(self) -> None:
        self._is_loading = False
        if self._current_worker and self._current_worker.isRunning():
            self._current_worker.terminate()
            self._current_worker.wait()
        self._current_worker = None


class CategoryService(QObject):
    categories_loaded = Signal(list)
    dramas_loaded = Signal(object)
    recommendations_loaded = Signal(list)
    error = Signal(object)
    loading_started = Signal()
    CACHE_TTL = 300000
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

    def __init__(self, api_client: ApiClient, cache: CacheManager, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._api_client = api_client
        self._cache = cache
        self._category_worker: Optional[AsyncWorker] = None
        self._recommendations_worker: Optional[AsyncWorker] = None
        self._is_loading_category = False
        self._is_loading_recommendations = False

    def fetch_categories(self) -> None:
        self.categories_loaded.emit(self.CATEGORIES)

    def fetch_category_dramas(self, category: str, offset: int = 1) -> None:
        self._cancel_category_worker()
        self._is_loading_category = True
        self.loading_started.emit()
        cache_key = CacheManager.generate_key("category", category, str(offset))
        cached = self._cache.get(cache_key)
        if cached:
            try:
                result = ResponseParser.parse_category_result(cached, category)
                self._is_loading_category = False
                self.dramas_loaded.emit(result)
                return
            except Exception:
                pass
        self._category_worker = AsyncWorker(self._do_fetch_category_dramas, category, offset, cache_key, parent=self)
        self._category_worker.finished_signal.connect(self._on_dramas_result)
        self._category_worker.error_signal.connect(self._on_dramas_error)
        self._category_worker.start()

    async def _do_fetch_category_dramas(self, category: str, offset: int, cache_key: str):
        response = await self._api_client.get(params={"classname": category, "offset": str(offset)})
        if response.success:
            self._cache.set(cache_key, response.body, self.CACHE_TTL)
            result = ResponseParser.parse_category_result(response.body, category)
            return ("dramas", result)
        else:
            raise Exception(response.error or "获取分类内容失败")

    def _on_dramas_result(self, result) -> None:
        if not self._is_loading_category:
            return
        self._is_loading_category = False
        result_type, data = result
        if result_type == "dramas":
            self.dramas_loaded.emit(data)

    def _on_dramas_error(self, e: Exception) -> None:
        self._is_loading_category = False
        self.error.emit(ApiError(code=0, message=str(e), details=""))

    def fetch_recommendations(self, force_refresh: bool = False) -> None:
        self._cancel_recommendations_worker()
        self._is_loading_recommendations = True
        cache_key = "recommendations"
        if force_refresh:
            self._cache.remove(cache_key)
        else:
            cached = self._cache.get(cache_key)
            if cached:
                try:
                    dramas = ResponseParser.parse_recommendations(cached)
                    self._is_loading_recommendations = False
                    self.recommendations_loaded.emit(dramas)
                    return
                except Exception:
                    pass
        self._recommendations_worker = AsyncWorker(self._do_fetch_recommendations, cache_key, parent=self)
        self._recommendations_worker.finished_signal.connect(self._on_recommendations_result)
        self._recommendations_worker.error_signal.connect(self._on_recommendations_error)
        self._recommendations_worker.start()

    async def _do_fetch_recommendations(self, cache_key: str):
        response = await self._api_client.get(params={"type": "recommend"})
        if response.success:
            self._cache.set(cache_key, response.body, self.CACHE_TTL)
            dramas = ResponseParser.parse_recommendations(response.body)
            return ("recommendations", dramas)
        else:
            raise Exception(response.error or "获取推荐失败")

    def _on_recommendations_result(self, result) -> None:
        if not self._is_loading_recommendations:
            return
        self._is_loading_recommendations = False
        result_type, data = result
        if result_type == "recommendations":
            self.recommendations_loaded.emit(data)

    def _on_recommendations_error(self, e: Exception) -> None:
        self._is_loading_recommendations = False
        self.error.emit(ApiError(code=0, message=str(e), details=""))

    def _cancel_category_worker(self) -> None:
        self._is_loading_category = False
        if self._category_worker and self._category_worker.isRunning():
            self._category_worker.terminate()
            self._category_worker.wait()
        self._category_worker = None

    def _cancel_recommendations_worker(self) -> None:
        self._is_loading_recommendations = False
        if self._recommendations_worker and self._recommendations_worker.isRunning():
            self._recommendations_worker.terminate()
            self._recommendations_worker.wait()
        self._recommendations_worker = None

    def cancel(self) -> None:
        self._cancel_category_worker()
        self._cancel_recommendations_worker()


class DownloadWorker(QThread):
    task_started = Signal(str)
    task_progress = Signal(str, float, int, int)
    task_completed = Signal(str)
    task_failed = Signal(str, str)
    video_info_fetched = Signal(str, str)

    def __init__(self, api_client: ApiClient, tasks: List[DownloadTask], download_dir: str, quality: str = "1080p", parent: Optional[QObject] = None):
        super().__init__(parent)
        self._api_client = api_client
        self._tasks = tasks
        self._download_dir = download_dir
        self._quality = quality
        self._cancelled = False

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._process_tasks())
        finally:
            loop.close()

    async def _process_tasks(self):
        for task in self._tasks:
            if self._cancelled:
                break
            self.task_started.emit(task.id)
            try:
                task.status = DownloadStatus.FETCHING
                video_url = await self._fetch_video_url(task.episode.video_id)
                if not video_url:
                    raise Exception("获取视频地址失败")
                task.video_url = video_url
                self.video_info_fetched.emit(task.id, video_url)
                if self._cancelled:
                    break
                task.status = DownloadStatus.DOWNLOADING
                await self._download_video(task)
                if not self._cancelled:
                    task.status = DownloadStatus.COMPLETED
                    task.progress = 100.0
                    self.task_completed.emit(task.id)
            except Exception as e:
                task.status = DownloadStatus.FAILED
                task.error = str(e)
                self.task_failed.emit(task.id, str(e))

    async def _fetch_video_url(self, video_id: str) -> str:
        response = await self._api_client.get(params={"video_id": video_id, "level": self._quality, "type": "json"})
        if response.success:
            video_info = ResponseParser.parse_video_info(response.body)
            return video_info.url
        return ""

    async def _download_video(self, task: DownloadTask):
        drama_dir = os.path.join(self._download_dir, sanitize_filename(task.drama.name))
        os.makedirs(drama_dir, exist_ok=True)
        filename = f"{task.episode.title}.mp4"
        file_path = os.path.join(drama_dir, sanitize_filename(filename))
        task.file_path = file_path
        timeout = aiohttp.ClientTimeout(total=3600)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(task.video_url) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")
                total_size = int(response.headers.get('content-length', 0))
                task.total_bytes = total_size
                downloaded = 0
                with open(file_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        if self._cancelled:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        task.downloaded_bytes = downloaded
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            task.progress = progress
                            self.task_progress.emit(task.id, progress, downloaded, total_size)

    def cancel(self):
        self._cancelled = True


class DownloadService(QObject):
    task_added = Signal(object)
    task_started = Signal(str)
    task_progress = Signal(str, float, int, int)
    task_completed = Signal(str)
    task_failed = Signal(str, str)
    all_completed = Signal()

    def __init__(self, api_client: ApiClient, download_dir: str, quality: str = "1080p", parent: Optional[QObject] = None):
        super().__init__(parent)
        self._api_client = api_client
        self._download_dir = download_dir
        self._quality = quality
        self._tasks: List[DownloadTask] = []
        self._worker: Optional[DownloadWorker] = None
        self._is_running = False

    def add_tasks(self, drama: DramaInfo, episodes: List[EpisodeInfo]) -> None:
        for episode in episodes:
            task = DownloadTask(drama=drama, episode=episode)
            if not any(t.id == task.id for t in self._tasks):
                self._tasks.append(task)
                self.task_added.emit(task)

    def start(self) -> None:
        if self._is_running:
            return
        pending_tasks = [t for t in self._tasks if t.status == DownloadStatus.PENDING]
        if not pending_tasks:
            return
        self._is_running = True
        self._worker = DownloadWorker(self._api_client, pending_tasks, self._download_dir, self._quality, self)
        self._worker.task_started.connect(self._on_task_started)
        self._worker.task_progress.connect(self._on_task_progress)
        self._worker.task_completed.connect(self._on_task_completed)
        self._worker.task_failed.connect(self._on_task_failed)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

    def cancel(self) -> None:
        if self._worker:
            self._worker.cancel()
            # 等待线程结束，如果超时则强制终止
            if not self._worker.wait(5000):
                self._worker.terminate()
                self._worker.wait()
            self._worker = None
            self._is_running = False

    def _on_task_started(self, task_id: str) -> None:
        self.task_started.emit(task_id)

    def _on_task_progress(self, task_id: str, progress: float, downloaded: int, total: int) -> None:
        for task in self._tasks:
            if task.id == task_id:
                task.progress = progress
                task.downloaded_bytes = downloaded
                task.total_bytes = total
                break
        self.task_progress.emit(task_id, progress, downloaded, total)

    def _on_task_completed(self, task_id: str) -> None:
        for task in self._tasks:
            if task.id == task_id:
                task.status = DownloadStatus.COMPLETED
                break
        self.task_completed.emit(task_id)

    def _on_task_failed(self, task_id: str, error: str) -> None:
        for task in self._tasks:
            if task.id == task_id:
                task.status = DownloadStatus.FAILED
                task.error = error
                break
        self.task_failed.emit(task_id, error)

    def _on_worker_finished(self) -> None:
        self._is_running = False
        self._worker = None
        self.all_completed.emit()

    def get_all_tasks(self) -> List[DownloadTask]:
        return self._tasks.copy()

    def clear_completed(self) -> None:
        self._tasks = [t for t in self._tasks if t.status != DownloadStatus.COMPLETED]

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def download_dir(self) -> str:
        return self._download_dir

    @download_dir.setter
    def download_dir(self, value: str) -> None:
        self._download_dir = value



# ==================== UI Controls ====================

class RoundedImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = None
        self._radius = (6, 6, 0, 0)

    def setPixmap(self, pixmap: QPixmap) -> None:
        self._pixmap = pixmap
        self.update()

    def paintEvent(self, event) -> None:
        if self._pixmap is None:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), self._radius[0], self._radius[0])
        painter.setClipPath(path)
        scaled = self._pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)


class DramaCard(QFrame):
    clicked = Signal(object)
    favorite_clicked = Signal(object, bool)
    CARD_WIDTH = 170
    CARD_HEIGHT = 330
    COVER_HEIGHT = 272

    def __init__(self, drama: DramaInfo, is_favorite: bool = False, parent: Optional[QFrame] = None):
        super().__init__(parent)
        self._drama = drama
        self._is_favorite = is_favorite
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setFixedSize(self.CARD_WIDTH, self.CARD_HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("DramaCard { background-color: transparent; border-radius: 8px; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 8)
        layout.setSpacing(4)
        self._cover_label = RoundedImageLabel()
        self._cover_label.setFixedSize(self.CARD_WIDTH, self.COVER_HEIGHT)
        layout.addWidget(self._cover_label)
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(8, 0, 8, 0)
        title_layout.setSpacing(4)
        self._title_label = BodyLabel(truncate(self._drama.name, 11))
        self._title_label.setWordWrap(False)
        title_layout.addWidget(self._title_label, 1)
        self._favorite_btn = ToolButton(FluentIcon.HEART)
        self._favorite_btn.setFixedSize(24, 24)
        self._favorite_btn.clicked.connect(self._on_favorite_clicked)
        title_layout.addWidget(self._favorite_btn)
        layout.addLayout(title_layout)
        info_text = f"{self._drama.episode_count}集"
        if self._drama.category:
            info_text = f"{self._drama.category} · {info_text}"
        self._info_label = CaptionLabel(info_text)
        self._info_label.setWordWrap(False)
        self._info_label.setContentsMargins(8, 0, 8, 0)
        layout.addWidget(self._info_label)

    def _on_favorite_clicked(self) -> None:
        self._is_favorite = not self._is_favorite
        self.favorite_clicked.emit(self._drama, self._is_favorite)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if not self._favorite_btn.geometry().contains(event.pos()):
                self.clicked.emit(self._drama)

    def set_cover(self, pixmap: QPixmap) -> None:
        if pixmap and not pixmap.isNull():
            self._cover_label.setPixmap(pixmap)

    def set_favorite(self, is_favorite: bool) -> None:
        self._is_favorite = is_favorite

    @property
    def drama(self) -> DramaInfo:
        return self._drama


class LoadingSpinner(QWidget):
    def __init__(self, text: str = "加载中...", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._text = text
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)
        self._progress_ring = IndeterminateProgressRing()
        self._progress_ring.setFixedSize(48, 48)
        self._progress_ring.setStrokeWidth(4)
        layout.addWidget(self._progress_ring, alignment=Qt.AlignmentFlag.AlignCenter)
        self._label = BodyLabel(self._text)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._label, alignment=Qt.AlignmentFlag.AlignCenter)

    def set_text(self, text: str) -> None:
        self._text = text
        self._label.setText(text)


class Pagination(QWidget):
    page_changed = Signal(int)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._current_page = 1
        self._total_pages = 1
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._pager = PipsPager()
        self._pager.setPageNumber(1)
        self._pager.setVisibleNumber(5)
        self._pager.setNextButtonDisplayMode(PipsScrollButtonDisplayMode.ALWAYS)
        self._pager.setPreviousButtonDisplayMode(PipsScrollButtonDisplayMode.ALWAYS)
        self._pager.currentIndexChanged.connect(self._on_index_changed)
        layout.addWidget(self._pager)
        self.setVisible(False)

    def _on_index_changed(self, index: int) -> None:
        new_page = index + 1
        if new_page != self._current_page:
            self._current_page = new_page
            self.page_changed.emit(self._current_page)

    def set_page_info(self, current_page: int, total_pages: int) -> None:
        self._total_pages = max(1, total_pages)
        self._current_page = max(1, min(current_page, self._total_pages))
        self._pager.setPageNumber(self._total_pages)
        self._pager.setCurrentIndex(self._current_page - 1)
        self.setVisible(self._total_pages > 1)


# ==================== UI Interfaces ====================

class HomeInterface(ScrollArea):
    drama_clicked = Signal(object)
    favorite_clicked = Signal(object, bool)

    def __init__(self, category_service: CategoryService, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._category_service = category_service
        self._dramas: List[DramaInfo] = []
        self._cards: List[DramaCard] = []
        self._favorites: set = set()
        self._image_loader = ImageLoader(self)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        self.setObjectName("homeInterface")
        self.setWidgetResizable(True)
        self.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.viewport().setStyleSheet("background: transparent;")
        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self.setWidget(self._container)
        layout = QVBoxLayout(self._container)
        layout.setContentsMargins(24, 24, 36, 24)
        layout.setSpacing(16)
        header_layout = QHBoxLayout()
        self._title_label = SubtitleLabel("推荐短剧")
        header_layout.addWidget(self._title_label)
        header_layout.addStretch()
        self._refresh_btn = PushButton("刷新", self, FluentIcon.SYNC)
        self._refresh_btn.clicked.connect(self.refresh)
        header_layout.addWidget(self._refresh_btn)
        layout.addLayout(header_layout)
        self._loading = LoadingSpinner("正在加载推荐...")
        self._loading.show()
        layout.addWidget(self._loading, alignment=Qt.AlignmentFlag.AlignCenter)
        self._flow_widget = QWidget()
        self._flow_widget.hide()
        self._flow_widget.setStyleSheet("background: transparent;")
        self._flow_layout = FlowLayout(self._flow_widget, needAni=False)
        self._flow_layout.setContentsMargins(0, 0, 0, 0)
        self._flow_layout.setHorizontalSpacing(16)
        self._flow_layout.setVerticalSpacing(16)
        layout.addWidget(self._flow_widget)
        layout.addStretch()

    def _connect_signals(self) -> None:
        self._category_service.recommendations_loaded.connect(self._on_recommendations_loaded)
        self._category_service.error.connect(self._on_error)
        self._image_loader.image_loaded.connect(self._on_image_loaded)

    def _on_recommendations_loaded(self, dramas: List[DramaInfo]) -> None:
        self._loading.hide()
        self._flow_widget.show()
        self._dramas = dramas
        self._update_cards()

    def _on_error(self, error) -> None:
        self._loading.hide()
        self._flow_widget.show()

    def _update_cards(self) -> None:
        for card in self._cards:
            self._flow_layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()
        for drama in self._dramas:
            is_fav = drama.book_id in self._favorites
            card = DramaCard(drama, is_fav)
            card.clicked.connect(self._on_card_clicked)
            card.favorite_clicked.connect(self._on_favorite_clicked)
            self._flow_layout.addWidget(card)
            self._cards.append(card)
            if drama.cover_url:
                self._image_loader.load(drama.cover_url)

    def _on_image_loaded(self, url: str, pixmap) -> None:
        for card in self._cards:
            if card.drama.cover_url == url:
                card.set_cover(pixmap)
                break

    def _on_card_clicked(self, drama: DramaInfo) -> None:
        self.drama_clicked.emit(drama)

    def _on_favorite_clicked(self, drama: DramaInfo, is_favorite: bool) -> None:
        if is_favorite:
            self._favorites.add(drama.book_id)
        else:
            self._favorites.discard(drama.book_id)
        self.favorite_clicked.emit(drama, is_favorite)

    def refresh(self) -> None:
        self._loading.show()
        self._flow_widget.hide()
        self._category_service.fetch_recommendations(force_refresh=True)

    def set_favorites(self, favorites: set) -> None:
        self._favorites = favorites
        for card in self._cards:
            card.set_favorite(card.drama.book_id in self._favorites)

    def load_data(self) -> None:
        self.refresh()


class SearchInterface(ScrollArea):
    drama_clicked = Signal(object)
    favorite_clicked = Signal(object, bool)

    def __init__(self, search_service: SearchService, config_manager: ConfigManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._search_service = search_service
        self._config = config_manager
        self._dramas: List[DramaInfo] = []
        self._cards: List[DramaCard] = []
        self._favorites: set = set()
        self._current_page = 1
        self._total_pages = 1
        self._image_loader = ImageLoader(self)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        self.setObjectName("searchInterface")
        self.setWidgetResizable(True)
        self.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.viewport().setStyleSheet("background: transparent;")
        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self.setWidget(self._container)
        layout = QVBoxLayout(self._container)
        layout.setContentsMargins(24, 24, 36, 24)
        layout.setSpacing(16)
        search_layout = QHBoxLayout()
        self._search_edit = SearchLineEdit()
        self._search_edit.setPlaceholderText("搜索短剧...")
        self._search_edit.setFixedWidth(400)
        self._search_edit.searchSignal.connect(self._on_search)
        self._search_edit.returnPressed.connect(lambda: self._on_search(self._search_edit.text()))
        search_layout.addWidget(self._search_edit)
        search_layout.addStretch()
        layout.addLayout(search_layout)
        self._result_label = SubtitleLabel("")
        self._result_label.hide()
        layout.addWidget(self._result_label)
        self._loading = LoadingSpinner("正在搜索...")
        self._loading.hide()
        layout.addWidget(self._loading, alignment=Qt.AlignmentFlag.AlignCenter)
        self._flow_widget = QWidget()
        self._flow_widget.setStyleSheet("background: transparent;")
        self._flow_layout = FlowLayout(self._flow_widget, needAni=False)
        self._flow_layout.setContentsMargins(0, 0, 0, 0)
        self._flow_layout.setHorizontalSpacing(16)
        self._flow_layout.setVerticalSpacing(16)
        layout.addWidget(self._flow_widget)
        self._pagination = Pagination()
        self._pagination.page_changed.connect(self._on_page_changed)
        layout.addWidget(self._pagination, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

    def _connect_signals(self) -> None:
        self._search_service.search_started.connect(self._on_search_started)
        self._search_service.search_completed.connect(self._on_search_completed)
        self._search_service.search_error.connect(self._on_search_error)
        self._image_loader.image_loaded.connect(self._on_image_loaded)

    def _on_search(self, keyword: str) -> None:
        if keyword.strip():
            self._current_page = 1
            self._search_service.search(keyword.strip(), self._current_page)
            self._config.add_search_history(keyword.strip())

    def _on_search_started(self) -> None:
        self._loading.show()
        self._flow_widget.hide()
        self._pagination.hide()

    def _on_search_completed(self, result: SearchResult) -> None:
        self._loading.hide()
        self._flow_widget.show()
        self._dramas = result.data
        self._result_label.setText(f"搜索结果: {len(result.data)} 部短剧")
        self._result_label.show()
        self._update_cards()
        has_more = len(result.data) >= 20
        total_pages = self._current_page + (1 if has_more else 0)
        self._pagination.set_page_info(self._current_page, total_pages)

    def _on_search_error(self, error) -> None:
        self._loading.hide()
        self._flow_widget.show()
        InfoBar.error(title="搜索失败", content=error.message, orient=Qt.Orientation.Horizontal, isClosable=True, position=InfoBarPosition.TOP_RIGHT, duration=3000, parent=self)

    def _on_page_changed(self, page: int) -> None:
        self._current_page = page
        keyword = self._search_service.current_keyword
        if keyword:
            self._search_service.search(keyword, page)

    def _update_cards(self) -> None:
        for card in self._cards:
            self._flow_layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()
        for drama in self._dramas:
            is_fav = drama.book_id in self._favorites
            card = DramaCard(drama, is_fav)
            card.clicked.connect(self._on_card_clicked)
            card.favorite_clicked.connect(self._on_favorite_clicked)
            self._flow_layout.addWidget(card)
            self._cards.append(card)
            if drama.cover_url:
                self._image_loader.load(drama.cover_url)

    def _on_image_loaded(self, url: str, pixmap) -> None:
        for card in self._cards:
            if card.drama.cover_url == url:
                card.set_cover(pixmap)
                break

    def _on_card_clicked(self, drama: DramaInfo) -> None:
        self.drama_clicked.emit(drama)

    def _on_favorite_clicked(self, drama: DramaInfo, is_favorite: bool) -> None:
        if is_favorite:
            self._favorites.add(drama.book_id)
        else:
            self._favorites.discard(drama.book_id)
        self.favorite_clicked.emit(drama, is_favorite)

    def set_favorites(self, favorites: set) -> None:
        self._favorites = favorites
        for card in self._cards:
            card.set_favorite(card.drama.book_id in self._favorites)

    def focus_search(self) -> None:
        self._search_edit.setFocus()


class CategoryInterface(ScrollArea):
    drama_clicked = Signal(object)
    favorite_clicked = Signal(object, bool)

    def __init__(self, category_service: CategoryService, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._category_service = category_service
        self._categories: List[str] = []
        self._current_category = ""
        self._current_offset = 1
        self._dramas: List[DramaInfo] = []
        self._cards: List[DramaCard] = []
        self._favorites: set = set()
        self._image_loader = ImageLoader(self)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        self.setObjectName("categoryInterface")
        self.setWidgetResizable(True)
        self.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.viewport().setStyleSheet("background: transparent;")
        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self.setWidget(self._container)
        layout = QVBoxLayout(self._container)
        layout.setContentsMargins(24, 24, 36, 24)
        layout.setSpacing(16)
        self._pivot = Pivot()
        self._pivot.currentItemChanged.connect(self._on_category_changed)
        layout.addWidget(self._pivot)
        self._loading = LoadingSpinner("正在加载...")
        self._loading.hide()
        layout.addWidget(self._loading, alignment=Qt.AlignmentFlag.AlignCenter)
        self._flow_widget = QWidget()
        self._flow_widget.setStyleSheet("background: transparent;")
        self._flow_layout = FlowLayout(self._flow_widget, needAni=False)
        self._flow_layout.setContentsMargins(0, 0, 0, 0)
        self._flow_layout.setHorizontalSpacing(16)
        self._flow_layout.setVerticalSpacing(16)
        layout.addWidget(self._flow_widget)
        self._pagination = Pagination()
        self._pagination.page_changed.connect(self._on_page_changed)
        layout.addWidget(self._pagination, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

    def _connect_signals(self) -> None:
        self._category_service.categories_loaded.connect(self._on_categories_loaded)
        self._category_service.dramas_loaded.connect(self._on_dramas_loaded)
        self._category_service.error.connect(self._on_error)
        self._image_loader.image_loaded.connect(self._on_image_loaded)

    def _on_categories_loaded(self, categories: List[str]) -> None:
        self._categories = categories
        display_categories = categories[:15]
        for i, category in enumerate(display_categories):
            self._pivot.addItem(routeKey=f"cat_{i}_{category}", text=category, onClick=lambda checked=False, c=category: self._load_category(c))
        if display_categories:
            first_key = f"cat_0_{display_categories[0]}"
            self._pivot.setCurrentItem(first_key)
            self._load_category(display_categories[0])

    def _on_category_changed(self, route_key: str) -> None:
        parts = route_key.split("_", 2)
        category = parts[2] if len(parts) >= 3 else route_key
        if category != self._current_category:
            self._current_offset = 1
            self._load_category(category)

    def _load_category(self, category: str) -> None:
        self._current_category = category
        self._loading.show()
        self._flow_widget.hide()
        self._pagination.hide()
        self._category_service.fetch_category_dramas(category, self._current_offset)

    def _on_dramas_loaded(self, result: CategoryResult) -> None:
        self._loading.hide()
        self._flow_widget.show()
        self._dramas = result.data
        self._current_offset = result.offset
        self._update_cards()
        has_more = len(result.data) >= 20
        total_pages = self._current_offset + (1 if has_more else 0)
        self._pagination.set_page_info(self._current_offset, total_pages)

    def _on_error(self, error) -> None:
        self._loading.hide()
        self._flow_widget.show()
        InfoBar.error(title="加载失败", content=error.message, orient=Qt.Orientation.Horizontal, isClosable=True, position=InfoBarPosition.TOP_RIGHT, duration=3000, parent=self)

    def _on_page_changed(self, page: int) -> None:
        self._current_offset = page
        if self._current_category:
            self._load_category(self._current_category)

    def _update_cards(self) -> None:
        for card in self._cards:
            self._flow_layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()
        for drama in self._dramas:
            is_fav = drama.book_id in self._favorites
            card = DramaCard(drama, is_fav)
            card.clicked.connect(self._on_card_clicked)
            card.favorite_clicked.connect(self._on_favorite_clicked)
            self._flow_layout.addWidget(card)
            self._cards.append(card)
            if drama.cover_url:
                self._image_loader.load(drama.cover_url)

    def _on_image_loaded(self, url: str, pixmap) -> None:
        for card in self._cards:
            if card.drama.cover_url == url:
                card.set_cover(pixmap)
                break

    def _on_card_clicked(self, drama: DramaInfo) -> None:
        self.drama_clicked.emit(drama)

    def _on_favorite_clicked(self, drama: DramaInfo, is_favorite: bool) -> None:
        if is_favorite:
            self._favorites.add(drama.book_id)
        else:
            self._favorites.discard(drama.book_id)
        self.favorite_clicked.emit(drama, is_favorite)

    def set_favorites(self, favorites: set) -> None:
        self._favorites = favorites
        for card in self._cards:
            card.set_favorite(card.drama.book_id in self._favorites)

    def load_data(self) -> None:
        self._category_service.fetch_categories()



class DownloadItemWidget(QWidget):
    def __init__(self, task: DownloadTask, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._task = task
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        title_layout = QHBoxLayout()
        self._title_label = BodyLabel(f"{self._task.drama.name}")
        self._title_label.setWordWrap(True)
        title_layout.addWidget(self._title_label, 1)
        self._status_label = CaptionLabel(self._get_status_text())
        title_layout.addWidget(self._status_label)
        layout.addLayout(title_layout)
        self._episode_label = CaptionLabel(self._task.episode.title)
        layout.addWidget(self._episode_label)
        self._progress_bar = ProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(int(self._task.progress))
        layout.addWidget(self._progress_bar)
        self._progress_label = CaptionLabel(self._get_progress_text())
        layout.addWidget(self._progress_label)

    def _get_status_text(self) -> str:
        status_map = {DownloadStatus.PENDING: "等待中", DownloadStatus.FETCHING: "获取信息...", DownloadStatus.DOWNLOADING: "下载中", DownloadStatus.COMPLETED: "已完成", DownloadStatus.FAILED: "失败", DownloadStatus.CANCELLED: "已取消"}
        return status_map.get(self._task.status, "未知")

    def _get_progress_text(self) -> str:
        if self._task.total_bytes > 0:
            downloaded_mb = self._task.downloaded_bytes / (1024 * 1024)
            total_mb = self._task.total_bytes / (1024 * 1024)
            return f"{downloaded_mb:.1f} MB / {total_mb:.1f} MB"
        return ""

    def update_progress(self, progress: float, downloaded: int, total: int) -> None:
        self._task.progress = progress
        self._task.downloaded_bytes = downloaded
        self._task.total_bytes = total
        self._progress_bar.setValue(int(progress))
        self._progress_label.setText(self._get_progress_text())
        self._status_label.setText("下载中")

    def update_status(self, status: DownloadStatus, error: str = "") -> None:
        self._task.status = status
        self._task.error = error
        self._status_label.setText(self._get_status_text())
        if status == DownloadStatus.COMPLETED:
            self._progress_bar.setValue(100)
            self._progress_label.setText("下载完成")
        elif status == DownloadStatus.FAILED:
            self._progress_label.setText(f"错误: {error}")

    @property
    def task_id(self) -> str:
        return self._task.id


class DownloadInterface(ScrollArea):
    def __init__(self, download_service: DownloadService, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._download_service = download_service
        self._item_widgets: Dict[str, DownloadItemWidget] = {}
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        self.setObjectName("downloadInterface")
        self.setWidgetResizable(True)
        self.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.viewport().setStyleSheet("background: transparent;")
        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self.setWidget(self._container)
        layout = QVBoxLayout(self._container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        header_layout = QHBoxLayout()
        self._title_label = SubtitleLabel("下载管理")
        header_layout.addWidget(self._title_label)
        header_layout.addStretch()
        self._open_dir_btn = PushButton("打开目录", self, FluentIcon.FOLDER)
        self._open_dir_btn.clicked.connect(self._open_download_dir)
        header_layout.addWidget(self._open_dir_btn)
        self._clear_btn = PushButton("清除已完成", self, FluentIcon.DELETE)
        self._clear_btn.clicked.connect(self._clear_completed)
        header_layout.addWidget(self._clear_btn)
        layout.addLayout(header_layout)
        self._empty_label = BodyLabel("暂无下载任务")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._empty_label, 1)
        self._list_container = QWidget()
        self._list_container.hide()
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(8)
        self._list_layout.addStretch()
        layout.addWidget(self._list_container, 1)

    def _connect_signals(self) -> None:
        self._download_service.task_added.connect(self._on_task_added)
        self._download_service.task_started.connect(self._on_task_started)
        self._download_service.task_progress.connect(self._on_task_progress)
        self._download_service.task_completed.connect(self._on_task_completed)
        self._download_service.task_failed.connect(self._on_task_failed)

    def _on_task_added(self, task: DownloadTask) -> None:
        self._empty_label.hide()
        self._list_container.show()
        item_widget = DownloadItemWidget(task)
        self._item_widgets[task.id] = item_widget
        self._list_layout.insertWidget(0, item_widget)

    def _on_task_started(self, task_id: str) -> None:
        if task_id in self._item_widgets:
            self._item_widgets[task_id].update_status(DownloadStatus.FETCHING)

    def _on_task_progress(self, task_id: str, progress: float, downloaded: int, total: int) -> None:
        if task_id in self._item_widgets:
            self._item_widgets[task_id].update_progress(progress, downloaded, total)

    def _on_task_completed(self, task_id: str) -> None:
        if task_id in self._item_widgets:
            self._item_widgets[task_id].update_status(DownloadStatus.COMPLETED)

    def _on_task_failed(self, task_id: str, error: str) -> None:
        if task_id in self._item_widgets:
            self._item_widgets[task_id].update_status(DownloadStatus.FAILED, error)

    def _open_download_dir(self) -> None:
        download_dir = self._download_service.download_dir
        if os.path.exists(download_dir):
            subprocess.run(['explorer', download_dir])
        else:
            os.makedirs(download_dir, exist_ok=True)
            subprocess.run(['explorer', download_dir])

    def _clear_completed(self) -> None:
        completed_ids = [task_id for task_id, widget in self._item_widgets.items() if widget._task.status == DownloadStatus.COMPLETED]
        for task_id in completed_ids:
            widget = self._item_widgets.pop(task_id)
            self._list_layout.removeWidget(widget)
            widget.deleteLater()
        self._download_service.clear_completed()
        if not self._item_widgets:
            self._list_container.hide()
            self._empty_label.show()


# ==================== Dialogs ====================

class EpisodeDialog(MessageBoxBase):
    episode_selected = Signal(object)
    episodes_download = Signal(list)

    def __init__(self, drama: DramaInfo, episodes: List[EpisodeInfo], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._drama = drama
        self._episodes = episodes
        self._buttons: List[PushButton] = []
        self._checkboxes: List[CheckBox] = []
        self._is_download_mode = False
        self._setup_ui()
        QTimer.singleShot(50, self._create_buttons)

    def _setup_ui(self) -> None:
        self.widget.setFixedSize(600, 500)
        self.yesButton.hide()
        self.cancelButton.hide()
        self.buttonGroup.hide()
        layout = self.viewLayout
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(10)
        self.titleLabel = SubtitleLabel(self._drama.name)
        layout.addWidget(self.titleLabel)
        self.countLabel = BodyLabel(f"共 {len(self._episodes)} 集")
        layout.addWidget(self.countLabel)
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(20)
        self._play_radio = RadioButton("播放")
        self._play_radio.setChecked(True)
        self._play_radio.clicked.connect(self._on_mode_changed)
        mode_layout.addWidget(self._play_radio)
        self._download_radio = RadioButton("下载")
        self._download_radio.clicked.connect(self._on_mode_changed)
        mode_layout.addWidget(self._download_radio)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)
        self._select_btn_layout = QHBoxLayout()
        self._select_btn_layout.setSpacing(10)
        self._select_all_btn = PushButton("全选")
        self._select_all_btn.clicked.connect(self._select_all)
        self._select_all_btn.hide()
        self._select_btn_layout.addWidget(self._select_all_btn)
        self._deselect_all_btn = PushButton("反选")
        self._deselect_all_btn.clicked.connect(self._toggle_selection)
        self._deselect_all_btn.hide()
        self._select_btn_layout.addWidget(self._deselect_all_btn)
        self._select_btn_layout.addStretch()
        layout.addLayout(self._select_btn_layout)
        self._scroll_area = ScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setMinimumHeight(320)
        self._scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self._scroll_area.viewport().setStyleSheet("background: transparent;")
        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self._grid_layout = QGridLayout(self._container)
        self._grid_layout.setSpacing(8)
        self._scroll_area.setWidget(self._container)
        layout.addWidget(self._scroll_area)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self._confirm_btn = PushButton("确认下载")
        self._confirm_btn.clicked.connect(self._on_confirm_download)
        self._confirm_btn.hide()
        btn_layout.addWidget(self._confirm_btn)
        self._close_btn = PushButton("关闭")
        self._close_btn.clicked.connect(self.close)
        btn_layout.addWidget(self._close_btn)
        layout.addLayout(btn_layout)

    def _create_buttons(self) -> None:
        cols = 5
        for i, episode in enumerate(self._episodes):
            btn = PushButton(f"第{episode.episode_number}集")
            btn.setFixedSize(80, 36)
            btn.setToolTip(episode.title)
            btn.clicked.connect(lambda checked, ep=episode: self._on_episode_clicked(ep))
            checkbox = CheckBox(f"第{episode.episode_number}集")
            checkbox.setToolTip(episode.title)
            checkbox.hide()
            row = i // cols
            col = i % cols
            self._grid_layout.addWidget(btn, row * 2, col)
            self._grid_layout.addWidget(checkbox, row * 2 + 1, col)
            self._buttons.append(btn)
            self._checkboxes.append(checkbox)

    def _on_mode_changed(self) -> None:
        self._is_download_mode = self._download_radio.isChecked()
        if self._is_download_mode:
            for btn in self._buttons:
                btn.hide()
            for cb in self._checkboxes:
                cb.show()
            self._select_all_btn.show()
            self._deselect_all_btn.show()
            self._confirm_btn.show()
        else:
            for btn in self._buttons:
                btn.show()
            for cb in self._checkboxes:
                cb.hide()
            self._select_all_btn.hide()
            self._deselect_all_btn.hide()
            self._confirm_btn.hide()

    def _select_all(self) -> None:
        for cb in self._checkboxes:
            cb.setChecked(True)

    def _toggle_selection(self) -> None:
        for cb in self._checkboxes:
            cb.setChecked(not cb.isChecked())

    def _on_episode_clicked(self, episode: EpisodeInfo) -> None:
        if not self._is_download_mode:
            self.episode_selected.emit(episode)
            self.close()

    def _on_confirm_download(self) -> None:
        selected_episodes = []
        for i, cb in enumerate(self._checkboxes):
            if cb.isChecked() and i < len(self._episodes):
                selected_episodes.append(self._episodes[i])
        if selected_episodes:
            self.episodes_download.emit(selected_episodes)
            self.close()


class CustomSettingCard(SettingCard):
    def __init__(self, icon, title, content, widget, parent=None):
        super().__init__(icon, title, content, parent)
        self.hBoxLayout.addWidget(widget, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)


class SettingsDialog(QDialog):
    theme_changed = Signal(object)
    timeout_changed = Signal(int)
    quality_changed = Signal(str)
    settings_saved = Signal()

    def __init__(self, config_manager: ConfigManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._config = config_manager
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setWindowTitle("设置")
        self.setFixedSize(600, 500)
        self.setModal(True)

        def update_theme():
            if isDarkTheme():
                self.setStyleSheet("QDialog { background-color: #202020; }")
            else:
                self.setStyleSheet("QDialog { background-color: #f9f9f9; }")
        update_theme()
        qconfig.themeChanged.connect(update_theme)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        self._appearance_group = SettingCardGroup("外观", self)
        self._appearance_group.setStyleSheet("SettingCardGroup { background: transparent; }")
        self._theme_combo = ComboBox()
        self._theme_combo.addItems(["浅色", "深色", "跟随系统"])
        theme_index = {ThemeMode.LIGHT: 0, ThemeMode.DARK: 1, ThemeMode.AUTO: 2}.get(self._config.theme_mode, 2)
        self._theme_combo.setCurrentIndex(theme_index)
        self._theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        self._theme_card = CustomSettingCard(FluentIcon.BRUSH, "主题模式", "选择应用的主题外观", self._theme_combo, self._appearance_group)
        self._appearance_group.addSettingCard(self._theme_card)
        layout.addWidget(self._appearance_group)
        self._playback_group = SettingCardGroup("播放", self)
        self._playback_group.setStyleSheet("SettingCardGroup { background: transparent; }")
        self._quality_combo = ComboBox()
        self._quality_combo.addItems(["360p", "480p", "720p", "1080p", "2160p"])
        quality_index = {"360p": 0, "480p": 1, "720p": 2, "1080p": 3, "2160p": 4}.get(self._config.default_quality, 3)
        self._quality_combo.setCurrentIndex(quality_index)
        self._quality_combo.currentTextChanged.connect(self._on_quality_changed)
        self._quality_card = CustomSettingCard(FluentIcon.VIDEO, "默认清晰度", "选择视频播放的默认清晰度", self._quality_combo, self._playback_group)
        self._playback_group.addSettingCard(self._quality_card)
        layout.addWidget(self._playback_group)
        self._network_group = SettingCardGroup("网络", self)
        self._network_group.setStyleSheet("SettingCardGroup { background: transparent; }")
        timeout_widget = QWidget()
        timeout_layout = QHBoxLayout(timeout_widget)
        timeout_layout.setContentsMargins(0, 0, 0, 0)
        self._timeout_slider = Slider(Qt.Orientation.Horizontal)
        self._timeout_slider.setRange(1, 60)
        self._timeout_slider.setValue(self._config.api_timeout // 1000)
        self._timeout_slider.setFixedWidth(200)
        self._timeout_slider.valueChanged.connect(self._on_timeout_changed)
        self._timeout_label = BodyLabel(f"{self._config.api_timeout // 1000}秒")
        self._timeout_label.setFixedWidth(40)
        timeout_layout.addWidget(self._timeout_slider)
        timeout_layout.addWidget(self._timeout_label)
        self._timeout_card = CustomSettingCard(FluentIcon.SPEED_HIGH, "API 超时时间", "设置网络请求的超时时间", timeout_widget, self._network_group)
        self._network_group.addSettingCard(self._timeout_card)
        layout.addWidget(self._network_group)
        layout.addStretch()
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self._cancel_btn = PushButton("取消")
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)
        self._save_btn = PrimaryPushButton("保存")
        self._save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self._save_btn)
        layout.addLayout(btn_layout)

    def _on_theme_changed(self, index: int) -> None:
        theme_map = {0: ThemeMode.LIGHT, 1: ThemeMode.DARK, 2: ThemeMode.AUTO}
        theme = theme_map.get(index, ThemeMode.AUTO)
        self.theme_changed.emit(theme)

    def _on_quality_changed(self, text: str) -> None:
        self.quality_changed.emit(text)

    def _on_timeout_changed(self, value: int) -> None:
        self._timeout_label.setText(f"{value}秒")
        self.timeout_changed.emit(value * 1000)

    def _on_save(self) -> None:
        theme_index = self._theme_combo.currentIndex()
        theme_map = {0: ThemeMode.LIGHT, 1: ThemeMode.DARK, 2: ThemeMode.AUTO}
        self._config.theme_mode = theme_map.get(theme_index, ThemeMode.AUTO)
        self._config.default_quality = self._quality_combo.currentText()
        self._config.api_timeout = self._timeout_slider.value() * 1000
        self._config.save()
        self.settings_saved.emit()
        self.accept()


class SplashDialog(QDialog):
    init_completed = Signal()
    init_failed = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._tasks: List[tuple] = []
        self._current_task = 0
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setWindowTitle("初始化")
        self.setFixedSize(400, 180)
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)

        def update_theme():
            if isDarkTheme():
                self.setStyleSheet("QDialog { background-color: #202020; }")
            else:
                self.setStyleSheet("QDialog { background-color: #f9f9f9; }")
        update_theme()
        qconfig.themeChanged.connect(update_theme)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)
        self.titleLabel = SubtitleLabel("短剧搜索")
        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.titleLabel)
        self._status_label = BodyLabel("正在初始化...")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status_label)
        self._progress = ProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        layout.addWidget(self._progress)
        self._exit_btn = PushButton("退出")
        self._exit_btn.clicked.connect(self.reject)
        self._exit_btn.hide()
        layout.addWidget(self._exit_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def add_task(self, name: str, callback: Callable[[], bool]) -> None:
        self._tasks.append((name, callback))

    def start(self) -> None:
        self._current_task = 0
        if self._tasks:
            QTimer.singleShot(100, self._run_next_task)
        else:
            self._on_completed()

    def _run_next_task(self) -> None:
        if self._current_task >= len(self._tasks):
            self._on_completed()
            return
        name, callback = self._tasks[self._current_task]
        self._status_label.setText(f"正在{name}...")
        progress = int((self._current_task / len(self._tasks)) * 100)
        self._progress.setValue(progress)
        QApplication.processEvents()
        try:
            success = callback()
            if success:
                self._current_task += 1
                QTimer.singleShot(50, self._run_next_task)
            else:
                self._on_failed(f"{name}失败")
        except Exception as e:
            self._on_failed(f"{name}出错: {e}")

    def _on_completed(self) -> None:
        self._progress.setValue(100)
        self._status_label.setText("初始化完成")
        QTimer.singleShot(300, lambda: self.init_completed.emit())
        QTimer.singleShot(500, self.accept)

    def _on_failed(self, error: str) -> None:
        self._status_label.setText(f"初始化失败: {error}")
        self.init_failed.emit(error)
        self._exit_btn.show()



# ==================== Player Window ====================

class PlayerWindow(QWidget):
    episode_changed = Signal(object)
    closed = Signal()
    select_episode_requested = Signal()
    LOCAL_VLC_PATH = os.path.join(BASE_PATH, "vlc", "vlc.exe")
    SYSTEM_VLC_PATHS = [r"C:\Program Files\VideoLAN\VLC\vlc.exe", r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"]

    def __init__(self, drama: DramaInfo, episode: EpisodeInfo, video_url: str, episodes: Optional[List[EpisodeInfo]] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._drama = drama
        self._episode = episode
        self._video_url = video_url
        self._episodes = episodes or []
        self._vlc_process: Optional[subprocess.Popen] = None
        self._on_play_episode: Optional[Callable[[EpisodeInfo], None]] = None
        self._setup_ui()
        self._update_nav_buttons()
        self._play_video()

    def _setup_ui(self) -> None:
        self.setWindowTitle(f"{self._drama.name} - {self._episode.title}")
        self.setFixedSize(450, 250)
        self.setWindowFlags(Qt.WindowType.Window)
        self._apply_theme()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        self._title_label = BodyLabel(f"正在播放: {self._drama.name}")
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._title_label)
        self._episode_label = BodyLabel(f"{self._episode.title}")
        self._episode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._episode_label)
        self._status_label = BodyLabel("正在启动播放器...")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status_label)
        layout.addStretch()
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(10)
        self._prev_btn = PushButton("上一集", self, FluentIcon.LEFT_ARROW)
        self._prev_btn.clicked.connect(self._play_prev_episode)
        nav_layout.addWidget(self._prev_btn)
        self._select_btn = PushButton("选集", self, FluentIcon.MENU)
        self._select_btn.clicked.connect(self._on_select_episode)
        nav_layout.addWidget(self._select_btn)
        self._next_btn = PushButton("下一集", self, FluentIcon.RIGHT_ARROW)
        self._next_btn.clicked.connect(self._play_next_episode)
        nav_layout.addWidget(self._next_btn)
        layout.addLayout(nav_layout)
        btn_layout = QHBoxLayout()
        self._browser_btn = PushButton("浏览器播放", self, FluentIcon.GLOBE)
        self._browser_btn.clicked.connect(self._play_in_browser)
        btn_layout.addWidget(self._browser_btn)
        self._close_btn = PushButton("关闭", self, FluentIcon.CLOSE)
        self._close_btn.clicked.connect(self.close)
        btn_layout.addWidget(self._close_btn)
        layout.addLayout(btn_layout)

    def _find_vlc(self) -> Optional[str]:
        local_vlc = os.path.normpath(self.LOCAL_VLC_PATH)
        if os.path.exists(local_vlc):
            return local_vlc
        for path in self.SYSTEM_VLC_PATHS:
            if os.path.exists(path):
                return path
        try:
            result = subprocess.run(["where", "vlc"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                vlc_path = result.stdout.strip().split('\n')[0]
                if os.path.exists(vlc_path):
                    return vlc_path
        except Exception:
            pass
        return None

    def _play_video(self) -> None:
        vlc_path = self._find_vlc()
        if vlc_path:
            self._play_with_vlc(vlc_path)
        else:
            self._status_label.setText("未找到 VLC，使用浏览器播放")
            self._play_in_browser()

    def _play_with_vlc(self, vlc_path: str) -> None:
        try:
            cmd = [vlc_path, self._video_url, f"--meta-title={self._drama.name} - {self._episode.title}", "--no-video-title-show"]
            self._vlc_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self._status_label.setText("VLC 播放中...")
        except Exception as e:
            self._status_label.setText(f"VLC 启动失败: {e}")
            InfoBar.error(title="播放失败", content=f"无法启动 VLC: {e}", orient=Qt.Orientation.Horizontal, isClosable=True, position=InfoBarPosition.TOP, duration=3000, parent=self)

    def _play_in_browser(self) -> None:
        try:
            webbrowser.open(self._video_url)
            self._status_label.setText("已在浏览器中打开")
        except Exception as e:
            self._status_label.setText(f"浏览器打开失败: {e}")

    def _stop_vlc(self) -> None:
        if self._vlc_process:
            try:
                self._vlc_process.terminate()
                self._vlc_process.wait(timeout=2)
            except Exception:
                try:
                    self._vlc_process.kill()
                except Exception:
                    pass
            self._vlc_process = None

    def closeEvent(self, event) -> None:
        self._stop_vlc()
        self.closed.emit()
        super().closeEvent(event)

    def _apply_theme(self) -> None:
        if isDarkTheme():
            self.setStyleSheet("PlayerWindow { background-color: #202020; }")
        else:
            self.setStyleSheet("PlayerWindow { background-color: #f9f9f9; }")

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)

    def set_episodes(self, episodes: List[EpisodeInfo]) -> None:
        self._episodes = episodes
        self._update_nav_buttons()

    def set_play_episode_callback(self, callback: Callable[[EpisodeInfo], None]) -> None:
        self._on_play_episode = callback

    def _get_current_index(self) -> int:
        for i, ep in enumerate(self._episodes):
            if ep.video_id == self._episode.video_id:
                return i
        return -1

    def _update_nav_buttons(self) -> None:
        current_idx = self._get_current_index()
        has_episodes = len(self._episodes) > 0
        self._prev_btn.setEnabled(has_episodes and current_idx > 0)
        self._next_btn.setEnabled(has_episodes and current_idx < len(self._episodes) - 1)
        self._select_btn.setEnabled(has_episodes)

    def _play_prev_episode(self) -> None:
        current_idx = self._get_current_index()
        if current_idx > 0:
            prev_episode = self._episodes[current_idx - 1]
            if self._on_play_episode:
                self._on_play_episode(prev_episode)

    def _play_next_episode(self) -> None:
        current_idx = self._get_current_index()
        if current_idx < len(self._episodes) - 1:
            next_episode = self._episodes[current_idx + 1]
            if self._on_play_episode:
                self._on_play_episode(next_episode)

    def _on_select_episode(self) -> None:
        self.select_episode_requested.emit()

    def update_episode(self, episode: EpisodeInfo, video_url: str) -> None:
        self._stop_vlc()
        self._episode = episode
        self._video_url = video_url
        self.setWindowTitle(f"{self._drama.name} - {self._episode.title}")
        self._episode_label.setText(f"{self._episode.title}")
        self._update_nav_buttons()
        self._play_video()


# ==================== Main Window ====================

class MainWindow(FluentWindow):
    initialization_completed = Signal()

    def __init__(self):
        super().__init__()
        self._initialized = False
        self._init_services()
        self._setup_ui()
        self._connect_signals()
        self._set_ui_enabled(False)

    def _init_services(self) -> None:
        self._config = ConfigManager()
        self._theme_manager = ThemeManager(self)
        self._theme_manager.set_theme(self._config.theme_mode)
        self._api_client = ApiClient(timeout=self._config.api_timeout)
        self._cache = CacheManager()
        self._search_service = SearchService(self._api_client, self._cache, self)
        self._video_service = VideoService(self._api_client, self)
        self._category_service = CategoryService(self._api_client, self._cache, self)
        download_dir = os.path.join(BASE_PATH, "downloads")
        self._download_service = DownloadService(self._api_client, download_dir, self._config.default_quality, self)
        self._favorites: set = set()
        self._player_window = None

    def _setup_ui(self) -> None:
        self.setWindowTitle("短剧搜索")
        self.setMinimumSize(900, 650)
        self.resize(1025, 750)
        self.navigationInterface.setExpandWidth(120)
        self._home_interface = HomeInterface(self._category_service, self)
        self._search_interface = SearchInterface(self._search_service, self._config, self)
        self._category_interface = CategoryInterface(self._category_service, self)
        self._download_interface = DownloadInterface(self._download_service, self)
        self.addSubInterface(self._home_interface, FluentIcon.HOME, "首页", NavigationItemPosition.TOP)
        self.addSubInterface(self._search_interface, FluentIcon.SEARCH, "搜索", NavigationItemPosition.TOP)
        self.addSubInterface(self._category_interface, FluentIcon.FOLDER, "分类", NavigationItemPosition.TOP)
        self.addSubInterface(self._download_interface, FluentIcon.DOWNLOAD, "下载", NavigationItemPosition.TOP)
        self.navigationInterface.addSeparator()
        self.navigationInterface.addItem(routeKey="github", icon=FluentIcon.GITHUB, text="GitHub", onClick=lambda: QDesktopServices.openUrl(QUrl("https://github.com/GamblerIX/DUANJU")), position=NavigationItemPosition.BOTTOM)
        gitee_icon_path = os.path.join(BASE_PATH, "assets", "gitee.ico")
        if os.path.exists(gitee_icon_path):
            self.navigationInterface.addItem(routeKey="gitee", icon=QIcon(gitee_icon_path), text="Gitee", onClick=lambda: QDesktopServices.openUrl(QUrl("https://gitee.com/GamblerIX/DUANJU")), position=NavigationItemPosition.BOTTOM)
        self.navigationInterface.addItem(routeKey="settings", icon=FluentIcon.SETTING, text="设置", onClick=self._show_settings, position=NavigationItemPosition.BOTTOM)
        self.navigationInterface.setCurrentItem(self._home_interface.objectName())

    def _connect_signals(self) -> None:
        self._home_interface.drama_clicked.connect(self._on_drama_clicked)
        self._search_interface.drama_clicked.connect(self._on_drama_clicked)
        self._category_interface.drama_clicked.connect(self._on_drama_clicked)
        self._home_interface.favorite_clicked.connect(self._on_favorite_clicked)
        self._search_interface.favorite_clicked.connect(self._on_favorite_clicked)
        self._category_interface.favorite_clicked.connect(self._on_favorite_clicked)
        self._video_service.episodes_loaded.connect(self._on_episodes_loaded)
        self._video_service.video_url_loaded.connect(self._on_video_url_loaded)
        self._video_service.error.connect(self._on_error)
        self._theme_manager.theme_changed.connect(self._on_theme_changed)

    def _set_ui_enabled(self, enabled: bool) -> None:
        self._home_interface.setEnabled(enabled)
        self._search_interface.setEnabled(enabled)
        self._category_interface.setEnabled(enabled)
        self.navigationInterface.setEnabled(enabled)

    def start_initialization(self) -> None:
        self._splash = SplashDialog(self)
        self._splash.add_task("加载配置", self._init_task_config)
        self._splash.add_task("预加载数据", self._init_task_preload)
        self._splash.init_completed.connect(self._on_init_completed)
        self._splash.init_failed.connect(self._on_init_failed)
        self._splash.show()
        QTimer.singleShot(100, self._splash.start)

    def _init_task_config(self) -> bool:
        try:
            return True
        except Exception:
            return False

    def _init_task_preload(self) -> bool:
        try:
            self._home_interface.load_data()
            self._category_interface.load_data()
            return True
        except Exception:
            return False

    def _on_init_completed(self) -> None:
        self._initialized = True
        self._set_ui_enabled(True)
        self.initialization_completed.emit()

    def _on_init_failed(self, error: str) -> None:
        InfoBar.error(title="初始化失败", content=error, orient=Qt.Orientation.Horizontal, isClosable=True, position=InfoBarPosition.TOP, duration=-1, parent=self)

    def _on_drama_clicked(self, drama: DramaInfo) -> None:
        self._current_drama = drama
        self._video_service.fetch_episodes(drama.book_id)

    def _on_episodes_loaded(self, episode_list) -> None:
        if hasattr(self, '_current_drama'):
            self._current_episodes = episode_list.episodes
            self._show_episode_dialog()

    def _show_episode_dialog(self) -> None:
        dialog = EpisodeDialog(self._current_drama, self._current_episodes, self)
        dialog.episode_selected.connect(self._on_episode_selected)
        dialog.episodes_download.connect(self._on_episodes_download)
        dialog.exec()

    def _on_episode_selected(self, episode) -> None:
        self._current_episode = episode
        self._video_service.fetch_video_url(episode.video_id, self._config.default_quality)

    def _on_episodes_download(self, episodes) -> None:
        if hasattr(self, '_current_drama'):
            self._download_service.add_tasks(self._current_drama, episodes)
            self._download_service.start()
            self.navigationInterface.setCurrentItem(self._download_interface.objectName())
            InfoBar.success(title="已添加下载", content=f"已添加 {len(episodes)} 集到下载队列", orient=Qt.Orientation.Horizontal, isClosable=True, position=InfoBarPosition.TOP_RIGHT, duration=3000, parent=self)

    def _on_video_url_loaded(self, video_info) -> None:
        if video_info.url and hasattr(self, '_current_drama') and hasattr(self, '_current_episode'):
            episodes = getattr(self, '_current_episodes', [])
            if self._player_window is None:
                self._player_window = PlayerWindow(self._current_drama, self._current_episode, video_info.url, episodes)
                self._player_window.closed.connect(self._on_player_closed)
                self._player_window.select_episode_requested.connect(self._on_player_select_episode)
                self._player_window.set_play_episode_callback(self._on_episode_selected)
                self._player_window.show()
            else:
                self._player_window.set_episodes(episodes)
                self._player_window.set_play_episode_callback(self._on_episode_selected)
                self._player_window.update_episode(self._current_episode, video_info.url)
                self._player_window.show()
                self._player_window.activateWindow()

    def _on_player_closed(self) -> None:
        self._player_window = None

    def _on_player_select_episode(self) -> None:
        if hasattr(self, '_current_drama') and hasattr(self, '_current_episodes'):
            self._show_episode_dialog()

    def _on_favorite_clicked(self, drama: DramaInfo, is_favorite: bool) -> None:
        if is_favorite:
            self._favorites.add(drama.book_id)
        else:
            self._favorites.discard(drama.book_id)
        self._home_interface.set_favorites(self._favorites)
        self._search_interface.set_favorites(self._favorites)
        self._category_interface.set_favorites(self._favorites)

    def _on_error(self, error) -> None:
        InfoBar.error(title="错误", content=error.message, orient=Qt.Orientation.Horizontal, isClosable=True, position=InfoBarPosition.TOP_RIGHT, duration=3000, parent=self)

    def _on_theme_changed(self, mode: ThemeMode) -> None:
        self._config.theme_mode = mode

    def _show_settings(self) -> None:
        dialog = SettingsDialog(self._config, self)
        dialog.theme_changed.connect(self._theme_manager.set_theme)
        dialog.exec()

    def keyPressEvent(self, event) -> None:
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_F:
                self.navigationInterface.setCurrentItem(self._search_interface.objectName())
                self._search_interface.focus_search()
                return
        if event.key() == Qt.Key.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event) -> None:
        # 确保所有服务都停止
        if self._download_service.is_running:
            self._download_service.cancel()

        # 停止所有正在运行的worker
        for interface in [self._home_interface, self._search_interface, self._category_interface]:
            if hasattr(interface, '_search_service') and interface._search_service:
                interface._search_service.cancel_search()

        # 关闭播放器窗口
        if self._player_window:
            self._player_window.close()

        # 确保应用退出
        QApplication.instance().quit()

        super().closeEvent(event)


# ==================== Application Entry ====================

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("短剧搜索")
    app.setApplicationVersion("1.0.0")

    # 确保最后一个窗口关闭时应用退出
    app.setQuitOnLastWindowClosed(True)

    setTheme(Theme.AUTO)
    window = MainWindow()
    window.show()
    window.start_initialization()

    # 运行应用
    exit_code = app.exec()

    # 确保所有线程都已停止
    app.closeAllWindows()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
