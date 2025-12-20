"""网络状态监控实现"""
from typing import Optional, Callable
from PySide6.QtCore import QObject, Signal, QTimer
import aiohttp
import asyncio


class NetworkMonitor(QObject):
    """
    网络状态监控器
    
    监控网络连接状态，提供断网提示和自动重试
    """
    
    # 信号
    connection_lost = Signal()
    connection_restored = Signal()
    slow_network = Signal()
    
    CHECK_INTERVAL = 30000  # 30秒检查一次
    SLOW_THRESHOLD = 3000   # 3秒响应视为慢网络
    RETRY_COUNT = 3
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._is_connected = True
        self._consecutive_failures = 0
        self._last_retry_callback: Optional[Callable] = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check_connection)
    
    def start(self) -> None:
        """开始监控"""
        self._timer.start(self.CHECK_INTERVAL)
        asyncio.create_task(self._do_check())
    
    def stop(self) -> None:
        """停止监控"""
        self._timer.stop()
    
    def _check_connection(self) -> None:
        """定时检查连接"""
        asyncio.create_task(self._do_check())
    
    async def _do_check(self) -> None:
        """执行连接检查"""
        try:
            import time
            start = time.time()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://www.baidu.com",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    elapsed = (time.time() - start) * 1000
                    
                    if response.status == 200:
                        if not self._is_connected:
                            self._is_connected = True
                            self._consecutive_failures = 0
                            self.connection_restored.emit()
                            # 自动重试上次失败的请求
                            if self._last_retry_callback:
                                self._last_retry_callback()
                                self._last_retry_callback = None
                        
                        if elapsed > self.SLOW_THRESHOLD:
                            self.slow_network.emit()
        except Exception:
            self._on_connection_failed()
    
    def _on_connection_failed(self) -> None:
        """处理连接失败"""
        self._consecutive_failures += 1
        
        if self._is_connected:
            self._is_connected = False
            self.connection_lost.emit()
    
    def report_request_failure(
        self, 
        retry_callback: Optional[Callable] = None
    ) -> None:
        """
        报告请求失败
        
        Args:
            retry_callback: 重试回调函数
        """
        self._consecutive_failures += 1
        self._last_retry_callback = retry_callback
        
        if self._consecutive_failures >= self.RETRY_COUNT:
            # 建议检查网络
            pass
    
    def report_request_success(self) -> None:
        """报告请求成功"""
        self._consecutive_failures = 0
        if not self._is_connected:
            self._is_connected = True
            self.connection_restored.emit()
    
    def report_slow_response(self, elapsed_ms: float) -> None:
        """
        报告慢响应
        
        Args:
            elapsed_ms: 响应时间（毫秒）
        """
        if elapsed_ms > self.SLOW_THRESHOLD:
            self.slow_network.emit()
    
    @property
    def is_connected(self) -> bool:
        """获取连接状态"""
        return self._is_connected
    
    @property
    def consecutive_failures(self) -> int:
        """获取连续失败次数"""
        return self._consecutive_failures
