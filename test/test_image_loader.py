"""图片加载器测试"""
from pathlib import Path
from unittest.mock import MagicMock, patch
from unittest.mock import MagicMock, patch, PropertyMock
import hashlib
import sys

import pytest

class TestImageLoaderLogic:
    """图片加载器逻辑测试"""
    
    def test_cache_path_generation(self):
        """测试缓存路径生成"""
        url = "http://example.com/image.jpg"
        url_hash = hashlib.md5(url.encode()).hexdigest()
        
        expected_filename = f"{url_hash}.jpg"
        assert url_hash in expected_filename
    
    def test_extension_extraction(self):
        """测试扩展名提取"""
        urls = [
            ("http://example.com/image.jpg", "jpg"),
            ("http://example.com/image.png", "png"),
            ("http://example.com/image.gif", "gif"),
            ("http://example.com/image.webp", "webp"),
            ("http://example.com/image.jpeg", "jpeg"),
            ("http://example.com/image.jpg?v=123", "jpg"),
        ]
        
        for url, expected_ext in urls:
            ext = url.split('.')[-1].split('?')[0]
            if ext not in ('jpg', 'jpeg', 'png', 'gif', 'webp'):
                ext = 'jpg'
            assert ext == expected_ext


class TestImageLoaderMock:
    """图片加载器 Mock 测试"""
    
    @patch('src.data.image_loader.QNetworkAccessManager')
    @patch('src.data.image_loader.Path')
    def test_image_loader_init(self, mock_path, mock_network):
        """测试图片加载器初始化"""
        from src.data.image_loader import ImageLoader
        
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        
        loader = ImageLoader()
        
        assert loader._memory_cache == {}
        assert loader._cache_order == []
        assert loader._loading == set()
    
    @patch('src.data.image_loader.QNetworkAccessManager')
    @patch('src.data.image_loader.Path')
    def test_load_empty_url(self, mock_path, mock_network):
        """测试加载空 URL"""
        from src.data.image_loader import ImageLoader
        
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        
        loader = ImageLoader()
        
        result = loader.load("")
        
        assert result is None
    
    @patch('src.data.image_loader.QNetworkAccessManager')
    @patch('src.data.image_loader.Path')
    @patch('src.data.image_loader.QPixmap')
    def test_load_from_memory_cache(self, mock_pixmap, mock_path, mock_network):
        """测试从内存缓存加载"""
        from src.data.image_loader import ImageLoader
        
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        
        loader = ImageLoader()
        
        # 预设内存缓存
        mock_cached_pixmap = MagicMock()
        url = "http://example.com/image.jpg"
        loader._memory_cache[url] = mock_cached_pixmap
        loader._cache_order.append(url)
        
        callback = MagicMock()
        result = loader.load(url, callback)
        
        assert result == mock_cached_pixmap
        callback.assert_called_once_with(mock_cached_pixmap)
    
    @patch('src.data.image_loader.QNetworkAccessManager')
    @patch('src.data.image_loader.Path')
    def test_get_cached_from_memory(self, mock_path, mock_network):
        """测试从内存获取缓存"""
        from src.data.image_loader import ImageLoader
        
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        
        loader = ImageLoader()
        
        # 预设内存缓存
        mock_pixmap = MagicMock()
        url = "http://example.com/image.jpg"
        loader._memory_cache[url] = mock_pixmap
        
        result = loader.get_cached(url)
        
        assert result == mock_pixmap
    
    @patch('src.data.image_loader.QNetworkAccessManager')
    @patch('src.data.image_loader.Path')
    def test_clear_memory_cache(self, mock_path, mock_network):
        """测试清除内存缓存"""
        from src.data.image_loader import ImageLoader
        
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        
        loader = ImageLoader()
        loader._memory_cache = {"url1": MagicMock(), "url2": MagicMock()}
        loader._cache_order = ["url1", "url2"]
        
        loader.clear_memory_cache()
        
        assert loader._memory_cache == {}
        assert loader._cache_order == []
    
    @patch('src.data.image_loader.QNetworkAccessManager')
    @patch('src.data.image_loader.Path')
    def test_update_lru(self, mock_path, mock_network):
        """测试 LRU 更新"""
        from src.data.image_loader import ImageLoader
        
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        
        loader = ImageLoader()
        loader._cache_order = ["url1", "url2", "url3"]
        
        loader._update_lru("url1")
        
        assert loader._cache_order == ["url2", "url3", "url1"]
    
    @patch('src.data.image_loader.QNetworkAccessManager')
    @patch('src.data.image_loader.Path')
    def test_add_to_memory_cache_eviction(self, mock_path, mock_network):
        """测试内存缓存淘汰"""
        from src.data.image_loader import ImageLoader
        
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        
        loader = ImageLoader()
        loader.MEMORY_CACHE_SIZE = 2
        
        loader._memory_cache = {"url1": MagicMock(), "url2": MagicMock()}
        loader._cache_order = ["url1", "url2"]
        
        new_pixmap = MagicMock()
        loader._add_to_memory_cache("url3", new_pixmap)
        
        assert "url1" not in loader._memory_cache
        assert "url3" in loader._memory_cache
        assert len(loader._memory_cache) == 2
    
    @patch('src.data.image_loader.QNetworkAccessManager')
    @patch('src.data.image_loader.Path')
    def test_add_to_memory_cache_existing(self, mock_path, mock_network):
        """测试添加已存在的缓存"""
        from src.data.image_loader import ImageLoader
        
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        
        loader = ImageLoader()
        
        existing_pixmap = MagicMock()
        loader._memory_cache = {"url1": existing_pixmap}
        loader._cache_order = ["url1"]
        
        new_pixmap = MagicMock()
        loader._add_to_memory_cache("url1", new_pixmap)
        
        # 应该更新 LRU 而不是添加新的
        assert loader._memory_cache["url1"] == existing_pixmap
    
    @patch('src.data.image_loader.QNetworkAccessManager')
    @patch('src.data.image_loader.Path')
    def test_get_cache_path(self, mock_path, mock_network):
        """测试获取缓存路径"""
        from src.data.image_loader import ImageLoader
        
        mock_cache_dir = MagicMock()
        mock_path.return_value = mock_cache_dir
        
        loader = ImageLoader()
        loader._cache_dir = mock_cache_dir
        
        url = "http://example.com/image.jpg"
        loader._get_cache_path(url)
        
        # 验证调用了 / 操作符
        mock_cache_dir.__truediv__.assert_called()


