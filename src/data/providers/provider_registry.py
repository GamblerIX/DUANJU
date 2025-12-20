"""数据提供者注册中心

管理所有已注册的数据提供者，支持动态切换数据源。
"""
from typing import Dict, Optional, Type, List
from .provider_base import IDataProvider, ProviderInfo
from ...utils.log_manager import get_logger

logger = get_logger()


class ProviderRegistry:
    """数据提供者注册中心（单例）"""
    
    _instance: Optional["ProviderRegistry"] = None
    
    def __new__(cls) -> "ProviderRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._providers: Dict[str, IDataProvider] = {}
            cls._instance._current_id: Optional[str] = None
        return cls._instance
    
    def register(self, provider: IDataProvider) -> None:
        """注册数据提供者"""
        provider_id = provider.info.id
        self._providers[provider_id] = provider
        logger.info(f"Provider registered: {provider_id} ({provider.info.name})")
        
        # 自动设置第一个为当前提供者
        if self._current_id is None:
            self._current_id = provider_id
    
    def unregister(self, provider_id: str) -> bool:
        """注销数据提供者"""
        if provider_id in self._providers:
            del self._providers[provider_id]
            if self._current_id == provider_id:
                self._current_id = next(iter(self._providers), None)
            return True
        return False
    
    def get(self, provider_id: str) -> Optional[IDataProvider]:
        """获取指定提供者"""
        return self._providers.get(provider_id)
    
    def get_current(self) -> Optional[IDataProvider]:
        """获取当前活动的提供者"""
        if self._current_id:
            return self._providers.get(self._current_id)
        return None
    
    def set_current(self, provider_id: str) -> bool:
        """设置当前活动的提供者"""
        if provider_id in self._providers:
            self._current_id = provider_id
            logger.info(f"Current provider set to: {provider_id}")
            return True
        return False
    
    def list_providers(self) -> List[ProviderInfo]:
        """列出所有已注册的提供者信息"""
        return [p.info for p in self._providers.values()]
    
    def list_provider_ids(self) -> List[str]:
        """列出所有提供者 ID"""
        return list(self._providers.keys())
    
    @property
    def current_id(self) -> Optional[str]:
        return self._current_id
    
    @property
    def count(self) -> int:
        return len(self._providers)


# 全局注册中心实例
_registry = ProviderRegistry()


def get_registry() -> ProviderRegistry:
    """获取全局注册中心"""
    return _registry


def get_current_provider() -> Optional[IDataProvider]:
    """快捷方法：获取当前提供者"""
    return _registry.get_current()
