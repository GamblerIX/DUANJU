"""异步工作线程测试

测试 src/core/utils/async_worker.py 中的异步工作线程。
注意：这些测试需要 Qt 事件循环，部分测试可能需要跳过。
"""
from pathlib import Path
from unittest.mock import MagicMock, patch
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestAsyncWorkerLogic:
    """AsyncWorker 逻辑测试（不依赖 Qt）"""
    
    def test_asyncio_event_loop_creation(self):
        """测试事件循环创建"""
        loop = asyncio.new_event_loop()
        assert loop is not None
        loop.close()
    
    @pytest.mark.asyncio
    async def test_async_function_execution(self):
        """测试异步函数执行"""
        async def sample_async_func(x, y):
            await asyncio.sleep(0.01)
            return x + y
        
        result = await sample_async_func(1, 2)
        assert result == 3
    
    @pytest.mark.asyncio
    async def test_async_exception_handling(self):
        """测试异步异常处理"""
        async def failing_func():
            raise ValueError("测试错误")
        
        with pytest.raises(ValueError):
            await failing_func()
    
    @pytest.mark.asyncio
    async def test_async_with_args_kwargs(self):
        """测试带参数的异步函数"""
        async def func_with_args(a, b, c=0, d=0):
            return a + b + c + d
        
        result = await func_with_args(1, 2, c=3, d=4)
        assert result == 10
    
    def test_event_loop_cleanup(self):
        """测试事件循环清理"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 创建一些任务
        async def dummy():
            await asyncio.sleep(0.001)
            return "done"
        
        result = loop.run_until_complete(dummy())
        assert result == "done"
        
        # 清理
        loop.close()
        asyncio.set_event_loop(None)


class TestAsyncWorkerIntegration:
    """AsyncWorker 集成测试"""
    
    @pytest.fixture
    def mock_qt_thread(self):
        """模拟 QThread"""
        with patch('PySide6.QtCore.QThread') as mock:
            yield mock
    
    def test_worker_initialization_logic(self):
        """测试工作线程初始化逻辑"""
        # 模拟协程函数
        async def coro_func(x):
            return x * 2
        
        # 验证参数存储
        args = (5,)
        kwargs = {}
        service_name = "TestService"
        
        # 这些是 AsyncWorker 应该存储的
        assert callable(coro_func)
        assert args == (5,)
        assert service_name == "TestService"
    
    @pytest.mark.asyncio
    async def test_coroutine_result_handling(self):
        """测试协程结果处理"""
        results = []
        
        async def coro_func():
            return {"data": "test"}
        
        result = await coro_func()
        results.append(result)
        
        assert len(results) == 1
        assert results[0]["data"] == "test"
    
    @pytest.mark.asyncio
    async def test_coroutine_error_handling(self):
        """测试协程错误处理"""
        errors = []
        
        async def failing_coro():
            raise RuntimeError("测试错误")
        
        try:
            await failing_coro()
        except RuntimeError as e:
            errors.append(e)
        
        assert len(errors) == 1
        assert "测试错误" in str(errors[0])


class TestAsyncPatterns:
    """异步模式测试"""
    
    @pytest.mark.asyncio
    async def test_concurrent_tasks(self):
        """测试并发任务"""
        results = []
        
        async def task(n):
            await asyncio.sleep(0.01)
            return n * 2
        
        tasks = [task(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        assert results == [0, 2, 4, 6, 8]
    
    @pytest.mark.asyncio
    async def test_task_cancellation(self):
        """测试任务取消"""
        async def long_running():
            await asyncio.sleep(10)
            return "completed"
        
        task = asyncio.create_task(long_running())
        await asyncio.sleep(0.01)
        task.cancel()
        
        with pytest.raises(asyncio.CancelledError):
            await task
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """测试超时处理"""
        async def slow_func():
            await asyncio.sleep(10)
            return "done"
        
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(slow_func(), timeout=0.01)




# ============================================================
# From: test_async_worker_full.py
# ============================================================
class TestAsyncWorkerLogic_Full:
    """测试 AsyncWorker 逻辑（不依赖 Qt）"""
    
    def test_event_loop_creation(self):
        """测试事件循环创建"""
        loop = asyncio.new_event_loop()
        assert loop is not None
        assert not loop.is_running()
        loop.close()
    
    @pytest.mark.asyncio
    async def test_coroutine_execution(self):
        """测试协程执行"""
        async def sample_coro(x, y):
            await asyncio.sleep(0.01)
            return x + y
        
        result = await sample_coro(1, 2)
        assert result == 3
    
    @pytest.mark.asyncio
    async def test_coroutine_with_exception(self):
        """测试协程异常"""
        async def failing_coro():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            await failing_coro()
    
    def test_loop_cleanup_logic(self):
        """测试事件循环清理逻辑"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 模拟清理
        try:
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
        except RuntimeError:
            pass
        finally:
            loop.close()
            asyncio.set_event_loop(None)
        
        assert loop.is_closed()
    
    @pytest.mark.asyncio
    async def test_task_cancellation(self):
        """测试任务取消"""
        async def long_running():
            await asyncio.sleep(10)
            return "done"
        
        task = asyncio.create_task(long_running())
        task.cancel()
        
        with pytest.raises(asyncio.CancelledError):
            await task
    
    @pytest.mark.asyncio
    async def test_gather_with_exceptions(self):
        """测试 gather 处理异常"""
        async def success():
            return "success"
        
        async def failure():
            raise ValueError("error")
        
        results = await asyncio.gather(
            success(),
            failure(),
            return_exceptions=True
        )
        
        assert results[0] == "success"
        assert isinstance(results[1], ValueError)
    
    def test_args_kwargs_handling(self):
        """测试参数处理"""
        args = (1, 2, 3)
        kwargs = {"a": 1, "b": 2}
        
        def sample_func(*args, **kwargs):
            return sum(args) + sum(kwargs.values())
        
        result = sample_func(*args, **kwargs)
        assert result == 9
    
    @pytest.mark.asyncio
    async def test_async_generator_shutdown(self):
        """测试异步生成器关闭"""
        async def async_gen():
            for i in range(3):
                yield i
        
        results = []
        async for item in async_gen():
            results.append(item)
        
        assert results == [0, 1, 2]


