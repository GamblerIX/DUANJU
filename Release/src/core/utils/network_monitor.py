from typing import Optional, Callable
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
import aiohttp
import asyncio


class NetworkMonitor(QObject):
    connection_lost = pyqtSignal()
    connection_restored = pyqtSignal()
    slow_network = pyqtSignal()
    
    CHECK_INTERVAL = 30000
    SLOW_THRESHOLD = 3000
    RETRY_COUNT = 3
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._is_connected = True
        self._consecutive_failures = 0
        self._last_retry_callback: Optional[Callable] = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check_connection)
    
    def start(self) -> None:
        self._timer.start(self.CHECK_INTERVAL)
        asyncio.create_task(self._do_check())
    
    def stop(self) -> None:
        self._timer.stop()
    
    def _check_connection(self) -> None:
        asyncio.create_task(self._do_check())
    
    async def _do_check(self) -> None:
        try:
            import time
            start = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get("https://www.baidu.com",
                                      timeout=aiohttp.ClientTimeout(total=5)) as response:
                    elapsed = (time.time() - start) * 1000
                    if response.status == 200:
                        if not self._is_connected:
                            self._is_connected = True
                            self._consecutive_failures = 0
                            self.connection_restored.emit()
                            if self._last_retry_callback:
                                self._last_retry_callback()
                                self._last_retry_callback = None
                        if elapsed > self.SLOW_THRESHOLD:
                            self.slow_network.emit()
        except Exception:
            self._on_connection_failed()
    
    def _on_connection_failed(self) -> None:
        self._consecutive_failures += 1
        if self._is_connected:
            self._is_connected = False
            self.connection_lost.emit()
    
    def report_request_failure(self, retry_callback: Optional[Callable] = None) -> None:
        self._consecutive_failures += 1
        self._last_retry_callback = retry_callback
    
    def report_request_success(self) -> None:
        self._consecutive_failures = 0
        if not self._is_connected:
            self._is_connected = True
            self.connection_restored.emit()
    
    def report_slow_response(self, elapsed_ms: float) -> None:
        if elapsed_ms > self.SLOW_THRESHOLD:
            self.slow_network.emit()
    
    @property
    def is_connected(self) -> bool:
        return self._is_connected
    
    @property
    def consecutive_failures(self) -> int:
        return self._consecutive_failures
