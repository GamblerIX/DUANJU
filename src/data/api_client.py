"""API 客户端实现

This module provides an async HTTP client for communicating with the drama API.
Uses aiohttp for async requests with configurable timeout.
"""
from typing import Dict, Optional, Protocol
import aiohttp
import asyncio

from ..core.models import ApiResponse
from ..utils.log_manager import get_logger

logger = get_logger()


class IApiClient(Protocol):
    """API 客户端接口协议"""
    
    async def get(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, str]] = None
    ) -> ApiResponse:
        """执行异步 GET 请求"""
        ...
    
    def set_timeout(self, milliseconds: int) -> None:
        """设置请求超时时间"""
        ...


class ApiClient:
    """基于 aiohttp 的 API 客户端实现"""
    
    DEFAULT_BASE_URL = "https://api.cenguigui.cn/api/duanju/api.php"
    DEFAULT_TIMEOUT = 10000  # 毫秒
    
    def __init__(
        self, 
        base_url: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT
    ):
        self._base_url = base_url or self.DEFAULT_BASE_URL
        self._timeout = timeout
    
    def _create_connector(self) -> aiohttp.TCPConnector:
        """创建新的 TCP 连接器"""
        return aiohttp.TCPConnector(force_close=True)
    
    def _create_session(self, loop: asyncio.AbstractEventLoop) -> aiohttp.ClientSession:
        """创建新的 HTTP 会话"""
        timeout = aiohttp.ClientTimeout(total=self._timeout / 1000)
        connector = self._create_connector()
        return aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            connector_owner=True
        )
    
    async def get(
        self, 
        endpoint: str = "",
        params: Optional[Dict[str, str]] = None
    ) -> ApiResponse:
        """执行异步 GET 请求"""
        url = self._base_url
        
        logger.debug(f"HTTP GET: {url} | Params: {params}")
        
        loop = asyncio.get_running_loop()
        session = self._create_session(loop)
        
        try:
            async with session:
                try:
                    async with session.get(url, params=params) as response:
                        body = await response.text()
                        success = 200 <= response.status < 300
                        logger.debug(f"HTTP Response: {response.status} | Success: {success}")
                        return ApiResponse(
                            status_code=response.status,
                            body=body,
                            success=success
                        )
                except asyncio.TimeoutError:
                    logger.debug(f"HTTP Timeout: {url}")
                    return ApiResponse(
                        status_code=0,
                        body="",
                        error="请求超时",
                        success=False
                    )
                except aiohttp.ClientError as e:
                    logger.debug(f"HTTP Error: {url} | {type(e).__name__}: {e}")
                    return ApiResponse(
                        status_code=0,
                        body="",
                        error=str(e),
                        success=False
                    )
        except Exception as e:
            logger.exception(f"Unexpected HTTP error: {url}")
            return ApiResponse(
                status_code=0,
                body="",
                error=str(e),
                success=False
            )
    
    def set_timeout(self, milliseconds: int) -> None:
        """设置请求超时时间"""
        self._timeout = max(1000, min(60000, milliseconds))
        logger.debug(f"API timeout set to {self._timeout}ms")
    
    def set_base_url(self, url: str) -> None:
        """设置基础 URL"""
        self._base_url = url
    
    @property
    def base_url(self) -> str:
        return self._base_url
    
    @property
    def timeout(self) -> int:
        return self._timeout
    
    async def close(self) -> None:
        """关闭 HTTP 会话（保留兼容性）"""
        pass
