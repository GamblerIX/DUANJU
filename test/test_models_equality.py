"""数据模型相等性测试"""
import pytest
from src.core.models import (
    DramaInfo, EpisodeInfo, VideoInfo, SearchResult, 
    CategoryResult, EpisodeList, ApiError, FavoriteItem, HistoryItem
)


class TestEpisodeInfoEquality:
    """剧集信息相等性测试"""
    
    def test_equal_episodes(self):
        """测试相等的剧集"""
        ep1 = EpisodeInfo(
            video_id="v001",
            title="第1集",
            episode_number=1,
            chapter_word_number=1000
        )
        ep2 = EpisodeInfo(
            video_id="v001",
            title="第1集",
            episode_number=1,
            chapter_word_number=1000
        )
        
        assert ep1 == ep2
    
    def test_not_equal_episodes(self):
        """测试不相等的剧集"""
        ep1 = EpisodeInfo(video_id="v001", title="第1集", episode_number=1)
        ep2 = EpisodeInfo(video_id="v002", title="第2集", episode_number=2)
        
        assert ep1 != ep2
    
    def test_not_equal_to_other_type(self):
        """测试与其他类型不相等"""
        ep = EpisodeInfo(video_id="v001", title="第1集", episode_number=1)
        
        result = ep.__eq__("not an episode")
        assert result is NotImplemented


class TestFavoriteItemEquality:
    """收藏项相等性测试"""
    
    def test_equal_favorites(self):
        """测试相等的收藏项"""
        drama = DramaInfo(book_id="d001", title="测试", cover="", episode_cnt=10)
        
        fav1 = FavoriteItem(drama=drama, added_time=1000.0)
        fav2 = FavoriteItem(drama=drama, added_time=1000.0)
        
        assert fav1 == fav2
    
    def test_not_equal_favorites(self):
        """测试不相等的收藏项"""
        drama1 = DramaInfo(book_id="d001", title="测试1", cover="", episode_cnt=10)
        drama2 = DramaInfo(book_id="d002", title="测试2", cover="", episode_cnt=20)
        
        fav1 = FavoriteItem(drama=drama1, added_time=1000.0)
        fav2 = FavoriteItem(drama=drama2, added_time=2000.0)
        
        assert fav1 != fav2
    
    def test_not_equal_to_other_type(self):
        """测试与其他类型不相等"""
        drama = DramaInfo(book_id="d001", title="测试", cover="", episode_cnt=10)
        fav = FavoriteItem(drama=drama, added_time=1000.0)
        
        result = fav.__eq__("not a favorite")
        assert result is NotImplemented


class TestHistoryItemEquality:
    """历史项相等性测试"""
    
    def test_equal_history(self):
        """测试相等的历史项"""
        drama = DramaInfo(book_id="d001", title="测试", cover="", episode_cnt=10)
        
        hist1 = HistoryItem(
            drama=drama,
            episode_number=1,
            position_ms=5000,
            watch_time=1000.0
        )
        hist2 = HistoryItem(
            drama=drama,
            episode_number=1,
            position_ms=5000,
            watch_time=1000.0
        )
        
        assert hist1 == hist2
    
    def test_not_equal_history(self):
        """测试不相等的历史项"""
        drama = DramaInfo(book_id="d001", title="测试", cover="", episode_cnt=10)
        
        hist1 = HistoryItem(drama=drama, episode_number=1, position_ms=5000, watch_time=1000.0)
        hist2 = HistoryItem(drama=drama, episode_number=2, position_ms=10000, watch_time=2000.0)
        
        assert hist1 != hist2
    
    def test_not_equal_to_other_type(self):
        """测试与其他类型不相等"""
        drama = DramaInfo(book_id="d001", title="测试", cover="", episode_cnt=10)
        hist = HistoryItem(drama=drama, episode_number=1, position_ms=5000, watch_time=1000.0)
        
        result = hist.__eq__("not a history item")
        assert result is NotImplemented