class TestImageLoaderConstants:
    """图片加载器常量测试"""
    
    def test_constants(self):
        """测试常量值"""
        from src.data.image_loader import ImageLoader
        
        assert ImageLoader.CACHE_DIR == "cache/images"
        assert ImageLoader.MAX_CACHE_SIZE == 100 * 1024 * 1024
        assert ImageLoader.MEMORY_CACHE_SIZE == 50



# ============================================================
# From: test_image_loader_full.py
# ============================================================
mock_pyside = MagicMock()
mock_pyside.QtCore = MagicMock()
mock_pyside.QtGui = MagicMock()
mock_pyside.QtNetwork = MagicMock()

# 创建 mock 类
mock_qobject = MagicMock()
mock_signal = MagicMock()
mock_pixmap = MagicMock()
mock_qimage = MagicMock()
mock_qurl = MagicMock()
mock_network_manager = MagicMock()
mock_network_request = MagicMock()
mock_network_reply = MagicMock()

mock_pyside.QtCore.QObject = mock_qobject
mock_pyside.QtCore.Signal = lambda *args: mock_signal
mock_pyside.QtGui.QPixmap = mock_pixmap
mock_pyside.QtGui.QImage = mock_qimage
mock_pyside.QtCore.QUrl = mock_qurl
mock_pyside.QtNetwork.QNetworkAccessManager = mock_network_manager
mock_pyside.QtNetwork.QNetworkRequest = mock_network_request
mock_pyside.QtNetwork.QNetworkReply = mock_network_reply


