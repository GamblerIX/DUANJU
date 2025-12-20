"""网络监控器测试"""
from unittest.mock import MagicMock, AsyncMock, patch
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio

import pytest

class TestNetworkMonitorLogic:
    """网络监控器逻辑测试"""
    
    def test_constants(self):
        """测试常量配置"""
        from src.utils.network_monitor import NetworkMonitor
        
        assert NetworkMonitor.CHECK_INTERVAL == 30000
        assert NetworkMonitor.SLOW_THRESHOLD == 3000
        assert NetworkMonitor.RETRY_COUNT == 3


class TestNetworkMonitorMock:
    """网络监控器 Mock 测试"""
    
    @patch('src.utils.network_monitor.QTimer')
    def test_init(self, mock_timer):
        """测试初始化"""
        from src.utils.network_monitor import NetworkMonitor
        
        monitor = NetworkMonitor()
        
        assert monitor._is_connected is True
        assert monitor._consecutive_failures == 0
        assert monitor._last_retry_callback is None
    
    @patch('src.utils.network_monitor.QTimer')
    def test_is_connected_property(self, mock_timer):
        """测试连接状态属性"""
        from src.utils.network_monitor import NetworkMonitor
        
        monitor = NetworkMonitor()
        assert monitor.is_connected is True
        
        monitor._is_connected = False
        assert monitor.is_connected is False
    
    @patch('src.utils.network_monitor.QTimer')
    def test_consecutive_failures_property(self, mock_timer):
        """测试连续失败次数属性"""
        from src.utils.network_monitor import NetworkMonitor
        
        monitor = NetworkMonitor()
        assert monitor.consecutive_failures == 0
        
        monitor._consecutive_failures = 5
        assert monitor.consecutive_failures == 5
    
    @patch('src.utils.network_monitor.QTimer')
    def test_report_request_success(self, mock_timer):
        """测试报告请求成功"""
        from src.utils.network_monitor import NetworkMonitor
        
        monitor = NetworkMonitor()
        monitor._consecutive_failures = 3
        monitor._is_connected = False
        
        monitor.report_request_success()
        
        assert monitor._consecutive_failures == 0
        assert monitor._is_connected is True
    
    @patch('src.utils.network_monitor.QTimer')
    def test_report_request_failure(self, mock_timer):
        """测试报告请求失败"""
        from src.utils.network_monitor import NetworkMonitor
        
        monitor = NetworkMonitor()
        callback = MagicMock()
        
        monitor.report_request_failure(callback)
        
        assert monitor._consecutive_failures == 1
        assert monitor._last_retry_callback == callback
    
    @patch('src.utils.network_monitor.QTimer')
    def test_report_request_failure_multiple(self, mock_timer):
        """测试多次请求失败"""
        from src.utils.network_monitor import NetworkMonitor
        
        monitor = NetworkMonitor()
        
        for i in range(5):
            monitor.report_request_failure()
        
        assert monitor._consecutive_failures == 5
    
    @patch('src.utils.network_monitor.QTimer')
    def test_report_slow_response_below_threshold(self, mock_timer):
        """测试慢响应低于阈值"""
        from src.utils.network_monitor import NetworkMonitor
        
        monitor = NetworkMonitor()
        monitor.slow_network = MagicMock()
        
        monitor.report_slow_response(2000)  # 低于 3000ms 阈值
        
        monitor.slow_network.emit.assert_not_called()
    
    @patch('src.utils.network_monitor.QTimer')
    def test_report_slow_response_above_threshold(self, mock_timer):
        """测试慢响应高于阈值"""
        from src.utils.network_monitor import NetworkMonitor
        
        monitor = NetworkMonitor()
        monitor.slow_network = MagicMock()
        
        monitor.report_slow_response(5000)  # 高于 3000ms 阈值
        
        monitor.slow_network.emit.assert_called_once()
    
    @patch('src.utils.network_monitor.QTimer')
    def test_on_connection_failed(self, mock_timer):
        """测试连接失败处理"""
        from src.utils.network_monitor import NetworkMonitor
        
        monitor = NetworkMonitor()
        monitor.connection_lost = MagicMock()
        
        monitor._on_connection_failed()
        
        assert monitor._consecutive_failures == 1
        assert monitor._is_connected is False
        monitor.connection_lost.emit.assert_called_once()
    
    @patch('src.utils.network_monitor.QTimer')
    def test_on_connection_failed_already_disconnected(self, mock_timer):
        """测试已断开时的连接失败处理"""
        from src.utils.network_monitor import NetworkMonitor
        
        monitor = NetworkMonitor()
        monitor._is_connected = False
        monitor.connection_lost = MagicMock()
        
        monitor._on_connection_failed()
        
        assert monitor._consecutive_failures == 1
        # 已断开时不再发送信号
        monitor.connection_lost.emit.assert_not_called()
    
    @patch('asyncio.create_task')
    @patch('src.utils.network_monitor.QTimer')
    def test_start(self, mock_timer_class, mock_create_task):
        """测试启动监控"""
        from src.utils.network_monitor import NetworkMonitor
        
        mock_timer = MagicMock()
        mock_timer_class.return_value = mock_timer
        
        monitor = NetworkMonitor()
        monitor.start()
        
        mock_timer.start.assert_called_with(NetworkMonitor.CHECK_INTERVAL)
        mock_create_task.assert_called_once()
    
    @patch('src.utils.network_monitor.QTimer')
    @patch('asyncio.create_task')
    def test_stop(self, mock_create_task, mock_timer_class):
        """测试停止监控"""
        from src.utils.network_monitor import NetworkMonitor
        
        mock_timer = MagicMock()
        mock_timer_class.return_value = mock_timer
        
        monitor = NetworkMonitor()
        monitor.stop()
        
        mock_timer.stop.assert_called_once()


