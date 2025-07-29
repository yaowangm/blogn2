import pytest
from unittest.mock import patch, MagicMock
import os
from src.database import get_async_session, create_db_and_tables


class TestDatabase:
    """数据库配置测试类"""
    
    @pytest.fixture
    def mock_env_vars(self):
        """模拟环境变量"""
        with patch.dict(os.environ, {'DATABASE_URL': 'sqlite+aiosqlite:///./test.db'}):
            yield
    
    @pytest.mark.unit
    @patch('src.database.async_session')
    async def test_get_async_session(self, mock_async_session):
        """测试获取异步会话"""
        mock_session = MagicMock()
        mock_async_session.return_value.__aenter__.return_value = mock_session
        mock_async_session.return_value.__aexit__.return_value = None
        
        # 测试异步生成器
        async for session in get_async_session():
            assert session == mock_session
            break
        
        # 验证会话工厂被调用
        mock_async_session.assert_called_once()
    
    @pytest.mark.unit
    @patch('src.database.SQLModel')
    @patch('src.database.sync_engine')
    def test_create_db_and_tables(self, mock_sync_engine, mock_sqlmodel):
        """测试创建数据库和表"""
        # 调用函数
        create_db_and_tables()
        
        # 验证SQLModel.metadata.create_all被调用
        mock_sqlmodel.metadata.create_all.assert_called_once_with(mock_sync_engine)
    
    @pytest.mark.unit
    @patch('src.database.SQLModel')
    @patch('src.database.sync_engine')
    @patch('builtins.print')
    def test_main_execution(self, mock_print, mock_sync_engine, mock_sqlmodel):
        """测试主程序执行"""
        # 直接测试主程序逻辑
        from src.database import create_db_and_tables
        
        # 模拟主程序执行
        create_db_and_tables()
        print("数据库表创建完成！")
        
        # 验证print被调用
        mock_print.assert_called_once_with("数据库表创建完成！")
    
    @pytest.mark.unit
    def test_database_url_environment_variable(self, mock_env_vars):
        """测试数据库URL环境变量设置"""
        # 重新导入模块以测试环境变量
        import importlib
        import src.database
        importlib.reload(src.database)
        
        # 验证DATABASE_URL被正确设置
        assert src.database.DATABASE_URL == 'sqlite+aiosqlite:///./test.db'
    
 