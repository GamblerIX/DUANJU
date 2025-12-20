"""日志管理器测试"""
from unittest.mock import MagicMock, patch
from unittest.mock import MagicMock, patch, call

import logging
import pytest

from src.utils.log_manager import LogManager, get_logger

class TestLogManagerLogic:
    """日志管理器逻辑测试"""
    
    def test_friendly_error_message_network(self):
        """测试网络错误友好消息"""
        from src.utils.log_manager import LogManager
        
        manager = LogManager()
        
        # 断开连接
        msg = manager.get_friendly_error_message(Exception("Connection disconnected"))
        assert "网络" in msg
        
        # 超时
        msg = manager.get_friendly_error_message(Exception("Request timeout"))
        assert "超时" in msg
        
        # 连接拒绝 - 使用 refused 关键词
        msg = manager.get_friendly_error_message(Exception("refused"))
        assert "拒绝" in msg or "服务器" in msg
        
        # DNS 解析
        msg = manager.get_friendly_error_message(Exception("DNS resolve failed"))
        assert "解析" in msg
        
        # SSL 错误
        msg = manager.get_friendly_error_message(Exception("SSL certificate error"))
        assert "SSL" in msg
    
    def test_friendly_error_message_http(self):
        """测试 HTTP 错误友好消息"""
        from src.utils.log_manager import LogManager
        
        manager = LogManager()
        
        # 404
        msg = manager.get_friendly_error_message(Exception("HTTP 404 Not Found"))
        assert "不存在" in msg
        
        # 403
        msg = manager.get_friendly_error_message(Exception("HTTP 403 Forbidden"))
        assert "拒绝" in msg
        
        # 500
        msg = manager.get_friendly_error_message(Exception("HTTP 500 Internal Server Error"))
        assert "服务器" in msg
    
    def test_friendly_error_message_parse(self):
        """测试解析错误友好消息"""
        from src.utils.log_manager import LogManager
        
        manager = LogManager()
        
        msg = manager.get_friendly_error_message(Exception("JSON parse error"))
        assert "解析" in msg
    
    def test_friendly_error_message_truncate(self):
        """测试长错误消息截断"""
        from src.utils.log_manager import LogManager
        
        manager = LogManager()
        
        long_error = "A" * 100
        msg = manager.get_friendly_error_message(Exception(long_error))
        
        assert len(msg) <= 53  # 50 + "..."
        assert msg.endswith("...")


