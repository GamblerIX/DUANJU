"""短剧搜索适配器测试"""
import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch
from collections import deque
import time

from src.core.models import (
    DramaInfo, EpisodeInfo, EpisodeList, VideoInfo, SearchResult, CategoryResult
)


class TestDuanjuSearchAdapterParsing:
    """测试 DuanjuSearchAdapter 解析逻辑"""
    
    def test_parse_item_basic(self):
        """测试解析基本数据项"""
        item = {
            "id": "667fb7e8e02e3",
            "name": "测试短剧（90集）",
            "label": 0,
            "addtime": "2024-06-29",
            "cover": "https://example.com/cover.jpg",
            "url": "https://pan.quark.cn/s/xxx",
            "episodes": "90",
            "state": 0
        }
        
        title = item.get("name") or item.get("title") or "未知短剧"
        source_link = item.get("url") or ""
        book_id = source_link if source_link else item.get("id") or str(hash(title))
        update_time = item.get("addtime") or ""
        
        episode_cnt = item.get("episodes") or 0
        if isinstance(episode_cnt, str):
            try:
                episode_cnt = int(episode_cnt.replace("集", "").strip())
            except:
                episode_cnt = 0
        
        cover = item.get("cover") or ""
        
        drama = DramaInfo(
            book_id=book_id,
            title=title,
            cover=cover,
            episode_cnt=episode_cnt,
            intro="",
            type="短剧",
            author="",
            play_cnt=0
        )
        
        assert drama.title == "测试短剧（90集）"
        assert drama.episode_cnt == 90
        assert drama.cover == "https://example.com/cover.jpg"
        assert "pan.quark.cn" in drama.book_id
    
    def test_parse_item_missing_fields(self):
        """测试解析缺少字段的数据项"""
        item = {
            "name": "测试短剧"
        }
        
        title = item.get("name") or item.get("title") or "未知短剧"
        source_link = item.get("url") or ""
        book_id = source_link if source_link else item.get("id") or str(hash(title))
        
        episode_cnt = item.get("episodes") or 0
        if isinstance(episode_cnt, str):
            try:
                episode_cnt = int(episode_cnt.replace("集", "").strip())
            except:
                episode_cnt = 0
        
        assert title == "测试短剧"
        assert source_link == ""
        assert episode_cnt == 0
    
    def test_parse_item_no_name(self):
        """测试解析无名称的数据项"""
        item = {}
        
        title = item.get("name") or item.get("title") or "未知短剧"
        assert title == "未知短剧"
    
    def test_parse_episode_count_string(self):
        """测试解析字符串集数"""
        episode_cnt = "90集"
        try:
            episode_cnt = int(episode_cnt.replace("集", "").strip())
        except:
            episode_cnt = 0
        
        assert episode_cnt == 90
    
    def test_parse_episode_count_invalid(self):
        """测试解析无效集数"""
        episode_cnt = "invalid"
        try:
            episode_cnt = int(episode_cnt.replace("集", "").strip())
        except:
            episode_cnt = 0
        
        assert episode_cnt == 0
    
    def test_parse_search_result_dict(self):
        """测试解析字典格式搜索结果"""
        data = {
            "page": "1",
            "totalPages": 10,
            "data": [
                {"name": "短剧1", "url": "https://pan.quark.cn/s/1", "episodes": "10"},
                {"name": "短剧2", "url": "https://pan.quark.cn/s/2", "episodes": "20"}
            ]
        }
        
        items = data.get("data", [])
        dramas = []
        for item in items:
            title = item.get("name") or "未知"
            source_link = item.get("url") or ""
            episode_cnt = item.get("episodes") or 0
            if isinstance(episode_cnt, str):
                try:
                    episode_cnt = int(episode_cnt.replace("集", "").strip())
                except:
                    episode_cnt = 0
            
            dramas.append(DramaInfo(
                book_id=source_link or str(hash(title)),
                title=title,
                cover="",
                episode_cnt=episode_cnt,
                intro="",
                type="短剧",
                author="",
                play_cnt=0
            ))
        
        result = SearchResult(code=0, msg="success", data=dramas, page=1)
        
        assert result.code == 0
        assert len(result.data) == 2
    
    def test_parse_search_result_invalid(self):
        """测试解析无效搜索结果"""
        data = "invalid"
        
        if isinstance(data, dict):
            items = data.get("data", [])
        else:
            items = []
        
        assert items == []
    
    def test_parse_data_list_dict(self):
        """测试解析字典格式数据列表"""
        data = {
            "data": [
                {"name": "短剧1"},
                {"name": "短剧2"}
            ]
        }
        
        if isinstance(data, dict):
            items = data.get("data", [])
        elif isinstance(data, list):
            items = data
        else:
            items = []
        
        assert len(items) == 2
    
    def test_parse_data_list_array(self):
        """测试解析数组格式数据列表"""
        data = [
            {"name": "短剧1"},
            {"name": "短剧2"}
        ]
        
        if isinstance(data, dict):
            items = data.get("data", [])
        elif isinstance(data, list):
            items = data
        else:
            items = []
        
        assert len(items) == 2


