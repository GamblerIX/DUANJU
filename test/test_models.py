"""数据模型单元测试

测试 src/core/models.py 中定义的所有数据模型。
"""
from dataclasses import asdict
from pathlib import Path
import sys

import pytest

from src.core.models import (
    DramaInfo, EpisodeInfo, EpisodeList, VideoInfo, 
    SearchResult, CategoryResult
)
from src.core.models import (
    DramaInfo, EpisodeInfo, EpisodeList, VideoInfo,
    SearchResult, CategoryResult, ApiResponse, ApiError,
    AppConfig, ThemeMode
)

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.models import (
    DramaInfo, EpisodeInfo, VideoInfo, SearchResult,
    EpisodeList, CategoryResult, ApiResponse, ApiError,
    AppConfig, ThemeMode, PlaybackState, ErrorType,
    CacheEntry, FavoriteItem, HistoryItem
)


class TestDramaInfo:
    """DramaInfo 模型测试"""
    
    def test_create_drama_info(self, sample_drama: DramaInfo):
        """测试创建 DramaInfo"""
        assert sample_drama.book_id == "test_001"
        assert sample_drama.title == "测试短剧"
        assert sample_drama.episode_cnt == 20
    
    def test_drama_info_backward_compatibility(self, sample_drama: DramaInfo):
        """测试向后兼容属性"""
        assert sample_drama.name == sample_drama.title
        assert sample_drama.cover_url == sample_drama.cover
        assert sample_drama.episode_count == sample_drama.episode_cnt
        assert sample_drama.description == sample_drama.intro
        assert sample_drama.category == sample_drama.type
    
    def test_drama_info_equality(self):
        """测试 DramaInfo 相等性比较"""
        drama1 = DramaInfo(book_id="1", title="Test", cover="url")
        drama2 = DramaInfo(book_id="1", title="Test", cover="url")
        drama3 = DramaInfo(book_id="2", title="Test", cover="url")
        
        assert drama1 == drama2
        assert drama1 != drama3
        assert drama1 != "not a drama"
    
    def test_drama_info_default_values(self):
        """测试默认值"""
        drama = DramaInfo(book_id="1", title="Test", cover="url")
        assert drama.episode_cnt == 0
        assert drama.intro == ""
        assert drama.type == ""
        assert drama.author == ""
        assert drama.play_cnt == 0


class TestEpisodeInfo:
    """EpisodeInfo 模型测试"""
    
    def test_create_episode_info(self, sample_episode: EpisodeInfo):
        """测试创建 EpisodeInfo"""
        assert sample_episode.video_id == "video_001"
        assert sample_episode.title == "第1集"
        assert sample_episode.episode_number == 1
    
    def test_episode_info_equality(self):
        """测试 EpisodeInfo 相等性比较"""
        ep1 = EpisodeInfo(video_id="1", title="Ep1", episode_number=1)
        ep2 = EpisodeInfo(video_id="1", title="Ep1", episode_number=1)
        ep3 = EpisodeInfo(video_id="2", title="Ep2", episode_number=2)
        
        assert ep1 == ep2
        assert ep1 != ep3


class TestVideoInfo:
    """VideoInfo 模型测试"""
    
    def test_create_video_info(self, sample_video_info: VideoInfo):
        """测试创建 VideoInfo"""
        assert sample_video_info.code == 200
        assert sample_video_info.url == "https://example.com/video.m3u8"
        assert sample_video_info.quality == "1080p"
    
    def test_video_info_backward_compatibility(self, sample_video_info: VideoInfo):
        """测试向后兼容属性"""
        assert sample_video_info.video_url == sample_video_info.url
        assert sample_video_info.cover_url == sample_video_info.pic


class TestSearchResult:
    """SearchResult 模型测试"""
    
    def test_create_search_result(self, sample_search_result: SearchResult):
        """测试创建 SearchResult"""
        assert sample_search_result.code == 200
        assert len(sample_search_result.data) == 5
        assert sample_search_result.page == 1
    
    def test_search_result_backward_compatibility(self, sample_search_result: SearchResult):
        """测试向后兼容属性"""
        assert sample_search_result.title == sample_search_result.msg
        assert sample_search_result.current_page == sample_search_result.page
        assert sample_search_result.total_pages == 1