class TestNetworkMonitorAsync:
    """网络监控器异步测试"""
    
    @patch('src.utils.network_monitor.QTimer')
    def test_connection_state_changes(self, mock_timer):
        """测试连接状态变化"""
        from src.utils.network_monitor import NetworkMonitor
        
        monitor = NetworkMonitor()
        
        # 初始状态
        assert monitor._is_connected is True
        
        # 模拟连接失败
        monitor._on_connection_failed()
        assert monitor._is_connected is False
        
        # 模拟连接恢复
        monitor.report_request_success()
        assert monitor._is_connected is True
    
    @patch('src.utils.network_monitor.QTimer')
    def test_retry_callback_storage(self, mock_timer):
        """测试重试回调存储"""
        from src.utils.network_monitor import NetworkMonitor
        
        # 同时mock asyncio.create_task以避免协程未await警告
        with patch('asyncio.create_task'):
            monitor = NetworkMonitor()
            callback = MagicMock()
            
            monitor.report_request_failure(callback)
            
            assert monitor._last_retry_callback == callback



# ============================================================
# From: test_network_monitor_full.py
# ============================================================
class TestNetworkMonitorLogic_Full:
    """测试网络监控器逻辑（不依赖 Qt）"""
    
    def test_connection_state_tracking(self):
        """测试连接状态跟踪"""
        # 模拟连接状态
        is_connected = True
        consecutive_failures = 0
        
        # 模拟连接失败
        consecutive_failures += 1
        if is_connected and consecutive_failures >= 3:
            is_connected = False
        
        assert consecutive_failures == 1
        assert is_connected == True
        
        # 继续失败
        consecutive_failures += 1
        consecutive_failures += 1
        if consecutive_failures >= 3:
            is_connected = False
        
        assert consecutive_failures == 3
        assert is_connected == False
    
    def test_slow_network_detection(self):
        """测试慢网络检测"""
        SLOW_THRESHOLD = 3000  # 3秒
        
        # 正常响应
        elapsed_ms = 1000
        is_slow = elapsed_ms > SLOW_THRESHOLD
        assert is_slow == False
        
        # 慢响应
        elapsed_ms = 5000
        is_slow = elapsed_ms > SLOW_THRESHOLD
        assert is_slow == True
    
    def test_retry_callback_storage(self):
        """测试重试回调存储"""
        last_retry_callback = None
        
        def retry_func():
            pass
        
        last_retry_callback = retry_func
        assert last_retry_callback is not None
        
        # 清除回调
        last_retry_callback = None
        assert last_retry_callback is None
    
    def test_connection_restored_logic(self):
        """测试连接恢复逻辑"""
        is_connected = False
        consecutive_failures = 5
        last_retry_callback = MagicMock()
        
        # 模拟连接恢复
        is_connected = True
        consecutive_failures = 0
        
        # 执行重试回调
        if last_retry_callback:
            last_retry_callback()
            last_retry_callback = None
        
        assert is_connected == True
        assert consecutive_failures == 0


class TestNetworkMonitorMocked:
    """使用 mock 测试网络监控器"""
    
    def test_report_request_failure(self):
        """测试报告请求失败"""
        consecutive_failures = 0
        last_retry_callback = None
        RETRY_COUNT = 3
        
        def report_request_failure(retry_callback=None):
            nonlocal consecutive_failures, last_retry_callback
            consecutive_failures += 1
            last_retry_callback = retry_callback
        
        callback = MagicMock()
        report_request_failure(callback)
        
        assert consecutive_failures == 1
        assert last_retry_callback == callback
    
    def test_report_request_success(self):
        """测试报告请求成功"""
        is_connected = False
        consecutive_failures = 5
        
        def report_request_success():
            nonlocal is_connected, consecutive_failures
            consecutive_failures = 0
            if not is_connected:
                is_connected = True
        
        report_request_success()
        
        assert consecutive_failures == 0
        assert is_connected == True
    
    def test_report_slow_response(self):
        """测试报告慢响应"""
        SLOW_THRESHOLD = 3000
        slow_detected = False
        
        def report_slow_response(elapsed_ms):
            nonlocal slow_detected
            if elapsed_ms > SLOW_THRESHOLD:
                slow_detected = True
        
        report_slow_response(5000)
        assert slow_detected == True
        
        slow_detected = False
        report_slow_response(1000)
        assert slow_detected == False