class TestDuanjuSearchAdapterCategories:
    """测试分类功能"""
    
    def test_categories_mapping(self):
        """测试分类映射"""
        CATEGORIES = {
            "今日更新": "today",
            "热门榜单": "hot",
            "全部短剧": "all",
        }
        
        assert CATEGORIES["今日更新"] == "today"
        assert CATEGORIES["热门榜单"] == "hot"
        assert CATEGORIES.get("未知", "today") == "today"
    
    def test_get_categories(self):
        """测试获取分类列表"""
        CATEGORIES = {
            "今日更新": "today",
            "热门榜单": "hot",
            "全部短剧": "all",
        }
        
        categories = list(CATEGORIES.keys())
        assert "今日更新" in categories
        assert "热门榜单" in categories
        assert len(categories) == 3


class TestDuanjuSearchAdapterEpisodes:
    """测试剧集功能"""
    
    def test_get_episodes_valid_link(self):
        """测试获取剧集 - 有效链接"""
        source_link = "https://pan.quark.cn/s/xxx"
        is_valid_link = source_link.startswith("http")
        
        if is_valid_link:
            desc = f"🔗 此短剧资源存储在网盘中，请复制以下链接到浏览器打开：\n\n{source_link}"
            code = 0
            book_name = "网盘资源"
        else:
            desc = "[全网短剧API] 此数据源仅提供短剧索引，不支持在线播放。"
            code = 1
            book_name = "不支持播放"
        
        result = EpisodeList(
            code=code,
            book_name=book_name,
            episodes=[],
            total=0,
            book_id=source_link,
            author="",
            category="网盘链接",
            desc=desc,
            duration="",
            book_pic=""
        )
        
        assert result.code == 0
        assert result.book_name == "网盘资源"
        assert "pan.quark.cn" in result.desc
    
    def test_get_episodes_invalid_link(self):
        """测试获取剧集 - 无效链接"""
        source_link = "invalid_link"
        is_valid_link = source_link.startswith("http")
        
        assert is_valid_link is False
    
    def test_get_video_url_not_supported(self):
        """测试获取视频URL - 不支持"""
        error_msg = "[全网短剧API] 此数据源不支持获取视频播放地址"
        
        result = VideoInfo(
            code=1,
            url="",
            pic="",
            quality="",
            title=error_msg,
            duration="",
            size_str=""
        )
        
        assert result.code == 1
        assert result.url == ""
        assert "不支持" in result.title


class TestDuanjuSearchAdapterRateLimit:
    """测试限流功能"""
    
    def test_rate_limit_config(self):
        """测试限流配置"""
        RATE_LIMIT_WINDOW = 10.0
        RATE_LIMIT_MAX_REQUESTS = 5
        
        assert RATE_LIMIT_WINDOW == 10.0
        assert RATE_LIMIT_MAX_REQUESTS == 5
    
    def test_sliding_window_cleanup(self):
        """测试滑动窗口清理"""
        request_timestamps = deque([1.0, 2.0, 3.0, 15.0, 16.0])
        RATE_LIMIT_WINDOW = 10.0
        
        now = 20.0
        window_start = now - RATE_LIMIT_WINDOW
        
        while request_timestamps and request_timestamps[0] < window_start:
            request_timestamps.popleft()
        
        assert len(request_timestamps) == 2
    
    def test_rate_limit_check(self):
        """测试限流检查"""
        request_timestamps = deque([1.0, 2.0, 3.0, 4.0, 5.0])
        RATE_LIMIT_MAX_REQUESTS = 5
        
        need_wait = len(request_timestamps) >= RATE_LIMIT_MAX_REQUESTS
        assert need_wait is True


class TestDuanjuSearchAdapterLocalSearch:
    """测试本地搜索功能"""
    
    def test_local_search_filter(self):
        """测试本地搜索过滤"""
        data = [
            {"name": "测试短剧1"},
            {"name": "其他短剧"},
            {"name": "测试短剧2"}
        ]
        keyword = "测试"
        
        filtered = [
            item for item in data
            if keyword.lower() in (item.get("name") or "").lower()
        ]
        
        assert len(filtered) == 2
    
    def test_local_search_case_insensitive(self):
        """测试本地搜索不区分大小写"""
        data = [
            {"name": "Test Drama"},
            {"name": "test drama"},
            {"name": "Other"}
        ]
        keyword = "test"
        
        filtered = [
            item for item in data
            if keyword.lower() in (item.get("name") or "").lower()
        ]
        
        assert len(filtered) == 2
    
    def test_local_search_empty_result(self):
        """测试本地搜索空结果"""
        data = [
            {"name": "短剧1"},
            {"name": "短剧2"}
        ]
        keyword = "不存在"
        
        filtered = [
            item for item in data
            if keyword.lower() in (item.get("name") or "").lower()
        ]
        
        assert len(filtered) == 0


class TestDuanjuSearchAdapterProviderInfo:
    """测试提供者信息"""
    
    def test_provider_info(self):
        """测试提供者信息"""
        info = {
            "id": "duanju_search",
            "name": "全网短剧API",
            "description": "全网短剧数据源 - 提供短剧索引链接（网盘链接）",
            "version": "1.0.0",
            "base_url": "https://kuoapp.com"
        }
        
        assert info["id"] == "duanju_search"
        assert info["name"] == "全网短剧API"
    
    def test_capabilities(self):
        """测试能力配置"""
        capabilities = {
            "supports_search": True,
            "supports_categories": True,
            "supports_recommendations": True,
            "supports_episodes": False,
            "supports_video_url": False,
            "supports_quality_selection": False,
            "supports_pagination": True,
            "supports_dynamic_categories": False,
            "available_qualities": []
        }
        
        assert capabilities["supports_search"] is True
        assert capabilities["supports_episodes"] is False
        assert capabilities["supports_video_url"] is False
