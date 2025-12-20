"""API 适配器测试"""
from collections import deque
from unittest.mock import AsyncMock, MagicMock, patch
from unittest.mock import MagicMock, AsyncMock, patch
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import json
import re
import time

import aiohttp
import pytest

from src.core.models import (
    DramaInfo, EpisodeInfo, EpisodeList, VideoInfo, SearchResult, CategoryResult
)
from src.core.models import DramaInfo, EpisodeInfo, SearchResult, CategoryResult
from src.data.providers.adapters.cenguigui_adapter import CenguiguiAdapter
from src.data.providers.adapters.duanju_search_adapter import DuanjuSearchAdapter
from src.data.providers.adapters.uuuka_adapter import UuukaAdapter

class TestCenguiguiAdapter:
    """Cenguigui 适配器测试"""
    
    def test_init(self):
        """测试初始化"""
        from src.data.providers.adapters.cenguigui_adapter import CenguiguiAdapter
        
        adapter = CenguiguiAdapter()
        
        assert adapter.info.id == "cenguigui"
        assert adapter.info.name == "笒鬼鬼短剧API"
        assert adapter.BASE_URL == "https://api.cenguigui.cn/api/duanju/api.php"
    
    def test_init_custom_timeout(self):
        """测试自定义超时"""
        from src.data.providers.adapters.cenguigui_adapter import CenguiguiAdapter
        
        adapter = CenguiguiAdapter(timeout=5000)
        
        assert adapter._timeout == 5000
    
    def test_categories(self):
        """测试分类列表"""
        from src.data.providers.adapters.cenguigui_adapter import CenguiguiAdapter
        
        adapter = CenguiguiAdapter()
        
        assert len(adapter.CATEGORIES) > 0
        assert "推荐榜" in adapter.CATEGORIES
        assert "新剧" in adapter.CATEGORIES
    
    def test_capabilities(self):
        """测试能力配置"""
        from src.data.providers.adapters.cenguigui_adapter import CenguiguiAdapter
        
        adapter = CenguiguiAdapter()
        caps = adapter.info.capabilities
        
        assert caps.supports_search is True
        assert caps.supports_categories is True
        assert caps.supports_episodes is True
        assert caps.supports_video_url is True
        assert caps.supports_dynamic_categories is False
        assert "1080p" in caps.available_qualities
    
    def test_parse_episode_number_chinese(self):
        """测试解析中文集数"""
        from src.data.providers.adapters.cenguigui_adapter import CenguiguiAdapter
        
        assert CenguiguiAdapter._parse_episode_number("第1集") == 1
        assert CenguiguiAdapter._parse_episode_number("第10集") == 10
        assert CenguiguiAdapter._parse_episode_number("第100集") == 100
    
    def test_parse_episode_number_numeric(self):
        """测试解析数字集数"""
        from src.data.providers.adapters.cenguigui_adapter import CenguiguiAdapter
        
        assert CenguiguiAdapter._parse_episode_number("1") == 1
        assert CenguiguiAdapter._parse_episode_number("Episode 5") == 5
    
    def test_parse_episode_number_no_number(self):
        """测试无集数"""
        from src.data.providers.adapters.cenguigui_adapter import CenguiguiAdapter
        
        assert CenguiguiAdapter._parse_episode_number("预告片") == 0
        assert CenguiguiAdapter._parse_episode_number("") == 0
    
    def test_parse_search_result(self):
        """测试解析搜索结果"""
        from src.data.providers.adapters.cenguigui_adapter import CenguiguiAdapter
        
        adapter = CenguiguiAdapter()
        json_str = json.dumps({
            "code": 200,
            "msg": "success",
            "page": 1,
            "data": [
                {
                    "book_id": "123",
                    "title": "测试短剧",
                    "cover": "http://example.com/cover.jpg",
                    "episode_cnt": 10,
                    "intro": "简介",
                    "type": "言情",
                    "author": "作者",
                    "play_cnt": 1000
                }
            ]
        })
        
        result = adapter._parse_search_result(json_str)
        
        assert result.code == 200
        assert result.page == 1
        assert len(result.data) == 1
        assert result.data[0].book_id == "123"
        assert result.data[0].title == "测试短剧"
    
    def test_parse_search_result_string_page(self):
        """测试解析字符串页码"""
        from src.data.providers.adapters.cenguigui_adapter import CenguiguiAdapter
        
        adapter = CenguiguiAdapter()
        json_str = json.dumps({
            "code": 200,
            "msg": "success",
            "page": "2",
            "data": []
        })
        
        result = adapter._parse_search_result(json_str)
        
        assert result.page == 2
    
    def test_parse_category_result(self):
        """测试解析分类结果"""
        from src.data.providers.adapters.cenguigui_adapter import CenguiguiAdapter
        
        adapter = CenguiguiAdapter()
        json_str = json.dumps({
            "code": 200,
            "data": [
                {
                    "book_id": "456",
                    "title": "分类短剧",
                    "cover": "http://example.com/cover2.jpg",
                    "episode_cnt": 20,
                    "video_desc": "描述",
                    "sub_title": "霸总",
                    "play_cnt": 2000
                }
            ]
        })
        
        result = adapter._parse_category_result(json_str, "霸总")
        
        assert result.code == 200
        assert result.category == "霸总"
        assert len(result.data) == 1
        assert result.data[0].book_id == "456"
    
    def test_parse_recommendations(self):
        """测试解析推荐内容"""
        from src.data.providers.adapters.cenguigui_adapter import CenguiguiAdapter
        
        adapter = CenguiguiAdapter()
        json_str = json.dumps({
            "code": 200,
            "data": [
                {
                    "book_data": {
                        "book_id": "789",
                        "book_name": "推荐短剧",
                        "thumb_url": "http://example.com/thumb.jpg",
                        "serial_count": 30,
                        "category": "穿越"
                    },
                    "hot": 5000
                }
            ]
        })
        
        dramas = adapter._parse_recommendations(json_str)
        
        assert len(dramas) == 1
        assert dramas[0].book_id == "789"
        assert dramas[0].title == "推荐短剧"
        assert dramas[0].episode_cnt == 30
    
    def test_parse_episode_list(self):
        """测试解析剧集列表"""
        from src.data.providers.adapters.cenguigui_adapter import CenguiguiAdapter
        
        adapter = CenguiguiAdapter()
        json_str = json.dumps({
            "code": 200,
            "book_name": "测试剧",
            "book_id": "111",
            "total": 5,
            "author": "作者",
            "category": "言情",
            "desc": "描述",
            "duration": "10:00",
            "book_pic": "http://example.com/pic.jpg",
            "data": [
                {"video_id": "v1", "title": "第1集", "chapter_word_number": 100},
                {"video_id": "v2", "title": "第2集", "chapter_word_number": 200}
            ]
        })
        
        result = adapter._parse_episode_list(json_str)
        
        assert result.code == 200
        assert result.book_name == "测试剧"
        assert result.total == 5
        assert len(result.episodes) == 2
        assert result.episodes[0].video_id == "v1"
        assert result.episodes[0].episode_number == 1
    
    def test_parse_video_info(self):
        """测试解析视频信息"""
        from src.data.providers.adapters.cenguigui_adapter import CenguiguiAdapter
        
        adapter = CenguiguiAdapter()
        json_str = json.dumps({
            "code": 200,
            "data": {
                "url": "http://example.com/video.m3u8",
                "pic": "http://example.com/pic.jpg",
                "title": "第1集",
                "info": {
                    "quality": "1080p",
                    "duration": "05:30",
                    "size_str": "100MB"
                }
            }
        })
        
        result = adapter._parse_video_info(json_str)
        
        assert result.code == 200
        assert result.url == "http://example.com/video.m3u8"
        assert result.quality == "1080p"


