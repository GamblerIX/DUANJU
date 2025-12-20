"""收藏和历史管理器测试

测试 src/data/favorites/ 和 src/data/history/ 中的功能。
"""
import pytest
import json
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.favorites_manager import FavoritesManager
from src.data.history_manager import HistoryManager
from src.core.models import DramaInfo, FavoriteItem, HistoryItem


class TestFavoritesManager:
    """FavoritesManager 测试"""
    
    @pytest.fixture
    def favorites_file(self, tmp_path):
        """创建临时收藏文件路径"""
        return tmp_path / "data" / "favorites.json"
    
    @pytest.fixture
    def favorites(self, favorites_file):
        """创建收藏管理器"""
        return FavoritesManager(str(favorites_file))
    
    @pytest.fixture
    def sample_drama(self):
        """示例短剧"""
        return DramaInfo(
            book_id="test_001",
            title="测试短剧",
            cover="https://example.com/cover.jpg",
            episode_cnt=20
        )
    
    def test_add_favorite(self, favorites, sample_drama):
        """测试添加收藏"""
        result = favorites.add(sample_drama)
        
        assert result is True
        assert favorites.is_favorite(sample_drama.book_id)
        assert favorites.count() == 1
    
    def test_add_duplicate(self, favorites, sample_drama):
        """测试重复添加"""
        favorites.add(sample_drama)
        result = favorites.add(sample_drama)
        
        assert result is False
        assert favorites.count() == 1
    
    def test_remove_favorite(self, favorites, sample_drama):
        """测试移除收藏"""
        favorites.add(sample_drama)
        result = favorites.remove(sample_drama.book_id)
        
        assert result is True
        assert not favorites.is_favorite(sample_drama.book_id)
        assert favorites.count() == 0
    
    def test_remove_nonexistent(self, favorites):
        """测试移除不存在的收藏"""
        result = favorites.remove("nonexistent")
        assert result is False
    
    def test_toggle_favorite(self, favorites, sample_drama):
        """测试切换收藏状态"""
        # 添加
        result = favorites.toggle(sample_drama)
        assert result is True
        assert favorites.is_favorite(sample_drama.book_id)
        
        # 移除
        result = favorites.toggle(sample_drama)
        assert result is False
        assert not favorites.is_favorite(sample_drama.book_id)
    
    def test_is_favorite(self, favorites, sample_drama):
        """测试检查收藏状态"""
        assert favorites.is_favorite(sample_drama.book_id) is False
        
        favorites.add(sample_drama)
        assert favorites.is_favorite(sample_drama.book_id) is True
    
    def test_get_all(self, favorites, sample_drama):
        """测试获取所有收藏"""
        favorites.add(sample_drama)
        
        all_favorites = favorites.get_all()
        
        assert len(all_favorites) == 1
        assert isinstance(all_favorites[0], FavoriteItem)
        assert all_favorites[0].drama.book_id == sample_drama.book_id
    
    def test_get_all_dramas(self, favorites, sample_drama):
        """测试获取所有收藏的短剧"""
        favorites.add(sample_drama)
        
        dramas = favorites.get_all_dramas()
        
        assert len(dramas) == 1
        assert dramas[0].book_id == sample_drama.book_id
    
    def test_get_ids(self, favorites, sample_drama):
        """测试获取所有收藏 ID"""
        favorites.add(sample_drama)
        
        ids = favorites.get_ids()
        
        assert sample_drama.book_id in ids
    
    def test_clear(self, favorites, sample_drama):
        """测试清空收藏"""
        favorites.add(sample_drama)
        favorites.clear()
        
        assert favorites.count() == 0
    
    def test_persistence(self, favorites_file, sample_drama):
        """测试持久化"""
        # 添加收藏
        favorites1 = FavoritesManager(str(favorites_file))
        favorites1.add(sample_drama)
        
        # 重新加载
        favorites2 = FavoritesManager(str(favorites_file))
        
        assert favorites2.is_favorite(sample_drama.book_id)
    
    def test_load_invalid_json(self, favorites_file):
        """测试加载无效 JSON"""
        favorites_file.parent.mkdir(parents=True, exist_ok=True)
        favorites_file.write_text("invalid json", encoding="utf-8")
        
        favorites = FavoritesManager(str(favorites_file))
        assert favorites.count() == 0


