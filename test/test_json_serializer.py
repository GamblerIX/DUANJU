"""JSON 序列化器测试

测试 src/core/utils/json_serializer.py 中的序列化功能。
"""
import pytest
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.json_serializer import (
    serialize_config, deserialize_config,
    serialize_drama, deserialize_drama,
    serialize_episode, deserialize_episode,
    serialize_dramas, deserialize_dramas
)
from src.core.models import AppConfig, ThemeMode, DramaInfo, EpisodeInfo


class TestConfigSerialization:
    """配置序列化测试"""
    
    def test_serialize_config(self):
        """测试序列化配置"""
        config = AppConfig(
            api_timeout=5000,
            default_quality="720p",
            theme_mode=ThemeMode.DARK,
            last_search_keyword="测试",
            search_history=["a", "b"],
            current_provider="test"
        )
        
        json_str = serialize_config(config)
        data = json.loads(json_str)
        
        assert data["apiTimeout"] == 5000
        assert data["defaultQuality"] == "720p"
        assert data["themeMode"] == "dark"
        assert data["lastSearchKeyword"] == "测试"
        assert data["searchHistory"] == ["a", "b"]
        assert data["currentProvider"] == "test"
    
    def test_deserialize_config(self):
        """测试反序列化配置"""
        json_str = json.dumps({
            "apiTimeout": 5000,
            "defaultQuality": "720p",
            "themeMode": "dark",
            "lastSearchKeyword": "测试",
            "searchHistory": ["a", "b"],
            "maxSearchHistory": 10,
            "currentProvider": "test",
            "enableCache": False,
            "cacheTTL": 100000,
            "maxRetries": 5,
            "retryDelay": 2000
        })
        
        config = deserialize_config(json_str)
        
        assert config.api_timeout == 5000
        assert config.default_quality == "720p"
        assert config.theme_mode == ThemeMode.DARK
        assert config.last_search_keyword == "测试"
        assert config.search_history == ["a", "b"]
        assert config.current_provider == "test"
        assert config.enable_cache is False
    
    def test_deserialize_config_defaults(self):
        """测试反序列化使用默认值"""
        json_str = json.dumps({})
        
        config = deserialize_config(json_str)
        
        assert config.api_timeout == 10000
        assert config.default_quality == "1080p"
        assert config.theme_mode == ThemeMode.AUTO
    
    def test_roundtrip_config(self):
        """测试配置序列化往返"""
        original = AppConfig(
            api_timeout=8000,
            theme_mode=ThemeMode.LIGHT,
            search_history=["x", "y", "z"]
        )
        
        json_str = serialize_config(original)
        restored = deserialize_config(json_str)
        
        assert restored.api_timeout == original.api_timeout
        assert restored.theme_mode == original.theme_mode
        assert restored.search_history == original.search_history


class TestDramaSerialization:
    """短剧序列化测试"""
    
    @pytest.fixture
    def sample_drama(self):
        """示例短剧"""
        return DramaInfo(
            book_id="123",
            title="测试短剧",
            cover="https://example.com/cover.jpg",
            episode_cnt=20,
            intro="这是简介",
            type="都市",
            author="作者",
            play_cnt=10000
        )
    
    def test_serialize_drama(self, sample_drama):
        """测试序列化短剧"""
        data = serialize_drama(sample_drama)
        
        assert data["book_id"] == "123"
        assert data["title"] == "测试短剧"
        assert data["cover"] == "https://example.com/cover.jpg"
        assert data["episode_cnt"] == 20
        assert data["intro"] == "这是简介"
        assert data["type"] == "都市"
        assert data["author"] == "作者"
        assert data["play_cnt"] == 10000
    
    def test_deserialize_drama(self):
        """测试反序列化短剧"""
        data = {
            "book_id": "123",
            "title": "测试短剧",
            "cover": "url",
            "episode_cnt": 20,
            "intro": "简介",
            "type": "都市",
            "author": "作者",
            "play_cnt": 10000
        }
        
        drama = deserialize_drama(data)
        
        assert drama.book_id == "123"
        assert drama.title == "测试短剧"
        assert drama.episode_cnt == 20
    
    def test_deserialize_drama_legacy_keys(self):
        """测试反序列化旧版键名"""
        data = {
            "bookId": "123",
            "name": "测试短剧",
            "coverUrl": "url",
            "episodeCount": 20,
            "description": "简介",
            "category": "都市"
        }
        
        drama = deserialize_drama(data)
        
        assert drama.book_id == "123"
        assert drama.title == "测试短剧"
        assert drama.cover == "url"
        assert drama.episode_cnt == 20
        assert drama.intro == "简介"
        assert drama.type == "都市"
    
    def test_roundtrip_drama(self, sample_drama):
        """测试短剧序列化往返"""
        data = serialize_drama(sample_drama)
        restored = deserialize_drama(data)
        
        assert restored.book_id == sample_drama.book_id
        assert restored.title == sample_drama.title
        assert restored.episode_cnt == sample_drama.episode_cnt