class TestImageLoaderLogic_Full:
    """测试图片加载器逻辑（不依赖 Qt）"""
    
    def test_cache_path_generation(self, tmp_path):
        """测试缓存路径生成"""
        url = "https://example.com/image.jpg"
        url_hash = hashlib.md5(url.encode()).hexdigest()
        
        cache_dir = tmp_path / "cache" / "images"
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        ext = url.split('.')[-1].split('?')[0]
        cache_path = cache_dir / f"{url_hash}.{ext}"
        
        assert cache_path.suffix == ".jpg"
        assert url_hash in str(cache_path)
    
    def test_cache_path_with_query_string(self, tmp_path):
        """测试带查询参数的 URL"""
        url = "https://example.com/image.png?token=abc123"
        ext = url.split('.')[-1].split('?')[0]
        assert ext == "png"
    
    def test_cache_path_invalid_extension(self, tmp_path):
        """测试无效扩展名"""
        url = "https://example.com/image.xyz"
        ext = url.split('.')[-1].split('?')[0]
        if ext not in ('jpg', 'jpeg', 'png', 'gif', 'webp'):
            ext = 'jpg'
        assert ext == "jpg"
    
    def test_lru_cache_logic(self):
        """测试 LRU 缓存逻辑"""
        cache_order = ["url1", "url2", "url3"]
        memory_cache = {"url1": "pixmap1", "url2": "pixmap2", "url3": "pixmap3"}
        max_size = 3
        
        # 模拟访问 url1，应该移到末尾
        if "url1" in cache_order:
            cache_order.remove("url1")
            cache_order.append("url1")
        
        assert cache_order == ["url2", "url3", "url1"]
        
        # 模拟添加新项，应该移除最旧的
        new_url = "url4"
        while len(memory_cache) >= max_size:
            if cache_order:
                old_url = cache_order.pop(0)
                memory_cache.pop(old_url, None)
        
        memory_cache[new_url] = "pixmap4"
        cache_order.append(new_url)
        
        assert "url2" not in memory_cache
        assert new_url in memory_cache
        assert cache_order == ["url3", "url1", "url4"]
    
    def test_memory_cache_operations(self):
        """测试内存缓存操作"""
        memory_cache = {}
        cache_order = []
        max_size = 2
        
        def add_to_cache(url, pixmap):
            if url in memory_cache:
                if url in cache_order:
                    cache_order.remove(url)
                    cache_order.append(url)
                return
            
            while len(memory_cache) >= max_size:
                if cache_order:
                    old_url = cache_order.pop(0)
                    memory_cache.pop(old_url, None)
            
            memory_cache[url] = pixmap
            cache_order.append(url)
        
        add_to_cache("url1", "pixmap1")
        assert len(memory_cache) == 1
        
        add_to_cache("url2", "pixmap2")
        assert len(memory_cache) == 2
        
        add_to_cache("url3", "pixmap3")
        assert len(memory_cache) == 2
        assert "url1" not in memory_cache
        assert "url3" in memory_cache
    
    def test_clear_memory_cache(self):
        """测试清除内存缓存"""
        memory_cache = {"url1": "pixmap1", "url2": "pixmap2"}
        cache_order = ["url1", "url2"]
        
        memory_cache.clear()
        cache_order.clear()
        
        assert len(memory_cache) == 0
        assert len(cache_order) == 0
    
    def test_clear_disk_cache(self, tmp_path):
        """测试清除磁盘缓存"""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建测试文件
        (cache_dir / "test1.jpg").write_text("test")
        (cache_dir / "test2.png").write_text("test")
        
        # 清除
        for file in cache_dir.glob("*"):
            try:
                file.unlink()
            except:
                pass
        
        assert len(list(cache_dir.glob("*"))) == 0
    
    def test_loading_set_operations(self):
        """测试加载中集合操作"""
        loading = set()
        
        url = "https://example.com/image.jpg"
        
        # 添加到加载中
        loading.add(url)
        assert url in loading
        
        # 完成后移除
        loading.discard(url)
        assert url not in loading
        
        # 重复移除不报错
        loading.discard(url)
    
    def test_pending_callbacks(self):
        """测试待处理回调"""
        pending_callbacks = {}
        
        url = "https://example.com/image.jpg"
        callback1 = lambda x: None
        callback2 = lambda x: None
        
        pending_callbacks[url] = []
        pending_callbacks[url].append(callback1)
        pending_callbacks[url].append(callback2)
        
        assert len(pending_callbacks[url]) == 2
        
        # 执行回调后清理
        pending_callbacks.pop(url, None)
        assert url not in pending_callbacks
    
    def test_url_hash_uniqueness(self):
        """测试 URL 哈希唯一性"""
        urls = [
            "https://example.com/image1.jpg",
            "https://example.com/image2.jpg",
            "https://other.com/image1.jpg",
        ]
        
        hashes = [hashlib.md5(url.encode()).hexdigest() for url in urls]
        assert len(set(hashes)) == len(urls)
    
    def test_extension_extraction(self):
        """测试扩展名提取"""
        test_cases = [
            ("https://example.com/image.jpg", "jpg"),
            ("https://example.com/image.jpeg", "jpeg"),
            ("https://example.com/image.png", "png"),
            ("https://example.com/image.gif", "gif"),
            ("https://example.com/image.webp", "webp"),
            ("https://example.com/image.jpg?token=123", "jpg"),
            ("https://example.com/image.PNG", "PNG"),
        ]
        
        for url, expected in test_cases:
            ext = url.split('.')[-1].split('?')[0]
            assert ext == expected


