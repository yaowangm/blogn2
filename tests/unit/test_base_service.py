import pytest
from unittest.mock import AsyncMock, MagicMock
from src.services.base_service import BaseService


class TestBaseService:
    """BaseService单元测试类"""
    
    @pytest.fixture
    def mock_repository1(self):
        """模拟仓库1"""
        return MagicMock()
    
    @pytest.fixture
    def mock_repository2(self):
        """模拟仓库2"""
        return MagicMock()
    
    @pytest.fixture
    def mock_session(self):
        """模拟数据库会话"""
        return AsyncMock()
    
    @pytest.fixture
    def base_service(self, mock_repository1, mock_repository2):
        """创建BaseService实例"""
        return BaseService(mock_repository1, mock_repository2)
    
    @pytest.mark.unit
    def test_init(self, mock_repository1, mock_repository2):
        """测试BaseService初始化"""
        service = BaseService(mock_repository1, mock_repository2)
        
        assert len(service.repositories) == 2
        assert service.repositories[0] == mock_repository1
        assert service.repositories[1] == mock_repository2
    
    @pytest.mark.unit
    def test_init_no_repositories(self):
        """测试BaseService初始化时无仓库"""
        service = BaseService()
        
        assert len(service.repositories) == 0
    
    @pytest.mark.unit
    def test_init_single_repository(self, mock_repository1):
        """测试BaseService初始化时单个仓库"""
        service = BaseService(mock_repository1)
        
        assert len(service.repositories) == 1
        assert service.repositories[0] == mock_repository1
    
    @pytest.mark.unit
    def test_create_with_session(self, mock_session):
        """测试使用会话创建服务实例"""
        class MockRepository1:
            def __init__(self, session):
                self.session = session
        
        class MockRepository2:
            def __init__(self, session):
                self.session = session
        
        service = BaseService.create_with_session(
            mock_session, 
            MockRepository1, 
            MockRepository2
        )
        
        assert len(service.repositories) == 2
        assert isinstance(service.repositories[0], MockRepository1)
        assert isinstance(service.repositories[1], MockRepository2)
        assert service.repositories[0].session == mock_session
        assert service.repositories[1].session == mock_session
    
    @pytest.mark.unit
    def test_create_with_session_no_repositories(self, mock_session):
        """测试使用会话创建服务实例时无仓库类"""
        service = BaseService.create_with_session(mock_session)
        
        assert len(service.repositories) == 0
    
    @pytest.mark.unit
    async def test_handle_async_operation_success(self, base_service):
        """测试处理异步操作成功"""
        async def mock_operation(arg1, arg2, kwarg1=None):
            return f"result: {arg1}, {arg2}, {kwarg1}"
        
        result = await base_service.handle_async_operation(
            mock_operation, 
            "value1", 
            "value2", 
            kwarg1="keyword_value"
        )
        
        assert result == "result: value1, value2, keyword_value"
    
    @pytest.mark.unit
    async def test_handle_async_operation_exception(self, base_service):
        """测试处理异步操作时发生异常"""
        async def mock_operation():
            raise ValueError("测试异常")
        
        with pytest.raises(ValueError, match="测试异常"):
            await base_service.handle_async_operation(mock_operation)
    
    @pytest.mark.unit
    async def test_handle_async_operation_no_args(self, base_service):
        """测试处理异步操作时无参数"""
        async def mock_operation():
            return "success"
        
        result = await base_service.handle_async_operation(mock_operation)
        
        assert result == "success"
    
    @pytest.mark.unit
    async def test_handle_async_operation_with_kwargs_only(self, base_service):
        """测试处理异步操作时只有关键字参数"""
        async def mock_operation(**kwargs):
            return kwargs
        
        result = await base_service.handle_async_operation(
            mock_operation, 
            key1="value1", 
            key2="value2"
        )
        
        assert result == {"key1": "value1", "key2": "value2"} 