class TestEpisodeList:
    """EpisodeList 模型测试"""
    
    def test_create_episode_list(self, sample_episode_list: EpisodeList):
        """测试创建 EpisodeList"""
        assert sample_episode_list.code == 200
        assert len(sample_episode_list.episodes) == 20
        assert sample_episode_list.total == 20
    
    def test_episode_list_backward_compatibility(self, sample_episode_list: EpisodeList):
        """测试向后兼容属性"""
        assert sample_episode_list.drama_name == sample_episode_list.book_name


class TestApiResponse:
    """ApiResponse 模型测试"""
    
    def test_create_api_response(self, sample_api_response: ApiResponse):
        """测试创建 ApiResponse"""
        assert sample_api_response.status_code == 200
        assert sample_api_response.success is True
        assert sample_api_response.error == ""
    
    def test_api_response_failure(self):
        """测试失败的 API 响应"""
        response = ApiResponse(
            status_code=500,
            body="",
            error="Internal Server Error",
            success=False
        )
        assert response.success is False
        assert response.error == "Internal Server Error"


class TestApiError:
    """ApiError 模型测试"""
    
    def test_create_api_error(self, sample_api_error: ApiError):
        """测试创建 ApiError"""
        assert sample_api_error.code == 500
        assert sample_api_error.message == "服务器内部错误"
    
    def test_api_error_equality(self):
        """测试 ApiError 相等性比较"""
        err1 = ApiError(code=500, message="Error")
        err2 = ApiError(code=500, message="Error")
        err3 = ApiError(code=404, message="Not Found")
        
        assert err1 == err2
        assert err1 != err3


class TestAppConfig:
    """AppConfig 模型测试"""
    
    def test_create_app_config(self, sample_config: AppConfig):
        """测试创建 AppConfig"""
        assert sample_config.api_timeout == 10000
        assert sample_config.theme_mode == ThemeMode.AUTO
        assert sample_config.current_provider == "cenguigui"
    
    def test_app_config_default_values(self):
        """测试默认配置值"""
        config = AppConfig()
        assert config.api_timeout == 10000
        assert config.default_quality == "1080p"
        assert config.theme_mode == ThemeMode.AUTO
        assert config.max_search_history == 20
        assert config.enable_cache is True
    
    def test_app_config_equality(self):
        """测试 AppConfig 相等性比较"""
        config1 = AppConfig()
        config2 = AppConfig()
        config3 = AppConfig(api_timeout=5000)
        
        assert config1 == config2
        assert config1 != config3


class TestCacheEntry:
    """CacheEntry 模型测试"""
    
    def test_cache_entry_not_expired(self):
        """测试未过期的缓存"""
        import time
        entry = CacheEntry(
            data="test_data",
            timestamp=time.time(),
            ttl=300000  # 5分钟
        )
        assert entry.is_expired(time.time()) is False
    
    def test_cache_entry_expired(self):
        """测试已过期的缓存"""
        import time
        entry = CacheEntry(
            data="test_data",
            timestamp=time.time() - 400,  # 400秒前
            ttl=300000  # 5分钟 = 300秒
        )
        assert entry.is_expired(time.time()) is True


class TestEnums:
    """枚举类型测试"""
    
    def test_theme_mode_values(self):
        """测试 ThemeMode 枚举值"""
        assert ThemeMode.LIGHT.value == "light"
        assert ThemeMode.DARK.value == "dark"
        assert ThemeMode.AUTO.value == "auto"
    
    def test_playback_state_values(self):
        """测试 PlaybackState 枚举值"""
        assert PlaybackState.STOPPED.value == "stopped"
        assert PlaybackState.PLAYING.value == "playing"
        assert PlaybackState.PAUSED.value == "paused"
        assert PlaybackState.BUFFERING.value == "buffering"
        assert PlaybackState.ERROR.value == "error"
    
    def test_error_type_values(self):
        """测试 ErrorType 枚举值"""
        assert ErrorType.NETWORK_ERROR.value == "network_error"
        assert ErrorType.TIMEOUT_ERROR.value == "timeout_error"
        assert ErrorType.PARSE_ERROR.value == "parse_error"
        assert ErrorType.API_ERROR.value == "api_error"