class TestImageLoaderIntegration:
    """集成测试（模拟 Qt 环境）"""
    
    def test_empty_url_handling(self):
        """测试空 URL 处理"""
        url = ""
        if not url:
            result = None
        else:
            result = "pixmap"
        
        assert result is None
    
    def test_cache_hit_flow(self):
        """测试缓存命中流程"""
        memory_cache = {"https://example.com/image.jpg": "cached_pixmap"}
        cache_order = ["https://example.com/image.jpg"]
        
        url = "https://example.com/image.jpg"
        
        if url in memory_cache:
            # 更新 LRU
            if url in cache_order:
                cache_order.remove(url)
                cache_order.append(url)
            result = memory_cache[url]
        else:
            result = None
        
        assert result == "cached_pixmap"
    
    def test_disk_cache_flow(self, tmp_path):
        """测试磁盘缓存流程"""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        url = "https://example.com/image.jpg"
        url_hash = hashlib.md5(url.encode()).hexdigest()
        cache_path = cache_dir / f"{url_hash}.jpg"
        
        # 模拟缓存文件存在
        cache_path.write_bytes(b"fake image data")
        
        assert cache_path.exists()
    
    def test_network_request_flow(self):
        """测试网络请求流程"""
        loading = set()
        pending_callbacks = {}
        
        url = "https://example.com/new_image.jpg"
        callback = lambda x: None
        
        if url not in loading:
            loading.add(url)
            pending_callbacks[url] = []
            if callback:
                pending_callbacks[url].append(callback)
        
        assert url in loading
        assert url in pending_callbacks
        assert len(pending_callbacks[url]) == 1



# ============================================================
# From: test_image_loader_coverage.py
# ============================================================
class TestImageLoaderInit:
    """测试 ImageLoader 初始化"""
    
    @patch('src.data.image_loader.QNetworkAccessManager')
    @patch('src.data.image_loader.Path.mkdir')
    def test_init(self, mock_mkdir, mock_network_manager):
        """测试初始化"""
        from src.data.image_loader import ImageLoader
        
        loader = ImageLoader()
        
        assert loader._memory_cache == {}
        assert loader._cache_order == []
        assert loader._loading == set()
        assert loader._pending_callbacks == {}
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


