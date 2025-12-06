from collections import deque
from typing import Optional, Deque, Callable, Dict
import time
from ..models import ErrorItem, ErrorType

IS_DEBUG = False


class ErrorQueue:
    DEFAULT_MAX_SIZE = 10
    
    def __init__(self, max_size: int = DEFAULT_MAX_SIZE):
        self._queue: Deque[ErrorItem] = deque(maxlen=max_size)
        self._max_size = max_size
    
    def push(self, error: ErrorItem) -> None:
        self._queue.append(error)
    
    def pop(self) -> Optional[ErrorItem]:
        if self._queue:
            return self._queue.popleft()
        return None
    
    def peek(self) -> Optional[ErrorItem]:
        if self._queue:
            return self._queue[0]
        return None
    
    def clear(self) -> None:
        self._queue.clear()
    
    def is_empty(self) -> bool:
        return len(self._queue) == 0
    
    def size(self) -> int:
        return len(self._queue)
    
    def is_full(self) -> bool:
        return len(self._queue) >= self._max_size
    
    def create_error(self, error_type: ErrorType, message: str, retryable: bool = False,
                     retry_callback: Optional[Callable[[], None]] = None) -> ErrorItem:
        error = ErrorItem(error_type=error_type, message=message, timestamp=time.time(),
                         retryable=retryable, retry_callback=retry_callback)
        self.push(error)
        return error
    
    def create_network_error(self, message: str, 
                            retry_callback: Optional[Callable[[], None]] = None) -> ErrorItem:
        return self.create_error(ErrorType.NETWORK_ERROR, message, retryable=True, 
                                retry_callback=retry_callback)
    
    def create_timeout_error(self, message: str = "请求超时",
                            retry_callback: Optional[Callable[[], None]] = None) -> ErrorItem:
        return self.create_error(ErrorType.TIMEOUT_ERROR, message, retryable=True,
                                retry_callback=retry_callback)
    
    def create_api_error(self, message: str) -> ErrorItem:
        return self.create_error(ErrorType.API_ERROR, message, retryable=False)
    
    def create_parse_error(self, message: str) -> ErrorItem:
        return self.create_error(ErrorType.PARSE_ERROR, message, retryable=False)


USER_FRIENDLY_MESSAGES: Dict[ErrorType, str] = {
    ErrorType.NETWORK_ERROR: "网络连接失败，请检查网络设置",
    ErrorType.TIMEOUT_ERROR: "请求超时，请稍后重试",
    ErrorType.PARSE_ERROR: "数据解析失败，请稍后重试",
    ErrorType.API_ERROR: "服务器错误，请稍后重试",
    ErrorType.VIDEO_ERROR: "视频播放失败，请尝试其他清晰度",
    ErrorType.CONFIG_ERROR: "配置错误，请检查设置",
}


def get_user_friendly_message(error_type: ErrorType, original_message: str = "") -> str:
    return USER_FRIENDLY_MESSAGES.get(error_type, "操作失败，请稍后重试")


def format_exception_for_display(e: Exception) -> str:
    return str(e) if str(e) else "操作失败"
