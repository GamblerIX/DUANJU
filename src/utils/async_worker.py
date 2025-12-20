"""异步工作线程模块 - 统一的 AsyncWorker 实现

This module provides a unified async worker implementation for running
asyncio coroutines in separate threads with Qt signal integration.
"""
from typing import Callable, Any, Optional
from PySide6.QtCore import QThread, Signal, QObject
import asyncio

from .log_manager import get_logger

logger = get_logger()


class AsyncWorker(QThread):
    """异步工作线程，用于在独立线程中运行 asyncio 协程
    
    Signals:
        finished_signal: 协程执行成功时发出，携带结果对象
        error_signal: 协程执行失败时发出，携带异常对象
    """
    
    finished_signal = Signal(object)
    error_signal = Signal(object)
    
    def __init__(
        self, 
        coro_func: Callable[..., Any], 
        *args, 
        parent: Optional[QObject] = None, 
        service_name: str = "AsyncWorker",
        **kwargs
    ):
        """初始化异步工作线程
        
        Args:
            coro_func: 协程函数
            *args: 传递给协程函数的位置参数
            parent: 父 QObject
            service_name: 服务名称，用于日志记录
            **kwargs: 传递给协程函数的关键字参数
        """
        super().__init__(parent)
        self._coro_func = coro_func
        self._args = args
        self._kwargs = kwargs
        self._service_name = service_name
    
    def run(self) -> None:
        """在新线程中运行协程"""
        loop: Optional[asyncio.AbstractEventLoop] = None
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            coro = self._coro_func(*self._args, **self._kwargs)
            result = loop.run_until_complete(coro)
            self.finished_signal.emit(result)
        except Exception as e:
            logger.log_service_error(self._service_name, "AsyncWorker", e)
            self.error_signal.emit(e)
        finally:
            if loop is not None:
                self._cleanup_loop(loop)
    
    def _cleanup_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """清理事件循环资源"""
        try:
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            
            if pending:
                loop.run_until_complete(
                    asyncio.gather(*pending, return_exceptions=True)
                )
            
            loop.run_until_complete(loop.shutdown_asyncgens())
        except Exception as e:
            logger.warning(f"Error during event loop cleanup: {e}")
        finally:
            loop.close()
            asyncio.set_event_loop(None)