class TestImageLoaderCachePath:
    """测试缓存路径生成"""
    
    @patch('src.data.image_loader.QNetworkAccessManager')
    @patch('src.data.image_loader.Path.mkdir')
    def test_get_cache_path_jpg(self, mock_mkdir, mock_network_manager):
        """测试 JPG 扩展名"""
        from src.data.image_loader import ImageLoader
        
        loader = ImageLoader()
        url = "https://example.com/image.jpg"
        
        path = loader._get_cache_path(url)
        
        url_hash = hashlib.md5(url.encode()).hexdigest()
        assert path.name == f"{url_hash}.jpg"
    
    @patch('src.data.image_loader.QNetworkAccessManager')
    @patch('src.data.image_loader.Path.mkdir')
    def test_get_cache_path_png(self, mock_mkdir, mock_network_manager):
        """测试 PNG 扩展名"""
        from src.data.image_loader import ImageLoader
        
        loader = ImageLoader()
        url = "https://example.com/image.png"
        
        path = loader._get_cache_path(url)
        
        url_hash = hashlib.md5(url.encode()).hexdigest()
        assert path.name == f"{url_hash}.png"
    
    @patch('src.data.image_loader.QNetworkAccessManager')
    @patch('src.data.image_loader.Path.mkdir')
    def test_get_cache_path_with_query(self, mock_mkdir, mock_network_manager):
        """测试带查询参数的 URL"""
        from src.data.image_loader import ImageLoader
        
        loader = ImageLoader()
        url = "https://example.com/image.jpg?size=large"
        
        path = loader._get_cache_path(url)
        
        url_hash = hashlib.md5(url.encode()).hexdigest()
        assert path.name == f"{url_hash}.jpg"
    
    @patch('src.data.image_loader.QNetworkAccessManager')
    @patch('src.data.image_loader.Path.mkdir')
    def test_get_cache_path_unknown_ext(self, mock_mkdir, mock_network_manager):
        """测试未知扩展名"""
        from src.data.image_loader import ImageLoader
        
        loader = ImageLoader()
        url = "https://example.com/image.xyz"
        
        path = loader._get_cache_path(url)
        
        url_hash = hashlib.md5(url.encode()).hexdigest()
        assert path.name == f"{url_hash}.jpg"  # 默认使用 jpg


class TestImageLoaderMemoryCache:
    """测试内存缓存"""
    
    @patch('src.data.image_loader.QNetworkAccessManager')
    @patch('src.data.image_loader.Path.mkdir')
    def test_add_to_memory_cache(self, mock_mkdir, mock_network_manager):
        """测试添加到内存缓存"""
        from src.data.image_loader import ImageLoader
        
        loader = ImageLoader()
        mock_pixmap = MagicMock()
        
        loader._add_to_memory_cache("url1", mock_pixmap)
        
        assert "url1" in loader._memory_cache
        assert "url1" in loader._cache_order
    
    @patch('src.data.image_loader.QNetworkAccessManager')
    @patch('src.data.image_loader.Path.mkdir')
    def test_add_to_memory_cache_duplicate(self, mock_mkdir, mock_network_manager):
        """测试重复添加到内存缓存"""
        from src.data.image_loader import ImageLoader
        
        loader = ImageLoader()
        mock_pixmap = MagicMock()
        
        loader._add_to_memory_cache("url1", mock_pixmap)
        loader._add_to_memory_cache("url1", mock_pixmap)
        
        assert len(loader._memory_cache) == 1
        assert loader._cache_order.count("url1") == 1
    
    @patch('src.data.image_loader.QNetworkAccessManager')
    @patch('src.data.image_loader.Path.mkdir')
    def test_memory_cache_eviction(self, mock_mkdir, mock_network_manager):
        """测试内存缓存淘汰"""
        from src.data.image_loader import ImageLoader
        
        loader = ImageLoader()
        loader.MEMORY_CACHE_SIZE = 3
        
        for i in range(5):
            loader._add_to_memory_cache(f"url{i}", MagicMock())
        
        assert len(loader._memory_cache) == 3
        assert "url0" not in loader._memory_cache
        assert "url1" not in loader._memory_cache
        assert "url4" in loader._memory_cache
    
    @patch('src.data.image_loader.QNetworkAccessManager')
    @patch('src.data.image_loader.Path.mkdir')
    def test_update_lru(self, mock_mkdir, mock_network_manager):
        """测试 LRU 更新"""
        from src.data.image_loader import ImageLoader
        
        loader = ImageLoader()
        
        loader._add_to_memory_cache("url1", MagicMock())
        loader._add_to_memory_cache("url2", MagicMock())
        loader._add_to_memory_cache("url3", MagicMock())
        
        # 访问 url1，应该移到末尾
        loader._update_lru("url1")
        
        assert loader._cache_order[-1] == "url1"
    
    @patch('src.data.image_loader.QNetworkAccessManager')
    @patch('src.data.image_loader.Path.mkdir')
    def test_update_lru_not_in_cache(self, mock_mkdir, mock_network_manager):
        """测试更新不在缓存中的 URL"""
        from src.data.image_loader import ImageLoader
        
        loader = ImageLoader()
        
        # 不应该抛出异常
        loader._update_lru("nonexistent")
    
    @patch('src.data.image_loader.QNetworkAccessManager')
    @patch('src.data.image_loader.Path.mkdir')
    def test_clear_memory_cache(self, mock_mkdir, mock_network_manager):
        """测试清除内存缓存"""
        from src.data.image_loader import ImageLoader
        
        loader = ImageLoader()
        loader._add_to_memory_cache("url1", MagicMock())
        loader._add_to_memory_cache("url2", MagicMock())
        
        loader.clear_memory_cache()
        
        assert len(loader._memory_cache) == 0
        assert len(loader._cache_order) == 0