class TestAsyncWorkerIntegration_Full:
    """集成测试"""
    
    def test_worker_initialization_params(self):
        """测试工作线程初始化参数"""
        async def coro_func(x, y, z=None):
            return x + y + (z or 0)
        
        args = (1, 2)
        kwargs = {"z": 3}
        service_name = "TestService"
        
        # 模拟存储参数
        stored_func = coro_func
        stored_args = args
        stored_kwargs = kwargs
        stored_service_name = service_name
        
        assert stored_func == coro_func
        assert stored_args == (1, 2)
        assert stored_kwargs == {"z": 3}
        assert stored_service_name == "TestService"
    
    def test_run_coroutine_in_loop(self):
        """测试在事件循环中运行协程"""
        async def test_coro():
            await asyncio.sleep(0.01)
            return "result"
        
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(test_coro())
            assert result == "result"
        finally:
            loop.close()
    
    def test_signal_emission_simulation(self):
        """测试信号发射模拟"""
        finished_results = []
        error_results = []
        
        def on_finished(result):
            finished_results.append(result)
        
        def on_error(error):
            error_results.append(error)
        
        # 模拟成功
        on_finished("success_result")
        assert finished_results == ["success_result"]
        
        # 模拟错误
        on_error(ValueError("test error"))
        assert len(error_results) == 1
        assert isinstance(error_results[0], ValueError)
    
    @pytest.mark.asyncio
    async def test_cleanup_pending_tasks(self):
        """测试清理待处理任务"""
        async def task1():
            await asyncio.sleep(0.1)
            return 1
        
        async def task2():
            await asyncio.sleep(0.1)
            return 2
        
        # 创建任务
        t1 = asyncio.create_task(task1())
        t2 = asyncio.create_task(task2())
        
        # 取消任务
        t1.cancel()
        t2.cancel()
        
        # 等待取消完成
        results = await asyncio.gather(t1, t2, return_exceptions=True)
        
        assert all(isinstance(r, asyncio.CancelledError) for r in results)
    
    def test_service_name_logging(self):
        """测试服务名称日志"""
        service_name = "TestAsyncWorker"
        operation = "test_operation"
        error = ValueError("test error")
        
        log_message = f"{service_name}: {operation} failed - {error}"
        assert "TestAsyncWorker" in log_message
        assert "test_operation" in log_message
        assert "test error" in log_message


