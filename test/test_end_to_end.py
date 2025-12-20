"""端到端测试

模拟完整的用户使用流程，确保各组件协同工作正常。
"""
import pytest
import json
import time
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.models import (
    DramaInfo, EpisodeInfo, VideoInfo, SearchResult,
    EpisodeList, CategoryResult, AppConfig, ThemeMode
)


class TestSearchFlow:
    """搜索流程端到端测试"""
    
    @pytest.fixture
    def mock_search_response(self):
        """模拟搜索响应"""
        return {
            "code": 200,
            "msg": "搜索成功",
            "page": 1,
            "data": [
                {
                    "book_id": "123",
                    "title": "测试短剧",
                    "cover": "https://example.com/cover.jpg",
                    "episode_cnt": 20,
                    "intro": "这是一部测试短剧",
                    "type": "都市",
                    "author": "测试作者",
                    "play_cnt": 10000
                }
            ]
        }
    
    def test_search_parse_display_flow(self, mock_search_response):
        """测试搜索 -> 解析 -> 显示流程"""
        from src.data.response_parser import ResponseParser
        
        # 1. 模拟 API 返回
        json_str = json.dumps(mock_search_response)
        
        # 2. 解析响应
        result = ResponseParser.parse_search_result(json_str)
        
        # 3. 验证结果
        assert result.code == 200
        assert len(result.data) == 1
        
        drama = result.data[0]
        assert drama.book_id == "123"
        assert drama.title == "测试短剧"
        assert drama.episode_cnt == 20
        
        # 4. 验证向后兼容属性
        assert drama.name == drama.title
        assert drama.episode_count == drama.episode_cnt


class TestEpisodeFlow:
    """剧集流程端到端测试"""
    
    @pytest.fixture
    def mock_episode_response(self):
        """模拟剧集响应"""
        return {
            "code": 200,
            "book_name": "测试短剧",
            "book_id": "123",
            "author": "测试作者",
            "category": "都市",
            "desc": "简介",
            "total": 20,
            "data": [
                {"video_id": f"v{i}", "title": f"第{i}集", "chapter_word_number": 0}
                for i in range(1, 21)
            ]
        }
    
    def test_episode_parse_flow(self, mock_episode_response):
        """测试剧集解析流程"""
        from src.data.response_parser import ResponseParser
        
        json_str = json.dumps(mock_episode_response)
        result = ResponseParser.parse_episode_list(json_str)
        
        assert result.code == 200
        assert result.book_name == "测试短剧"
        assert len(result.episodes) == 20
        
        # 验证集数解析
        for i, ep in enumerate(result.episodes, 1):
            assert ep.episode_number == i


class TestVideoFlow:
    """视频播放流程端到端测试"""
    
    @pytest.fixture
    def mock_video_response(self):
        """模拟视频响应"""
        return {
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
        }
    
    def test_video_parse_flow(self, mock_video_response):
        """测试视频解析流程"""
        from src.data.response_parser import ResponseParser
        
        json_str = json.dumps(mock_video_response)
        result = ResponseParser.parse_video_info(json_str)
        
        assert result.code == 200
        assert result.url == "https://example.com/video.m3u8"
        assert result.quality == "1080p"
        assert result.video_url == result.url  # 向后兼容


class TestFavoritesFlow:
    """收藏流程端到端测试"""
    
    @pytest.fixture
    def favorites_manager(self, tmp_path):
        """创建收藏管理器"""
        from src.data.favorites_manager import FavoritesManager
        return FavoritesManager(str(tmp_path / "favorites.json"))
    
    @pytest.fixture
    def sample_drama(self):
        """示例短剧"""
        return DramaInfo(
            book_id="123",
            title="测试短剧",
            cover="https://example.com/cover.jpg",
            episode_cnt=20
        )
    
    def test_add_check_remove_flow(self, favorites_manager, sample_drama):
        """测试添加 -> 检查 -> 移除流程"""
        # 1. 初始状态
        assert not favorites_manager.is_favorite(sample_drama.book_id)
        
        # 2. 添加收藏
        favorites_manager.add(sample_drama)
        assert favorites_manager.is_favorite(sample_drama.book_id)
        assert favorites_manager.count() == 1
        
        # 3. 获取收藏列表
        dramas = favorites_manager.get_all_dramas()
        assert len(dramas) == 1
        assert dramas[0].book_id == sample_drama.book_id
        
        # 4. 移除收藏
        favorites_manager.remove(sample_drama.book_id)
        assert not favorites_manager.is_favorite(sample_drama.book_id)
        assert favorites_manager.count() == 0


class TestHistoryFlow:
    """历史记录流程端到端测试"""
    
    @pytest.fixture
    def history_manager(self, tmp_path):
        """创建历史管理器"""
        from src.data.history_manager import HistoryManager
        return HistoryManager(str(tmp_path / "history.json"))
    
    @pytest.fixture
    def sample_drama(self):
        """示例短剧"""
        return DramaInfo(
            book_id="123",
            title="测试短剧",
            cover="https://example.com/cover.jpg",
            episode_cnt=20
        )
    
    def test_watch_resume_flow(self, history_manager, sample_drama):
        """测试观看 -> 记录 -> 恢复流程"""
        # 1. 开始观看
        history_manager.add(sample_drama, episode_number=1, position_ms=0)
        
        # 2. 更新进度
        history_manager.update_position(sample_drama.book_id, 30000)  # 30秒
        
        # 3. 获取进度
        item = history_manager.get(sample_drama.book_id)
        assert item is not None
        assert item.position_ms == 30000
        
        # 4. 继续观看下一集
        history_manager.add(sample_drama, episode_number=2, position_ms=0)
        
        item = history_manager.get(sample_drama.book_id)
        assert item.episode_number == 2