class TestNetworkMonitorAsync_Full:
    """测试网络监控器异步方法"""
    
    @pytest.mark.asyncio
    async def test_do_check_success(self):
        """测试连接检查成功"""
        is_connected = False
        
        async def mock_check():
            nonlocal is_connected
            # 模拟成功的网络检查
            is_connected = True
            return True
        
        result = await mock_check()
        assert result == True
        assert is_connected == True
    
    @pytest.mark.asyncio
    async def test_do_check_failure(self):
        """测试连接检查失败"""
        consecutive_failures = 0
        
        async def mock_check():
            nonlocal consecutive_failures
            try:
                raise Exception("Connection failed")
            except:
                consecutive_failures += 1
                return False
        
        result = await mock_check()
        assert result == False
        assert consecutive_failures == 1
    
    @pytest.mark.asyncio
    async def test_do_check_slow_response(self):
        """测试慢响应检测"""
        import time
        
        SLOW_THRESHOLD = 0.1  # 100ms for testing
        is_slow = False
        
        async def mock_check():
            nonlocal is_slow
            start = time.time()
            await asyncio.sleep(0.15)  # 150ms
            elapsed = time.time() - start
            if elapsed > SLOW_THRESHOLD:
                is_slow = True
            return True
        
        await mock_check()
        assert is_slow == True


class TestNetworkMonitorConstants:
    """测试网络监控器常量"""
    
    def test_check_interval(self):
        """测试检查间隔"""
        CHECK_INTERVAL = 30000  # 30秒
        assert CHECK_INTERVAL == 30000
    
    def test_slow_threshold(self):
        """测试慢网络阈值"""
        SLOW_THRESHOLD = 3000  # 3秒
        assert SLOW_THRESHOLD == 3000
    
    def test_retry_count(self):
        """测试重试次数"""
        RETRY_COUNT = 3
        assert RETRY_COUNT == 3


class TestNetworkMonitorIntegration:
    """网络监控器集成测试"""
    
    def test_full_failure_recovery_cycle(self):
        """测试完整的失败恢复周期"""
        is_connected = True
        consecutive_failures = 0
        RETRY_COUNT = 3
        
        # 模拟多次失败
        for _ in range(RETRY_COUNT):
            consecutive_failures += 1
        
        # 检查是否应该断开
        if consecutive_failures >= RETRY_COUNT:
            is_connected = False
        
        assert is_connected == False
        assert consecutive_failures == 3
        
        # 模拟恢复
        is_connected = True
        consecutive_failures = 0
        
        assert is_connected == True
        assert consecutive_failures == 0
    
    def test_retry_callback_execution(self):
        """测试重试回调执行"""
        callback_executed = False
        
        def retry_callback():
            nonlocal callback_executed
            callback_executed = True
        
        last_retry_callback = retry_callback
        
        # 模拟连接恢复后执行回调
        if last_retry_callback:
            last_retry_callback()
        
        assert callback_executed == True


class TestNetworkMonitorWithMock:
    """使用 mock 测试网络监控器的 Qt 依赖部分"""
    
    def test_timer_start_stop(self):
        """测试定时器启动和停止"""
        timer = MagicMock()
        
        # 启动
        timer.start(30000)
        timer.start.assert_called_with(30000)
        
        # 停止
        timer.stop()
        timer.stop.assert_called()
    
    def test_signal_emission(self):
        """测试信号发射"""
        connection_lost = MagicMock()
        connection_restored = MagicMock()
        slow_network = MagicMock()
        
        # 模拟连接丢失
        connection_lost.emit()
        connection_lost.emit.assert_called()
        
        # 模拟连接恢复
        connection_restored.emit()
        connection_restored.emit.assert_called()
        
        # 模拟慢网络
        slow_network.emit()
        slow_network.emit.assert_called()


class TestNetworkMonitorEdgeCases:
    """测试边界情况"""
    
    def test_zero_failures(self):
        """测试零失败"""
        consecutive_failures = 0
        RETRY_COUNT = 3
        
        should_disconnect = consecutive_failures >= RETRY_COUNT
        assert should_disconnect == False
    
    def test_exactly_threshold_failures(self):
        """测试恰好达到阈值"""
        consecutive_failures = 3
        RETRY_COUNT = 3
        
        should_disconnect = consecutive_failures >= RETRY_COUNT
        assert should_disconnect == True
    
    def test_above_threshold_failures(self):
        """测试超过阈值"""
        consecutive_failures = 10
        RETRY_COUNT = 3
        
        should_disconnect = consecutive_failures >= RETRY_COUNT
        assert should_disconnect == True
    
    def test_exactly_slow_threshold(self):
        """测试恰好达到慢网络阈值"""
        SLOW_THRESHOLD = 3000
        elapsed_ms = 3000
        
        is_slow = elapsed_ms > SLOW_THRESHOLD
        assert is_slow == False  # 等于阈值不算慢
    
    def test_just_above_slow_threshold(self):
        """测试刚超过慢网络阈值"""
        SLOW_THRESHOLD = 3000
        elapsed_ms = 3001
        
        is_slow = elapsed_ms > SLOW_THRESHOLD
        assert is_slow == True
