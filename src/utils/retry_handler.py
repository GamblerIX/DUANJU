"""网络请求重试处理器

提供自动重试机制，支持指数退避策略。
"""
import asyncio
from typing import TypeVar, Callable, Awaitable, Optional
from functools import wraps

from .log_manager import get_logger

logger = get_logger()

T = TypeVar('T')


class RetryConfig:
    """重试配置"""
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        retryable_exceptions: tuple = (Exception,)
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retryable_exceptions = retryable_exceptions


DEFAULT_RETRY_CONFIG = RetryConfig()


async def retry_async(
    func: Callable[..., Awaitable[T]],
    *args,
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
    **kwargs
) -> T:
    """异步函数重试包装器
    
    Args:
        func: 要执行的异步函数
        config: 重试配置
        on_retry: 重试时的回调函数
        
    Returns:
        函数执行结果
        
    Raises:
        最后一次重试的异常
    """
    config = config or DEFAULT_RETRY_CONFIG
    last_exception: Optional[Exception] = None
    
    for attempt in range(config.max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except config.retryable_exceptions as e:
            last_exception = e
            
            if attempt >= config.max_retries:
                logger.error(f"All {config.max_retries + 1} attempts failed: {e}")
                raise
            
            # 计算延迟（指数退避）
            delay = min(
                config.base_delay * (config.exponential_base ** attempt),
                config.max_delay
            )
            
            logger.warning(
                f"Attempt {attempt + 1} failed: {e}. "
                f"Retrying in {delay:.1f}s..."
            )
            
            if on_retry:
                on_retry(attempt + 1, e)
            
            await asyncio.sleep(delay)
    
    raise last_exception  # type: ignore


def with_retry(config: Optional[RetryConfig] = None):
    """重试装饰器
    
    Usage:
        @with_retry(RetryConfig(max_retries=3))
        async def fetch_data():
            ...
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await retry_async(func, *args, config=config, **kwargs)
        return wrapper
    return decorator


class CircuitBreaker:
    """熔断器
    
    当连续失败次数达到阈值时，暂时停止请求。
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._is_open = False
    
    def record_success(self) -> None:
        """记录成功"""
        self._failure_count = 0
        self._is_open = False
    
    def record_failure(self) -> None:
        """记录失败"""
        import time
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        if self._failure_count >= self.failure_threshold:
            self._is_open = True
            logger.warning(
                f"Circuit breaker opened after {self._failure_count} failures"
            )
    
    def can_execute(self) -> bool:
        """检查是否可以执行请求"""
        if not self._is_open:
            return True
        
        import time
        if self._last_failure_time:
            elapsed = time.time() - self._last_failure_time
            if elapsed >= self.recovery_timeout:
                logger.info("Circuit breaker entering half-open state")
                return True
        
        return False
    
    def reset(self) -> None:
        """重置熔断器"""
        self._failure_count = 0
        self._is_open = False
        self._last_failure_time = None
