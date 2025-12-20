"""数据提供者初始化模块

在应用启动时调用 init_providers() 注册所有数据提供者。
"""
from .provider_registry import get_registry
from .adapters.cenguigui_adapter import CenguiguiAdapter
from .adapters.uuuka_adapter import UuukaAdapter
from .adapters.duanju_search_adapter import DuanjuSearchAdapter
from ...utils.log_manager import get_logger

logger = get_logger()


def init_providers(timeout: int = 10000) -> None:
    """初始化并注册所有数据提供者
    
    Args:
        timeout: API 请求超时时间（毫秒）
    """
    registry = get_registry()
    
    # 注册默认提供者
    cenguigui = CenguiguiAdapter(timeout=timeout)
    registry.register(cenguigui)
    
    # 注册即刻短剧 API
    uuuka = UuukaAdapter(timeout=timeout)
    registry.register(uuuka)
    
    # 注册全网短剧 API（需要配置实际 API 地址）
    # 注意：默认 API 地址是占位符，需要用户配置实际地址
    duanju_search = DuanjuSearchAdapter(timeout=timeout)
    registry.register(duanju_search)
    
    logger.info(f"Initialized {registry.count} data provider(s)")


def get_provider_by_id(provider_id: str):
    """根据 ID 获取提供者"""
    return get_registry().get(provider_id)


def set_current_provider(provider_id: str) -> bool:
    """设置当前提供者"""
    return get_registry().set_current(provider_id)
