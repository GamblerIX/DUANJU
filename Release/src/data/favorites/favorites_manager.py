import json
import time
from pathlib import Path
from typing import List, Optional, Set
from ...core.models import DramaInfo, FavoriteItem
from ...core.utils.json_serializer import serialize_drama, deserialize_drama


class FavoritesManager:
    DEFAULT_PATH = "data/favorites.json"
    
    def __init__(self, file_path: Optional[str] = None):
        self._file_path = Path(file_path or self.DEFAULT_PATH)
        self._favorites: List[FavoriteItem] = []
        self._load()
    
    def _load(self) -> None:
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
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        data = {"favorites": [{"drama": serialize_drama(item.drama), "addedTime": item.added_time}
                             for item in self._favorites]}
        self._file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    
    def load(self) -> None:
        self._load()
    
    def save(self) -> None:
        self._save()
    
    def add(self, drama: DramaInfo) -> bool:
        if self.is_favorite(drama.book_id):
            return False
        self._favorites.append(FavoriteItem(drama, time.time()))
        self._save()
        return True
    
    def remove(self, book_id: str) -> bool:
        for i, item in enumerate(self._favorites):
            if item.drama.book_id == book_id:
                del self._favorites[i]
                self._save()
                return True
        return False
    
    def toggle(self, drama: DramaInfo) -> bool:
        if self.is_favorite(drama.book_id):
            self.remove(drama.book_id)
            return False
        else:
            self.add(drama)
            return True
    
    def is_favorite(self, book_id: str) -> bool:
        return any(item.drama.book_id == book_id for item in self._favorites)
    
    def get_all(self) -> List[FavoriteItem]:
        return self._favorites.copy()
    
    def get_all_dramas(self) -> List[DramaInfo]:
        return [item.drama for item in self._favorites]
    
    def get_ids(self) -> Set[str]:
        return {item.drama.book_id for item in self._favorites}
    
    def clear(self) -> None:
        self._favorites.clear()
        self._save()
    
    def count(self) -> int:
        return len(self._favorites)