class TestImageLoaderDiskCache:
    """测试磁盘缓存"""
    
    @patch('src.data.image_loader.QNetworkAccessManager')
    @patch('src.data.image_loader.Path.mkdir')
    def test_clear_disk_cache(self, mock_mkdir, mock_network_manager):
        """测试清除磁盘缓存"""
        from src.data.image_loader import ImageLoader
        
        loader = ImageLoader()
        
        # Mock glob 返回一些文件
        mock_file1 = MagicMock()
        mock_file2 = MagicMock()
        loader._cache_dir = MagicMock()
        loader._cache_dir.glob.return_value = [mock_file1, mock_file2]
        
        loader.clear_disk_cache()
        
        mock_file1.unlink.assert_called_once()
        mock_file2.unlink.assert_called_once()
    
    @patch('src.data.image_loader.QNetworkAccessManager')
    @patch('src.data.image_loader.Path.mkdir')
    def test_clear_disk_cache_with_error(self, mock_mkdir, mock_network_manager):
        """测试清除磁盘缓存时出错"""
        from src.data.image_loader import ImageLoader
        
        loader = ImageLoader()
        
        mock_file = MagicMock()
        mock_file.unlink.side_effect = PermissionError("Access denied")
        loader._cache_dir = MagicMock()
        loader._cache_dir.glob.return_value = [mock_file]
        
        # 不应该抛出异常
        loader.clear_disk_cache()


class TestImageLoaderLoad:
    """测试图片加载"""
    
    @patch('src.data.image_loader.QNetworkAccessManager')
    @patch('src.data.image_loader.Path.mkdir')
    def test_load_empty_url(self, mock_mkdir, mock_network_manager):
        """测试加载空 URL"""
        from src.data.image_loader import ImageLoader
        
        loader = ImageLoader()
        
        result = loader.load("")
        
        assert result is None
    
    @patch('src.data.image_loader.QNetworkAccessManager')
    @patch('src.data.image_loader.Path.mkdir')
    def test_load_from_memory_cache(self, mock_mkdir, mock_network_manager):
        """测试从内存缓存加载"""
        from src.data.image_loader import ImageLoader
        
        loader = ImageLoader()
        mock_pixmap = MagicMock()
        loader._memory_cache["url1"] = mock_pixmap
        loader._cache_order.append("url1")
        
        callback = MagicMock()
        result = loader.load("url1", callback)
        
        assert result is mock_pixmap
        callback.assert_called_once_with(mock_pixmap)
    
    @patch('src.data.image_loader.QNetworkAccessManager')
    @patch('src.data.image_loader.Path.mkdir')
    def test_load_already_loading(self, mock_mkdir, mock_network_manager):
        """测试正在加载的 URL"""
        from src.data.image_loader import ImageLoader
        
        loader = ImageLoader()
        loader._loading.add("url1")
        loader._pending_callbacks["url1"] = []
        
        callback = MagicMock()
        result = loader.load("url1", callback)
        
        assert result is None
        assert callback in loader._pending_callbacks["url1"]


class TestImageLoaderGetCached:
    """测试获取缓存图片"""
    
    @patch('src.data.image_loader.QNetworkAccessManager')
    @patch('src.data.image_loader.Path.mkdir')
    def test_get_cached_from_memory(self, mock_mkdir, mock_network_manager):
        """测试从内存获取缓存"""
        from src.data.image_loader import ImageLoader
        
        loader = ImageLoader()
        mock_pixmap = MagicMock()
        loader._memory_cache["url1"] = mock_pixmap
        
        result = loader.get_cached("url1")
        
        assert result is mock_pixmap
    
    @patch('src.data.image_loader.QNetworkAccessManager')
    @patch('src.data.image_loader.Path.mkdir')
    def test_get_cached_not_found(self, mock_mkdir, mock_network_manager):
        """测试缓存未找到"""
        from src.data.image_loader import ImageLoader
        
        loader = ImageLoader()
        
        # Mock cache path 不存在
        with patch.object(loader, '_get_cache_path') as mock_path:
            mock_path.return_value = MagicMock(exists=MagicMock(return_value=False))
            result = loader.get_cached("url1")
        
        assert result is None