class TestLogManagerMock:
    """日志管理器 Mock 测试"""
    
    def test_singleton(self):
        """测试单例模式"""
        from src.utils.log_manager import LogManager
        
        manager1 = LogManager()
        manager2 = LogManager()
        
        assert manager1 is manager2
    
    def test_get_logger(self):
        """测试获取日志实例"""
        from src.utils.log_manager import get_logger
        
        logger = get_logger()
        
        assert logger is not None
    
    @patch.object(logging.Logger, 'debug')
    def test_debug(self, mock_debug):
        """测试调试日志"""
        from src.utils.log_manager import LogManager
        
        manager = LogManager()
        manager.debug("Test debug message")
        
        mock_debug.assert_called()
    
    @patch.object(logging.Logger, 'info')
    def test_info(self, mock_info):
        """测试信息日志"""
        from src.utils.log_manager import LogManager
        
        manager = LogManager()
        manager.info("Test info message")
        
        mock_info.assert_called()
    
    @patch.object(logging.Logger, 'warning')
    def test_warning(self, mock_warning):
        """测试警告日志"""
        from src.utils.log_manager import LogManager
        
        manager = LogManager()
        manager.warning("Test warning message")
        
        mock_warning.assert_called()
    
    @patch.object(logging.Logger, 'error')
    def test_error(self, mock_error):
        """测试错误日志"""
        from src.utils.log_manager import LogManager
        
        manager = LogManager()
        manager.error("Test error message")
        
        mock_error.assert_called()
    
    @patch.object(logging.Logger, 'critical')
    def test_critical(self, mock_critical):
        """测试严重错误日志"""
        from src.utils.log_manager import LogManager
        
        manager = LogManager()
        manager.critical("Test critical message")
        
        mock_critical.assert_called()
    
    @patch.object(logging.Logger, 'exception')
    def test_exception(self, mock_exception):
        """测试异常日志"""
        from src.utils.log_manager import LogManager
        
        manager = LogManager()
        manager.exception("Test exception message")
        
        mock_exception.assert_called()
    
    @patch.object(logging.Logger, 'debug')
    def test_log_api_request(self, mock_debug):
        """测试 API 请求日志"""
        from src.utils.log_manager import LogManager
        
        manager = LogManager()
        manager.log_api_request("http://api.example.com", {"key": "value"})
        
        mock_debug.assert_called()
    
    @patch.object(logging.Logger, 'error')
    def test_log_api_request_error(self, mock_error):
        """测试 API 请求错误日志"""
        from src.utils.log_manager import LogManager
        
        manager = LogManager()
        manager.log_api_request("http://api.example.com", error="Connection failed")
        
        mock_error.assert_called()
    
    @patch.object(logging.Logger, 'debug')
    def test_log_api_response(self, mock_debug):
        """测试 API 响应日志"""
        from src.utils.log_manager import LogManager
        
        manager = LogManager()
        manager.log_api_response("http://api.example.com", 200, True)
        
        mock_debug.assert_called()
    
    @patch.object(logging.Logger, 'info')
    def test_log_user_action(self, mock_info):
        """测试用户操作日志"""
        from src.utils.log_manager import LogManager
        
        manager = LogManager()
        manager.log_user_action("search", "keyword=test")
        
        mock_info.assert_called()
    
    @patch.object(logging.Logger, 'error')
    def test_log_error(self, mock_error):
        """测试错误日志方法"""
        from src.utils.log_manager import LogManager
        
        manager = LogManager()
        manager.log_error("NetworkError", "Connection failed", "Details here")
        
        mock_error.assert_called()
    
    @patch.object(logging.Logger, 'error')
    @patch.object(logging.Logger, 'debug')
    def test_log_service_error(self, mock_debug, mock_error):
        """测试服务错误日志"""
        from src.utils.log_manager import LogManager
        
        manager = LogManager()
        manager.log_service_error("SearchService", "search", Exception("Test error"))
        
        mock_error.assert_called()
        mock_debug.assert_called()
    
    @patch.object(logging.Logger, 'error')
    @patch.object(logging.Logger, 'debug')
    def test_log_ui_error(self, mock_debug, mock_error):
        """测试 UI 错误日志"""
        from src.utils.log_manager import LogManager
        
        manager = LogManager()
        manager.log_ui_error("MainWindow", Exception("UI error"))
        
        mock_error.assert_called()
        mock_debug.assert_called()
    
    @patch.object(logging.Logger, 'debug')
    def test_log_cache_operation_hit(self, mock_debug):
        """测试缓存命中日志"""
        from src.utils.log_manager import LogManager
        
        manager = LogManager()
        manager.log_cache_operation("GET", "cache_key", hit=True)
        
        mock_debug.assert_called()
        call_args = mock_debug.call_args[0][0]
        assert "HIT" in call_args
    
    @patch.object(logging.Logger, 'debug')
    def test_log_cache_operation_miss(self, mock_debug):
        """测试缓存未命中日志"""
        from src.utils.log_manager import LogManager
        
        manager = LogManager()
        manager.log_cache_operation("GET", "cache_key", hit=False)
        
        mock_debug.assert_called()
        call_args = mock_debug.call_args[0][0]
        assert "MISS" in call_args
    
    @patch.object(logging.Logger, 'info')
    def test_log_config_change(self, mock_info):
        """测试配置变更日志"""
        from src.utils.log_manager import LogManager
        
        manager = LogManager()
        manager.log_config_change("theme", "light", "dark")
        
        mock_info.assert_called()
        call_args = mock_info.call_args[0][0]
        assert "light" in call_args
        assert "dark" in call_args


class TestLogManagerConstants:
    """日志管理器常量测试"""
    
    def test_constants(self):
        """测试常量值"""
        from src.utils.log_manager import LogManager
        
        assert LogManager.DEFAULT_LOG_DIR == "logs"
        assert LogManager.MAX_FILE_SIZE == 10 * 1024 * 1024
        assert LogManager.BACKUP_COUNT == 5



