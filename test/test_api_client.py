"""API 客户端测试

测试 src/data/api/api_client.py 中的 API 客户端实现。
"""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.api_client import ApiClient
from src.core.models import ApiResponse


class TestApiClient:
    """ApiClient 测试"""
    
    def test_init_default_values(self):
        """测试默认初始化值"""
        client = ApiClient()
        assert client.base_url == ApiClient.DEFAULT_BASE_URL
        assert client.timeout == ApiClient.DEFAULT_TIMEOUT
    
    def test_init_custom_values(self):
        """测试自定义初始化值"""
        client = ApiClient(
            base_url="https://custom.api.com",
            timeout=5000
        )
        assert client.base_url == "https://custom.api.com"
        assert client.timeout == 5000
    
    def test_set_timeout(self):
        """测试设置超时时间"""
        client = ApiClient()
        client.set_timeout(5000)
        assert client.timeout == 5000
    
    def test_set_timeout_min_limit(self):
        """测试超时时间最小限制"""
        client = ApiClient()
        client.set_timeout(100)  # 小于最小值
        assert client.timeout == 1000  # 应该被限制为 1000
    
    def test_set_timeout_max_limit(self):
        """测试超时时间最大限制"""
        client = ApiClient()
        client.set_timeout(100000)  # 大于最大值
        assert client.timeout == 60000  # 应该被限制为 60000
    
    def test_set_base_url(self):
        """测试设置基础 URL"""
        client = ApiClient()
        client.set_base_url("https://new.api.com")
        assert client.base_url == "https://new.api.com"
    
    @pytest.mark.asyncio
    async def test_get_success(self):
        """测试成功的 GET 请求"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            # 设置 mock
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value='{"code": 200}')
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            
            mock_session = MagicMock()
            mock_session.get = MagicMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            
            mock_session_class.return_value = mock_session
            
            client = ApiClient()
            response = await client.get(params={"name": "test"})
            
            assert response.status_code == 200
            assert response.success is True
            assert response.body == '{"code": 200}'
    
    @pytest.mark.asyncio
    async def test_get_timeout(self):
        """测试请求超时"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session.get = MagicMock(side_effect=asyncio.TimeoutError())
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            
            mock_session_class.return_value = mock_session
            
            client = ApiClient()
            response = await client.get()
            
            assert response.success is False
            assert response.error == "请求超时"
    
    @pytest.mark.asyncio
    async def test_close(self):
        """测试关闭客户端"""
        client = ApiClient()
        # close 方法应该不抛出异常
        await client.close()