# ============================================================
# From: test_models_coverage.py
# ============================================================
class TestDramaInfoModel:
    """测试 DramaInfo 模型"""
    
    def test_basic_creation(self):
        """测试基本创建"""
        drama = DramaInfo(
            book_id="123",
            title="测试短剧",
            cover="https://example.com/cover.jpg",
            episode_cnt=20
        )
        
        assert drama.book_id == "123"
        assert drama.title == "测试短剧"
        assert drama.episode_cnt == 20
    
    def test_full_creation(self):
        """测试完整创建"""
        drama = DramaInfo(
            book_id="123",
            title="测试短剧",
            cover="https://example.com/cover.jpg",
            episode_cnt=20,
            intro="这是简介",
            type="都市",
            author="作者",
            play_cnt=10000
        )
        
        assert drama.intro == "这是简介"
        assert drama.type == "都市"
        assert drama.author == "作者"
        assert drama.play_cnt == 10000
    
    def test_name_property(self):
        """测试 name 属性"""
        drama = DramaInfo(
            book_id="123",
            title="测试短剧",
            cover="",
            episode_cnt=10
        )
        
        assert drama.name == "测试短剧"
    
    def test_episode_count_property(self):
        """测试 episode_count 属性"""
        drama = DramaInfo(
            book_id="123",
            title="测试短剧",
            cover="",
            episode_cnt=20
        )
        
        assert drama.episode_count == 20
    
    def test_category_property(self):
        """测试 category 属性"""
        drama = DramaInfo(
            book_id="123",
            title="测试短剧",
            cover="",
            episode_cnt=10,
            type="甜宠"
        )
        
        assert drama.category == "甜宠"
    
    def test_default_values(self):
        """测试默认值"""
        drama = DramaInfo(
            book_id="123",
            title="测试",
            cover="",
            episode_cnt=0
        )
        
        assert drama.intro == ""
        assert drama.type == ""
        assert drama.author == ""
        assert drama.play_cnt == 0


class TestEpisodeInfoModel:
    """测试 EpisodeInfo 模型"""
    
    def test_basic_creation(self):
        """测试基本创建"""
        episode = EpisodeInfo(
            video_id="v001",
            title="第1集",
            episode_number=1
        )
        
        assert episode.video_id == "v001"
        assert episode.title == "第1集"
        assert episode.episode_number == 1
    
    def test_with_chapter_word_number(self):
        """测试带字数"""
        episode = EpisodeInfo(
            video_id="v001",
            title="第1集",
            episode_number=1,
            chapter_word_number=5000
        )
        
        assert episode.chapter_word_number == 5000
    
    def test_default_chapter_word_number(self):
        """测试默认字数"""
        episode = EpisodeInfo(
            video_id="v001",
            title="第1集",
            episode_number=1
        )
        
        assert episode.chapter_word_number == 0


class TestEpisodeListModel:
    """测试 EpisodeList 模型"""
    
    def test_basic_creation(self):
        """测试基本创建"""
        episodes = [
            EpisodeInfo(video_id=f"v{i}", title=f"第{i}集", episode_number=i)
            for i in range(1, 6)
        ]
        
        episode_list = EpisodeList(
            code=200,
            book_name="测试短剧",
            episodes=episodes,
            total=5,
            book_id="123"
        )
        
        assert episode_list.code == 200
        assert episode_list.book_name == "测试短剧"
        assert len(episode_list.episodes) == 5
        assert episode_list.total == 5
    
    def test_full_creation(self):
        """测试完整创建"""
        episode_list = EpisodeList(
            code=200,
            book_name="测试短剧",
            episodes=[],
            total=20,
            book_id="123",
            author="作者",
            category="都市",
            desc="描述",
            duration="05:00",
            book_pic="https://example.com/pic.jpg"
        )
        
        assert episode_list.author == "作者"
        assert episode_list.category == "都市"
        assert episode_list.desc == "描述"
        assert episode_list.duration == "05:00"
        assert episode_list.book_pic == "https://example.com/pic.jpg"


