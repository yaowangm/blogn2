"""
全局统计服务单元测试

测试GlobalStatsService类的各种统计管理功能
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.services.global_stats_service import GlobalStatsService
from src.models.glovar import Glovar


class TestGlobalStatsService:
    """全局统计服务测试类"""

    @pytest.fixture
    def mock_session(self):
        """模拟数据库会话"""
        return AsyncMock()

    @pytest.fixture
    def stats_service(self, mock_session):
        """创建统计服务实例"""
        return GlobalStatsService(mock_session)

    @pytest.fixture
    def sample_glovar_records(self):
        """示例glovar记录"""
        return [
            Glovar(varname="usercount", varvalue=100),
            Glovar(varname="projectcount", varvalue=50),
            Glovar(varname="projectitemcount", varvalue=200)
        ]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_stat_value_existing(self, stats_service, mock_session, sample_glovar_records):
        """测试获取已存在的统计值"""
        # 准备测试数据
        mock_result = MagicMock()
        mock_result.first.return_value = sample_glovar_records[0]  # usercount=100
        mock_session.exec.return_value = mock_result
        
        # 执行测试
        result = await stats_service.get_stat_value("usercount")
        
        # 验证结果
        assert result == 100
        mock_session.exec.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_stat_value_not_existing(self, stats_service, mock_session):
        """测试获取不存在的统计值"""
        # 准备测试数据
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result
        
        # 执行测试
        result = await stats_service.get_stat_value("nonexistent")
        
        # 验证结果
        assert result == 0
        mock_session.exec.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_stat_value_none_value(self, stats_service, mock_session):
        """测试获取值为None的统计值"""
        # 准备测试数据
        glovar_record = Glovar(varname="testcount", varvalue=None)
        mock_result = MagicMock()
        mock_result.first.return_value = glovar_record
        mock_session.exec.return_value = mock_result
        
        # 执行测试
        result = await stats_service.get_stat_value("testcount")
        
        # 验证结果
        assert result == 0
        mock_session.exec.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_set_stat_value_update_existing(self, stats_service, mock_session, sample_glovar_records):
        """测试更新已存在的统计值"""
        # 准备测试数据
        mock_result = MagicMock()
        mock_result.first.return_value = sample_glovar_records[0]  # usercount=100
        mock_session.exec.return_value = mock_result
        mock_session.commit.return_value = None
        
        # 执行测试
        result = await stats_service.set_stat_value("usercount", 150)
        
        # 验证结果
        assert result is True
        mock_session.exec.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_set_stat_value_create_new(self, stats_service, mock_session):
        """测试创建新的统计值"""
        # 准备测试数据
        mock_result = MagicMock()
        mock_result.first.return_value = None  # 记录不存在
        mock_result.rowcount = 0  # 更新没有影响任何行
        mock_session.exec.return_value = mock_result
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        
        # 执行测试
        result = await stats_service.set_stat_value("newcount", 75)
        
        # 验证结果
        assert result is True
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_set_stat_value_error(self, stats_service, mock_session):
        """测试设置统计值时发生错误"""
        # 准备测试数据
        mock_session.exec.side_effect = Exception("数据库错误")
        
        # 执行测试
        result = await stats_service.set_stat_value("testcount", 100)
        
        # 验证结果
        assert result is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_increment_stat_success(self, stats_service, mock_session, sample_glovar_records):
        """测试成功增加统计值"""
        # 准备测试数据
        mock_result = MagicMock()
        mock_result.first.return_value = sample_glovar_records[0]  # usercount=100
        mock_result.rowcount = 1  # 更新了一行
        mock_session.exec.return_value = mock_result
        mock_session.commit.return_value = None
        
        # 执行测试
        result = await stats_service.increment_stat("usercount", 10)
        
        # 验证结果
        assert result is True
        # increment_stat会调用get_stat_value和set_stat_value，所以会有多次exec调用
        assert mock_session.exec.call_count >= 2
        mock_session.commit.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_increment_stat_create_new(self, stats_service, mock_session):
        """测试增加不存在的统计值（创建新记录）"""
        # 准备测试数据
        mock_result = MagicMock()
        mock_result.first.return_value = None  # 记录不存在
        mock_result.rowcount = 0  # 更新没有影响任何行
        mock_session.exec.return_value = mock_result
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        
        # 执行测试
        result = await stats_service.increment_stat("newcount", 5)
        
        # 验证结果
        assert result is True
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_decrement_stat_success(self, stats_service, mock_session, sample_glovar_records):
        """测试成功减少统计值"""
        # 准备测试数据
        mock_result = MagicMock()
        mock_result.first.return_value = sample_glovar_records[1]  # projectcount=50
        mock_result.rowcount = 1  # 更新了一行
        mock_session.exec.return_value = mock_result
        mock_session.commit.return_value = None
        
        # 执行测试
        result = await stats_service.decrement_stat("projectcount", 5)
        
        # 验证结果
        assert result is True
        # decrement_stat会调用get_stat_value和set_stat_value，所以会有多次exec调用
        assert mock_session.exec.call_count >= 2
        mock_session.commit.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_decrement_stat_below_zero(self, stats_service, mock_session, sample_glovar_records):
        """测试减少统计值到负数（应该设为0）"""
        # 准备测试数据
        mock_result = MagicMock()
        mock_result.first.return_value = sample_glovar_records[1]  # projectcount=50
        mock_result.rowcount = 1  # 更新了一行
        mock_session.exec.return_value = mock_result
        mock_session.commit.return_value = None
        
        # 执行测试 - 减少60，但当前只有50，应该设为0
        result = await stats_service.decrement_stat("projectcount", 60)
        
        # 验证结果
        assert result is True
        # decrement_stat会调用get_stat_value和set_stat_value，所以会有多次exec调用
        assert mock_session.exec.call_count >= 2
        mock_session.commit.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_all_stats(self, stats_service, mock_session, sample_glovar_records):
        """测试获取所有统计数据"""
        # 准备测试数据 - get_all_stats会为每个统计项调用get_stat_value
        call_count = 0
        def mock_exec_side_effect(statement):
            nonlocal call_count
            mock_result = MagicMock()
            # 按顺序返回不同的值
            if call_count == 0:
                mock_result.first.return_value = sample_glovar_records[0]  # usercount=100
            elif call_count == 1:
                mock_result.first.return_value = sample_glovar_records[1]  # projectcount=50
            elif call_count == 2:
                mock_result.first.return_value = sample_glovar_records[2]  # projectitemcount=200
            else:
                mock_result.first.return_value = None
            call_count += 1
            return mock_result
        
        mock_session.exec.side_effect = mock_exec_side_effect
        
        # 执行测试
        result = await stats_service.get_all_stats()
        
        # 验证结果
        expected = {
            "usercount": 100,
            "projectcount": 50,
            "projectitemcount": 200
        }
        assert result == expected
        assert mock_session.exec.call_count == 3  # 每个统计项调用一次

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_all_stats_empty(self, stats_service, mock_session):
        """测试获取空统计数据"""
        # 准备测试数据 - 所有统计项都不存在
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result
        
        # 执行测试
        result = await stats_service.get_all_stats()
        
        # 验证结果
        expected = {
            "usercount": 0,
            "projectcount": 0,
            "projectitemcount": 0
        }
        assert result == expected
        assert mock_session.exec.call_count == 3  # 每个统计项调用一次

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sync_stats_from_database(self, stats_service, mock_session):
        """测试从数据库同步统计数据"""
        # 准备测试数据 - sync_stats_from_database会查询实际数据并更新统计
        def mock_exec_side_effect(statement):
            mock_result = MagicMock()
            # 根据查询类型返回不同的值
            if 'count(User.id)' in str(statement):
                mock_result.first.return_value = 150  # 实际用户数
            elif 'count(Project.id)' in str(statement):
                mock_result.first.return_value = 75   # 实际项目数
            elif 'count(ProjectItem.id)' in str(statement):
                mock_result.first.return_value = 300  # 实际项目项数
            else:
                # 对于set_stat_value的查询
                mock_result.rowcount = 1
            return mock_result
        
        mock_session.exec.side_effect = mock_exec_side_effect
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        
        # 执行测试
        result = await stats_service.sync_stats_from_database()
        
        # 验证结果
        assert result is True
        # sync_stats_from_database会查询3次实际数据，然后为每个统计项调用set_stat_value
        assert mock_session.exec.call_count >= 6  # 3次查询 + 3次set_stat_value
        assert mock_session.commit.call_count == 3  # 每个统计项提交一次

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sync_stats_error(self, stats_service, mock_session):
        """测试同步统计数据时发生错误"""
        # 准备测试数据
        mock_session.exec.side_effect = Exception("数据库错误")
        
        # 执行测试
        result = await stats_service.sync_stats_from_database()
        
        # 验证结果
        assert result is False
