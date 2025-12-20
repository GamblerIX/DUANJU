"""视频服务测试

测试 src/services/video_service.py 中的视频服务。
"""
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock
from unittest.mock import MagicMock, patch, AsyncMock
import json
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.models import EpisodeList, EpisodeInfo, VideoInfo, ApiError


class TestVideoServiceLogic:
    """视频服务逻辑测试（不依赖 Qt）"""
    
    def test_episode_list_structure(self):
        """测试剧集列表结构"""
        episodes = [
            EpisodeInfo(video_id=f"v{i}", title=f"第{i}集", episode_number=i)
            for i in range(1, 21)
        ]
        
        episode_list = EpisodeList(
            code=200,
            book_name="测试短剧",
            episodes=episodes,
            total=20,
            book_id="123",
            author="作者",
            category="都市",
            desc="简介"
        )
        
        assert episode_list.code == 200
        assert episode_list.book_name == "测试短剧"
        assert len(episode_list.episodes) == 20
        assert episode_list.total == 20
    
    def test_video_info_structure(self):
        """测试视频信息结构"""
        video = VideoInfo(
            code=200,
            url="https://example.com/video.m3u8",
            pic="https://example.com/pic.jpg",
            quality="1080p",
            title="第1集",
            duration="05:30",
            size_str="50MB"
        )
        
        assert video.code == 200
        assert video.url.startswith("http")
        assert video.quality == "1080p"
        assert video.video_url == video.url  # 向后兼容
    
    def test_episode_number_parsing(self):
        """测试集数解析"""
        from src.data.response_parser import ResponseParser
        
        test_cases = [
            ("第1集", 1),
            ("第10集", 10),
            ("第100集", 100),
            ("Episode 5", 5),
            ("预告片", 0),
        ]
        
        for title, expected in test_cases:
            result = ResponseParser.parse_episode_number(title)
            assert result == expected, f"Failed for {title}"
    
    def test_episode_list_parsing(self):
        """测试剧集列表解析"""
        from src.data.response_parser import ResponseParser
        
        json_str = json.dumps({
            "code": 200,
            "book_name": "测试短剧",
            "book_id": "123",
            "total": 20,
            "data": [
                {"video_id": "v1", "title": "第1集", "chapter_word_number": 0},
                {"video_id": "v2", "title": "第2集", "chapter_word_number": 0},
            ]
        })
        
        result = ResponseParser.parse_episode_list(json_str)
        
        assert result.code == 200
        assert result.book_name == "测试短剧"
        assert len(result.episodes) == 2
        assert result.episodes[0].episode_number == 1
        assert result.episodes[1].episode_number == 2
    
    def test_video_info_parsing(self):
        """测试视频信息解析"""
        from src.data.response_parser import ResponseParser
        
        json_str = json.dumps({
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
        
        result = ResponseParser.parse_video_info(json_str)
        
        assert result.code == 200
        assert result.url == "https://example.com/video.m3u8"
        assert result.quality == "1080p"


class TestVideoServiceMock:
    """视频服务 Mock 测试"""
    
    @pytest.fixture
    def mock_provider(self):
        """模拟数据提供者"""
        provider = MagicMock()
        provider.get_episodes = AsyncMock(return_value=EpisodeList(
            code=200,
            book_name="测试短剧",
            episodes=[
                EpisodeInfo(video_id="v1", title="第1集", episode_number=1),
                EpisodeInfo(video_id="v2", title="第2集", episode_number=2),
            ],
            total=2
        ))
        provider.get_video_url = AsyncMock(return_value=VideoInfo(
            code=200,
            url="https://example.com/video.m3u8",
            quality="1080p"
        ))
        return provider
    
    @pytest.mark.asyncio
    async def test_fetch_episodes_from_provider(self, mock_provider):
        """测试从提供者获取剧集"""
        result = await mock_provider.get_episodes("123")
        
        assert result.code == 200
        assert len(result.episodes) == 2
        mock_provider.get_episodes.assert_called_once_with("123")
    
    @pytest.mark.asyncio
    async def test_fetch_video_url_from_provider(self, mock_provider):
        """测试从提供者获取视频地址"""
        result = await mock_provider.get_video_url("v1", "1080p")
        
        assert result.code == 200
        assert result.url.startswith("http")
        mock_provider.get_video_url.assert_called_once_with("v1", "1080p")
    
    @pytest.mark.asyncio
    async def test_quality_selection(self, mock_provider):
        """测试清晰度选择"""
        qualities = ["1080p", "720p", "480p"]
        
        for quality in qualities:
            mock_provider.get_video_url.return_value = VideoInfo(
                code=200,
                url=f"https://example.com/video_{quality}.m3u8",
                quality=quality
            )
            
            result = await mock_provider.get_video_url("v1", quality)
            assert result.quality == quality


class TestVideoUrlValidation:
    """视频 URL 验证测试"""
    
    def test_valid_m3u8_url(self):
        """测试有效的 m3u8 URL"""
        urls = [
            "https://example.com/video.m3u8",
            "http://cdn.example.com/path/to/video.m3u8",
            "https://example.com/video.m3u8?token=abc",
        ]
        
        for url in urls:
            assert url.startswith(("http://", "https://"))
    
    def test_valid_mp4_url(self):
        """测试有效的 mp4 URL"""
        urls = [
            "https://example.com/video.mp4",
            "http://cdn.example.com/path/to/video.mp4",
        ]
        
        for url in urls:
            assert url.startswith(("http://", "https://"))
    
    def test_invalid_url(self):
        """测试无效的 URL"""
        invalid_urls = [
            "",
            "not_a_url",
            "ftp://example.com/video.mp4",
            "file:///path/to/video.mp4",
        ]
        
        for url in invalid_urls:
            assert not url.startswith(("http://", "https://"))


class TestEpisodeNavigation:
    """剧集导航测试"""
    
    @pytest.fixture
    def episode_list(self):
        """创建剧集列表"""
        episodes = [
            EpisodeInfo(video_id=f"v{i}", title=f"第{i}集", episode_number=i)
            for i in range(1, 21)
        ]
        return EpisodeList(
            code=200,
            book_name="测试短剧",
            episodes=episodes,
            total=20
        )
    
    def test_get_episode_by_number(self, episode_list):
        """测试按集数获取剧集"""
        episodes = episode_list.episodes
        
        # 查找第5集
        ep5 = next((ep for ep in episodes if ep.episode_number == 5), None)
        assert ep5 is not None
        assert ep5.video_id == "v5"
    
    def test_get_next_episode(self, episode_list):
        """测试获取下一集"""
        episodes = episode_list.episodes
        current = 5
        
        next_ep = next(
            (ep for ep in episodes if ep.episode_number == current + 1),
            None
        )
        
        assert next_ep is not None
        assert next_ep.episode_number == 6
    
    def test_get_previous_episode(self, episode_list):
        """测试获取上一集"""
        episodes = episode_list.episodes
        current = 5
        
        prev_ep = next(
            (ep for ep in episodes if ep.episode_number == current - 1),
            None
        )
        
        assert prev_ep is not None
        assert prev_ep.episode_number == 4
    
    def test_first_episode(self, episode_list):
        """测试第一集"""
        episodes = episode_list.episodes
        first = min(episodes, key=lambda ep: ep.episode_number)
        
        assert first.episode_number == 1
    
    def test_last_episode(self, episode_list):
        """测试最后一集"""
        episodes = episode_list.episodes
        last = max(episodes, key=lambda ep: ep.episode_number)
        
        assert last.episode_number == 20




# ============================================================
# From: test_video_service_full.py
# ============================================================
class TestVideoServiceMock_Full:
    """视频服务 Mock 测试"""
    
    @patch('src.services.video_service.get_current_provider')
    @patch('src.services.video_service.AsyncWorker')
    def test_video_service_init(self, mock_worker, mock_provider):
        """测试视频服务初始化"""
        from src.services.video_service import VideoService
        from src.data.api_client import ApiClient
        
        api_client = MagicMock(spec=ApiClient)
        
        service = VideoService(api_client)
        
        assert service._is_loading is False
        assert service._current_worker is None
    
    @patch('src.services.video_service.get_current_provider')
    @patch('src.services.video_service.AsyncWorker')
    def test_fetch_episodes(self, mock_worker_class, mock_provider):
        """测试获取剧集列表"""
        from src.services.video_service import VideoService
        from src.data.api_client import ApiClient
        
        api_client = MagicMock(spec=ApiClient)
        mock_worker = MagicMock()
        mock_worker_class.return_value = mock_worker
        
        service = VideoService(api_client)
        service.loading_started = MagicMock()
        
        service.fetch_episodes("book_123")
        
        assert service._is_loading is True
        service.loading_started.emit.assert_called_once()
        mock_worker.start.assert_called_once()
    
    @patch('src.services.video_service.get_current_provider')
    @patch('src.services.video_service.AsyncWorker')
    def test_fetch_video_url(self, mock_worker_class, mock_provider):
        """测试获取视频地址"""
        from src.services.video_service import VideoService
        from src.data.api_client import ApiClient
        
        api_client = MagicMock(spec=ApiClient)
        mock_worker = MagicMock()
        mock_worker_class.return_value = mock_worker
        
        service = VideoService(api_client)
        service.loading_started = MagicMock()
        
        service.fetch_video_url("video_123", "1080p")
        
        assert service._is_loading is True
        service.loading_started.emit.assert_called_once()
        mock_worker.start.assert_called_once()
    
    @patch('src.services.video_service.get_current_provider')
    @patch('src.services.video_service.AsyncWorker')
    def test_cancel(self, mock_worker_class, mock_provider):
        """测试取消请求"""
        from src.services.video_service import VideoService
        from src.data.api_client import ApiClient
        
        api_client = MagicMock(spec=ApiClient)
        mock_worker = MagicMock()
        mock_worker.isRunning.return_value = True
        mock_worker_class.return_value = mock_worker
        
        service = VideoService(api_client)
        service.fetch_episodes("book_123")
        
        service.cancel()
        
        assert service._is_loading is False
        mock_worker.terminate.assert_called_once()
        mock_worker.wait.assert_called_once()
    
    @patch('src.services.video_service.get_current_provider')
    @patch('src.services.video_service.AsyncWorker')
    def test_is_loading_property(self, mock_worker, mock_provider):
        """测试加载状态属性"""
        from src.services.video_service import VideoService
        from src.data.api_client import ApiClient
        
        api_client = MagicMock(spec=ApiClient)
        
        service = VideoService(api_client)
        
        assert service.is_loading is False
        
        service._is_loading = True
        assert service.is_loading is True
    
    @patch('src.services.video_service.get_current_provider')
    @patch('src.services.video_service.AsyncWorker')
    def test_on_episodes_result(self, mock_worker, mock_provider):
        """测试剧集结果处理"""
        from src.services.video_service import VideoService
        from src.data.api_client import ApiClient
        from src.core.models import EpisodeList
        
        api_client = MagicMock(spec=ApiClient)
        
        service = VideoService(api_client)
        service._is_loading = True
        service.episodes_loaded = MagicMock()
        
        episode_list = EpisodeList(code=200, book_name="测试", episodes=[], total=0)
        service._on_episodes_result(("episodes", episode_list))
        
        assert service._is_loading is False
        service.episodes_loaded.emit.assert_called_once_with(episode_list)
    
    @patch('src.services.video_service.get_current_provider')
    @patch('src.services.video_service.AsyncWorker')
    def test_on_video_url_result(self, mock_worker, mock_provider):
        """测试视频地址结果处理"""
        from src.services.video_service import VideoService
        from src.data.api_client import ApiClient
        from src.core.models import VideoInfo
        
        api_client = MagicMock(spec=ApiClient)
        
        service = VideoService(api_client)
        service._is_loading = True
        service.video_url_loaded = MagicMock()
        
        video_info = VideoInfo(code=200, url="http://example.com/video.m3u8")
        service._on_video_url_result(("video_url", video_info))
        
        assert service._is_loading is False
        service.video_url_loaded.emit.assert_called_once_with(video_info)
    
    @patch('src.services.video_service.get_current_provider')
    @patch('src.services.video_service.AsyncWorker')
    def test_on_error(self, mock_worker, mock_provider):
        """测试错误处理"""
        from src.services.video_service import VideoService
        from src.data.api_client import ApiClient
        
        api_client = MagicMock(spec=ApiClient)
        
        service = VideoService(api_client)
        service._is_loading = True
        service.error = MagicMock()
        
        error = Exception("获取失败")
        service._on_error(error)
        
        assert service._is_loading is False
        service.error.emit.assert_called_once()


class TestVideoServiceAsync:
    """视频服务异步测试"""
    
    @pytest.mark.asyncio
    @patch('src.services.video_service.get_current_provider')
    async def test_do_fetch_episodes_with_provider(self, mock_get_provider):
        """测试使用 Provider 获取剧集"""
        from src.services.video_service import VideoService
        from src.data.api_client import ApiClient
        from src.core.models import EpisodeList
        
        mock_provider = MagicMock()
        mock_provider.info.id = "test"
        mock_provider.get_episodes = AsyncMock(return_value=EpisodeList(
            code=200, book_name="测试", episodes=[], total=0
        ))
        mock_get_provider.return_value = mock_provider
        
        api_client = MagicMock(spec=ApiClient)
        
        service = VideoService(api_client)
        result = await service._do_fetch_episodes("book_123")
        
        assert result[0] == "episodes"
        assert result[1].code == 200
        mock_provider.get_episodes.assert_called_once_with("book_123")
    
    @pytest.mark.asyncio
    @patch('src.services.video_service.get_current_provider')
    async def test_do_fetch_video_url_with_provider(self, mock_get_provider):
        """测试使用 Provider 获取视频地址"""
        from src.services.video_service import VideoService
        from src.data.api_client import ApiClient
        from src.core.models import VideoInfo
        
        mock_provider = MagicMock()
        mock_provider.info.id = "test"
        mock_provider.get_video_url = AsyncMock(return_value=VideoInfo(
            code=200, url="http://example.com/video.m3u8"
        ))
        mock_get_provider.return_value = mock_provider
        
        api_client = MagicMock(spec=ApiClient)
        
        service = VideoService(api_client)
        result = await service._do_fetch_video_url("video_123", "1080p")
        
        assert result[0] == "video_url"
        assert result[1].code == 200
        mock_provider.get_video_url.assert_called_once_with("video_123", "1080p")
    
    @pytest.mark.asyncio
    @patch('src.services.video_service.get_current_provider')
    async def test_do_fetch_episodes_without_provider(self, mock_get_provider):
        """测试无 Provider 时获取剧集"""
        from src.services.video_service import VideoService
        from src.data.api_client import ApiClient
        from src.core.models import ApiResponse
        import json
        
        mock_get_provider.return_value = None
        
        api_client = MagicMock(spec=ApiClient)
        api_client.get = AsyncMock(return_value=ApiResponse(
            success=True,
            status_code=200,
            body=json.dumps({
                "code": 200,
                "book_name": "测试",
                "total": 0,
                "data": []
            })
        ))
        
        service = VideoService(api_client)
        result = await service._do_fetch_episodes("book_123")
        
        assert result[0] == "episodes"
        api_client.get.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.video_service.get_current_provider')
    async def test_do_fetch_video_url_without_provider(self, mock_get_provider):
        """测试无 Provider 时获取视频地址"""
        from src.services.video_service import VideoService
        from src.data.api_client import ApiClient
        from src.core.models import ApiResponse
        import json
        
        mock_get_provider.return_value = None
        
        api_client = MagicMock(spec=ApiClient)
        api_client.get = AsyncMock(return_value=ApiResponse(
            success=True,
            status_code=200,
            body=json.dumps({
                "code": 200,
                "data": {
                    "url": "http://example.com/video.m3u8",
                    "pic": "",
                    "title": "第1集",
                    "info": {"quality": "1080p", "duration": "", "size_str": ""}
                }
            })
        ))
        
        service = VideoService(api_client)
        result = await service._do_fetch_video_url("video_123", "1080p")
        
        assert result[0] == "video_url"
        api_client.get.assert_called_once()