class TestVideoInfoModel:
    """测试 VideoInfo 模型"""
    
    def test_basic_creation(self):
        """测试基本创建"""
        video = VideoInfo(
            code=200,
            url="https://example.com/video.m3u8"
        )
        
        assert video.code == 200
        assert video.url == "https://example.com/video.m3u8"
    
    def test_full_creation(self):
        """测试完整创建"""
        video = VideoInfo(
            code=200,
            url="https://example.com/video.m3u8",
            pic="https://example.com/pic.jpg",
            quality="1080p",
            title="第1集",
            duration="05:30",
            size_str="50MB"
        )
        
        assert video.pic == "https://example.com/pic.jpg"
        assert video.quality == "1080p"
        assert video.title == "第1集"
        assert video.duration == "05:30"
        assert video.size_str == "50MB"


class TestSearchResultModel:
    """测试 SearchResult 模型"""
    
    def test_basic_creation(self):
        """测试基本创建"""
        result = SearchResult(
            code=200,
            msg="success",
            data=[],
            page=1
        )
        
        assert result.code == 200
        assert result.msg == "success"
        assert result.data == []
        assert result.page == 1
    
    def test_with_data(self):
        """测试带数据"""
        dramas = [
            DramaInfo(book_id=f"{i}", title=f"短剧{i}", cover="", episode_cnt=10)
            for i in range(1, 4)
        ]
        
        result = SearchResult(
            code=200,
            msg="success",
            data=dramas,
            page=1
        )
        
        assert len(result.data) == 3


class TestCategoryResultModel:
    """测试 CategoryResult 模型"""
    
    def test_basic_creation(self):
        """测试基本创建"""
        result = CategoryResult(
            code=200,
            category="都市",
            data=[],
            offset=1
        )
        
        assert result.code == 200
        assert result.category == "都市"
        assert result.offset == 1


class TestApiResponseModel:
    """测试 ApiResponse 模型"""
    
    def test_success_response(self):
        """测试成功响应"""
        response = ApiResponse(
            status_code=200,
            body='{"code": 200, "data": []}',
            error="",
            success=True
        )
        
        assert response.status_code == 200
        assert response.success is True
        assert response.error == ""
    
    def test_error_response(self):
        """测试错误响应"""
        response = ApiResponse(
            status_code=500,
            body="",
            error="Internal Server Error",
            success=False
        )
        
        assert response.status_code == 500
        assert response.success is False
        assert response.error == "Internal Server Error"


class TestApiErrorModel:
    """测试 ApiError 模型"""
    
    def test_basic_creation(self):
        """测试基本创建"""
        error = ApiError(
            code=500,
            message="服务器错误"
        )
        
        assert error.code == 500
        assert error.message == "服务器错误"
    
    def test_with_details(self):
        """测试带详情"""
        error = ApiError(
            code=500,
            message="服务器错误",
            details="Connection timeout"
        )
        
        assert error.details == "Connection timeout"


class TestAppConfigModel:
    """测试 AppConfig 模型"""
    
    def test_basic_creation(self):
        """测试基本创建"""
        config = AppConfig(
            api_timeout=10000,
            default_quality="1080p",
            theme_mode=ThemeMode.AUTO,
            current_provider="cenguigui"
        )
        
        assert config.api_timeout == 10000
        assert config.default_quality == "1080p"
        assert config.theme_mode == ThemeMode.AUTO
        assert config.current_provider == "cenguigui"
    
    def test_full_creation(self):
        """测试完整创建"""
        config = AppConfig(
            api_timeout=10000,
            default_quality="1080p",
            theme_mode=ThemeMode.DARK,
            current_provider="cenguigui",
            enable_cache=True,
            cache_ttl=300000,
            max_retries=3
        )
        
        assert config.enable_cache is True
        assert config.cache_ttl == 300000
        assert config.max_retries == 3


