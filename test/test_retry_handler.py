"""重试处理器测试

测试 src/core/utils/retry_handler.py 中的重试功能。
"""
import pytest
import asyncio
import time
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.retry_handler import (
    RetryConfig, retry_async, with_retry, CircuitBreaker,
    DEFAULT_RETRY_CONFIG
)


class TestRetryConfig:
    """RetryConfig 测试"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = RetryConfig()
        
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 30.0
        assert config.exponential_base == 2.0
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = RetryConfig(
            max_retries=5,
            base_delay=0.5,
            max_delay=10.0,
            exponential_base=3.0
        )
        
        assert config.max_retries == 5
        assert config.base_delay == 0.5
        assert config.max_delay == 10.0
        assert config.exponential_base == 3.0
    
    def test_retryable_exceptions(self):
        """测试可重试异常配置"""
        config = RetryConfig(
            retryable_exceptions=(ValueError, TypeError)
        )
        
        assert ValueError in config.retryable_exceptions
        assert TypeError in config.retryable_exceptions


class TestRetryAsync:
    """retry_async 测试"""
    
    @pytest.mark.asyncio
    async def test_success_first_try(self):
        """测试首次成功"""
        async def success_func():
            return "success"
        
        result = await retry_async(success_func)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_success_after_retry(self):
        """测试重试后成功"""
        call_count = 0
        
        async def fail_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("临时错误")
            return "success"
        
        config = RetryConfig(max_retries=3, base_delay=0.01)
        result = await retry_async(fail_then_success, config=config)
        
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_all_retries_fail(self):
        """测试所有重试都失败"""
        async def always_fail():
            raise ValueError("永久错误")
        
        config = RetryConfig(max_retries=2, base_delay=0.01)
        
        with pytest.raises(ValueError):
            await retry_async(always_fail, config=config)
    
    @pytest.mark.asyncio
    async def test_on_retry_callback(self):
        """测试重试回调"""
        retry_attempts = []
        
        async def fail_twice():
            if len(retry_attempts) < 2:
                raise ValueError("错误")
            return "success"
        
        def on_retry(attempt, error):
            retry_attempts.append(attempt)
        
        config = RetryConfig(max_retries=3, base_delay=0.01)
        await retry_async(fail_twice, config=config, on_retry=on_retry)
        
        assert len(retry_attempts) == 2
        assert retry_attempts == [1, 2]
    
    @pytest.mark.asyncio
    async def test_non_retryable_exception(self):
        """测试不可重试的异常"""
        call_count = 0
        
        async def raise_key_error():
            nonlocal call_count
            call_count += 1
            raise KeyError("不可重试")
        
        config = RetryConfig(
            max_retries=3,
            base_delay=0.01,
            retryable_exceptions=(ValueError,)  # 只重试 ValueError
        )
        
        with pytest.raises(KeyError):
            await retry_async(raise_key_error, config=config)
        
        # 不应该重试
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_with_args_and_kwargs(self):
        """测试带参数的函数"""
        async def add(a, b, c=0):
            return a + b + c
        
        result = await retry_async(add, 1, 2, c=3)
        assert result == 6


class TestWithRetryDecorator:
    """with_retry 装饰器测试"""
    
    @pytest.mark.asyncio
    async def test_decorator_success(self):
        """测试装饰器成功"""
        @with_retry(RetryConfig(max_retries=2, base_delay=0.01))
        async def success_func():
            return "decorated success"
        
        result = await success_func()
        assert result == "decorated success"
    
    @pytest.mark.asyncio
    async def test_decorator_retry(self):
        """测试装饰器重试"""
        call_count = 0
        
        @with_retry(RetryConfig(max_retries=3, base_delay=0.01))
        async def fail_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("临时错误")
            return "success"
        
        result = await fail_then_success()
        assert result == "success"
        assert call_count == 2


class TestCircuitBreaker:
    """CircuitBreaker 测试"""
    
    @pytest.fixture
    def breaker(self):
        """创建熔断器"""
        return CircuitBreaker(failure_threshold=3, recovery_timeout=0.1)
    
    def test_initial_state(self, breaker):
        """测试初始状态"""
        assert breaker.can_execute() is True
    
    def test_record_success(self, breaker):
        """测试记录成功"""
        breaker.record_failure()
        breaker.record_failure()
        breaker.record_success()
        
        assert breaker.can_execute() is True
        assert breaker._failure_count == 0
    
    def test_open_after_threshold(self, breaker):
        """测试达到阈值后打开"""
        for _ in range(3):
            breaker.record_failure()
        
        assert breaker._is_open is True
        assert breaker.can_execute() is False
    
    def test_recovery_after_timeout(self, breaker):
        """测试超时后恢复"""
        for _ in range(3):
            breaker.record_failure()
        
        assert breaker.can_execute() is False
        
        # 等待恢复超时
        time.sleep(0.15)
        
        assert breaker.can_execute() is True
    
    def test_reset(self, breaker):
        """测试重置"""
        for _ in range(3):
            breaker.record_failure()
        
        breaker.reset()
        
        assert breaker._failure_count == 0
        assert breaker._is_open is False
        assert breaker.can_execute() is True
    
    def test_half_open_state(self, breaker):
        """测试半开状态"""
        for _ in range(3):
            breaker.record_failure()
        
        # 等待进入半开状态
        time.sleep(0.15)
        
        # 半开状态允许执行
        assert breaker.can_execute() is True
        
        # 成功后关闭熔断器
        breaker.record_success()
        assert breaker._is_open is False

