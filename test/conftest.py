"""Pytest 配置和共享 fixtures

提供测试所需的通用配置、mock 对象和 fixtures。
支持自动化测试和未来新代码测试。
"""
import sys
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Any
from unittest.mock import MagicMock, AsyncMock
from dataclasses import dataclass

import pytest


# ==================== Qt Mock 设置 ====================
# 在导入任何可能依赖 Qt 的模块之前设置 mock

def _setup_qt_mocks():
    """设置 Qt mock（如果 PySide6 不可用）"""
    try:
        import PySide6
        # PySide6 可用，不需要 mock
        return False
    except ImportError:
        pass
    
    # 创建 mock 模块
    class MockSignal:
        def __init__(self, *args):
            self._callbacks = []
        def connect(self, callback):
            self._callbacks.append(callback)
        def emit(self, *args):
            for cb in self._callbacks:
                try:
                    cb(*args)
                except:
                    pass
    
    class MockQObject:
        def __init__(self, parent=None):
            self._parent = parent
    
    class MockQThread(MockQObject):
        finished = MockSignal()
        def __init__(self, parent=None):
            super().__init__(parent)
        def start(self):
            pass
        def wait(self, timeout=None):
            return True
        def terminate(self):
            pass
        def isRunning(self):
            return False
    
    class MockQTimer(MockQObject):
        timeout = MockSignal()
        def start(self, interval=None):
            pass
        def stop(self):
            pass
    
    mock_qtcore = MagicMock()
    mock_qtcore.QObject = MockQObject
    mock_qtcore.QThread = MockQThread
    mock_qtcore.Signal = MockSignal
    mock_qtcore.QTimer = MockQTimer
    mock_qtcore.QUrl = MagicMock()
    mock_qtcore.Qt = MagicMock()
    
    mock_qtwidgets = MagicMock()
    mock_qtgui = MagicMock()
    mock_qtnetwork = MagicMock()
    
    mock_pyside6 = MagicMock()
    mock_pyside6.QtCore = mock_qtcore
    mock_pyside6.QtWidgets = mock_qtwidgets
    mock_pyside6.QtGui = mock_qtgui
    mock_pyside6.QtNetwork = mock_qtnetwork
    
    mock_fluent = MagicMock()
    mock_fluent.setTheme = MagicMock()
    mock_fluent.setThemeColor = MagicMock()
    mock_fluent.isDarkTheme = MagicMock(return_value=False)
    mock_fluent.Theme = MagicMock()
    
    sys.modules['PySide6'] = mock_pyside6
    sys.modules['PySide6.QtCore'] = mock_qtcore
    sys.modules['PySide6.QtWidgets'] = mock_qtwidgets
    sys.modules['PySide6.QtGui'] = mock_qtgui
    sys.modules['PySide6.QtNetwork'] = mock_qtnetwork
    sys.modules['qfluentwidgets'] = mock_fluent
    
    return True

# 尝试设置 Qt mock
_qt_mocked = _setup_qt_mocks()

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ==================== pytest 配置 ====================

def pytest_configure(config):
    """pytest 配置钩子"""
    config.addinivalue_line("markers", "unit: 单元测试")
    config.addinivalue_line("markers", "integration: 集成测试")
    config.addinivalue_line("markers", "e2e: 端到端测试")
    config.addinivalue_line("markers", "slow: 慢速测试")


def pytest_collection_modifyitems(config, items):
    """修改测试收集"""
    for item in items:
        # 自动标记测试类型
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "e2e" in item.nodeid or "end_to_end" in item.nodeid:
            item.add_marker(pytest.mark.e2e)
        else:
            item.add_marker(pytest.mark.unit)

from src.core.models import (
    DramaInfo, EpisodeInfo, VideoInfo, SearchResult,
    EpisodeList, CategoryResult, ApiResponse, ApiError,
    AppConfig, ThemeMode
)


# ==================== 事件循环配置 ====================

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环供异步测试使用"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ==================== 模拟数据 Fixtures ====================

@pytest.fixture
def sample_drama() -> DramaInfo:
    """示例短剧数据"""
    return DramaInfo(
        book_id="test_001",
        title="测试短剧",
        cover="https://example.com/cover.jpg",
        episode_cnt=20,
        intro="这是一部测试短剧的简介",
        type="都市",
        author="测试作者",
        play_cnt=10000
    )