class TestThemeModeEnum:
    """测试 ThemeMode 枚举"""
    
    def test_auto_mode(self):
        """测试自动模式"""
        mode = ThemeMode.AUTO
        assert mode == ThemeMode.AUTO
    
    def test_light_mode(self):
        """测试浅色模式"""
        mode = ThemeMode.LIGHT
        assert mode == ThemeMode.LIGHT
    
    def test_dark_mode(self):
        """测试深色模式"""
        mode = ThemeMode.DARK
        assert mode == ThemeMode.DARK
    
    def test_mode_comparison(self):
        """测试模式比较"""
        assert ThemeMode.AUTO != ThemeMode.LIGHT
        assert ThemeMode.LIGHT != ThemeMode.DARK
        assert ThemeMode.AUTO == ThemeMode.AUTO



# ============================================================
# From: test_models_full_coverage.py
# ============================================================
class TestDramaInfoEdgeCases:
    """测试 DramaInfo 边界情况"""
    
    def test_drama_info_minimal(self):
        """测试最小 DramaInfo"""
        drama = DramaInfo(book_id="1", title="", cover="")
        
        assert drama.book_id == "1"
        assert drama.title == ""
        assert drama.cover == ""
        assert drama.episode_cnt == 0
    
    def test_drama_info_full(self):
        """测试完整 DramaInfo"""
        drama = DramaInfo(
            book_id="123",
            title="测试短剧",
            cover="http://cover.jpg",
            episode_cnt=20,
            intro="这是简介",
            type="都市",
            author="作者",
            play_cnt=10000
        )
        
        assert drama.book_id == "123"
        assert drama.title == "测试短剧"
        assert drama.cover == "http://cover.jpg"
        assert drama.episode_cnt == 20
        assert drama.intro == "这是简介"
        assert drama.type == "都市"
        assert drama.author == "作者"
        assert drama.play_cnt == 10000
    
    def test_drama_info_name_property(self):
        """测试 name 属性"""
        drama = DramaInfo(book_id="1", title="测试", cover="")
        
        # name 应该是 title 的别名
        assert drama.name == "测试"


class TestEpisodeInfoEdgeCases:
    """测试 EpisodeInfo 边界情况"""
    
    def test_episode_info_minimal(self):
        """测试最小 EpisodeInfo"""
        episode = EpisodeInfo(video_id="v1", title="")
        
        assert episode.video_id == "v1"
        assert episode.title == ""
        assert episode.episode_number == 0
    
    def test_episode_info_full(self):
        """测试完整 EpisodeInfo"""
        episode = EpisodeInfo(
            video_id="v1",
            title="第1集",
            episode_number=1,
            chapter_word_number=100
        )
        
        assert episode.video_id == "v1"
        assert episode.title == "第1集"
        assert episode.episode_number == 1
        assert episode.chapter_word_number == 100


class TestEpisodeListEdgeCases:
    """测试 EpisodeList 边界情况"""
    
    def test_episode_list_minimal(self):
        """测试最小 EpisodeList"""
        ep_list = EpisodeList(code=200, book_name="测试", episodes=[], total=0)
        
        assert ep_list.code == 200
        assert ep_list.book_name == "测试"
        assert len(ep_list.episodes) == 0
        assert ep_list.total == 0
    
    def test_episode_list_full(self):
        """测试完整 EpisodeList"""
        episodes = [
            EpisodeInfo(video_id="v1", title="第1集", episode_number=1),
            EpisodeInfo(video_id="v2", title="第2集", episode_number=2)
        ]
        
        ep_list = EpisodeList(
            code=200,
            book_name="测试短剧",
            episodes=episodes,
            total=20,
            book_id="123",
            author="作者",
            category="都市",
            desc="描述",
            duration="05:00",
            book_pic="http://pic.jpg"
        )
        
        assert ep_list.code == 200
        assert ep_list.book_name == "测试短剧"
        assert len(ep_list.episodes) == 2
        assert ep_list.total == 20
        assert ep_list.book_id == "123"
        assert ep_list.author == "作者"
        assert ep_list.category == "都市"
        assert ep_list.desc == "描述"
        assert ep_list.duration == "05:00"
        assert ep_list.book_pic == "http://pic.jpg"


