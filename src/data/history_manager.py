"""观看历史管理器实现"""
import json
import time
from pathlib import Path
from typing import List, Optional

from ..core.models import DramaInfo, HistoryItem
from ..utils.json_serializer import serialize_drama, deserialize_drama


class HistoryManager:
    """观看历史管理器 - 管理用户的观看历史，支持 JSON 持久化"""
    
    DEFAULT_PATH = "data/history.json"
    MAX_HISTORY = 100
    
    def __init__(self, file_path: Optional[str] = None, max_items: int = MAX_HISTORY):
        self._file_path = Path(file_path or self.DEFAULT_PATH)
        self._max_items = max_items
        self._history: List[HistoryItem] = []
        self._load()
    
    def _load(self) -> None:
        """从文件加载历史"""
        try:
            if self._file_path.exists():
                data = json.loads(self._file_path.read_text(encoding='utf-8'))
                self._history = []
                for item in data.get("history", []):
                    drama = deserialize_drama(item.get("drama", {}))
                    self._history.append(HistoryItem(
                        drama=drama,
                        episode_number=item.get("episodeNumber", 1),
                        position_ms=item.get("positionMs", 0),
                        watch_time=item.get("watchTime", time.time())
                    ))
        except (json.JSONDecodeError, KeyError):
            self._history = []
    
    def _save(self) -> None:
        """保存历史到文件"""
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "history": [
                {
                    "drama": serialize_drama(item.drama),
                    "episodeNumber": item.episode_number,
                    "positionMs": item.position_ms,
                    "watchTime": item.watch_time
                }
                for item in self._history
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
    
    def add(self, drama: DramaInfo, episode_number: int, position_ms: int = 0) -> None:
        """添加或更新观看历史"""
        for i, item in enumerate(self._history):
            if item.drama.book_id == drama.book_id:
                self._history[i] = HistoryItem(
                    drama=drama,
                    episode_number=episode_number,
                    position_ms=position_ms,
                    watch_time=time.time()
                )
                self._history.insert(0, self._history.pop(i))
                self._save()
                return
        
        self._history.insert(0, HistoryItem(
            drama=drama,
            episode_number=episode_number,
            position_ms=position_ms,
            watch_time=time.time()
        ))
        
        if len(self._history) > self._max_items:
            self._history = self._history[:self._max_items]
        
        self._save()
    
    def get_position(self, book_id: str, episode: int) -> int:
        """获取指定剧集的播放位置"""
        for item in self._history:
            if item.drama.book_id == book_id and item.episode_number == episode:
                return item.position_ms
        return 0
    
    def update_position(self, book_id: str, position_ms: int) -> bool:
        """更新播放位置"""
        for i, item in enumerate(self._history):
            if item.drama.book_id == book_id:
                self._history[i] = HistoryItem(
                    drama=item.drama,
                    episode_number=item.episode_number,
                    position_ms=position_ms,
                    watch_time=time.time()
                )
                self._save()
                return True
        return False
    
    def get(self, book_id: str) -> Optional[HistoryItem]:
        """获取指定短剧的观看历史"""
        for item in self._history:
            if item.drama.book_id == book_id:
                return item
        return None
    
    def get_all(self) -> List[HistoryItem]:
        """获取所有观看历史"""
        return self._history.copy()
    
    def remove(self, book_id: str) -> bool:
        """移除指定短剧的观看历史"""
        for i, item in enumerate(self._history):
            if item.drama.book_id == book_id:
                del self._history[i]
                self._save()
                return True
        return False
    
    def clear(self) -> None:
        """清空所有观看历史"""
        self._history.clear()
        self._save()
    
    def count(self) -> int:
        """获取历史记录数量"""
        return len(self._history)