# ============================================================
# From: test_log_manager_full.py
# ============================================================
class TestLogManagerFriendlyMessages:
    """测试友好错误消息"""
    
    @pytest.fixture
    def log_manager(self):
        return get_logger()
    
    def test_disconnect_error(self, log_manager):
        error = Exception("Connection disconnected")
        msg = log_manager.get_friendly_error_message(error)
        assert "网络连接断开" in msg
    
    def test_timeout_error(self, log_manager):
        error = Exception("Request timeout")
        msg = log_manager.get_friendly_error_message(error)
        assert "超时" in msg
    
    def test_refused_error(self, log_manager):
        error = Exception("refused by server")
        msg = log_manager.get_friendly_error_message(error)
        assert "拒绝" in msg
    
    def test_dns_error(self, log_manager):
        error = Exception("DNS resolution failed")
        msg = log_manager.get_friendly_error_message(error)
        assert "无法解析" in msg
    
    def test_ssl_error(self, log_manager):
        error = Exception("SSL certificate error")
        msg = log_manager.get_friendly_error_message(error)
        assert "SSL" in msg
    
    def test_404_error(self, log_manager):
        error = Exception("HTTP 404 Not Found")
        msg = log_manager.get_friendly_error_message(error)
        assert "不存在" in msg
    
    def test_403_error(self, log_manager):
        error = Exception("HTTP 403 Forbidden")
        msg = log_manager.get_friendly_error_message(error)
        assert "拒绝" in msg
    
    def test_500_error(self, log_manager):
        error = Exception("HTTP 500 Internal Server Error")
        msg = log_manager.get_friendly_error_message(error)
        assert "服务器内部错误" in msg
    
    def test_502_error(self, log_manager):
        error = Exception("HTTP 502 Bad Gateway")
        msg = log_manager.get_friendly_error_message(error)
        assert "服务器内部错误" in msg
    
    def test_503_error(self, log_manager):
        error = Exception("HTTP 503 Service Unavailable")
        msg = log_manager.get_friendly_error_message(error)
        assert "服务暂时不可用" in msg
    
    def test_json_error(self, log_manager):
        error = Exception("JSON decode error")
        msg = log_manager.get_friendly_error_message(error)
        assert "解析失败" in msg
    
    def test_parse_error(self, log_manager):
        error = Exception("Parse error occurred")
        msg = log_manager.get_friendly_error_message(error)
        assert "解析失败" in msg
    
    def test_long_error_truncation(self, log_manager):
        error = Exception("A" * 100)
        msg = log_manager.get_friendly_error_message(error)
        assert len(msg) <= 53  # 50 + "..."
        assert msg.endswith("...")
    
    def test_short_error_no_truncation(self, log_manager):
        error = Exception("Short error")
        msg = log_manager.get_friendly_error_message(error)
        assert msg == "Short error"


class TestLogManagerMethods:
    """测试日志管理器方法"""
    
    @pytest.fixture
    def log_manager(self):
        return get_logger()
    
    def test_debug(self, log_manager):
        log_manager.debug("Debug message")
    
    def test_info(self, log_manager):
        log_manager.info("Info message")
    
    def test_warning(self, log_manager):
        log_manager.warning("Warning message")
    
    def test_error(self, log_manager):
        log_manager.error("Error message")
    
    def test_error_with_exc_info(self, log_manager):
        log_manager.error("Error with exc_info", exc_info=True)
    
    def test_critical(self, log_manager):
        log_manager.critical("Critical message")
    
    def test_critical_with_exc_info(self, log_manager):
        log_manager.critical("Critical with exc_info", exc_info=True)
    
    def test_log_api_request(self, log_manager):
        log_manager.log_api_request("https://api.example.com", {"key": "value"})
    
    def test_log_api_request_with_status(self, log_manager):
        log_manager.log_api_request("https://api.example.com", status_code=200)
    
    def test_log_api_request_with_error(self, log_manager):
        log_manager.log_api_request("https://api.example.com", error="Connection failed")
    
    def test_log_api_response_success(self, log_manager):
        log_manager.log_api_response("https://api.example.com", 200, True)
    
    def test_log_api_response_failure(self, log_manager):
        log_manager.log_api_response("https://api.example.com", 500, False)
    
    def test_log_user_action(self, log_manager):
        log_manager.log_user_action("search", "keyword=test")
    
    def test_log_user_action_no_details(self, log_manager):
        log_manager.log_user_action("click")
    
    def test_log_error(self, log_manager):
        log_manager.log_error("NetworkError", "Connection failed", "Details here")
    
    def test_log_error_no_details(self, log_manager):
        log_manager.log_error("NetworkError", "Connection failed")
    
    def test_log_service_error(self, log_manager):
        error = ValueError("Test error")
        log_manager.log_service_error("SearchService", "search", error)
    
    def test_log_ui_error(self, log_manager):
        error = RuntimeError("UI error")
        log_manager.log_ui_error("MainWindow", error)
    
    def test_log_cache_operation_hit(self, log_manager):
        log_manager.log_cache_operation("GET", "search_key", hit=True)
    
    def test_log_cache_operation_miss(self, log_manager):
        log_manager.log_cache_operation("GET", "search_key", hit=False)
    
    def test_log_config_change(self, log_manager):
        log_manager.log_config_change("theme", "light", "dark")


class TestLogManagerSingleton:
    """测试单例模式"""
    
    def test_singleton(self):
        logger1 = LogManager()
        logger2 = LogManager()
        assert logger1 is logger2
    
    def test_get_logger(self):
        logger1 = get_logger()
        logger2 = get_logger()
        assert logger1 is logger2


class TestLogManagerQtHook:
    """测试 Qt 异常钩子"""
    
    def test_setup_qt_exception_hook_no_pyside(self):
        log_manager = get_logger()
        # 即使没有 PySide6 也不应该崩溃
        with patch.dict('sys.modules', {'PySide6': None, 'PySide6.QtCore': None}):
            log_manager.setup_qt_exception_hook()