class TestEpisodeSerialization:
    """剧集序列化测试"""
    
    @pytest.fixture
    def sample_episode(self):
        """示例剧集"""
        return EpisodeInfo(
            video_id="v123",
            title="第1集",
            episode_number=1,
            chapter_word_number=0
        )
    
    def test_serialize_episode(self, sample_episode):
        """测试序列化剧集"""
        data = serialize_episode(sample_episode)
        
        assert data["video_id"] == "v123"
        assert data["title"] == "第1集"
        assert data["episode_number"] == 1
        assert data["chapter_word_number"] == 0
    
    def test_deserialize_episode(self):
        """测试反序列化剧集"""
        data = {
            "video_id": "v123",
            "title": "第1集",
            "episode_number": 1,
            "chapter_word_number": 0
        }
        
        episode = deserialize_episode(data)
        
        assert episode.video_id == "v123"
        assert episode.title == "第1集"
        assert episode.episode_number == 1
    
    def test_deserialize_episode_legacy_keys(self):
        """测试反序列化旧版键名"""
        data = {
            "videoId": "v123",
            "title": "第1集",
            "episodeNumber": 1
        }
        
        episode = deserialize_episode(data)
        
        assert episode.video_id == "v123"
        assert episode.episode_number == 1
    
    def test_roundtrip_episode(self, sample_episode):
        """测试剧集序列化往返"""
        data = serialize_episode(sample_episode)
        restored = deserialize_episode(data)
        
        assert restored.video_id == sample_episode.video_id
        assert restored.title == sample_episode.title


class TestDramaListSerialization:
    """短剧列表序列化测试"""
    
    @pytest.fixture
    def sample_dramas(self):
        """示例短剧列表"""
        return [
            DramaInfo(book_id="1", title="Drama 1", cover="url1"),
            DramaInfo(book_id="2", title="Drama 2", cover="url2"),
            DramaInfo(book_id="3", title="Drama 3", cover="url3"),
        ]
    
    def test_serialize_dramas(self, sample_dramas):
        """测试序列化短剧列表"""
        json_str = serialize_dramas(sample_dramas)
        data = json.loads(json_str)
        
        assert len(data) == 3
        assert data[0]["book_id"] == "1"
        assert data[1]["book_id"] == "2"
        assert data[2]["book_id"] == "3"
    
    def test_deserialize_dramas(self):
        """测试反序列化短剧列表"""
        json_str = json.dumps([
            {"book_id": "1", "title": "Drama 1", "cover": "url1"},
            {"book_id": "2", "title": "Drama 2", "cover": "url2"},
        ])
        
        dramas = deserialize_dramas(json_str)
        
        assert len(dramas) == 2
        assert dramas[0].book_id == "1"
        assert dramas[1].book_id == "2"
    
    def test_roundtrip_dramas(self, sample_dramas):
        """测试短剧列表序列化往返"""
        json_str = serialize_dramas(sample_dramas)
        restored = deserialize_dramas(json_str)
        
        assert len(restored) == len(sample_dramas)
        for original, restored_item in zip(sample_dramas, restored):
            assert restored_item.book_id == original.book_id
            assert restored_item.title == original.title
    
    def test_empty_list(self):
        """测试空列表"""
        json_str = serialize_dramas([])
        restored = deserialize_dramas(json_str)
        
        assert restored == []