class TestVideoInfoEdgeCases:
    """测试 VideoInfo 边界情况"""
    
    def test_video_info_minimal(self):
        """测试最小 VideoInfo"""
        video = VideoInfo(code=200, url="http://video.m3u8")
        
        assert video.code == 200
        assert video.url == "http://video.m3u8"
        assert video.pic == ""
        assert video.quality == ""
    
    def test_video_info_full(self):
        """测试完整 VideoInfo"""
        video = VideoInfo(
            code=200,
            url="http://video.m3u8",
            pic="http://pic.jpg",
            quality="1080p",
            title="第1集",
            duration="05:30",
            size_str="50MB"
        )
        
        assert video.code == 200
        assert video.url == "http://video.m3u8"
        assert video.pic == "http://pic.jpg"
        assert video.quality == "1080p"
        assert video.title == "第1集"
        assert video.duration == "05:30"
        assert video.size_str == "50MB"


class TestSearchResultEdgeCases:
    """测试 SearchResult 边界情况"""
    
    def test_search_result_empty(self):
        """测试空搜索结果"""
        result = SearchResult(code=200, msg="success", data=[], page=1)
        
        assert result.code == 200
        assert result.msg == "success"
        assert len(result.data) == 0
        assert result.page == 1
    
    def test_search_result_with_data(self):
        """测试带数据的搜索结果"""
        dramas = [
            DramaInfo(book_id="1", title="短剧1", cover=""),
            DramaInfo(book_id="2", title="短剧2", cover="")
        ]
        
        result = SearchResult(code=200, msg="success", data=dramas, page=1)
        
        assert len(result.data) == 2
        assert result.data[0].title == "短剧1"
    
    def test_search_result_error(self):
        """测试错误搜索结果"""
        result = SearchResult(code=500, msg="服务器错误", data=[], page=1)
        
        assert result.code == 500
        assert result.msg == "服务器错误"


class TestCategoryResultEdgeCases:
    """测试 CategoryResult 边界情况"""
    
    def test_category_result_empty(self):
        """测试空分类结果"""
        result = CategoryResult(code=200, category="都市", data=[], offset=1)
        
        assert result.code == 200
        assert result.category == "都市"
        assert len(result.data) == 0
        assert result.offset == 1
    
    def test_category_result_with_data(self):
        """测试带数据的分类结果"""
        dramas = [
            DramaInfo(book_id="1", title="短剧1", cover=""),
            DramaInfo(book_id="2", title="短剧2", cover="")
        ]
        
        result = CategoryResult(code=200, category="都市", data=dramas, offset=2)
        
        assert len(result.data) == 2
        assert result.offset == 2


class TestModelEquality:
    """测试模型相等性"""
    
    def test_drama_info_equality(self):
        """测试 DramaInfo 相等性"""
        drama1 = DramaInfo(book_id="1", title="测试", cover="")
        drama2 = DramaInfo(book_id="1", title="测试", cover="")
        drama3 = DramaInfo(book_id="2", title="测试", cover="")
        
        assert drama1 == drama2
        assert drama1 != drama3
    
    def test_episode_info_equality(self):
        """测试 EpisodeInfo 相等性"""
        ep1 = EpisodeInfo(video_id="v1", title="第1集")
        ep2 = EpisodeInfo(video_id="v1", title="第1集")
        ep3 = EpisodeInfo(video_id="v2", title="第1集")
        
        assert ep1 == ep2
        assert ep1 != ep3