class TestCacheFlow:
    """缓存流程端到端测试"""
    
    @pytest.fixture
    def cache_manager(self):
        """创建缓存管理器"""
        from src.data.cache_manager import CacheManager
        return CacheManager(max_entries=100, enable_persistence=False)
    
    def test_cache_hit_miss_flow(self, cache_manager):
        """测试缓存命中/未命中流程"""
        from src.data.cache_manager import CacheManager
        
        # 1. 生成缓存键
        key = CacheManager.generate_key("search", "测试", "1")
        
        # 2. 首次请求 - 未命中
        cached = cache_manager.get(key)
        assert cached is None
        
        # 3. 存储结果
        data = '{"code": 200, "data": []}'
        cache_manager.set(key, data)
        
        # 4. 再次请求 - 命中
        cached = cache_manager.get(key)
        assert cached == data
        
        # 5. 验证统计
        assert cache_manager.hit_rate > 0


class TestConfigFlow:
    """配置流程端到端测试"""
    
    @pytest.fixture
    def config_manager(self, tmp_path):
        """创建配置管理器"""
        from src.data.config_manager import ConfigManager
        return ConfigManager(str(tmp_path / "config.json"))
    
    def test_config_change_persist_flow(self, config_manager, tmp_path):
        """测试配置修改 -> 持久化 -> 重新加载流程"""
        from src.data.config_manager import ConfigManager
        
        # 1. 修改配置
        config_manager.theme_mode = ThemeMode.DARK
        config_manager.api_timeout = 5000
        config_manager.add_search_history("测试关键词")
        
        # 2. 重新加载
        new_manager = ConfigManager(str(tmp_path / "config.json"))
        
        # 3. 验证持久化
        assert new_manager.theme_mode == ThemeMode.DARK
        assert new_manager.api_timeout == 5000
        assert "测试关键词" in new_manager.search_history


class TestErrorHandlingFlow:
    """错误处理流程端到端测试"""
    
    def test_api_error_handling(self):
        """测试 API 错误处理流程"""
        from src.data.response_parser import ResponseParser, ApiResponseError
        
        # 模拟错误响应
        error_response = json.dumps({
            "code": 500,
            "msg": "服务器内部错误",
            "tips": "请稍后重试"
        })
        
        # 验证抛出异常
        with pytest.raises(ApiResponseError) as exc_info:
            ResponseParser.parse_search_result(error_response)
        
        assert exc_info.value.code == 500
        assert "服务器" in exc_info.value.message
    
    def test_invalid_json_handling(self):
        """测试无效 JSON 处理"""
        from src.data.response_parser import ResponseParser
        
        error = ResponseParser.parse_error("not valid json")
        
        assert error.code == 0
        assert "JSON" in error.message


class TestDataIntegrity:
    """数据完整性测试"""
    
    def test_drama_info_completeness(self):
        """测试短剧信息完整性"""
        drama = DramaInfo(
            book_id="123",
            title="测试短剧",
            cover="https://example.com/cover.jpg",
            episode_cnt=20,
            intro="简介",
            type="都市",
            author="作者",
            play_cnt=10000
        )
        
        # 验证所有字段
        assert drama.book_id
        assert drama.title
        assert drama.cover
        assert drama.episode_cnt > 0
        
        # 验证向后兼容
        assert drama.name == drama.title
        assert drama.cover_url == drama.cover
        assert drama.episode_count == drama.episode_cnt
        assert drama.description == drama.intro
        assert drama.category == drama.type
    
    def test_search_result_structure(self):
        """测试搜索结果结构"""
        dramas = [
            DramaInfo(book_id=str(i), title=f"Drama {i}", cover=f"url{i}")
            for i in range(5)
        ]
        
        result = SearchResult(
            code=200,
            msg="success",
            data=dramas,
            page=1
        )
        
        assert result.code == 200
        assert len(result.data) == 5
        assert result.current_page == 1
        assert all(isinstance(d, DramaInfo) for d in result.data)


class TestConcurrencySimulation:
    """并发模拟测试"""
    
    def test_cache_concurrent_access(self):
        """测试缓存并发访问"""
        from src.data.cache_manager import CacheManager
        import threading
        
        cache = CacheManager(max_entries=100)
        errors = []
        
        def writer():
            try:
                for i in range(100):
                    cache.set(f"key_{i}", f"value_{i}")
            except Exception as e:
                errors.append(e)
        
        def reader():
            try:
                for i in range(100):
                    cache.get(f"key_{i}")
            except Exception as e:
                errors.append(e)
        
        threads = [
            threading.Thread(target=writer),
            threading.Thread(target=reader),
            threading.Thread(target=writer),
            threading.Thread(target=reader),
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # 不应该有错误
        assert len(errors) == 0