@pytest.fixture
def sample_drama_list() -> list[DramaInfo]:
    """示例短剧列表"""
    return [
        DramaInfo(
            book_id=f"drama_{i}",
            title=f"短剧{i}",
            cover=f"https://example.com/cover_{i}.jpg",
            episode_cnt=10 + i,
            intro=f"短剧{i}的简介",
            type="都市" if i % 2 == 0 else "甜宠",
            author=f"作者{i}",
            play_cnt=1000 * i
        )
        for i in range(1, 6)
    ]


@pytest.fixture
def sample_episode() -> EpisodeInfo:
    """示例剧集数据"""
    return EpisodeInfo(
        video_id="video_001",
        title="第1集",
        episode_number=1,
        chapter_word_number=0
    )


@pytest.fixture
def sample_episode_list(sample_drama: DramaInfo) -> EpisodeList:
    """示例剧集列表"""
    episodes = [
        EpisodeInfo(
            video_id=f"video_{i:03d}",
            title=f"第{i}集",
            episode_number=i,
            chapter_word_number=0
        )
        for i in range(1, 21)
    ]
    return EpisodeList(
        code=200,
        book_name=sample_drama.title,
        episodes=episodes,
        total=20,
        book_id=sample_drama.book_id,
        author=sample_drama.author,
        category=sample_drama.type,
        desc=sample_drama.intro,
        book_pic=sample_drama.cover
    )


@pytest.fixture
def sample_video_info() -> VideoInfo:
    """示例视频信息"""
    return VideoInfo(
        code=200,
        url="https://example.com/video.m3u8",
        pic="https://example.com/pic.jpg",
        quality="1080p",
        title="第1集",
        duration="00:05:30",
        size_str="50MB"
    )


@pytest.fixture
def sample_search_result(sample_drama_list: list[DramaInfo]) -> SearchResult:
    """示例搜索结果"""
    return SearchResult(
        code=200,
        msg="搜索成功",
        data=sample_drama_list,
        page=1
    )


@pytest.fixture
def sample_category_result(sample_drama_list: list[DramaInfo]) -> CategoryResult:
    """示例分类结果"""
    return CategoryResult(
        code=200,
        category="都市",
        data=sample_drama_list,
        offset=1
    )


@pytest.fixture
def sample_api_response() -> ApiResponse:
    """示例 API 响应"""
    return ApiResponse(
        status_code=200,
        body='{"code": 200, "msg": "success", "data": []}',
        error="",
        success=True
    )


@pytest.fixture
def sample_api_error() -> ApiError:
    """示例 API 错误"""
    return ApiError(
        code=500,
        message="服务器内部错误",
        details="Connection timeout"
    )


@pytest.fixture
def sample_config() -> AppConfig:
    """示例应用配置"""
    return AppConfig(
        api_timeout=10000,
        default_quality="1080p",
        theme_mode=ThemeMode.AUTO,
        current_provider="cenguigui",
        enable_cache=True,
        cache_ttl=300000,
        max_retries=3
    )


# ==================== Mock Fixtures ====================

@pytest.fixture
def mock_api_client() -> MagicMock:
    """模拟 API 客户端"""
    client = MagicMock()
    client.get = AsyncMock(return_value=ApiResponse(
        status_code=200,
        body='{"code": 200, "data": []}',
        success=True
    ))
    client.set_timeout = MagicMock()
    client.base_url = "https://api.example.com"
    client.timeout = 10000
    return client


@pytest.fixture
def mock_cache_manager() -> MagicMock:
    """模拟缓存管理器"""
    cache = MagicMock()
    cache.get = MagicMock(return_value=None)
    cache.set = MagicMock()
    cache.clear = MagicMock()
    cache.generate_key = MagicMock(side_effect=lambda *args: "_".join(args))
    return cache


@pytest.fixture
def mock_provider() -> MagicMock:
    """模拟数据提供者"""
    provider = MagicMock()
    provider.info = MagicMock()
    provider.info.id = "test_provider"
    provider.info.name = "测试提供者"
    provider.search = AsyncMock()
    provider.get_categories = AsyncMock(return_value=["都市", "甜宠", "悬疑"])
    provider.get_category_dramas = AsyncMock()
    provider.get_episodes = AsyncMock()
    provider.get_video_url = AsyncMock()
    provider.get_recommendations = AsyncMock()
    return provider


