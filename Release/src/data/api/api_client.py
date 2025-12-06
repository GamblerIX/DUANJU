from typing import Dict, Optional, Protocol
import aiohttp
import asyncio
from ...core.models import ApiResponse


class IApiClient(Protocol):
    async def get(self, endpoint: str, params: Optional[Dict[str, str]] = None) -> ApiResponse: ...
    def set_timeout(self, milliseconds: int) -> None: ...


class ApiClient:
    DEFAULT_BASE_URL = "https://api.cenguigui.cn/api/duanju/api.php"
    DEFAULT_TIMEOUT = 10000
    
    def __init__(self, base_url: Optional[str] = None, timeout: int = DEFAULT_TIMEOUT):
        self._base_url = base_url or self.DEFAULT_BASE_URL
        self._timeout = timeout
    
    def _create_connector(self) -> aiohttp.TCPConnector:
        return aiohttp.TCPConnector(force_close=True)
    
    def _create_session(self, loop: asyncio.AbstractEventLoop) -> aiohttp.ClientSession:
        timeout = aiohttp.ClientTimeout(total=self._timeout / 1000)
        connector = self._create_connector()
        return aiohttp.ClientSession(timeout=timeout, connector=connector, connector_owner=True)
    
    async def get(self, endpoint: str = "", params: Optional[Dict[str, str]] = None) -> ApiResponse:
        url = self._base_url
        loop = asyncio.get_running_loop()
        session = self._create_session(loop)
        try:
            async with session:
                try:
                    async with session.get(url, params=params) as response:
                        body = await response.text()
                        success = 200 <= response.status < 300
                        return ApiResponse(status_code=response.status, body=body, success=success)
                except asyncio.TimeoutError:
                    return ApiResponse(status_code=0, body="", error="请求超时", success=False)
                except aiohttp.ClientError as e:
                    return ApiResponse(status_code=0, body="", error=str(e), success=False)
        except Exception as e:
            return ApiResponse(status_code=0, body="", error=str(e), success=False)
    
    def set_timeout(self, milliseconds: int) -> None:
        self._timeout = max(1000, min(60000, milliseconds))
    
    def set_base_url(self, url: str) -> None:
        self._base_url = url
    
    @property
    def base_url(self) -> str:
        return self._base_url
    
    @property
    def timeout(self) -> int:
        return self._timeout
    
    async def close(self) -> None:
        pass