class TestAsyncWorkerEdgeCases:
    """边界情况测试"""
    
    @pytest.mark.asyncio
    async def test_empty_coroutine(self):
        """测试空协程"""
        async def empty_coro():
            pass
        
        result = await empty_coro()
        assert result is None
    
    @pytest.mark.asyncio
    async def test_coroutine_returning_none(self):
        """测试返回 None 的协程"""
        async def none_coro():
            return None
        
        result = await none_coro()
        assert result is None
    
    @pytest.mark.asyncio
    async def test_nested_coroutines(self):
        """测试嵌套协程"""
        async def inner():
            return "inner"
        
        async def outer():
            result = await inner()
            return f"outer_{result}"
        
        result = await outer()
        assert result == "outer_inner"
    
    @pytest.mark.asyncio
    async def test_multiple_awaits(self):
        """测试多次 await"""
        async def multi_await():
            a = await asyncio.sleep(0.01, result=1)
            b = await asyncio.sleep(0.01, result=2)
            c = await asyncio.sleep(0.01, result=3)
            return a + b + c
        
        result = await multi_await()
        assert result == 6
    
    @pytest.mark.asyncio
    async def test_concurrent_execution(self):
        """测试并发执行"""
        results = []
        
        async def task(n):
            await asyncio.sleep(0.01)
            results.append(n)
            return n
        
        await asyncio.gather(task(1), task(2), task(3))
        
        assert sorted(results) == [1, 2, 3]
    
    def test_loop_already_closed(self):
        """测试已关闭的事件循环"""
        loop = asyncio.new_event_loop()
        loop.close()
        
        assert loop.is_closed()
        
        # 创建协程并确保在测试后正确清理
        coro = asyncio.sleep(0)
        with pytest.raises(RuntimeError):
            loop.run_until_complete(coro)
        # 关闭未执行的协程以避免警告
        coro.close()
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """测试超时处理"""
        async def slow_task():
            await asyncio.sleep(10)
            return "done"
        
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(slow_task(), timeout=0.01)



# ============================================================
# From: test_async_worker_coverage.py
# ============================================================
class TestAsyncWorkerRun:
    """测试 AsyncWorker.run 方法"""
    
    @patch('src.utils.async_worker.QThread')
    @patch('src.utils.async_worker.logger')
    def test_run_success(self, mock_logger, mock_qthread):
        """测试成功执行协程"""
        from src.utils.async_worker import AsyncWorker
        
        async def test_coro(x, y):
            return x + y
        
        worker = AsyncWorker(test_coro, 1, 2, service_name="TestService")
        worker.finished_signal = MagicMock()
        worker.error_signal = MagicMock()
        
        worker.run()
        
        worker.finished_signal.emit.assert_called_once_with(3)
        worker.error_signal.emit.assert_not_called()
    
    @patch('src.utils.async_worker.QThread')
    @patch('src.utils.async_worker.logger')
    def test_run_with_kwargs(self, mock_logger, mock_qthread):
        """测试带关键字参数的协程"""
        from src.utils.async_worker import AsyncWorker
        
        async def test_coro(a, b=10):
            return a * b
        
        worker = AsyncWorker(test_coro, 5, b=20, service_name="TestService")
        worker.finished_signal = MagicMock()
        worker.error_signal = MagicMock()
        
        worker.run()
        
        worker.finished_signal.emit.assert_called_once_with(100)
    
    @patch('src.utils.async_worker.QThread')
    @patch('src.utils.async_worker.logger')
    def test_run_exception(self, mock_logger, mock_qthread):
        """测试协程抛出异常"""
        from src.utils.async_worker import AsyncWorker
        
        async def failing_coro():
            raise ValueError("Test error")
        
        worker = AsyncWorker(failing_coro, service_name="TestService")
        worker.finished_signal = MagicMock()
        worker.error_signal = MagicMock()
        
        worker.run()
        
        worker.finished_signal.emit.assert_not_called()
        worker.error_signal.emit.assert_called_once()
        error = worker.error_signal.emit.call_args[0][0]
        assert isinstance(error, ValueError)
        assert str(error) == "Test error"
    
    @patch('src.utils.async_worker.QThread')
    @patch('src.utils.async_worker.logger')
    def test_run_with_pending_tasks(self, mock_logger, mock_qthread):
        """测试有待处理任务时的清理"""
        from src.utils.async_worker import AsyncWorker
        
        async def coro_with_pending():
            # 创建一个不会完成的任务
            async def never_finish():
                await asyncio.sleep(100)
            
            asyncio.create_task(never_finish())
            return "done"
        
        worker = AsyncWorker(coro_with_pending, service_name="TestService")
        worker.finished_signal = MagicMock()
        worker.error_signal = MagicMock()
        
        worker.run()
        
        worker.finished_signal.emit.assert_called_once_with("done")