# ==================== 辅助函数 ====================

def create_mock_response(data: dict, success: bool = True) -> ApiResponse:
    """创建模拟 API 响应"""
    import json
    return ApiResponse(
        status_code=200 if success else 500,
        body=json.dumps(data),
        error="" if success else "Error",
        success=success
    )


# ==================== 临时目录 Fixtures ====================

@pytest.fixture
def temp_dir(tmp_path):
    """创建临时目录"""
    return tmp_path


@pytest.fixture
def temp_config_file(tmp_path):
    """创建临时配置文件"""
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.json"


@pytest.fixture
def temp_data_dir(tmp_path):
    """创建临时数据目录"""
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@pytest.fixture
def temp_cache_dir(tmp_path):
    """创建临时缓存目录"""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


# ==================== 管理器 Fixtures ====================

@pytest.fixture
def cache_manager(temp_cache_dir):
    """创建缓存管理器"""
    from src.data.cache_manager import CacheManager
    return CacheManager(
        max_entries=100,
        enable_persistence=True,
        cache_dir=str(temp_cache_dir)
    )


@pytest.fixture
def config_manager(temp_config_file):
    """创建配置管理器"""
    from src.data.config_manager import ConfigManager
    return ConfigManager(str(temp_config_file))


@pytest.fixture
def favorites_manager(temp_data_dir):
    """创建收藏管理器"""
    from src.data.favorites_manager import FavoritesManager
    return FavoritesManager(str(temp_data_dir / "favorites.json"))


@pytest.fixture
def history_manager(temp_data_dir):
    """创建历史管理器"""
    from src.data.history_manager import HistoryManager
    return HistoryManager(str(temp_data_dir / "history.json"))


# ==================== API 响应 Fixtures ====================

@pytest.fixture
def mock_search_response_json():
    """模拟搜索响应 JSON"""
    import json
    return json.dumps({
        "code": 200,
        "msg": "搜索成功",
        "page": 1,
        "data": [
            {
                "book_id": "123",
                "title": "测试短剧",
                "cover": "https://example.com/cover.jpg",
                "episode_cnt": 20,
                "intro": "简介",
                "type": "都市",
                "author": "作者",
                "play_cnt": 10000
            }
        ]
    })


@pytest.fixture
def mock_episode_response_json():
    """模拟剧集响应 JSON"""
    import json
    return json.dumps({
        "code": 200,
        "book_name": "测试短剧",
        "book_id": "123",
        "total": 20,
        "data": [
            {"video_id": f"v{i}", "title": f"第{i}集", "chapter_word_number": 0}
            for i in range(1, 21)
        ]
    })


@pytest.fixture
def mock_video_response_json():
    """模拟视频响应 JSON"""
    import json
    return json.dumps({
        "code": 200,
        "data": {
            "url": "https://example.com/video.m3u8",
            "pic": "https://example.com/pic.jpg",
            "title": "第1集",
            "info": {
                "quality": "1080p",
                "duration": "05:30",
                "size_str": "50MB"
            }
        }
    })


@pytest.fixture
def mock_error_response_json():
    """模拟错误响应 JSON"""
    import json
    return json.dumps({
        "code": 500,
        "msg": "服务器内部错误",
        "tips": "请稍后重试"
    })


# ==================== 辅助函数 ====================

def assert_drama_valid(drama: DramaInfo):
    """断言短剧数据有效"""
    assert drama.book_id, "book_id 不能为空"
    assert drama.title, "title 不能为空"
    assert drama.cover, "cover 不能为空"


def assert_episode_valid(episode):
    """断言剧集数据有效"""
    from src.core.models import EpisodeInfo
    assert isinstance(episode, EpisodeInfo)
    assert episode.video_id, "video_id 不能为空"
    assert episode.title, "title 不能为空"


def assert_video_valid(video: VideoInfo):
    """断言视频数据有效"""
    assert video.url, "url 不能为空"
    assert video.url.startswith("http"), "url 必须是有效的 HTTP 地址"

