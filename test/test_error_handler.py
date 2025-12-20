"""错误处理器测试

测试 src/core/utils/error_handler.py 中的错误处理功能。
"""
import pytest
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.error_handler import (
    ErrorQueue, get_user_friendly_message, format_exception_for_display,
    USER_FRIENDLY_MESSAGES
)
from src.core.models import ErrorType, ErrorItem


class TestErrorQueue:
    """ErrorQueue 测试"""
    
    @pytest.fixture
    def queue(self):
        """创建错误队列"""
        return ErrorQueue(max_size=5)
    
    def test_init(self, queue):
        """测试初始化"""
        assert queue.is_empty()
        assert queue.size() == 0
        assert not queue.is_full()
    
    def test_push_and_pop(self, queue):
        """测试入队和出队"""
        error = ErrorItem(
            error_type=ErrorType.NETWORK_ERROR,
            message="测试错误",
            timestamp=time.time()
        )
        
        queue.push(error)
        assert queue.size() == 1
        assert not queue.is_empty()
        
        popped = queue.pop()
        assert popped == error
        assert queue.is_empty()
    
    def test_peek(self, queue):
        """测试查看队首"""
        error = ErrorItem(
            error_type=ErrorType.API_ERROR,
            message="API错误",
            timestamp=time.time()
        )
        
        queue.push(error)
        
        peeked = queue.peek()
        assert peeked == error
        assert queue.size() == 1  # 不移除
    
    def test_peek_empty(self, queue):
        """测试空队列查看"""
        assert queue.peek() is None
    
    def test_pop_empty(self, queue):
        """测试空队列出队"""
        assert queue.pop() is None
    
    def test_clear(self, queue):
        """测试清空队列"""
        for i in range(3):
            queue.push(ErrorItem(
                error_type=ErrorType.NETWORK_ERROR,
                message=f"错误{i}",
                timestamp=time.time()
            ))
        
        queue.clear()
        assert queue.is_empty()
        assert queue.size() == 0
    
    def test_max_size(self, queue):
        """测试最大容量"""
        for i in range(10):
            queue.push(ErrorItem(
                error_type=ErrorType.NETWORK_ERROR,
                message=f"错误{i}",
                timestamp=time.time()
            ))
        
        # 队列最大容量为5
        assert queue.size() == 5
        assert queue.is_full()
    
    def test_fifo_order(self, queue):
        """测试先进先出顺序"""
        for i in range(3):
            queue.push(ErrorItem(
                error_type=ErrorType.NETWORK_ERROR,
                message=f"错误{i}",
                timestamp=time.time()
            ))
        
        assert queue.pop().message == "错误0"
        assert queue.pop().message == "错误1"
        assert queue.pop().message == "错误2"
    
    def test_create_error(self, queue):
        """测试创建错误"""
        error = queue.create_error(
            ErrorType.API_ERROR,
            "API错误",
            retryable=False
        )
        
        assert error.error_type == ErrorType.API_ERROR
        assert error.message == "API错误"
        assert error.retryable is False
        assert queue.size() == 1
    
    def test_create_network_error(self, queue):
        """测试创建网络错误"""
        callback = lambda: None
        error = queue.create_network_error("网络断开", callback)
        
        assert error.error_type == ErrorType.NETWORK_ERROR
        assert error.retryable is True
        assert error.retry_callback is callback
    
    def test_create_timeout_error(self, queue):
        """测试创建超时错误"""
        error = queue.create_timeout_error()
        
        assert error.error_type == ErrorType.TIMEOUT_ERROR
        assert error.message == "请求超时"
        assert error.retryable is True
    
    def test_create_api_error(self, queue):
        """测试创建API错误"""
        error = queue.create_api_error("服务器错误")
        
        assert error.error_type == ErrorType.API_ERROR
        assert error.retryable is False
    
    def test_create_parse_error(self, queue):
        """测试创建解析错误"""
        error = queue.create_parse_error("JSON解析失败")
        
        assert error.error_type == ErrorType.PARSE_ERROR
        assert error.retryable is False


class TestUserFriendlyMessage:
    """用户友好消息测试"""
    
    def test_network_error_message(self):
        """测试网络错误消息"""
        msg = get_user_friendly_message(ErrorType.NETWORK_ERROR)
        assert "网络" in msg
    
    def test_timeout_error_message(self):
        """测试超时错误消息"""
        msg = get_user_friendly_message(ErrorType.TIMEOUT_ERROR)
        assert "超时" in msg
    
    def test_parse_error_message(self):
        """测试解析错误消息"""
        msg = get_user_friendly_message(ErrorType.PARSE_ERROR)
        assert "解析" in msg
    
    def test_api_error_message(self):
        """测试API错误消息"""
        msg = get_user_friendly_message(ErrorType.API_ERROR)
        assert "服务器" in msg
    
    def test_video_error_message(self):
        """测试视频错误消息"""
        msg = get_user_friendly_message(ErrorType.VIDEO_ERROR)
        assert "视频" in msg
    
    def test_config_error_message(self):
        """测试配置错误消息"""
        msg = get_user_friendly_message(ErrorType.CONFIG_ERROR)
        assert "配置" in msg
    
    def test_with_original_message(self):
        """测试带原始消息"""
        msg = get_user_friendly_message(
            ErrorType.NETWORK_ERROR,
            "Connection refused"
        )
        # Debug模式下应包含详情
        assert "网络" in msg
    
    def test_all_error_types_have_messages(self):
        """测试所有错误类型都有消息"""
        for error_type in ErrorType:
            msg = get_user_friendly_message(error_type)
            assert msg  # 不为空


class TestFormatException:
    """异常格式化测试"""
    
    def test_format_value_error(self):
        """测试格式化 ValueError"""
        try:
            raise ValueError("无效的值")
        except ValueError as e:
            msg = format_exception_for_display(e)
            assert "ValueError" in msg or "无效的值" in msg
    
    def test_format_type_error(self):
        """测试格式化 TypeError"""
        try:
            raise TypeError("类型错误")
        except TypeError as e:
            msg = format_exception_for_display(e)
            assert "TypeError" in msg or "类型错误" in msg
    
    def test_format_empty_message(self):
        """测试格式化空消息异常"""
        try:
            raise Exception()
        except Exception as e:
            msg = format_exception_for_display(e)
            assert msg is not None