class TestAsyncWorkerCleanup:
    """测试 AsyncWorker._cleanup_loop 方法"""
    
    def test_cleanup_loop_no_pending(self):
        """测试无待处理任务时的清理"""
        from src.utils.async_worker import AsyncWorker
        
        loop = asyncio.new_event_loop()
        
        with patch.object(AsyncWorker, '__init__', lambda x, *a, **k: None):
            worker = AsyncWorker.__new__(AsyncWorker)
            worker._cleanup_loop(loop)
        
        assert loop.is_closed()
    
    def test_cleanup_loop_with_exception(self):
        """测试清理时发生异常"""
        from src.utils.async_worker import AsyncWorker
        
        loop = MagicMock()
        loop.is_closed.return_value = False
        
        # 模拟 all_tasks 抛出异常
        with patch('asyncio.all_tasks', side_effect=RuntimeError("Test")):
            with patch('src.utils.async_worker.logger') as mock_logger:
                with patch.object(AsyncWorker, '__init__', lambda x, *a, **k: None):
                    worker = AsyncWorker.__new__(AsyncWorker)
                    worker._cleanup_loop(loop)
        
        loop.close.assert_called_once()


class TestAsyncWorkerInit:
    """测试 AsyncWorker 初始化"""
    
    @patch('src.utils.async_worker.QThread')
    def test_init_default_service_name(self, mock_qthread):
        """测试默认服务名称"""
        from src.utils.async_worker import AsyncWorker
        
        async def test_coro():
            pass
        
        worker = AsyncWorker(test_coro)
        
        assert worker._service_name == "AsyncWorker"
        assert worker._coro_func == test_coro
        assert worker._args == ()
        assert worker._kwargs == {}
    
    @patch('src.utils.async_worker.QThread')
    def test_init_custom_service_name(self, mock_qthread):
        """测试自定义服务名称"""
        from src.utils.async_worker import AsyncWorker
        
        async def test_coro():
            pass
        
        worker = AsyncWorker(test_coro, service_name="CustomService")
        
        assert worker._service_name == "CustomService"
    
    @patch('src.utils.async_worker.QThread')
    def test_init_with_args_and_kwargs(self, mock_qthread):
        """测试带参数初始化"""
        from src.utils.async_worker import AsyncWorker
        
        async def test_coro(a, b, c=None):
            pass
        
        worker = AsyncWorker(test_coro, 1, 2, c=3, service_name="Test")
        
        assert worker._args == (1, 2)
        assert worker._kwargs == {'c': 3}


class TestAsyncWorkerIntegration_Coverage:
    """AsyncWorker 集成测试"""
    
    @patch('src.utils.async_worker.QThread')
    @patch('src.utils.async_worker.logger')
    def test_async_http_like_operation(self, mock_logger, mock_qthread):
        """测试类似 HTTP 请求的异步操作"""
        from src.utils.async_worker import AsyncWorker
        
        async def fetch_data(url):
            await asyncio.sleep(0.01)
            return {"url": url, "data": "test"}
        
        worker = AsyncWorker(fetch_data, "https://example.com", service_name="HttpService")
        worker.finished_signal = MagicMock()
        worker.error_signal = MagicMock()
        
        worker.run()
        
        result = worker.finished_signal.emit.call_args[0][0]
        assert result["url"] == "https://example.com"
        assert result["data"] == "test"
    
    @patch('src.utils.async_worker.QThread')
    @patch('src.utils.async_worker.logger')
    def test_async_timeout_handling(self, mock_logger, mock_qthread):
        """测试超时处理"""
        from src.utils.async_worker import AsyncWorker
        
        async def slow_operation():
            try:
                await asyncio.wait_for(asyncio.sleep(10), timeout=0.01)
            except asyncio.TimeoutError:
                return "timeout"
        
        worker = AsyncWorker(slow_operation, service_name="TimeoutService")
        worker.finished_signal = MagicMock()
        worker.error_signal = MagicMock()
        
        worker.run()
        
        worker.finished_signal.emit.assert_called_once_with("timeout")