class TestApiErrorEquality:
    """API 错误相等性测试"""
    
    def test_equal_errors(self):
        """测试相等的错误"""
        err1 = ApiError(code=400, message="Bad Request", details="")
        err2 = ApiError(code=400, message="Bad Request", details="")
        
        assert err1 == err2
    
    def test_not_equal_errors(self):
        """测试不相等的错误"""
        err1 = ApiError(code=400, message="Bad Request", details="")
        err2 = ApiError(code=500, message="Server Error", details="")
        
        assert err1 != err2
    
    def test_not_equal_to_other_type(self):
        """测试与其他类型不相等"""
        err = ApiError(code=400, message="Bad Request", details="")
        
        result = err.__eq__("not an error")
        assert result is NotImplemented


class TestDramaInfoEquality:
    """短剧信息相等性测试"""
    
    def test_equal_dramas(self):
        """测试相等的短剧"""
        drama1 = DramaInfo(
            book_id="d001",
            title="测试短剧",
            cover="https://example.com/cover.jpg",
            episode_cnt=10,
            intro="简介",
            type="言情",
            author="作者",
            play_cnt=1000
        )
        drama2 = DramaInfo(
            book_id="d001",
            title="测试短剧",
            cover="https://example.com/cover.jpg",
            episode_cnt=10,
            intro="简介",
            type="言情",
            author="作者",
            play_cnt=1000
        )
        
        assert drama1 == drama2
    
    def test_not_equal_dramas(self):
        """测试不相等的短剧"""
        drama1 = DramaInfo(book_id="d001", title="测试1", cover="", episode_cnt=10)
        drama2 = DramaInfo(book_id="d002", title="测试2", cover="", episode_cnt=20)
        
        assert drama1 != drama2


class TestVideoInfoEquality:
    """视频信息相等性测试"""
    
    def test_video_info_fields(self):
        """测试视频信息字段"""
        video = VideoInfo(
            code=200,
            url="https://example.com/video.mp4",
            pic="https://example.com/pic.jpg",
            quality="1080p",
            title="第1集",
            duration="10:00",
            size_str="100MB"
        )
        
        assert video.code == 200
        assert video.url == "https://example.com/video.mp4"
        assert video.video_url == "https://example.com/video.mp4"  # 向后兼容属性
        assert video.quality == "1080p"


class TestSearchResultEquality:
    """搜索结果相等性测试"""
    
    def test_search_result_fields(self):
        """测试搜索结果字段"""
        drama = DramaInfo(book_id="d001", title="测试", cover="", episode_cnt=10)
        result = SearchResult(
            code=200,
            msg="success",
            data=[drama],
            page=1
        )
        
        assert result.code == 200
        assert result.msg == "success"
        assert len(result.data) == 1
        assert result.page == 1


class TestCategoryResultEquality:
    """分类结果相等性测试"""
    
    def test_category_result_fields(self):
        """测试分类结果字段"""
        drama = DramaInfo(book_id="d001", title="测试", cover="", episode_cnt=10)
        result = CategoryResult(
            code=200,
            category="推荐榜",
            data=[drama],
            offset=1
        )
        
        assert result.code == 200
        assert result.category == "推荐榜"
        assert len(result.data) == 1
        assert result.offset == 1


class TestEpisodeListEquality:
    """剧集列表相等性测试"""
    
    def test_episode_list_fields(self):
        """测试剧集列表字段"""
        episode = EpisodeInfo(video_id="v001", title="第1集", episode_number=1)
        result = EpisodeList(
            code=200,
            book_name="测试短剧",
            episodes=[episode],
            total=1,
            book_id="d001",
            author="作者",
            category="言情",
            desc="描述",
            duration="10:00",
            book_pic="https://example.com/pic.jpg"
        )
        
        assert result.code == 200
        assert result.book_name == "测试短剧"
        assert len(result.episodes) == 1
        assert result.total == 1
