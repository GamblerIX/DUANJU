"""缓存管理器

提供内存缓存和可选的持久化缓存支持。
支持 TTL 过期、LRU 淘汰策略。
"""
import time
import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from collections import OrderedDict

from ..utils.log_manager import get_logger

logger = get_logger()


@dataclass
class CacheEntry:
    """缓存条目"""
    data: str
    timestamp: float
    ttl: int  # 毫秒
    
    def is_expired(self) -> bool:
        elapsed = (time.time() - self.timestamp) * 1000
        return elapsed > self.ttl


class CacheManager:
    """缓存管理器
    
    特性:
    - 内存缓存 + 可选持久化
    - TTL 过期机制
    - LRU 淘汰策略
    - 自动清理过期条目
    """
    
    DEFAULT_TTL = 300000  # 5 分钟
    MAX_MEMORY_ENTRIES = 500
    CACHE_DIR = "cache"
    
    def __init__(
        self, 
        max_entries: int = MAX_MEMORY_ENTRIES,
        enable_persistence: bool = False,
        cache_dir: str = CACHE_DIR
    ):
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_entries = max_entries
        self._enable_persistence = enable_persistence
        self._cache_dir = Path(cache_dir)
        self._hit_count = 0
        self._miss_count = 0
        
        if enable_persistence:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            self._load_persistent_cache()
    
    def get(self, key: str) -> Optional[str]:
        """获取缓存"""
        # 先查内存
        entry = self._cache.get(key)
        if entry:
            if entry.is_expired():
                self.remove(key)
                self._miss_count += 1
                return None
            # LRU: 移到末尾
            self._cache.move_to_end(key)
            self._hit_count += 1
            return entry.data
        
        # 查持久化缓存
        if self._enable_persistence:
            data = self._load_from_disk(key)
            if data:
                self._hit_count += 1
                return data
        
        self._miss_count += 1
        return None
    
    def set(self, key: str, data: str, ttl: int = DEFAULT_TTL) -> None:
        """设置缓存"""
        # 淘汰旧条目
        while len(self._cache) >= self._max_entries:
            oldest_key = next(iter(self._cache))
            self._cache.pop(oldest_key)
        
        entry = CacheEntry(data=data, timestamp=time.time(), ttl=ttl)
        self._cache[key] = entry
        
        # 持久化
        if self._enable_persistence:
            self._save_to_disk(key, entry)
    
    def remove(self, key: str) -> bool:
        """移除缓存"""
        removed = key in self._cache
        self._cache.pop(key, None)
        
        if self._enable_persistence:
            self._remove_from_disk(key)
        
        return removed
    
    def clear(self) -> None:
        """清空所有缓存"""
        self._cache.clear()
        self._hit_count = 0
        self._miss_count = 0
        
        if self._enable_persistence:
            for file in self._cache_dir.glob("*.cache"):
                file.unlink()
    
    def cleanup_expired(self) -> int:
        """清理过期条目，返回清理数量"""
        expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
        for key in expired_keys:
            self.remove(key)
        return len(expired_keys)
    
    @staticmethod
    def generate_key(*parts: str) -> str:
        """生成缓存键"""
        combined = ":".join(parts)
        return hashlib.md5(combined.encode()).hexdigest()
    
    # ==================== 持久化方法 ====================
    
    def _get_cache_path(self, key: str) -> Path:
        return self._cache_dir / f"{key}.cache"
    
    def _save_to_disk(self, key: str, entry: CacheEntry) -> None:
        try:
            path = self._get_cache_path(key)
            cache_data = {
                "data": entry.data,
                "timestamp": entry.timestamp,
                "ttl": entry.ttl
            }
            path.write_text(json.dumps(cache_data), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to save cache to disk: {e}")
    
    def _load_from_disk(self, key: str) -> Optional[str]:
        try:
            path = self._get_cache_path(key)
            if not path.exists():
                return None
            
            cache_data = json.loads(path.read_text(encoding="utf-8"))
            entry = CacheEntry(
                data=cache_data["data"],
                timestamp=cache_data["timestamp"],
                ttl=cache_data["ttl"]
            )
            
            if entry.is_expired():
                path.unlink()
                return None
            
            # 加载到内存
            self._cache[key] = entry
            return entry.data
        except Exception as e:
            logger.warning(f"Failed to load cache from disk: {e}")
            return None
    
    def _remove_from_disk(self, key: str) -> None:
        try:
            path = self._get_cache_path(key)
            if path.exists():
                path.unlink()
        except Exception:
            pass
    
    def _load_persistent_cache(self) -> None:
        """启动时加载持久化缓存索引"""
        try:
            count = 0
            for file in self._cache_dir.glob("*.cache"):
                if count >= self._max_entries:
                    break
                key = file.stem
                self._load_from_disk(key)
                count += 1
            logger.debug(f"Loaded {count} cached entries from disk")
        except Exception as e:
            logger.warning(f"Failed to load persistent cache: {e}")
    
    # ==================== 统计信息 ====================
    
    @property
    def size(self) -> int:
        return len(self._cache)
    
    @property
    def hit_rate(self) -> float:
        total = self._hit_count + self._miss_count
        return self._hit_count / total if total > 0 else 0.0
    
    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "size": self.size,
            "max_entries": self._max_entries,
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "hit_rate": f"{self.hit_rate:.2%}",
            "persistence_enabled": self._enable_persistence
        }
