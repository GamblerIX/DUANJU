"""收藏管理器实现"""
import json
import time
from pathlib import Path
from typing import List, Optional, Set

from ..core.models import DramaInfo, FavoriteItem
from ..utils.json_serializer import serialize_drama, deserialize_drama
from ..utils.resource_utils import get_app_path


def _get_favorites_path() -> Path:
    """获取收藏文件路径"""
    data_dir = Path(get_app_path("data"))
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / "favorites.json"
    except (PermissionError, OSError):
        user_data_dir = Path.home() / ".duanjuapp" / "data"
        user_data_dir.mkdir(parents=True, exist_ok=True)
        return user_data_dir / "favorites.json"


class FavoritesManager:
    """收藏管理器 - 管理用户收藏的短剧，支持 JSON 持久化"""
    
    def __init__(self, file_path: Optional[str] = None):
        self._file_path = Path(file_path) if file_path else _get_favorites_path()
        self._favorites: List[FavoriteItem] = []
        self._load()
    
    def _load(self) -> None:
        """从文件加载收藏"""
        try:
            if self._file_path.exists():
                data = json.loads(self._file_path.read_text(encoding='utf-8'))
                self._favorites = []
                for item in data.get("favorites", []):
                    drama = deserialize_drama(item.get("drama", {}))
                    added_time = item.get("addedTime", time.time())
                    self._favorites.append(FavoriteItem(drama, added_time))
        except (json.JSONDecodeError, KeyError):
            self._favorites = []
    
    def _save(self) -> None:
        """保存收藏到文件"""
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "favorites": [
                {
                    "drama": serialize_drama(item.drama),
                    "addedTime": item.added_time
                }
                for item in self._favorites
            ]
        }
        self._file_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
    
    def load(self) -> None:
        """公开的加载方法"""
        self._load()
    
    def save(self) -> None:
        """公开的保存方法"""
        self._save()
    
    def add(self, drama: DramaInfo) -> bool:
        """添加收藏"""
        if self.is_favorite(drama.book_id):
            return False
        self._favorites.append(FavoriteItem(drama, time.time()))
        self._save()
        return True
    
    def remove(self, book_id: str) -> bool:
        """移除收藏"""
        for i, item in enumerate(self._favorites):
            if item.drama.book_id == book_id:
                del self._favorites[i]
                self._save()
                return True
        return False
    
    def toggle(self, drama: DramaInfo) -> bool:
        """切换收藏状态"""
        if self.is_favorite(drama.book_id):
            self.remove(drama.book_id)
            return False
        else:
            self.add(drama)
            return True
    
    def is_favorite(self, book_id: str) -> bool:
        """检查是否已收藏"""
        return any(item.drama.book_id == book_id for item in self._favorites)
    
    def get_all(self) -> List[FavoriteItem]:
        """获取所有收藏项"""
        return self._favorites.copy()
    
    def get_all_dramas(self) -> List[DramaInfo]:
        """获取所有收藏的短剧"""
        return [item.drama for item in self._favorites]
    
    def get_ids(self) -> Set[str]:
        """获取所有收藏的短剧ID集合"""
        return {item.drama.book_id for item in self._favorites}
    
    def clear(self) -> None:
        """清空所有收藏"""
        self._favorites.clear()
        self._save()
    
    def count(self) -> int:
        """获取收藏数量"""
        return len(self._favorites)
