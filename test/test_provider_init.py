"""数据提供者初始化测试"""
import pytest
from unittest.mock import MagicMock, patch


class TestProviderInit:
    """提供者初始化测试"""
    
    @patch('src.data.providers.provider_init.get_registry')
    @patch('src.data.providers.provider_init.CenguiguiAdapter')
    @patch('src.data.providers.provider_init.UuukaAdapter')
    @patch('src.data.providers.provider_init.DuanjuSearchAdapter')
    def test_init_providers(self, mock_duanju, mock_uuuka, mock_cenguigui, mock_registry_func):
        """测试初始化提供者"""
        from src.data.providers.provider_init import init_providers
        
        mock_registry = MagicMock()
        mock_registry.count = 3
        mock_registry_func.return_value = mock_registry
        
        mock_cenguigui_instance = MagicMock()
        mock_cenguigui.return_value = mock_cenguigui_instance
        
        mock_uuuka_instance = MagicMock()
        mock_uuuka.return_value = mock_uuuka_instance
        
        mock_duanju_instance = MagicMock()
        mock_duanju.return_value = mock_duanju_instance
        
        init_providers(timeout=5000)
        
        # 验证适配器创建
        mock_cenguigui.assert_called_once_with(timeout=5000)
        mock_uuuka.assert_called_once_with(timeout=5000)
        mock_duanju.assert_called_once_with(timeout=5000)
        
        # 验证注册
        assert mock_registry.register.call_count == 3
    
    @patch('src.data.providers.provider_init.get_registry')
    @patch('src.data.providers.provider_init.CenguiguiAdapter')
    @patch('src.data.providers.provider_init.UuukaAdapter')
    @patch('src.data.providers.provider_init.DuanjuSearchAdapter')
    def test_init_providers_default_timeout(self, mock_duanju, mock_uuuka, mock_cenguigui, mock_registry_func):
        """测试默认超时初始化"""
        from src.data.providers.provider_init import init_providers
        
        mock_registry = MagicMock()
        mock_registry.count = 3
        mock_registry_func.return_value = mock_registry
        
        init_providers()
        
        mock_cenguigui.assert_called_once_with(timeout=10000)
    
    @patch('src.data.providers.provider_init.get_registry')
    def test_get_provider_by_id(self, mock_registry_func):
        """测试根据 ID 获取提供者"""
        from src.data.providers.provider_init import get_provider_by_id
        
        mock_registry = MagicMock()
        mock_provider = MagicMock()
        mock_registry.get.return_value = mock_provider
        mock_registry_func.return_value = mock_registry
        
        result = get_provider_by_id("cenguigui")
        
        mock_registry.get.assert_called_once_with("cenguigui")
        assert result == mock_provider
    
    @patch('src.data.providers.provider_init.get_registry')
    def test_get_provider_by_id_not_found(self, mock_registry_func):
        """测试获取不存在的提供者"""
        from src.data.providers.provider_init import get_provider_by_id
        
        mock_registry = MagicMock()
        mock_registry.get.return_value = None
        mock_registry_func.return_value = mock_registry
        
        result = get_provider_by_id("nonexistent")
        
        assert result is None
    
    @patch('src.data.providers.provider_init.get_registry')
    def test_set_current_provider_success(self, mock_registry_func):
        """测试设置当前提供者成功"""
        from src.data.providers.provider_init import set_current_provider
        
        mock_registry = MagicMock()
        mock_registry.set_current.return_value = True
        mock_registry_func.return_value = mock_registry
        
        result = set_current_provider("cenguigui")
        
        mock_registry.set_current.assert_called_once_with("cenguigui")
        assert result is True
    
    @patch('src.data.providers.provider_init.get_registry')
    def test_set_current_provider_failure(self, mock_registry_func):
        """测试设置当前提供者失败"""
        from src.data.providers.provider_init import set_current_provider
        
        mock_registry = MagicMock()
        mock_registry.set_current.return_value = False
        mock_registry_func.return_value = mock_registry
        
        result = set_current_provider("nonexistent")
        
        assert result is False
