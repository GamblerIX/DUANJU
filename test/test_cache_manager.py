"""缓存管理器测试

测试 src/data/cache/cache_manager.py 中的缓存功能。
"""
from pathlib import Path
import json
import sys
import tempfile
import time

import pytest

from src.data.cache_manager import CacheManager

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.cache_manager import CacheManager, CacheEntry


class TestCacheEntry:
    """CacheEntry 测试"""
    
    def test_cache_entry_not_expired(self):
        """测试未过期的缓存条目"""
        entry = CacheEntry(
            data="test_data",
            timestamp=time.time(),
            ttl=300000  # 5分钟
        )
        assert entry.is_expired() is False
    
    def test_cache_entry_expired(self):
        """测试已过期的缓存条目"""
        entry = CacheEntry(
            data="test_data",
            timestamp=time.time() - 400,  # 400秒前
            ttl=300000  # 5分钟 = 300秒
        )
        assert entry.is_expired() is True
    
    def test_cache_entry_just_expired(self):
        """测试刚好过期的缓存"""
        entry = CacheEntry(
            data="test_data",
            timestamp=time.time() - 301,  # 刚过期
            ttl=300000
        )
        assert entry.is_expired() is True


class TestCacheManager:
    """CacheManager 测试"""
    
    @pytest.fixture
    def cache(self):
        """创建测试用缓存管理器"""
        return CacheManager(max_entries=10, enable_persistence=False)
    
    @pytest.fixture
    def persistent_cache(self, tmp_path):
        """创建持久化缓存管理器"""
        cache_dir = tmp_path / "cache"
        return CacheManager(
            max_entries=10,
            enable_persistence=True,
            cache_dir=str(cache_dir)
        )
    
    def test_set_and_get(self, cache):
        """测试设置和获取缓存"""
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
    
    def test_get_nonexistent(self, cache):
        """测试获取不存在的缓存"""
        assert cache.get("nonexistent") is None
    
    def test_get_expired(self, cache):
        """测试获取过期的缓存"""
        cache.set("key1", "value1", ttl=1)  # 1毫秒过期
        time.sleep(0.01)  # 等待过期
        assert cache.get("key1") is None
    
    def test_remove(self, cache):
        """测试移除缓存"""
        cache.set("key1", "value1")
        assert cache.remove("key1") is True
        assert cache.get("key1") is None
    
    def test_remove_nonexistent(self, cache):
        """测试移除不存在的缓存"""
        assert cache.remove("nonexistent") is False
    
    def test_clear(self, cache):
        """测试清空缓存"""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.size == 0
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    def test_lru_eviction(self, cache):
        """测试 LRU 淘汰策略"""
        # 填满缓存
        for i in range(10):
            cache.set(f"key{i}", f"value{i}")
        
        # 添加新条目，应该淘汰最旧的
        cache.set("key_new", "value_new")
        
        # 最旧的 key0 应该被淘汰
        assert cache.get("key0") is None
        assert cache.get("key_new") == "value_new"
    
    def test_lru_access_updates_order(self, cache):
        """测试访问更新 LRU 顺序"""
        for i in range(10):
            cache.set(f"key{i}", f"value{i}")
        
        # 访问 key0，使其变为最新
        cache.get("key0")
        
        # 添加新条目
        cache.set("key_new", "value_new")
        
        # key0 不应该被淘汰，key1 应该被淘汰
        assert cache.get("key0") == "value0"
        assert cache.get("key1") is None
    
    def test_cleanup_expired(self, cache):
        """测试清理过期条目"""
        cache.set("key1", "value1", ttl=1)
        cache.set("key2", "value2", ttl=1000000)
        
        time.sleep(0.01)
        
        cleaned = cache.cleanup_expired()
        assert cleaned == 1
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
    
    def test_generate_key(self):
        """测试缓存键生成"""
        key1 = CacheManager.generate_key("search", "测试", "1")
        key2 = CacheManager.generate_key("search", "测试", "1")
        key3 = CacheManager.generate_key("search", "其他", "1")
        
        assert key1 == key2  # 相同参数生成相同键
        assert key1 != key3  # 不同参数生成不同键
        assert len(key1) == 32  # MD5 哈希长度
    
    def test_stats(self, cache):
        """测试统计信息"""
        cache.set("key1", "value1")
        cache.get("key1")  # hit
        cache.get("key2")  # miss
        
        stats = cache.stats
        assert stats["size"] == 1
        assert stats["hit_count"] == 1
        assert stats["miss_count"] == 1
        assert "50" in stats["hit_rate"]  # 50%
    
    def test_hit_rate(self, cache):
        """测试命中率计算"""
        cache.set("key1", "value1")
        
        # 3次命中，1次未命中
        cache.get("key1")
        cache.get("key1")
        cache.get("key1")
        cache.get("nonexistent")
        
        assert cache.hit_rate == 0.75
    
    def test_hit_rate_empty(self, cache):
        """测试空缓存的命中率"""
        assert cache.hit_rate == 0.0
    
    def test_persistence_save_and_load(self, persistent_cache):
        """测试持久化保存和加载"""
        persistent_cache.set("key1", "value1")
        
        # 创建新的缓存管理器，应该能加载之前的数据
        new_cache = CacheManager(
            max_entries=10,
            enable_persistence=True,
            cache_dir=persistent_cache._cache_dir
        )
        
        assert new_cache.get("key1") == "value1"
    
    def test_persistence_expired_not_loaded(self, tmp_path):
        """测试过期的持久化缓存不被加载"""
        cache_dir = tmp_path / "cache"
        cache = CacheManager(
            max_entries=10,
            enable_persistence=True,
            cache_dir=str(cache_dir)
        )
        
        cache.set("key1", "value1", ttl=1)
        time.sleep(0.01)
        
        # 创建新的缓存管理器
        new_cache = CacheManager(
            max_entries=10,
            enable_persistence=True,
            cache_dir=str(cache_dir)
        )
        
        assert new_cache.get("key1") is None
    
    def test_size_property(self, cache):
        """测试 size 属性"""
        assert cache.size == 0
        cache.set("key1", "value1")
        assert cache.size == 1
        cache.set("key2", "value2")
        assert cache.size == 2
    
    def test_custom_ttl(self, cache):
        """测试自定义 TTL"""
        cache.set("key1", "value1", ttl=100)  # 100毫秒
        assert cache.get("key1") == "value1"
        
        time.sleep(0.15)  # 等待过期
        assert cache.get("key1") is None
    
    def test_unicode_data(self, cache):
        """测试 Unicode 数据"""
        cache.set("key1", "中文数据测试")
        assert cache.get("key1") == "中文数据测试"
    
    def test_large_data(self, cache):
        """测试大数据"""
        large_data = "x" * 100000  # 100KB
        cache.set("key1", large_data)
        assert cache.get("key1") == large_data