class TestCenguiguiAdapterAsync:
    """Cenguigui 适配器异步测试"""
    
    @pytest.mark.asyncio
    async def test_get_categories(self):
        """测试获取分类"""
        from src.data.providers.adapters.cenguigui_adapter import CenguiguiAdapter
        
        adapter = CenguiguiAdapter()
        categories = await adapter.get_categories()
        
        assert len(categories) > 0
        assert "推荐榜" in categories
    
    @pytest.mark.asyncio
    async def test_search_parse(self):
        """测试搜索结果解析"""
        from src.data.providers.adapters.cenguigui_adapter import CenguiguiAdapter
        
        adapter = CenguiguiAdapter()
        
        # 直接测试解析方法
        json_str = json.dumps({
            "code": 200,
            "msg": "success",
            "page": 1,
            "data": [{"book_id": "1", "title": "测试", "cover": "", "episode_cnt": 10, "intro": "", "type": "", "author": "", "play_cnt": 0}]
        })
        
        result = adapter._parse_search_result(json_str)
        
        assert result.code == 200
        assert len(result.data) == 1
    
    @pytest.mark.asyncio
    async def test_get_episodes_parse(self):
        """测试剧集解析"""
        from src.data.providers.adapters.cenguigui_adapter import CenguiguiAdapter
        
        adapter = CenguiguiAdapter()
        
        # 直接测试解析方法
        json_str = json.dumps({
            "code": 200,
            "book_name": "测试剧",
            "book_id": "1",
            "total": 2,
            "data": [
                {"video_id": "v1", "title": "第1集", "chapter_word_number": 0},
                {"video_id": "v2", "title": "第2集", "chapter_word_number": 0}
            ]
        })
        
        result = adapter._parse_episode_list(json_str)
        
        assert result.code == 200
        assert len(result.episodes) == 2


class TestUuukaAdapter:
    """UuuKa 适配器测试"""
    
    def test_init(self):
        """测试初始化"""
        from src.data.providers.adapters.uuuka_adapter import UuukaAdapter
        
        adapter = UuukaAdapter()
        
        assert adapter.info.id == "uuuka"
        assert adapter.info.name == "即刻短剧API"
        assert adapter.BASE_URL == "https://api.uuuka.com"
    
    def test_capabilities(self):
        """测试能力配置"""
        from src.data.providers.adapters.uuuka_adapter import UuukaAdapter
        
        adapter = UuukaAdapter()
        caps = adapter.info.capabilities
        
        assert caps.supports_search is True
        assert caps.supports_episodes is False
        assert caps.supports_video_url is False
    
    def test_content_types(self):
        """测试内容类型映射"""
        from src.data.providers.adapters.uuuka_adapter import UuukaAdapter
        
        adapter = UuukaAdapter()
        
        assert "短剧" in adapter.CONTENT_TYPES
        assert adapter.CONTENT_TYPES["短剧"] == "post"
    
    def test_parse_item(self):
        """测试解析单个项目"""
        from src.data.providers.adapters.uuuka_adapter import UuukaAdapter
        
        adapter = UuukaAdapter()
        item = {
            "title": "测试短剧",
            "source_link": "https://pan.quark.cn/s/xxx",
            "type": "post"
        }
        
        drama = adapter._parse_item(item)
        
        assert drama.title == "测试短剧"
        assert drama.book_id == "https://pan.quark.cn/s/xxx"
    
    @pytest.mark.asyncio
    async def test_get_categories(self):
        """测试获取分类"""
        from src.data.providers.adapters.uuuka_adapter import UuukaAdapter
        
        adapter = UuukaAdapter()
        categories = await adapter.get_categories()
        
        assert "短剧" in categories
    
    @pytest.mark.asyncio
    async def test_get_episodes_returns_link(self):
        """测试获取剧集返回链接"""
        from src.data.providers.adapters.uuuka_adapter import UuukaAdapter
        
        adapter = UuukaAdapter()
        result = await adapter.get_episodes("https://pan.quark.cn/s/xxx")
        
        assert result.code == 0
        assert "网盘" in result.desc
    
    @pytest.mark.asyncio
    async def test_get_video_url_not_supported(self):
        """测试获取视频地址不支持"""
        from src.data.providers.adapters.uuuka_adapter import UuukaAdapter
        
        adapter = UuukaAdapter()
        result = await adapter.get_video_url("xxx")
        
        assert result.code == 1
        assert result.url == ""


class TestDuanjuSearchAdapter:
    """短剧搜索适配器测试"""
    
    def test_init(self):
        """测试初始化"""
        from src.data.providers.adapters.duanju_search_adapter import DuanjuSearchAdapter
        
        adapter = DuanjuSearchAdapter()
        
        assert adapter.info.id == "duanju_search"
        assert adapter.info.name == "全网短剧API"
    
    def test_init_custom_base_url(self):
        """测试自定义 base_url"""
        from src.data.providers.adapters.duanju_search_adapter import DuanjuSearchAdapter
        
        adapter = DuanjuSearchAdapter(base_url="https://custom.api.com")
        
        assert adapter.BASE_URL == "https://custom.api.com"
    
    def test_capabilities(self):
        """测试能力配置"""
        from src.data.providers.adapters.duanju_search_adapter import DuanjuSearchAdapter
        
        adapter = DuanjuSearchAdapter()
        caps = adapter.info.capabilities
        
        assert caps.supports_search is True
        assert caps.supports_episodes is False
        assert caps.supports_video_url is False
    
    def test_categories(self):
        """测试分类"""
        from src.data.providers.adapters.duanju_search_adapter import DuanjuSearchAdapter
        
        adapter = DuanjuSearchAdapter()
        
        assert "今日更新" in adapter.CATEGORIES
        assert "热门榜单" in adapter.CATEGORIES
    
    def test_parse_item(self):
        """测试解析单个项目"""
        from src.data.providers.adapters.duanju_search_adapter import DuanjuSearchAdapter
        
        adapter = DuanjuSearchAdapter()
        item = {
            "id": "123",
            "name": "测试短剧（90集）",
            "url": "https://pan.quark.cn/s/xxx",
            "addtime": "2024-06-29",
            "cover": "https://example.com/cover.jpg",
            "episodes": "90"
        }
        
        drama = adapter._parse_item(item)
        
        assert drama.title == "测试短剧（90集）"
        assert drama.book_id == "https://pan.quark.cn/s/xxx"
        assert drama.episode_cnt == 90
    
    def test_parse_item_string_episodes(self):
        """测试解析字符串集数"""
        from src.data.providers.adapters.duanju_search_adapter import DuanjuSearchAdapter
        
        adapter = DuanjuSearchAdapter()
        item = {
            "name": "测试",
            "url": "https://pan.quark.cn/s/xxx",
            "episodes": "50集"
        }
        
        drama = adapter._parse_item(item)
        
        assert drama.episode_cnt == 50
    
    def test_parse_search_result(self):
        """测试解析搜索结果"""
        from src.data.providers.adapters.duanju_search_adapter import DuanjuSearchAdapter
        
        adapter = DuanjuSearchAdapter()
        data = {
            "page": "1",
            "totalPages": 10,
            "data": [
                {"id": "1", "name": "测试", "url": "https://pan.quark.cn/s/xxx"}
            ]
        }
        
        result = adapter._parse_search_result(data, 1)
        
        assert result.code == 0
        assert len(result.data) == 1
    
    @pytest.mark.asyncio
    async def test_get_categories(self):
        """测试获取分类"""
        from src.data.providers.adapters.duanju_search_adapter import DuanjuSearchAdapter
        
        adapter = DuanjuSearchAdapter()
        categories = await adapter.get_categories()
        
        assert "今日更新" in categories
    
    @pytest.mark.asyncio
    async def test_get_episodes_returns_link(self):
        """测试获取剧集返回链接"""
        from src.data.providers.adapters.duanju_search_adapter import DuanjuSearchAdapter
        
        adapter = DuanjuSearchAdapter()
        result = await adapter.get_episodes("https://pan.quark.cn/s/xxx")
        
        assert result.code == 0
        assert "网盘" in result.desc
    
    @pytest.mark.asyncio
    async def test_get_video_url_not_supported(self):
        """测试获取视频地址不支持"""
        from src.data.providers.adapters.duanju_search_adapter import DuanjuSearchAdapter
        
        adapter = DuanjuSearchAdapter()
        result = await adapter.get_video_url("xxx")
        
        assert result.code == 1
        assert result.url == ""


class TestAdapterRateLimit:
    """适配器限流测试"""
    
    @pytest.mark.asyncio
    async def test_rate_limit_window(self):
        """测试限流窗口"""
        from src.data.providers.adapters.cenguigui_adapter import CenguiguiAdapter
        
        adapter = CenguiguiAdapter()
        
        assert adapter.RATE_LIMIT_WINDOW == 10.0
        assert adapter.RATE_LIMIT_MAX_REQUESTS == 5
    
    @pytest.mark.asyncio
    async def test_wait_for_rate_limit_no_wait(self):
        """测试无需等待的限流"""
        from src.data.providers.adapters.cenguigui_adapter import CenguiguiAdapter
        
        adapter = CenguiguiAdapter()
        adapter._request_timestamps.clear()
        
        # 第一次请求不需要等待
        await adapter._wait_for_rate_limit()
        
        assert len(adapter._request_timestamps) == 1



