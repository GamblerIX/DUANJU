"""错误处理工具 - Debug Version

This module provides error handling utilities including error queue management
and user-friendly error message generation.
"""
from collections import deque
from typing import Optional, Deque, Callable, Dict
import time

from ..core.models import ErrorItem, ErrorType


# Debug版本显示详细错误信息
IS_DEBUG = True


class ErrorQueue:
    """错误队列管理器"""
    
    DEFAULT_MAX_SIZE = 10
    
    def __init__(self, max_size: int = DEFAULT_MAX_SIZE):
        self._queue: Deque[ErrorItem] = deque(maxlen=max_size)
        self._max_size = max_size
    
    def push(self, error: ErrorItem) -> None:
        """添加错误到队列"""
        self._queue.append(error)
    
    def pop(self) -> Optional[ErrorItem]:
        """获取并移除队首错误"""
        if self._queue:
            return self._queue.popleft()
        return None
    
    def peek(self) -> Optional[ErrorItem]:
        """查看队首错误但不移除"""
        if self._queue:
            return self._queue[0]
        return None
    
    def clear(self) -> None:
        """清空错误队列"""
        self._queue.clear()
    
    def is_empty(self) -> bool:
        return len(self._queue) == 0
    
    def size(self) -> int:
        return len(self._queue)
    
    def is_full(self) -> bool:
        return len(self._queue) >= self._max_size
    
    def create_error(
        self,
        error_type: ErrorType,
        message: str,
        retryable: bool = False,
        retry_callback: Optional[Callable[[], None]] = None
    ) -> ErrorItem:
        """创建并添加错误项"""
        error = ErrorItem(
            error_type=error_type,
            message=message,
            timestamp=time.time(),
            retryable=retryable,
            retry_callback=retry_callback
        )
        self.push(error)
        return error
    
    def create_network_error(
        self, 
        message: str,
        retry_callback: Optional[Callable[[], None]] = None
    ) -> ErrorItem:
        return self.create_error(
            ErrorType.NETWORK_ERROR,
            message,
            retryable=True,
            retry_callback=retry_callback
        )
    
    def create_timeout_error(
        self,
        message: str = "请求超时",
        retry_callback: Optional[Callable[[], None]] = None
    ) -> ErrorItem:
        return self.create_error(
            ErrorType.TIMEOUT_ERROR,
            message,
            retryable=True,
            retry_callback=retry_callback
        )
    
    def create_api_error(self, message: str) -> ErrorItem:
        return self.create_error(ErrorType.API_ERROR, message, retryable=False)
    
    def create_parse_error(self, message: str) -> ErrorItem:
        return self.create_error(ErrorType.PARSE_ERROR, message, retryable=False)


# 用户友好的错误消息映射
USER_FRIENDLY_MESSAGES: Dict[ErrorType, str] = {
    ErrorType.NETWORK_ERROR: "网络连接失败，请检查网络设置",
    ErrorType.TIMEOUT_ERROR: "请求超时，请稍后重试",
    ErrorType.PARSE_ERROR: "数据解析失败，请稍后重试",
    ErrorType.API_ERROR: "服务器错误，请稍后重试",
    ErrorType.VIDEO_ERROR: "视频播放失败，请尝试其他清晰度",
    ErrorType.CONFIG_ERROR: "配置错误，请检查设置",
}


def get_user_friendly_message(error_type: ErrorType, original_message: str = "") -> str:
    """获取用户友好的错误消息
    
    Debug版本返回详细信息，Release版本返回简化消息
    """
    if IS_DEBUG:
        # Debug版本：显示详细错误信息
        base_msg = USER_FRIENDLY_MESSAGES.get(error_type, "未知错误")
        if original_message:
            return f"{base_msg}\n详情: {original_message}"
        return base_msg
    else:
        # Release版本：只显示用户友好消息
        return USER_FRIENDLY_MESSAGES.get(error_type, "操作失败，请稍后重试")


def format_exception_for_display(e: Exception) -> str:
    """格式化异常用于显示
    
    Debug版本显示完整异常信息，Release版本隐藏技术细节
    """
    if IS_DEBUG:
        return f"{type(e).__name__}: {str(e)}"
    else:
        # Release版本不显示异常类名
        return str(e) if str(e) else "操作失败"
