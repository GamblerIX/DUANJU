from typing import Callable, Any, Optional
from PyQt6.QtCore import QThread, pyqtSignal, QObject
import asyncio


class AsyncWorker(QThread):
    finished_signal = pyqtSignal(object)
    error_signal = pyqtSignal(object)
    
    def __init__(self, coro_func: Callable[..., Any], *args, 
                 parent: Optional[QObject] = None, service_name: str = "AsyncWorker", **kwargs):
        super().__init__(parent)
        self._coro_func = coro_func
        self._args = args
        self._kwargs = kwargs
        self._service_name = service_name
    
    def run(self) -> None:
        loop: Optional[asyncio.AbstractEventLoop] = None
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            coro = self._coro_func(*self._args, **self._kwargs)
            result = loop.run_until_complete(coro)
            self.finished_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(e)
        finally:
            if loop is not None:
                self._cleanup_loop(loop)
    
    def _cleanup_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        try:
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.run_until_complete(loop.shutdown_asyncgens())
        except Exception:
            pass
        finally:
            loop.close()
            asyncio.set_event_loop(None)