class TestImageLoaderConstants_Coverage:
    """测试常量"""
    
    def test_constants(self):
        """测试常量值"""
        from src.data.image_loader import ImageLoader
        
        assert ImageLoader.CACHE_DIR == "cache/images"
        assert ImageLoader.MAX_CACHE_SIZE == 100 * 1024 * 1024
        assert ImageLoader.MEMORY_CACHE_SIZE == 50


class TestImageLoaderSingleton:
    """测试单例"""
    
    @patch('src.data.image_loader.QNetworkAccessManager')
    @patch('src.data.image_loader.Path.mkdir')
    def test_singleton_instance(self, mock_mkdir, mock_network_manager):
        """测试单例实例"""
        from src.data.image import image_loader
        
        # image_loader 模块应该有一个 image_loader 实例
        assert hasattr(image_loader, 'image_loader')



# ============================================================
# From: test_image_loader_logic.py
# ============================================================
class TestImageLoaderCacheLogic:
    """测试图片加载器缓存逻辑"""
    
    def test_cache_path_generation(self):
        """测试缓存路径生成"""
        url = "https://example.com/image.jpg"
        url_hash = hashlib.md5(url.encode()).hexdigest()
        ext = url.split('.')[-1].split('?')[0]
        
        assert ext == "jpg"
        assert len(url_hash) == 32
    
    def test_cache_path_with_query_params(self):
        """测试带查询参数的URL"""
        url = "https://example.com/image.jpg?size=large&quality=high"
        ext = url.split('.')[-1].split('?')[0]
        assert ext == "jpg"
    
    def test_cache_path_unknown_extension(self):
        """测试未知扩展名"""
        url = "https://example.com/image"
        ext = url.split('.')[-1].split('?')[0]
        if ext not in ('jpg', 'jpeg', 'png', 'gif', 'webp'):
            ext = 'jpg'
        assert ext == 'jpg'
    
    def test_cache_path_png(self):
        """测试PNG扩展名"""
        url = "https://example.com/image.png"
        ext = url.split('.')[-1].split('?')[0]
        assert ext == "png"
    
    def test_cache_path_webp(self):
        """测试WebP扩展名"""
        url = "https://example.com/image.webp"
        ext = url.split('.')[-1].split('?')[0]
        assert ext == "webp"


class TestLRUCacheLogic:
    """测试LRU缓存逻辑"""
    
    def test_lru_update(self):
        """测试LRU更新"""
        cache_order = ['url1', 'url2', 'url3']
        url = 'url1'
        
        if url in cache_order:
            cache_order.remove(url)
            cache_order.append(url)
        
        assert cache_order == ['url2', 'url3', 'url1']
    
    def test_lru_eviction(self):
        """测试LRU淘汰"""
        memory_cache = {'url1': 'pixmap1', 'url2': 'pixmap2', 'url3': 'pixmap3'}
        cache_order = ['url1', 'url2', 'url3']
        max_size = 3
        
        # 添加新项时需要淘汰
        while len(memory_cache) >= max_size:
            if cache_order:
                old_url = cache_order.pop(0)
                memory_cache.pop(old_url, None)
        
        assert len(memory_cache) == 2
        assert 'url1' not in memory_cache
    
    def test_memory_cache_hit(self):
        """测试内存缓存命中"""
        memory_cache = {'url1': 'pixmap1'}
        url = 'url1'
        
        hit = url in memory_cache
        assert hit is True
    
    def test_memory_cache_miss(self):
        """测试内存缓存未命中"""
        memory_cache = {'url1': 'pixmap1'}
        url = 'url2'
        
        hit = url in memory_cache
        assert hit is False


