"""
模型配置单元测试

测试 get_model_device、_resolve_model_path_to_snapshot 等，含 CUDA 架构与路径回退告警。
"""

import pytest
from unittest.mock import patch, MagicMock

import torch  # 先导入，以便 patch torch.cuda 在 get_model_device 内 import torch 时生效
from src.config.model import get_model_device, _resolve_model_path_to_snapshot


class TestGetModelDevice:
    """get_model_device 单元测试"""

    @pytest.mark.unit
    def test_auto_returns_cpu_when_cuda_unavailable(self):
        """device=auto 且 CUDA 不可用时返回 cpu"""
        mock_settings = MagicMock()
        mock_settings.device = "auto"
        with patch("src.config.model.model_settings", mock_settings):
            with patch("torch.cuda.is_available", return_value=False):
                assert get_model_device() == "cpu"

    @pytest.mark.unit
    def test_auto_returns_cpu_when_device_count_zero(self):
        """device=auto 且 device_count < 1 时返回 cpu，避免假定 device 0 存在"""
        mock_settings = MagicMock()
        mock_settings.device = "auto"
        with patch("src.config.model.model_settings", mock_settings):
            with patch("torch.cuda.is_available", return_value=True):
                with patch("torch.cuda.device_count", return_value=0):
                    assert get_model_device() == "cpu"

    @pytest.mark.unit
    def test_explicit_device_returned_unchanged(self):
        """非 auto 时直接返回配置的 device"""
        for dev in ("cuda", "cpu"):
            mock_settings = MagicMock()
            mock_settings.device = dev
            with patch("src.config.model.model_settings", mock_settings):
                assert get_model_device() == dev

    @pytest.mark.unit
    def test_auto_returns_cuda_when_arch_list_has_suffixed_entry(self):
        """device=auto 且 get_arch_list 仅含带后缀架构（如 sm_90a）时仍返回 cuda"""
        mock_settings = MagicMock()
        mock_settings.device = "auto"
        with patch("src.config.model.model_settings", mock_settings):
            with patch("torch.cuda.is_available", return_value=True):
                with patch("torch.cuda.device_count", return_value=1):
                    with patch("torch.cuda.get_device_capability", return_value=(9, 0)):
                        # 仅 sm_90a 无 sm_90 时，startswith 匹配仍应选 cuda
                        with patch("torch.cuda.get_arch_list", return_value=["sm_90a", "sm_89"]):
                            assert get_model_device() == "cuda"