# ============================================================
# From: test_cache_manager_full.py
# ============================================================
class TestCacheManagerBasic:
    """测试缓存管理器基本功能"""
    
    @pytest.fixture
    def cache_manager(self, tmp_path):
        return CacheManager(
            max_entries=100,
            enable_persistence=True,
            cache_dir=str(tmp_path / "cache")
        )
    
    def test_set_and_get(self, cache_manager):
        """测试设置和获取"""
        cache_manager.set("key1", "value1", ttl=60000)
        result = cache_manager.get("key1")
        
        assert result == "value1"
    
    def test_get_nonexistent(self, cache_manager):
        """测试获取不存在的键"""
        result = cache_manager.get("nonexistent")
        
        assert result is None
    
    def test_remove(self, cache_manager):
        """测试移除"""
        cache_manager.set("key1", "value1", ttl=60000)
        cache_manager.remove("key1")
        result = cache_manager.get("key1")
        
        assert result is None
    
    def test_clear(self, cache_manager):
        """测试清除"""
        cache_manager.set("key1", "value1", ttl=60000)
        cache_manager.set("key2", "value2", ttl=60000)
        cache_manager.clear()
        
        assert cache_manager.get("key1") is None
        assert cache_manager.get("key2") is None
    
    def test_key_exists(self, cache_manager):
        """测试检查键是否存在"""
        cache_manager.set("key1", "value1", ttl=60000)
        
        # 使用 get 来检查
        assert cache_manager.get("key1") is not None
        assert cache_manager.get("key2") is None


class TestCacheManagerTTL:
    """测试缓存 TTL"""
    
    @pytest.fixture
    def cache_manager(self, tmp_path):
        return CacheManager(
            max_entries=100,
            enable_persistence=False,
            cache_dir=str(tmp_path / "cache")
        )
    
    def test_ttl_not_expired(self, cache_manager):
        """测试未过期的缓存"""
        cache_manager.set("key1", "value1", ttl=60000)  # 60秒
        result = cache_manager.get("key1")
        
        assert result == "value1"
    
    def test_default_ttl(self, cache_manager):
        """测试默认 TTL"""
        cache_manager.set("key1", "value1")  # 使用默认 TTL
        result = cache_manager.get("key1")
        
        assert result == "value1"


class TestCacheManagerKeyGeneration:
    """测试缓存键生成"""
    
    def test_generate_key_single(self):
        """测试单参数键生成"""
        key = CacheManager.generate_key("search")
        
        # generate_key 使用 MD5 哈希
        assert len(key) == 32  # MD5 哈希长度
        assert key.isalnum()
    
    def test_generate_key_multiple(self):
        """测试多参数键生成"""
        key = CacheManager.generate_key("search", "keyword", "1")
        
        assert len(key) == 32
        assert key.isalnum()
    
    def test_generate_key_consistency(self):
        """测试键生成一致性"""
        key1 = CacheManager.generate_key("search", "test")
        key2 = CacheManager.generate_key("search", "test")
        
        assert key1 == key2
    
    def test_generate_key_different_inputs(self):
        """测试不同输入产生不同键"""
        key1 = CacheManager.generate_key("search", "test1")
        key2 = CacheManager.generate_key("search", "test2")
        
        assert key1 != key2


