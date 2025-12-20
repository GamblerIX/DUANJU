"""异步图片加载器实现"""
import hashlib
from pathlib import Path
from typing import Optional, Dict, Callable
from PySide6.QtCore import QObject, Signal, QUrl
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply


class ImageLoader(QObject):
    """异步图片加载器 - 支持内存缓存和磁盘缓存"""
    
    image_loaded = Signal(str, QPixmap)
    image_failed = Signal(str, str)
    
    CACHE_DIR = "cache/images"
    MAX_CACHE_SIZE = 100 * 1024 * 1024
    MEMORY_CACHE_SIZE = 50
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._memory_cache: Dict[str, QPixmap] = {}
        self._cache_order: list = []
        self._cache_dir = Path(self.CACHE_DIR)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._loading: set = set()
        self._pending_callbacks: Dict[str, list] = {}
        
        self._network_manager = QNetworkAccessManager(self)
        self._network_manager.finished.connect(self._on_network_finished)
    
    def load(self, url: str, callback: Optional[Callable[[QPixmap], None]] = None) -> Optional[QPixmap]:
        """加载图片"""
        if not url:
            return None
        
        if url in self._memory_cache:
            self._update_lru(url)
            pixmap = self._memory_cache[url]
            if callback:
                callback(pixmap)
            return pixmap
        
        cache_path = self._get_cache_path(url)
        if cache_path.exists():
            pixmap = QPixmap(str(cache_path))
            if not pixmap.isNull():
                self._add_to_memory_cache(url, pixmap)
                if callback:
                    callback(pixmap)
                return pixmap
        
        if url not in self._loading:
            self._loading.add(url)
            self._pending_callbacks[url] = []
            if callback:
                self._pending_callbacks[url].append(callback)
            
            request = QNetworkRequest(QUrl(url))
            request.setRawHeader(b"User-Agent", b"Mozilla/5.0")
            reply = self._network_manager.get(request)
            reply.setProperty("url", url)
        elif callback:
            if url in self._pending_callbacks:
                self._pending_callbacks[url].append(callback)
        
        return None
    
    def get_cached(self, url: str) -> Optional[QPixmap]:
        """获取缓存的图片"""
        if url in self._memory_cache:
            return self._memory_cache[url]
        cache_path = self._get_cache_path(url)
        if cache_path.exists():
            pixmap = QPixmap(str(cache_path))
            if not pixmap.isNull():
                self._add_to_memory_cache(url, pixmap)
                return pixmap
        return None
    
    def _on_network_finished(self, reply: QNetworkReply) -> None:
        """处理网络请求完成"""
        url = reply.property("url")
        
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll()
            image = QImage()
            image.loadFromData(data)
            pixmap = QPixmap.fromImage(image)
            
            if not pixmap.isNull():
                cache_path = self._get_cache_path(url)
                pixmap.save(str(cache_path))
                self._add_to_memory_cache(url, pixmap)
                self.image_loaded.emit(url, pixmap)
                
                for callback in self._pending_callbacks.get(url, []):
                    callback(pixmap)
            else:
                self.image_failed.emit(url, "Invalid image data")
        else:
            self.image_failed.emit(url, reply.errorString())
        
        self._loading.discard(url)
        self._pending_callbacks.pop(url, None)
        reply.deleteLater()
    
    def _get_cache_path(self, url: str) -> Path:
        """获取缓存文件路径"""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        ext = url.split('.')[-1].split('?')[0]
        if ext not in ('jpg', 'jpeg', 'png', 'gif', 'webp'):
            ext = 'jpg'
        return self._cache_dir / f"{url_hash}.{ext}"
    
    def _add_to_memory_cache(self, url: str, pixmap: QPixmap) -> None:
        """添加到内存缓存"""
        if url in self._memory_cache:
            self._update_lru(url)
            return
        
        while len(self._memory_cache) >= self.MEMORY_CACHE_SIZE:
            if self._cache_order:
                old_url = self._cache_order.pop(0)
                self._memory_cache.pop(old_url, None)
        
        self._memory_cache[url] = pixmap
        self._cache_order.append(url)
    
    def _update_lru(self, url: str) -> None:
        """更新 LRU 顺序"""
        if url in self._cache_order:
            self._cache_order.remove(url)
            self._cache_order.append(url)
    
    def clear_memory_cache(self) -> None:
        """清除内存缓存"""
        self._memory_cache.clear()
        self._cache_order.clear()
    
    def clear_disk_cache(self) -> None:
        """清除磁盘缓存"""
        for file in self._cache_dir.glob("*"):
            try:
                file.unlink()
            except OSError:
                pass


image_loader = ImageLoader()