class TestHistoryManager:
    """HistoryManager 测试"""
    
    @pytest.fixture
    def history_file(self, tmp_path):
        """创建临时历史文件路径"""
        return tmp_path / "data" / "history.json"
    
    @pytest.fixture
    def history(self, history_file):
        """创建历史管理器"""
        return HistoryManager(str(history_file), max_items=10)
    
    @pytest.fixture
    def sample_drama(self):
        """示例短剧"""
        return DramaInfo(
            book_id="test_001",
            title="测试短剧",
            cover="https://example.com/cover.jpg",
            episode_cnt=20
        )
    
    def test_add_history(self, history, sample_drama):
        """测试添加历史"""
        history.add(sample_drama, episode_number=1, position_ms=5000)
        
        assert history.count() == 1
        item = history.get(sample_drama.book_id)
        assert item is not None
        assert item.episode_number == 1
        assert item.position_ms == 5000
    
    def test_add_updates_existing(self, history, sample_drama):
        """测试添加更新已存在的记录"""
        history.add(sample_drama, episode_number=1, position_ms=5000)
        history.add(sample_drama, episode_number=2, position_ms=10000)
        
        assert history.count() == 1
        item = history.get(sample_drama.book_id)
        assert item.episode_number == 2
        assert item.position_ms == 10000
    
    def test_add_moves_to_front(self, history):
        """测试添加将记录移到最前"""
        drama1 = DramaInfo(book_id="1", title="Drama 1", cover="url")
        drama2 = DramaInfo(book_id="2", title="Drama 2", cover="url")
        
        history.add(drama1, 1)
        history.add(drama2, 1)
        history.add(drama1, 2)  # 更新 drama1
        
        all_history = history.get_all()
        assert all_history[0].drama.book_id == "1"  # drama1 在最前
    
    def test_max_items_limit(self, history):
        """测试最大数量限制"""
        for i in range(15):
            drama = DramaInfo(book_id=str(i), title=f"Drama {i}", cover="url")
            history.add(drama, 1)
        
        assert history.count() == 10  # max_items=10
    
    def test_get_position(self, history, sample_drama):
        """测试获取播放位置"""
        history.add(sample_drama, episode_number=1, position_ms=5000)
        
        position = history.get_position(sample_drama.book_id, 1)
        assert position == 5000
    
    def test_get_position_nonexistent(self, history):
        """测试获取不存在的播放位置"""
        position = history.get_position("nonexistent", 1)
        assert position == 0
    
    def test_update_position(self, history, sample_drama):
        """测试更新播放位置"""
        history.add(sample_drama, episode_number=1, position_ms=5000)
        result = history.update_position(sample_drama.book_id, 10000)
        
        assert result is True
        item = history.get(sample_drama.book_id)
        assert item.position_ms == 10000
    
    def test_update_position_nonexistent(self, history):
        """测试更新不存在的记录"""
        result = history.update_position("nonexistent", 5000)
        assert result is False
    
    def test_get(self, history, sample_drama):
        """测试获取历史记录"""
        history.add(sample_drama, 1, 5000)
        
        item = history.get(sample_drama.book_id)
        
        assert item is not None
        assert item.drama.book_id == sample_drama.book_id
    
    def test_get_nonexistent(self, history):
        """测试获取不存在的记录"""
        item = history.get("nonexistent")
        assert item is None
    
    def test_get_all(self, history, sample_drama):
        """测试获取所有历史"""
        history.add(sample_drama, 1, 5000)
        
        all_history = history.get_all()
        
        assert len(all_history) == 1
        assert isinstance(all_history[0], HistoryItem)
    
    def test_remove(self, history, sample_drama):
        """测试移除历史"""
        history.add(sample_drama, 1)
        result = history.remove(sample_drama.book_id)
        
        assert result is True
        assert history.get(sample_drama.book_id) is None
    
    def test_remove_nonexistent(self, history):
        """测试移除不存在的记录"""
        result = history.remove("nonexistent")
        assert result is False
    
    def test_clear(self, history, sample_drama):
        """测试清空历史"""
        history.add(sample_drama, 1)
        history.clear()
        
        assert history.count() == 0
    
    def test_persistence(self, history_file, sample_drama):
        """测试持久化"""
        # 添加历史
        history1 = HistoryManager(str(history_file))
        history1.add(sample_drama, 1, 5000)
        
        # 重新加载
        history2 = HistoryManager(str(history_file))
        
        item = history2.get(sample_drama.book_id)
        assert item is not None
        assert item.position_ms == 5000
    
    def test_load_invalid_json(self, history_file):
        """测试加载无效 JSON"""
        history_file.parent.mkdir(parents=True, exist_ok=True)
        history_file.write_text("invalid json", encoding="utf-8")
        
        history = HistoryManager(str(history_file))
        assert history.count() == 0