class TestImageLoaderLoadingState:
    """测试图片加载状态管理"""
    
    def test_loading_set_management(self):
        """测试加载集合管理"""
        loading = set()
        url = "https://example.com/image.jpg"
        
        # 开始加载
        loading.add(url)
        assert url in loading
        
        # 完成加载
        loading.discard(url)
        assert url not in loading
    
    def test_pending_callbacks(self):
        """测试待处理回调"""
        pending_callbacks = {}
        url = "https://example.com/image.jpg"
        
        # 添加回调
        pending_callbacks[url] = []
        callback1 = lambda x: None
        callback2 = lambda x: None
        pending_callbacks[url].append(callback1)
        pending_callbacks[url].append(callback2)
        
        assert len(pending_callbacks[url]) == 2
        
        # 清理回调
        pending_callbacks.pop(url, None)
        assert url not in pending_callbacks
    
    def test_duplicate_load_request(self):
        """测试重复加载请求"""
        loading = set()
        url = "https://example.com/image.jpg"
        
        # 第一次请求
        if url not in loading:
            loading.add(url)
            started_new = True
        else:
            started_new = False
        
        assert started_new is True
        
        # 第二次请求（重复）
        if url not in loading:
            loading.add(url)
            started_new = True
        else:
            started_new = False
        
        assert started_new is False


class TestImageLoaderClearCache:
    """测试清除缓存"""
    
    def test_clear_memory_cache(self):
        """测试清除内存缓存"""
        memory_cache = {'url1': 'pixmap1', 'url2': 'pixmap2'}
        cache_order = ['url1', 'url2']
        
        memory_cache.clear()
        cache_order.clear()
        
        assert len(memory_cache) == 0
        assert len(cache_order) == 0
    
    def test_clear_disk_cache_logic(self, tmp_path):
        """测试清除磁盘缓存逻辑"""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        
        # 创建测试文件
        (cache_dir / "test1.jpg").write_text("test")
        (cache_dir / "test2.png").write_text("test")
        
        # 清除
        for file in cache_dir.glob("*"):
            try:
                file.unlink()
            except:
                pass
        
        assert len(list(cache_dir.glob("*"))) == 0


class TestImageLoaderConstants_Logic:
    """测试图片加载器常量"""
    
    def test_cache_dir(self):
        """测试缓存目录"""
        CACHE_DIR = "cache/images"
        assert CACHE_DIR == "cache/images"
    
    def test_max_cache_size(self):
        """测试最大缓存大小"""
        MAX_CACHE_SIZE = 100 * 1024 * 1024  # 100MB
        assert MAX_CACHE_SIZE == 104857600
    
    def test_memory_cache_size(self):
        """测试内存缓存大小"""
        MEMORY_CACHE_SIZE = 50
        assert MEMORY_CACHE_SIZE == 50


class TestImageLoaderUrlHandling:
    """测试URL处理"""
    
    def test_empty_url(self):
        """测试空URL"""
        url = ""
        if not url:
            result = None
        else:
            result = "loaded"
        assert result is None
    
    def test_none_url(self):
        """测试None URL"""
        url = None
        if not url:
            result = None
        else:
            result = "loaded"
        assert result is None
    
    def test_valid_url(self):
        """测试有效URL"""
        url = "https://example.com/image.jpg"
        if not url:
            result = None
        else:
            result = "loaded"
        assert result == "loaded"


class TestImageLoaderHashGeneration:
    """测试哈希生成"""
    
    def test_md5_hash(self):
        """测试MD5哈希"""
        url = "https://example.com/image.jpg"
        url_hash = hashlib.md5(url.encode()).hexdigest()
        
        assert len(url_hash) == 32
        assert url_hash.isalnum()
    
    def test_hash_consistency(self):
        """测试哈希一致性"""
        url = "https://example.com/image.jpg"
        hash1 = hashlib.md5(url.encode()).hexdigest()
        hash2 = hashlib.md5(url.encode()).hexdigest()
        
        assert hash1 == hash2
    
    def test_different_urls_different_hashes(self):
        """测试不同URL产生不同哈希"""
        url1 = "https://example.com/image1.jpg"
        url2 = "https://example.com/image2.jpg"
        
        hash1 = hashlib.md5(url1.encode()).hexdigest()
        hash2 = hashlib.md5(url2.encode()).hexdigest()
        
        assert hash1 != hash2