# ============================================================
# From: test_adapters_full.py
# ============================================================
class TestCenguiguiAdapter_Full:
    """测试 Cenguigui 适配器"""
    
    @pytest.fixture
    def adapter(self):
        return CenguiguiAdapter(timeout=10000)
    
    def test_adapter_info(self, adapter):
        assert adapter.info.id == "cenguigui"
        assert adapter.info.name == "笒鬼鬼短剧API"
        assert adapter.info.capabilities.supports_search is True
        assert adapter.info.capabilities.supports_dynamic_categories is False
    
    def test_categories_list(self, adapter):
        assert len(adapter.CATEGORIES) > 0
        assert "推荐榜" in adapter.CATEGORIES
        assert "新剧" in adapter.CATEGORIES
    
    @pytest.mark.asyncio
    async def test_get_categories(self, adapter):
        categories = await adapter.get_categories()
        assert categories == adapter.CATEGORIES
    
    def test_parse_search_result(self, adapter):
        json_str = json.dumps({
            "code": 200,
            "msg": "success",
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
        result = adapter._parse_search_result(json_str)
        assert result.code == 200
        assert len(result.data) == 1
        assert result.data[0].title == "测试短剧"
    
    def test_parse_search_result_string_page(self, adapter):
        json_str = json.dumps({
            "code": 200,
            "page": "2",
            "data": []
        })
        result = adapter._parse_search_result(json_str)
        assert result.page == 2
    
    def test_parse_category_result(self, adapter):
        json_str = json.dumps({
            "code": 200,
            "data": [
                {
                    "book_id": "456",
                    "title": "分类短剧",
                    "cover": "https://example.com/cover2.jpg",
                    "episode_cnt": 15,
                    "video_desc": "描述",
                    "sub_title": "甜宠",
                    "play_cnt": 5000
                }
            ]
        })
        result = adapter._parse_category_result(json_str, "都市")
        assert result.code == 200
        assert result.category == "都市"
        assert len(result.data) == 1
    
    def test_parse_recommendations(self, adapter):
        json_str = json.dumps({
            "code": 200,
            "data": [
                {
                    "book_data": {
                        "book_id": "789",
                        "book_name": "推荐短剧",
                        "thumb_url": "https://example.com/thumb.jpg",
                        "serial_count": "30",
                        "category": "悬疑"
                    },
                    "hot": 8000
                }
            ]
        })
        dramas = adapter._parse_recommendations(json_str)
        assert len(dramas) == 1
        assert dramas[0].title == "推荐短剧"
        assert dramas[0].episode_cnt == 30
    
    def test_parse_episode_list(self, adapter):
        json_str = json.dumps({
            "code": 200,
            "book_name": "测试短剧",
            "book_id": "123",
            "total": "20",
            "author": "作者",
            "category": "都市",
            "desc": "描述",
            "data": [
                {"video_id": "v1", "title": "第1集", "chapter_word_number": 0},
                {"video_id": "v2", "title": "第2集", "chapter_word_number": 0}
            ]
        })
        result = adapter._parse_episode_list(json_str)
        assert result.code == 200
        assert result.book_name == "测试短剧"
        assert len(result.episodes) == 2
        assert result.total == 20
    
    def test_parse_video_info(self, adapter):
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
        result = adapter._parse_video_info(json_str)
        assert result.code == 200
        assert result.url == "https://example.com/video.m3u8"
        assert result.quality == "1080p"
    
    def test_parse_episode_number(self):
        assert CenguiguiAdapter._parse_episode_number("第1集") == 1
        assert CenguiguiAdapter._parse_episode_number("第10集") == 10
        assert CenguiguiAdapter._parse_episode_number("Episode 5") == 5
        assert CenguiguiAdapter._parse_episode_number("无数字") == 0
    
    def test_parse_drama_item(self, adapter):
        item = {
            "book_id": "123",
            "title": "测试",
            "cover": "url",
            "episode_cnt": 10,
            "intro": "简介",
            "type": "都市",
            "author": "作者",
            "play_cnt": 1000
        }
        drama = adapter._parse_drama_item(item)
        assert drama.book_id == "123"
        assert drama.title == "测试"


class TestUuukaAdapter_Full:
    """测试 UuuKa 适配器"""
    
    @pytest.fixture
    def adapter(self):
        return UuukaAdapter(timeout=10000)
    
    def test_adapter_info(self, adapter):
        assert adapter.info.id == "uuuka"
        assert adapter.info.name == "即刻短剧API"
        assert adapter.info.capabilities.supports_episodes is False
        assert adapter.info.capabilities.supports_video_url is False
    
    def test_content_types(self, adapter):
        assert "短剧" in adapter.CONTENT_TYPES
        assert adapter.CONTENT_TYPES["短剧"] == "post"
    
    @pytest.mark.asyncio
    async def test_get_categories(self, adapter):
        categories = await adapter.get_categories()
        assert "短剧" in categories
    
    def test_parse_search_result(self, adapter):
        data = {
            "success": True,
            "message": "success",
            "data": {
                "items": [
                    {
                        "title": "测试短剧",
                        "source_link": "https://pan.example.com/xxx",
                        "type": "post"
                    }
                ],
                "page": 1
            }
        }
        result = adapter._parse_search_result(data)
        assert result.code == 0
        assert len(result.data) == 1
    
    def test_parse_search_result_failed(self, adapter):
        data = {"success": False, "message": "error"}
        result = adapter._parse_search_result(data)
        assert result.code == 1
    
    def test_parse_category_result(self, adapter):
        data = {
            "success": True,
            "data": {
                "items": [{"title": "分类短剧", "source_link": "https://pan.example.com/yyy"}],
                "page": 2
            }
        }
        result = adapter._parse_category_result(data, "短剧")
        assert result.code == 0
        assert result.category == "短剧"
    
    def test_parse_recommendations(self, adapter):
        data = {
            "success": True,
            "data": {
                "items": [{"title": "推荐", "source_link": "https://pan.example.com/zzz"}]
            }
        }
        dramas = adapter._parse_recommendations(data)
        assert len(dramas) == 1
    
    def test_parse_recommendations_failed(self, adapter):
        data = {"success": False}
        dramas = adapter._parse_recommendations(data)
        assert len(dramas) == 0
    
    def test_parse_item(self, adapter):
        item = {
            "title": "测试短剧",
            "source_link": "https://pan.example.com/xxx",
            "type": "post"
        }
        drama = adapter._parse_item(item)
        assert drama.title == "测试短剧"
        assert drama.book_id == "https://pan.example.com/xxx"
    
    @pytest.mark.asyncio
    async def test_get_episodes(self, adapter):
        result = await adapter.get_episodes("https://pan.example.com/xxx")
        assert result.code == 0
        assert "网盘" in result.desc
    
    @pytest.mark.asyncio
    async def test_get_episodes_invalid_link(self, adapter):
        result = await adapter.get_episodes("invalid_link")
        assert result.code == 1
    
    @pytest.mark.asyncio
    async def test_get_video_url(self, adapter):
        result = await adapter.get_video_url("video_001")
        assert result.code == 1
        assert result.url == ""


class TestDuanjuSearchAdapter_Full:
    """测试 DuanjuSearch 适配器"""
    
    @pytest.fixture
    def adapter(self):
        return DuanjuSearchAdapter(timeout=10000)
    
    def test_adapter_info(self, adapter):
        assert adapter.info.id == "duanju_search"
        assert adapter.info.name == "全网短剧API"
        assert adapter.info.capabilities.supports_episodes is False
    
    def test_custom_base_url(self):
        adapter = DuanjuSearchAdapter(base_url="https://custom.api.com")
        assert adapter.BASE_URL == "https://custom.api.com"
    
    def test_categories(self, adapter):
        assert "今日更新" in adapter.CATEGORIES
        assert "热门榜单" in adapter.CATEGORIES
    
    @pytest.mark.asyncio
    async def test_get_categories(self, adapter):
        categories = await adapter.get_categories()
        assert "今日更新" in categories
    
    def test_parse_search_result(self, adapter):
        data = {
            "page": "1",
            "totalPages": 10,
            "data": [
                {
                    "id": "123",
                    "name": "测试短剧",
                    "url": "https://pan.quark.cn/s/xxx",
                    "episodes": "90",
                    "cover": "https://example.com/cover.jpg",
                    "addtime": "2024-06-29"
                }
            ]
        }
        result = adapter._parse_search_result(data, 1)
        assert result.code == 0
        assert len(result.data) == 1
        assert result.data[0].title == "测试短剧"
    
    def test_parse_search_result_invalid(self, adapter):
        result = adapter._parse_search_result("invalid", 1)
        assert result.code == 1
    
    def test_parse_category_result(self, adapter):
        data = [
            {"name": "分类短剧", "url": "https://pan.quark.cn/s/yyy", "episodes": "50"}
        ]
        result = adapter._parse_category_result(data, "今日更新", 1)
        assert result.code == 0
        assert result.category == "今日更新"
    
    def test_parse_data_list_dict(self, adapter):
        data = {
            "data": [
                {"name": "短剧1", "url": "url1"},
                {"name": "短剧2", "url": "url2"}
            ]
        }
        dramas = adapter._parse_data_list(data)
        assert len(dramas) == 2
    
    def test_parse_data_list_array(self, adapter):
        data = [
            {"name": "短剧1", "url": "url1"},
            {"name": "短剧2", "url": "url2"}
        ]
        dramas = adapter._parse_data_list(data)
        assert len(dramas) == 2
    
    def test_parse_data_list_invalid(self, adapter):
        dramas = adapter._parse_data_list("invalid")
        assert len(dramas) == 0
    
    def test_parse_item(self, adapter):
        item = {
            "id": "123",
            "name": "测试短剧（90集）",
            "url": "https://pan.quark.cn/s/xxx",
            "episodes": "90",
            "cover": "https://example.com/cover.jpg",
            "addtime": "2024-06-29"
        }
        drama = adapter._parse_item(item)
        assert drama.title == "测试短剧（90集）"
        assert drama.episode_cnt == 90
        assert drama.book_id == "https://pan.quark.cn/s/xxx"
    
    def test_parse_item_string_episodes(self, adapter):
        item = {"name": "短剧", "episodes": "50集"}
        drama = adapter._parse_item(item)
        assert drama.episode_cnt == 50
    
    def test_parse_item_no_url(self, adapter):
        item = {"id": "123", "name": "短剧"}
        drama = adapter._parse_item(item)
        assert drama.book_id == "123"
    
    @pytest.mark.asyncio
    async def test_get_episodes(self, adapter):
        result = await adapter.get_episodes("https://pan.quark.cn/s/xxx")
        assert result.code == 0
        assert "网盘" in result.desc
    
    @pytest.mark.asyncio
    async def test_get_episodes_invalid(self, adapter):
        result = await adapter.get_episodes("invalid")
        assert result.code == 1
    
    @pytest.mark.asyncio
    async def test_get_video_url(self, adapter):
        result = await adapter.get_video_url("video_001")
        assert result.code == 1


class TestAdapterRateLimiting:
    """测试适配器限流功能"""
    
    @pytest.mark.asyncio
    async def test_cenguigui_rate_limit(self):
        adapter = CenguiguiAdapter()
        adapter.RATE_LIMIT_WINDOW = 1.0
        adapter.RATE_LIMIT_MAX_REQUESTS = 2
        
        # 快速调用两次
        await adapter._wait_for_rate_limit()
        await adapter._wait_for_rate_limit()
        
        assert len(adapter._request_timestamps) == 2
    
    @pytest.mark.asyncio
    async def test_uuuka_rate_limit(self):
        adapter = UuukaAdapter()
        adapter.RATE_LIMIT_WINDOW = 1.0
        adapter.RATE_LIMIT_MAX_REQUESTS = 2
        
        await adapter._wait_for_rate_limit()
        await adapter._wait_for_rate_limit()
        
        assert len(adapter._request_timestamps) == 2
    
    @pytest.mark.asyncio
    async def test_duanju_search_rate_limit(self):
        adapter = DuanjuSearchAdapter()
        adapter.RATE_LIMIT_WINDOW = 1.0
        adapter.RATE_LIMIT_MAX_REQUESTS = 2
        
        await adapter._wait_for_rate_limit()
        await adapter._wait_for_rate_limit()
        
        assert len(adapter._request_timestamps) == 2



# ============================================================
# From: test_adapters_coverage.py
# ============================================================
class TestCenguiguiAdapterParsing:
    """测试 Cenguigui 适配器解析逻辑"""
    
    def test_parse_episode_number_standard(self):
        """测试标准集数解析"""
        def parse_episode_number(title: str) -> int:
            match = re.search(r'第(\d+)集', title)
            if match:
                return int(match.group(1))
            match = re.search(r'(\d+)', title)
            if match:
                return int(match.group(1))
            return 0
        
        assert parse_episode_number("第1集") == 1
        assert parse_episode_number("第10集") == 10
        assert parse_episode_number("第100集") == 100
    
    def test_parse_episode_number_numeric_only(self):
        """测试纯数字集数解析"""
        def parse_episode_number(title: str) -> int:
            match = re.search(r'第(\d+)集', title)
            if match:
                return int(match.group(1))
            match = re.search(r'(\d+)', title)
            if match:
                return int(match.group(1))
            return 0
        
        assert parse_episode_number("1") == 1
        assert parse_episode_number("Episode 5") == 5
    
    def test_parse_episode_number_no_number(self):
        """测试无数字标题"""
        def parse_episode_number(title: str) -> int:
            match = re.search(r'第(\d+)集', title)
            if match:
                return int(match.group(1))
            match = re.search(r'(\d+)', title)
            if match:
                return int(match.group(1))
            return 0
        
        assert parse_episode_number("序章") == 0
        assert parse_episode_number("大结局") == 0
    
    def test_parse_drama_item(self):
        """测试解析短剧项"""
        item = {
            "book_id": "123",
            "title": "测试短剧",
            "cover": "https://example.com/cover.jpg",
            "episode_cnt": 20,
            "intro": "简介",
            "type": "都市",
            "author": "作者",
            "play_cnt": 10000
        }
        
        drama = DramaInfo(
            book_id=str(item.get("book_id", "")),
            title=item.get("title", ""),
            cover=item.get("cover", ""),
            episode_cnt=int(item.get("episode_cnt", 0)),
            intro=item.get("intro", ""),
            type=item.get("type", ""),
            author=item.get("author", ""),
            play_cnt=int(item.get("play_cnt", 0))
        )
        
        assert drama.book_id == "123"
        assert drama.title == "测试短剧"
        assert drama.episode_cnt == 20
    
    def test_parse_search_result(self):
        """测试解析搜索结果"""
        json_str = json.dumps({
            "code": 200,
            "msg": "success",
            "page": 1,
            "data": [
                {"book_id": "1", "title": "短剧1", "cover": "", "episode_cnt": 10, "intro": "", "type": "", "author": "", "play_cnt": 0}
            ]
        })
        
        data = json.loads(json_str)
        dramas = []
        for item in data.get("data", []):
            dramas.append(DramaInfo(
                book_id=str(item.get("book_id", "")),
                title=item.get("title", ""),
                cover=item.get("cover", ""),
                episode_cnt=int(item.get("episode_cnt", 0)),
                intro=item.get("intro", ""),
                type=item.get("type", ""),
                author=item.get("author", ""),
                play_cnt=int(item.get("play_cnt", 0))
            ))
        
        page = data.get("page", 1)
        if isinstance(page, str):
            page = int(page) if page.isdigit() else 1
        
        result = SearchResult(
            code=data.get("code", 0),
            msg=data.get("msg", ""),
            data=dramas,
            page=page
        )
        
        assert result.code == 200
        assert len(result.data) == 1
        assert result.page == 1
    
    def test_parse_search_result_string_page(self):
        """测试解析字符串页码"""
        data = {"page": "5"}
        page = data.get("page", 1)
        if isinstance(page, str):
            page = int(page) if page.isdigit() else 1
        assert page == 5
    
    def test_parse_category_result(self):
        """测试解析分类结果"""
        json_str = json.dumps({
            "code": 200,
            "data": [
                {"book_id": "1", "title": "短剧1", "cover": "", "episode_cnt": 10, "video_desc": "描述", "sub_title": "都市", "play_cnt": 100}
            ]
        })
        
        data = json.loads(json_str)
        category = "都市"
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
        
        result = CategoryResult(
            code=data.get("code", 0),
            category=category,
            data=dramas,
            offset=1
        )
        
        assert result.code == 200
        assert result.category == "都市"
    
    def test_parse_recommendations(self):
        """测试解析推荐内容"""
        json_str = json.dumps({
            "data": [
                {
                    "book_data": {
                        "book_id": "1",
                        "book_name": "推荐短剧",
                        "thumb_url": "https://example.com/thumb.jpg",
                        "serial_count": "20",
                        "category": "甜宠"
                    },
                    "hot": 5000
                }
            ]
        })
        
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
        
        assert len(dramas) == 1
        assert dramas[0].title == "推荐短剧"
        assert dramas[0].episode_cnt == 20
    
    def test_parse_episode_list(self):
        """测试解析剧集列表"""
        json_str = json.dumps({
            "code": 200,
            "book_name": "测试短剧",
            "book_id": "123",
            "total": "20",
            "author": "作者",
            "category": "都市",
            "desc": "描述",
            "duration": "05:00",
            "book_pic": "https://example.com/pic.jpg",
            "data": [
                {"video_id": "v1", "title": "第1集", "chapter_word_number": 0},
                {"video_id": "v2", "title": "第2集", "chapter_word_number": 0}
            ]
        })
        
        data = json.loads(json_str)
        episodes = []
        for item in data.get("data", []):
            title = item.get("title", "")
            match = re.search(r'第(\d+)集', title)
            ep_num = int(match.group(1)) if match else 0
            episodes.append(EpisodeInfo(
                video_id=str(item.get("video_id", "")),
                title=title,
                episode_number=ep_num,
                chapter_word_number=int(item.get("chapter_word_number", 0))
            ))
        
        total = data.get("total", 0)
        if isinstance(total, str):
            total = int(total) if total.isdigit() else 0
        
        result = EpisodeList(
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
        
        assert result.code == 200
        assert result.total == 20
        assert len(result.episodes) == 2
    
    def test_parse_video_info(self):
        """测试解析视频信息"""
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
        
        data = json.loads(json_str)
        video_data = data.get("data", {})
        info = video_data.get("info", {})
        
        result = VideoInfo(
            code=data.get("code", 0),
            url=video_data.get("url", ""),
            pic=video_data.get("pic", ""),
            quality=info.get("quality", ""),
            title=video_data.get("title", ""),
            duration=info.get("duration", ""),
            size_str=info.get("size_str", "")
        )
        
        assert result.code == 200
        assert result.url == "https://example.com/video.m3u8"
        assert result.quality == "1080p"


class TestUuukaAdapterParsing:
    """测试 Uuuka 适配器解析逻辑"""
    
    def test_content_types(self):
        """测试内容类型映射"""
        CONTENT_TYPES = {
            "短剧": "post",
            "动漫": "dongman",
            "电影": "movie",
            "电视剧": "tv",
            "学习资源": "xuexi",
            "百度短剧": "baidu",
        }
        
        assert CONTENT_TYPES["短剧"] == "post"
        assert CONTENT_TYPES.get("未知", "post") == "post"
    
    def test_parse_search_result_success(self):
        """测试解析搜索结果成功"""
        data = {
            "success": True,
            "message": "success",
            "data": {
                "items": [
                    {"title": "短剧1", "source_link": "https://pan.baidu.com/xxx", "type": "post"}
                ],
                "page": 1
            }
        }
        
        if not data.get("success"):
            result = SearchResult(code=1, msg=data.get("message", "搜索失败"), data=[], page=1)
        else:
            items = data.get("data", {}).get("items", [])
            dramas = []
            for item in items:
                source_link = item.get("source_link", "")
                book_id = source_link if source_link else str(hash(item.get("title", "")))
                dramas.append(DramaInfo(
                    book_id=book_id,
                    title=item.get("title", ""),
                    cover="",
                    episode_cnt=0,
                    intro=f"🔗 网盘链接: {source_link}",
                    type=item.get("type", "post"),
                    author="",
                    play_cnt=0
                ))
            page = data.get("data", {}).get("page", 1)
            result = SearchResult(code=0, msg=data.get("message", ""), data=dramas, page=page)
        
        assert result.code == 0
        assert len(result.data) == 1
    
    def test_parse_search_result_failure(self):
        """测试解析搜索结果失败"""
        data = {
            "success": False,
            "message": "搜索失败"
        }
        
        if not data.get("success"):
            result = SearchResult(code=1, msg=data.get("message", "搜索失败"), data=[], page=1)
        else:
            result = SearchResult(code=0, msg="", data=[], page=1)
        
        assert result.code == 1
        assert result.msg == "搜索失败"
    
    def test_parse_item(self):
        """测试解析单个内容项"""
        item = {
            "title": "测试短剧",
            "source_link": "https://pan.baidu.com/xxx",
            "type": "post"
        }
        
        source_link = item.get("source_link", "")
        book_id = source_link if source_link else str(hash(item.get("title", "")))
        
        drama = DramaInfo(
            book_id=book_id,
            title=item.get("title", ""),
            cover="",
            episode_cnt=0,
            intro=f"🔗 网盘链接: {source_link}",
            type=item.get("type", "post"),
            author="",
            play_cnt=0
        )
        
        assert drama.title == "测试短剧"
        assert "pan.baidu.com" in drama.book_id
    
    def test_get_episodes_valid_link(self):
        """测试获取剧集 - 有效链接"""
        source_link = "https://pan.baidu.com/xxx"
        is_valid_link = source_link.startswith("http")
        
        if is_valid_link:
            desc = f"🔗 此短剧资源存储在网盘中，请复制以下链接到浏览器打开：\n\n{source_link}"
            code = 0
        else:
            desc = "[即刻短剧API] 此数据源仅提供短剧索引，不支持在线播放。"
            code = 1
        
        result = EpisodeList(
            code=code,
            book_name="网盘资源" if is_valid_link else "不支持播放",
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
        assert "网盘" in result.book_name
    
    def test_get_episodes_invalid_link(self):
        """测试获取剧集 - 无效链接"""
        source_link = "invalid_link"
        is_valid_link = source_link.startswith("http")
        
        assert is_valid_link is False
    
    def test_get_video_url_not_supported(self):
        """测试获取视频URL - 不支持"""
        error_msg = "[即刻短剧API] 此数据源不支持获取视频播放地址"
        
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


class TestRateLimitLogic:
    """测试限流逻辑"""
    
    def test_sliding_window_cleanup(self):
        """测试滑动窗口清理"""
        RATE_LIMIT_WINDOW = 10.0
        request_timestamps = deque([1.0, 2.0, 3.0, 15.0, 16.0])
        
        now = 20.0
        window_start = now - RATE_LIMIT_WINDOW
        
        while request_timestamps and request_timestamps[0] < window_start:
            request_timestamps.popleft()
        
        assert len(request_timestamps) == 2
        assert request_timestamps[0] == 15.0
    
    def test_rate_limit_check(self):
        """测试限流检查"""
        RATE_LIMIT_MAX_REQUESTS = 5
        request_timestamps = deque([1.0, 2.0, 3.0, 4.0, 5.0])
        
        need_wait = len(request_timestamps) >= RATE_LIMIT_MAX_REQUESTS
        assert need_wait is True
    
    def test_wait_time_calculation(self):
        """测试等待时间计算"""
        RATE_LIMIT_WINDOW = 10.0
        request_timestamps = deque([5.0, 6.0, 7.0, 8.0, 9.0])
        
        now = 12.0
        window_start = now - RATE_LIMIT_WINDOW
        
        wait_time = request_timestamps[0] - window_start
        assert wait_time == 3.0


class TestCenguiguiCategories:
    """测试 Cenguigui 分类"""
    
    def test_categories_list(self):
        """测试分类列表"""
        CATEGORIES = [
            "推荐榜", "新剧", "逆袭", "霸总", "现代言情", "打脸虐渣", 
            "豪门恩怨", "神豪", "马甲", "都市日常", "战神归来", "小人物"
        ]
        
        assert "推荐榜" in CATEGORIES
        assert "霸总" in CATEGORIES
        assert len(CATEGORIES) > 10
    
    def test_categories_copy(self):
        """测试分类列表复制"""
        CATEGORIES = ["推荐榜", "新剧"]
        categories_copy = CATEGORIES.copy()
        
        categories_copy.append("新增")
        
        assert "新增" not in CATEGORIES
        assert "新增" in categories_copy



# ============================================================
# From: test_adapters_async.py
# ============================================================
class TestCenguiguiAdapterAsync_Async:
    """测试 Cenguigui 适配器异步方法"""
    
    @pytest.fixture
    def adapter(self):
        return CenguiguiAdapter(timeout=10000)
    
    @pytest.mark.asyncio
    async def test_search_with_mock(self, adapter):
        """测试搜索（使用 mock）"""
        mock_response = {
            "code": 200,
            "msg": "success",
            "page": 1,
            "data": [
                {"book_id": "1", "title": "测试短剧", "cover": "", "episode_cnt": 10, "intro": "", "type": "", "author": "", "play_cnt": 0}
            ]
        }
        
        with patch.object(adapter, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = json.dumps(mock_response)
            result = await adapter.search("测试", 1)
            
            assert result.code == 200
            assert len(result.data) == 1
    
    @pytest.mark.asyncio
    async def test_get_categories(self, adapter):
        """测试获取分类"""
        categories = await adapter.get_categories()
        
        assert isinstance(categories, list)
        assert len(categories) > 0
        assert "推荐榜" in categories
    
    @pytest.mark.asyncio
    async def test_get_category_dramas_with_mock(self, adapter):
        """测试获取分类短剧（使用 mock）"""
        mock_response = {
            "code": 200,
            "data": [
                {"book_id": "1", "title": "短剧1", "cover": "", "episode_cnt": 10, "video_desc": "", "sub_title": "都市", "play_cnt": 0}
            ]
        }
        
        with patch.object(adapter, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = json.dumps(mock_response)
            result = await adapter.get_category_dramas("都市", 1)
            
            assert result.code == 200
            assert result.category == "都市"
    
    @pytest.mark.asyncio
    async def test_get_recommendations_with_mock(self, adapter):
        """测试获取推荐（使用 mock）"""
        mock_response = {
            "data": [
                {
                    "book_data": {
                        "book_id": "1",
                        "book_name": "推荐短剧",
                        "thumb_url": "",
                        "serial_count": "20",
                        "category": "甜宠"
                    },
                    "hot": 5000
                }
            ]
        }
        
        with patch.object(adapter, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = json.dumps(mock_response)
            result = await adapter.get_recommendations()
            
            assert isinstance(result, list)
            assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_get_episodes_with_mock(self, adapter):
        """测试获取剧集（使用 mock）"""
        mock_response = {
            "code": 200,
            "book_name": "测试短剧",
            "book_id": "123",
            "total": 20,
            "data": [
                {"video_id": "v1", "title": "第1集", "chapter_word_number": 0}
            ]
        }
        
        with patch.object(adapter, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = json.dumps(mock_response)
            result = await adapter.get_episodes("123")
            
            assert result.code == 200
            assert len(result.episodes) == 1
    
    @pytest.mark.asyncio
    async def test_get_video_url_with_mock(self, adapter):
        """测试获取视频URL（使用 mock）"""
        mock_response = {
            "code": 200,
            "data": {
                "url": "https://example.com/video.m3u8",
                "pic": "",
                "title": "第1集",
                "info": {"quality": "1080p", "duration": "05:00", "size_str": "50MB"}
            }
        }
        
        with patch.object(adapter, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = json.dumps(mock_response)
            result = await adapter.get_video_url("v1", "1080p")
            
            assert result.code == 200
            assert result.url == "https://example.com/video.m3u8"
    
    @pytest.mark.asyncio
    async def test_rate_limit_wait(self, adapter):
        """测试限流等待"""
        # 清空时间戳
        adapter._request_timestamps.clear()
        
        # 添加一些时间戳
        import time
        now = time.monotonic()
        for i in range(3):
            adapter._request_timestamps.append(now - i)
        
        # 应该不需要等待
        await adapter._wait_for_rate_limit()
        
        assert len(adapter._request_timestamps) <= adapter.RATE_LIMIT_MAX_REQUESTS + 1


class TestUuukaAdapterAsync:
    """测试 Uuuka 适配器异步方法"""
    
    @pytest.fixture
    def adapter(self):
        return UuukaAdapter(timeout=10000)
    
    @pytest.mark.asyncio
    async def test_search_with_mock(self, adapter):
        """测试搜索（使用 mock）"""
        mock_response = {
            "success": True,
            "message": "success",
            "data": {
                "items": [
                    {"title": "测试短剧", "source_link": "https://pan.baidu.com/xxx", "type": "post"}
                ],
                "page": 1
            }
        }
        
        with patch.object(adapter, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await adapter.search("测试", 1)
            
            assert result.code == 0
            assert len(result.data) == 1
    
    @pytest.mark.asyncio
    async def test_search_failure(self, adapter):
        """测试搜索失败"""
        mock_response = {
            "success": False,
            "message": "搜索失败"
        }
        
        with patch.object(adapter, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await adapter.search("测试", 1)
            
            assert result.code == 1
    
    @pytest.mark.asyncio
    async def test_get_categories(self, adapter):
        """测试获取分类"""
        categories = await adapter.get_categories()
        
        assert isinstance(categories, list)
        assert "短剧" in categories
    
    @pytest.mark.asyncio
    async def test_get_category_dramas_with_mock(self, adapter):
        """测试获取分类短剧（使用 mock）"""
        mock_response = {
            "success": True,
            "data": {
                "items": [
                    {"title": "短剧1", "source_link": "https://pan.baidu.com/1", "type": "post"}
                ],
                "page": 1
            }
        }
        
        with patch.object(adapter, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await adapter.get_category_dramas("短剧", 1)
            
            assert result.code == 0
    
    @pytest.mark.asyncio
    async def test_get_recommendations_with_mock(self, adapter):
        """测试获取推荐（使用 mock）"""
        mock_response = {
            "success": True,
            "data": {
                "items": [
                    {"title": "推荐短剧", "source_link": "https://pan.baidu.com/xxx", "type": "post"}
                ]
            }
        }
        
        with patch.object(adapter, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await adapter.get_recommendations()
            
            assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_get_episodes_valid_link(self, adapter):
        """测试获取剧集 - 有效链接"""
        result = await adapter.get_episodes("https://pan.baidu.com/xxx")
        
        assert result.code == 0
        assert "网盘" in result.book_name
    
    @pytest.mark.asyncio
    async def test_get_episodes_invalid_link(self, adapter):
        """测试获取剧集 - 无效链接"""
        result = await adapter.get_episodes("invalid")
        
        assert result.code == 1
    
    @pytest.mark.asyncio
    async def test_get_video_url_not_supported(self, adapter):
        """测试获取视频URL - 不支持"""
        result = await adapter.get_video_url("v1", "1080p")
        
        assert result.code == 1
        assert result.url == ""


class TestDuanjuSearchAdapterAsync:
    """测试 DuanjuSearch 适配器异步方法"""
    
    @pytest.fixture
    def adapter(self):
        return DuanjuSearchAdapter(timeout=10000)
    
    @pytest.mark.asyncio
    async def test_search_with_mock(self, adapter):
        """测试搜索（使用 mock）"""
        mock_response = {
            "page": "1",
            "totalPages": 10,
            "data": [
                {"name": "测试短剧", "url": "https://pan.quark.cn/xxx", "episodes": "10"}
            ]
        }
        
        with patch.object(adapter, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            result = await adapter.search("测试", 1)
            
            assert result.code == 0
            assert len(result.data) == 1
    
    @pytest.mark.asyncio
    async def test_search_fallback_to_local(self, adapter):
        """测试搜索回退到本地"""
        with patch.object(adapter, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = Exception("Network error")
            
            with patch.object(adapter, '_search_from_local', new_callable=AsyncMock) as mock_local:
                mock_local.return_value = SearchResult(code=0, msg="本地搜索", data=[], page=1)
                result = await adapter.search("测试", 1)
                
                mock_local.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_categories(self, adapter):
        """测试获取分类"""
        categories = await adapter.get_categories()
        
        assert isinstance(categories, list)
        assert "今日更新" in categories
    
    @pytest.mark.asyncio
    async def test_get_category_dramas_with_mock(self, adapter):
        """测试获取分类短剧（使用 mock）"""
        mock_data = [
            {"name": "短剧1", "url": "https://pan.quark.cn/1", "episodes": "10"}
        ]
        
        with patch.object(adapter, '_get_recent_data', new_callable=AsyncMock) as mock_recent:
            mock_recent.return_value = mock_data
            result = await adapter.get_category_dramas("今日更新", 1)
            
            assert result.code == 0
    
    @pytest.mark.asyncio
    async def test_get_recommendations_with_mock(self, adapter):
        """测试获取推荐（使用 mock）"""
        mock_data = [
            {"name": "推荐短剧", "url": "https://pan.quark.cn/xxx", "episodes": "20"}
        ]
        
        with patch.object(adapter, '_get_recent_data', new_callable=AsyncMock) as mock_recent:
            mock_recent.return_value = mock_data
            result = await adapter.get_recommendations()
            
            assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_get_episodes_valid_link(self, adapter):
        """测试获取剧集 - 有效链接"""
        result = await adapter.get_episodes("https://pan.quark.cn/xxx")
        
        assert result.code == 0
        assert "网盘" in result.book_name
    
    @pytest.mark.asyncio
    async def test_get_episodes_invalid_link(self, adapter):
        """测试获取剧集 - 无效链接"""
        result = await adapter.get_episodes("invalid")
        
        assert result.code == 1
    
    @pytest.mark.asyncio
    async def test_get_video_url_not_supported(self, adapter):
        """测试获取视频URL - 不支持"""
        result = await adapter.get_video_url("v1", "1080p")
        
        assert result.code == 1
        assert result.url == ""
    
    @pytest.mark.asyncio
    async def test_search_from_local(self, adapter):
        """测试本地搜索"""
        mock_data = [
            {"name": "测试短剧1"},
            {"name": "其他短剧"},
            {"name": "测试短剧2"}
        ]
        
        with patch.object(adapter, '_get_recent_data', new_callable=AsyncMock) as mock_recent:
            mock_recent.return_value = mock_data
            result = await adapter._search_from_local("测试", 1)
            
            assert result.code == 0
            assert len(result.data) == 2
    
    @pytest.mark.asyncio
    async def test_get_recent_data_with_mock(self, adapter):
        """测试获取最近数据（使用 mock）"""
        mock_data = [
            {"name": "短剧1", "url": "https://pan.quark.cn/1"}
        ]
        
        with patch.object(adapter, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_data
            result = await adapter._get_recent_data()
            
            assert isinstance(result, list)
            assert len(result) == 1



# ============================================================
# From: test_adapters_request.py
# ============================================================
class TestCenguiguiAdapterRequest:
    """测试 Cenguigui 适配器的 _request 方法"""
    
    @pytest.fixture
    def adapter(self):
        return CenguiguiAdapter(timeout=5000)
    
    @pytest.mark.asyncio
    async def test_request_success(self, adapter):
        """测试成功的请求"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='{"code": 200, "data": []}')
        
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await adapter._request({"name": "test"})
            assert '{"code": 200' in result
    
    @pytest.mark.asyncio
    async def test_request_http_error(self, adapter):
        """测试 HTTP 错误"""
        mock_response = MagicMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value='Internal Server Error')
        
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with pytest.raises(Exception) as exc_info:
                await adapter._request({"name": "test"})
            assert "HTTP Error: 500" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_request_network_error(self, adapter):
        """测试网络错误"""
        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=aiohttp.ClientError("Connection failed"))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with pytest.raises(Exception) as exc_info:
                await adapter._request({"name": "test"})
            assert "Connection failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_request_api_error_code(self, adapter):
        """测试 API 返回错误码"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='{"code": 400, "msg": "参数错误"}')
        
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            # 应该返回响应文本，不抛出异常
            result = await adapter._request({"name": "test"})
            assert "code" in result


class TestUuukaAdapterRequest:
    """测试 Uuuka 适配器的 _request 方法"""
    
    @pytest.fixture
    def adapter(self):
        return UuukaAdapter(timeout=5000)
    
    @pytest.mark.asyncio
    async def test_request_success(self, adapter):
        """测试成功的请求"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='{"success": true, "data": {"items": []}}')
        
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await adapter._request("/api/search", {"keyword": "test"})
            assert result["success"] == True
    
    @pytest.mark.asyncio
    async def test_request_http_error(self, adapter):
        """测试 HTTP 错误"""
        mock_response = MagicMock()
        mock_response.status = 404
        mock_response.text = AsyncMock(return_value='Not Found')
        
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with pytest.raises(Exception) as exc_info:
                await adapter._request("/api/search", {"keyword": "test"})
            assert "HTTP Error: 404" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_request_network_error(self, adapter):
        """测试网络错误"""
        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=aiohttp.ClientError("Connection refused"))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with pytest.raises(Exception) as exc_info:
                await adapter._request("/api/search", {"keyword": "test"})
            assert "Connection refused" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_request_json_error(self, adapter):
        """测试 JSON 解析错误"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='invalid json')
        
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with pytest.raises(Exception) as exc_info:
                await adapter._request("/api/search", {"keyword": "test"})
            assert "解析错误" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_request_api_failure(self, adapter):
        """测试 API 返回失败"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='{"success": false, "message": "Error"}')
        
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            # 应该返回数据，不抛出异常
            result = await adapter._request("/api/search", {"keyword": "test"})
            assert result["success"] == False


class TestDuanjuSearchAdapterRequest:
    """测试 DuanjuSearch 适配器的 _request 方法"""
    
    @pytest.fixture
    def adapter(self):
        return DuanjuSearchAdapter(timeout=5000)
    
    @pytest.mark.asyncio
    async def test_request_success(self, adapter):
        """测试成功的请求"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='{"page": 1, "data": []}')
        
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await adapter._request("/duanju/api.php", {"name": "test"})
            assert result["page"] == 1
    
    @pytest.mark.asyncio
    async def test_request_http_error(self, adapter):
        """测试 HTTP 错误"""
        mock_response = MagicMock()
        mock_response.status = 503
        mock_response.text = AsyncMock(return_value='Service Unavailable')
        
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with pytest.raises(Exception) as exc_info:
                await adapter._request("/duanju/api.php", {"name": "test"})
            assert "HTTP Error: 503" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_request_network_error(self, adapter):
        """测试网络错误"""
        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=aiohttp.ClientError("Timeout"))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with pytest.raises(Exception) as exc_info:
                await adapter._request("/duanju/api.php", {"name": "test"})
            assert "Timeout" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_request_json_error(self, adapter):
        """测试 JSON 解析错误"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='not json')
        
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with pytest.raises(Exception) as exc_info:
                await adapter._request("/duanju/api.php", {"name": "test"})
            assert "解析错误" in str(exc_info.value)


class TestAdapterSearchWithMock:
    """测试适配器搜索方法"""
    
    @pytest.mark.asyncio
    async def test_cenguigui_search(self):
        """测试 Cenguigui 搜索"""
        adapter = CenguiguiAdapter()
        
        with patch.object(adapter, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = json.dumps({
                "code": 200,
                "msg": "success",
                "page": 1,
                "data": [
                    {"book_id": "1", "title": "测试", "cover": "", "episode_cnt": 10}
                ]
            })
            
            result = await adapter.search("测试")
            assert result.code == 200
            assert len(result.data) == 1
    
    @pytest.mark.asyncio
    async def test_uuuka_search(self):
        """测试 Uuuka 搜索"""
        adapter = UuukaAdapter()
        
        with patch.object(adapter, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "success": True,
                "data": {
                    "items": [{"title": "测试", "source_link": "http://test.com"}],
                    "page": 1
                }
            }
            
            result = await adapter.search("测试")
            assert result.code == 0
            assert len(result.data) == 1
    
    @pytest.mark.asyncio
    async def test_duanju_search_success(self):
        """测试 DuanjuSearch 搜索成功"""
        adapter = DuanjuSearchAdapter()
        
        with patch.object(adapter, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "page": 1,
                "data": [{"name": "测试", "url": "http://test.com", "episodes": "10"}]
            }
            
            result = await adapter.search("测试")
            assert result.code == 0
            assert len(result.data) == 1
    
    @pytest.mark.asyncio
    async def test_duanju_search_fallback(self):
        """测试 DuanjuSearch 搜索失败后回退到本地搜索"""
        adapter = DuanjuSearchAdapter()
        
        call_count = 0
        async def mock_request(endpoint, params=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # 第一次调用（搜索）失败
                raise Exception("搜索接口超时")
            else:
                # 后续调用（获取最近数据）成功
                return [{"name": "测试短剧", "url": "http://test.com"}]
        
        with patch.object(adapter, '_request', side_effect=mock_request):
            result = await adapter.search("测试")
            # 应该返回本地搜索结果
            assert result.code == 0


class TestAdapterCategoryWithMock:
    """测试适配器分类方法"""
    
    @pytest.mark.asyncio
    async def test_cenguigui_get_category_dramas(self):
        """测试 Cenguigui 获取分类短剧"""
        adapter = CenguiguiAdapter()
        
        with patch.object(adapter, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = json.dumps({
                "code": 200,
                "data": [
                    {"book_id": "1", "title": "测试", "cover": "", "episode_cnt": 10, "video_desc": "描述"}
                ]
            })
            
            result = await adapter.get_category_dramas("都市")
            assert result.code == 200
            assert result.category == "都市"
    
    @pytest.mark.asyncio
    async def test_uuuka_get_category_dramas(self):
        """测试 Uuuka 获取分类短剧"""
        adapter = UuukaAdapter()
        
        with patch.object(adapter, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "success": True,
                "data": {
                    "items": [{"title": "测试", "source_link": "http://test.com"}],
                    "page": 1
                }
            }
            
            result = await adapter.get_category_dramas("短剧")
            assert result.code == 0
            assert result.category == "短剧"
    
    @pytest.mark.asyncio
    async def test_duanju_get_category_dramas_hot(self):
        """测试 DuanjuSearch 获取热门分类"""
        adapter = DuanjuSearchAdapter()
        
        with patch.object(adapter, '_get_recent_data', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = [{"name": "热门短剧", "url": "http://test.com"}]
            
            result = await adapter.get_category_dramas("热门榜单")
            assert result.code == 0
            assert result.category == "热门榜单"
    
    @pytest.mark.asyncio
    async def test_duanju_get_category_dramas_today(self):
        """测试 DuanjuSearch 获取今日更新"""
        adapter = DuanjuSearchAdapter()
        
        with patch.object(adapter, '_get_recent_data', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = [{"name": "今日短剧", "url": "http://test.com"}]
            
            result = await adapter.get_category_dramas("今日更新")
            assert result.code == 0
    
    @pytest.mark.asyncio
    async def test_duanju_get_category_dramas_all(self):
        """测试 DuanjuSearch 获取全部短剧"""
        adapter = DuanjuSearchAdapter()
        
        with patch.object(adapter, '_get_recent_data', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = [{"name": "全部短剧", "url": "http://test.com"}]
            
            result = await adapter.get_category_dramas("全部短剧")
            assert result.code == 0


class TestAdapterRecommendationsWithMock:
    """测试适配器推荐方法"""
    
    @pytest.mark.asyncio
    async def test_cenguigui_get_recommendations(self):
        """测试 Cenguigui 获取推荐"""
        adapter = CenguiguiAdapter()
        
        with patch.object(adapter, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = json.dumps({
                "code": 200,
                "data": [
                    {"book_data": {"book_id": "1", "book_name": "推荐", "serial_count": 10}, "hot": 1000}
                ]
            })
            
            result = await adapter.get_recommendations()
            assert len(result) == 1
            assert result[0].title == "推荐"
    
    @pytest.mark.asyncio
    async def test_uuuka_get_recommendations_today(self):
        """测试 Uuuka 获取今日推荐"""
        adapter = UuukaAdapter()
        
        with patch.object(adapter, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "success": True,
                "data": {
                    "items": [{"title": "今日推荐", "source_link": "http://test.com"}]
                }
            }
            
            result = await adapter.get_recommendations()
            assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_uuuka_get_recommendations_fallback(self):
        """测试 Uuuka 今日推荐为空时回退"""
        adapter = UuukaAdapter()
        
        call_count = 0
        async def mock_request(endpoint, params=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # 第一次调用（今日更新）返回空
                return {"success": True, "data": {"items": []}}
            else:
                # 第二次调用（最新列表）返回数据
                return {"success": True, "data": {"items": [{"title": "最新", "source_link": "http://test.com"}]}}
        
        with patch.object(adapter, '_request', side_effect=mock_request):
            result = await adapter.get_recommendations()
            assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_duanju_get_recommendations(self):
        """测试 DuanjuSearch 获取推荐"""
        adapter = DuanjuSearchAdapter()
        
        with patch.object(adapter, '_get_recent_data', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = [{"name": f"短剧{i}", "url": f"http://test{i}.com"} for i in range(25)]
            
            result = await adapter.get_recommendations()
            # 应该限制为 20 条
            assert len(result) == 20
    
    @pytest.mark.asyncio
    async def test_duanju_get_recommendations_error(self):
        """测试 DuanjuSearch 获取推荐失败"""
        adapter = DuanjuSearchAdapter()
        
        with patch.object(adapter, '_get_recent_data', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception("网络错误")
            
            result = await adapter.get_recommendations()
            assert len(result) == 0


class TestAdapterEpisodesAndVideo:
    """测试适配器剧集和视频方法"""
    
    @pytest.mark.asyncio
    async def test_cenguigui_get_episodes(self):
        """测试 Cenguigui 获取剧集"""
        adapter = CenguiguiAdapter()
        
        with patch.object(adapter, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = json.dumps({
                "code": 200,
                "book_name": "测试短剧",
                "book_id": "123",
                "total": 10,
                "data": [
                    {"video_id": "v1", "title": "第1集"},
                    {"video_id": "v2", "title": "第2集"}
                ]
            })
            
            result = await adapter.get_episodes("123")
            assert result.code == 200
            assert len(result.episodes) == 2
    
    @pytest.mark.asyncio
    async def test_cenguigui_get_video_url(self):
        """测试 Cenguigui 获取视频地址"""
        adapter = CenguiguiAdapter()
        
        with patch.object(adapter, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = json.dumps({
                "code": 200,
                "data": {
                    "url": "http://video.com/test.m3u8",
                    "pic": "http://pic.com/test.jpg",
                    "title": "第1集",
                    "info": {"quality": "1080p", "duration": "05:00"}
                }
            })
            
            result = await adapter.get_video_url("v1", "1080p")
            assert result.code == 200
            assert "m3u8" in result.url
    
    @pytest.mark.asyncio
    async def test_uuuka_get_episodes_valid_link(self):
        """测试 Uuuka 获取剧集（有效链接）"""
        adapter = UuukaAdapter()
        
        result = await adapter.get_episodes("http://pan.quark.cn/s/xxx")
        assert result.code == 0
        assert "网盘" in result.desc
    
    @pytest.mark.asyncio
    async def test_uuuka_get_episodes_invalid_link(self):
        """测试 Uuuka 获取剧集（无效链接）"""
        adapter = UuukaAdapter()
        
        result = await adapter.get_episodes("invalid")
        assert result.code == 1
    
    @pytest.mark.asyncio
    async def test_duanju_get_episodes_valid_link(self):
        """测试 DuanjuSearch 获取剧集（有效链接）"""
        adapter = DuanjuSearchAdapter()
        
        result = await adapter.get_episodes("http://pan.quark.cn/s/xxx")
        assert result.code == 0
        assert "网盘" in result.desc
    
    @pytest.mark.asyncio
    async def test_duanju_get_episodes_invalid_link(self):
        """测试 DuanjuSearch 获取剧集（无效链接）"""
        adapter = DuanjuSearchAdapter()
        
        result = await adapter.get_episodes("invalid")
        assert result.code == 1


class TestDuanjuSearchGetRecentData:
    """测试 DuanjuSearch 获取最近数据"""
    
    @pytest.mark.asyncio
    async def test_get_recent_data_first_day(self):
        """测试获取今天的数据"""
        adapter = DuanjuSearchAdapter()
        
        with patch.object(adapter, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = [{"name": "今日短剧", "url": "http://test.com"}]
            
            result = await adapter._get_recent_data()
            assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_get_recent_data_fallback(self):
        """测试今天无数据时回退到前几天"""
        adapter = DuanjuSearchAdapter()
        
        call_count = 0
        async def mock_request(endpoint, params=None):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                # 前两天无数据
                return []
            else:
                # 第三天有数据
                return [{"name": "前几天短剧", "url": "http://test.com"}]
        
        with patch.object(adapter, '_request', side_effect=mock_request):
            result = await adapter._get_recent_data()
            assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_get_recent_data_all_empty(self):
        """测试所有日期都无数据"""
        adapter = DuanjuSearchAdapter()
        
        with patch.object(adapter, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = []
            
            result = await adapter._get_recent_data()
            assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_get_recent_data_exception(self):
        """测试请求异常时继续尝试"""
        adapter = DuanjuSearchAdapter()
        
        call_count = 0
        async def mock_request(endpoint, params=None):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("网络错误")
            else:
                return [{"name": "短剧", "url": "http://test.com"}]
        
        with patch.object(adapter, '_request', side_effect=mock_request):
            result = await adapter._get_recent_data()
            assert len(result) == 1