class TestCacheManagerSize:
    """测试缓存大小限制"""
    
    @pytest.fixture
    def small_cache(self, tmp_path):
        return CacheManager(
            max_entries=5,
            enable_persistence=False,
            cache_dir=str(tmp_path / "cache")
        )
    
    def test_max_entries_limit(self, small_cache):
        """测试最大条目限制"""
        for i in range(10):
            small_cache.set(f"key_{i}", f"value_{i}", ttl=60000)
        
        # 应该只保留最近的条目
        assert small_cache.size <= 5
    
    def test_size_property(self, small_cache):
        """测试 size 属性"""
        small_cache.set("key1", "value1", ttl=60000)
        small_cache.set("key2", "value2", ttl=60000)
        
        assert small_cache.size == 2


class TestCacheManagerPersistence:
    """测试缓存持久化"""
    
    @pytest.fixture
    def persistent_cache(self, tmp_path):
        cache_dir = tmp_path / "cache"
        return CacheManager(
            max_entries=100,
            enable_persistence=True,
            cache_dir=str(cache_dir)
        )
    
    def test_persistence_enabled(self, persistent_cache):
        """测试持久化启用"""
        persistent_cache.set("key1", "value1", ttl=60000)
        
        # 检查缓存目录是否创建
        cache_dir = Path(persistent_cache._cache_dir)
        assert cache_dir.exists()
    
    def test_persistence_reload(self, tmp_path):
        """测试持久化重新加载"""
        cache_dir = str(tmp_path / "cache")
        
        # 创建缓存并设置值
        cache1 = CacheManager(
            max_entries=100,
            enable_persistence=True,
            cache_dir=cache_dir
        )
        cache1.set("key1", "value1", ttl=60000)
        
        # 创建新缓存实例（会自动加载持久化数据）
        cache2 = CacheManager(
            max_entries=100,
            enable_persistence=True,
            cache_dir=cache_dir
        )
        
        # 验证数据
        result = cache2.get("key1")
        assert result == "value1"


class TestCacheManagerJSON:
    """测试 JSON 数据缓存"""
    
    @pytest.fixture
    def cache_manager(self, tmp_path):
        return CacheManager(
            max_entries=100,
            enable_persistence=False,
            cache_dir=str(tmp_path / "cache")
        )
    
    def test_cache_json_string(self, cache_manager):
        """测试缓存 JSON 字符串"""
        data = {"code": 200, "data": [{"id": 1, "name": "test"}]}
        json_str = json.dumps(data)
        
        cache_manager.set("json_key", json_str, ttl=60000)
        result = cache_manager.get("json_key")
        
        assert result == json_str
        parsed = json.loads(result)
        assert parsed["code"] == 200
    
    def test_cache_complex_data(self, cache_manager):
        """测试缓存复杂数据"""
        data = {
            "code": 200,
            "data": [
                {"id": 1, "name": "短剧1", "episodes": 20},
                {"id": 2, "name": "短剧2", "episodes": 30}
            ],
            "page": 1,
            "total": 100
        }
        json_str = json.dumps(data)
        
        cache_manager.set("complex_key", json_str, ttl=60000)
        result = cache_manager.get("complex_key")
        
        parsed = json.loads(result)
        assert len(parsed["data"]) == 2


class TestCacheManagerEdgeCases:
    """测试边界情况"""
    
    @pytest.fixture
    def cache_manager(self, tmp_path):
        return CacheManager(
            max_entries=100,
            enable_persistence=False,
            cache_dir=str(tmp_path / "cache")
        )
    
    def test_empty_value(self, cache_manager):
        """测试空值"""
        cache_manager.set("empty_key", "", ttl=60000)
        result = cache_manager.get("empty_key")
        
        assert result == ""
    
    def test_unicode_key(self, cache_manager):
        """测试 Unicode 键"""
        cache_manager.set("中文键", "中文值", ttl=60000)
        result = cache_manager.get("中文键")
        
        assert result == "中文值"
    
    def test_special_characters_in_key(self, cache_manager):
        """测试键中的特殊字符"""
        key = "search_测试_1"
        cache_manager.set(key, "value", ttl=60000)
        result = cache_manager.get(key)
        
        assert result == "value"
    
    def test_overwrite_existing(self, cache_manager):
        """测试覆盖现有值"""
        cache_manager.set("key1", "value1", ttl=60000)
        cache_manager.set("key1", "value2", ttl=60000)
        result = cache_manager.get("key1")
        
        assert result == "value2"
    
    def test_remove_nonexistent(self, cache_manager):
        """测试移除不存在的键"""
        # 不应该抛出异常
        cache_manager.remove("nonexistent")
