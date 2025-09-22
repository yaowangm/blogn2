"""
图片处理工具类单元测试
"""

import pytest
from unittest.mock import patch, MagicMock, mock_open
from PIL import Image
import tempfile
import os
from src.utils.image_utils import ImageProcessor


class TestImageProcessor:
    """图片处理工具类测试类"""

    @pytest.fixture
    def image_processor(self):
        """创建ImageProcessor实例"""
        return ImageProcessor()

    @pytest.fixture
    def sample_image_path(self):
        """创建示例图片文件"""
        # 创建一个临时的测试图片
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            # 创建一个简单的测试图片
            img = Image.new('RGB', (400, 300), color='red')
            img.save(tmp_file.name, 'JPEG')
            yield tmp_file.name
        # 清理临时文件
        try:
            os.unlink(tmp_file.name)
        except OSError:
            pass

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_resize_and_save_image_success(self, image_processor, sample_image_path):
        """测试图片resize和保存成功"""
        # 创建临时目标文件
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_target:
            target_path = tmp_target.name
        
        try:
            # 执行测试
            await image_processor.resize_and_save_image(
                source_path=sample_image_path,
                target_path=target_path,
                max_size=(200, 200)
            )
            
            # 验证目标文件存在
            assert os.path.exists(target_path)
            
            # 验证图片尺寸
            with Image.open(target_path) as resized_img:
                assert resized_img.size[0] <= 200
                assert resized_img.size[1] <= 200
                assert resized_img.format == 'JPEG'
        
        finally:
            # 清理临时文件
            try:
                os.unlink(target_path)
            except OSError:
                pass

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_resize_and_save_image_larger_than_max(self, image_processor, sample_image_path):
        """测试图片尺寸大于最大尺寸时的resize"""
        # 创建临时目标文件
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_target:
            target_path = tmp_target.name
        
        try:
            # 执行测试 - 原图400x300，最大尺寸200x200
            await image_processor.resize_and_save_image(
                source_path=sample_image_path,
                target_path=target_path,
                max_size=(200, 200)
            )
            
            # 验证目标文件存在
            assert os.path.exists(target_path)
            
            # 验证图片尺寸被正确缩放
            with Image.open(target_path) as resized_img:
                # 应该保持宽高比，所以宽度或高度应该等于200
                assert resized_img.size[0] == 200 or resized_img.size[1] == 200
                assert resized_img.size[0] <= 200
                assert resized_img.size[1] <= 200
        
        finally:
            # 清理临时文件
            try:
                os.unlink(target_path)
            except OSError:
                pass

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_resize_and_save_image_smaller_than_max(self, image_processor, sample_image_path):
        """测试图片尺寸小于最大尺寸时的resize"""
        # 创建临时目标文件
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_target:
            target_path = tmp_target.name
        
        try:
            # 执行测试 - 原图400x300，最大尺寸500x500
            await image_processor.resize_and_save_image(
                source_path=sample_image_path,
                target_path=target_path,
                max_size=(500, 500)
            )
            
            # 验证目标文件存在
            assert os.path.exists(target_path)
            
            # 验证图片尺寸保持不变（因为原图小于最大尺寸）
            with Image.open(target_path) as resized_img:
                assert resized_img.size == (400, 300)
        
        finally:
            # 清理临时文件
            try:
                os.unlink(target_path)
            except OSError:
                pass

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_resize_and_save_image_source_not_exists(self, image_processor):
        """测试源文件不存在时的异常处理"""
        # 执行测试并验证异常
        with pytest.raises(FileNotFoundError):
            await image_processor.resize_and_save_image(
                source_path="nonexistent_file.jpg",
                target_path="output.jpg",
                max_size=(200, 200)
            )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_resize_and_save_image_invalid_source(self, image_processor):
        """测试无效源文件时的异常处理"""
        # 创建一个无效的图片文件
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            tmp_file.write(b"invalid image data")
            invalid_path = tmp_file.name
        
        try:
            # 执行测试并验证异常
            from PIL import UnidentifiedImageError
            with pytest.raises(UnidentifiedImageError):
                await image_processor.resize_and_save_image(
                    source_path=invalid_path,
                    target_path="output.jpg",
                    max_size=(200, 200)
                )
        
        finally:
            # 清理临时文件
            try:
                os.unlink(invalid_path)
            except OSError:
                pass

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_resize_and_save_image_different_formats(self, image_processor):
        """测试不同图片格式的处理"""
        # 测试PNG格式
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_source:
            img = Image.new('RGB', (300, 200), color='blue')
            img.save(tmp_source.name, 'PNG')
            source_path = tmp_source.name
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_target:
            target_path = tmp_target.name
        
        try:
            # 执行测试
            await image_processor.resize_and_save_image(
                source_path=source_path,
                target_path=target_path,
                max_size=(150, 150)
            )
            
            # 验证目标文件存在且为JPEG格式
            assert os.path.exists(target_path)
            with Image.open(target_path) as resized_img:
                assert resized_img.format == 'JPEG'
                assert resized_img.size[0] <= 150
                assert resized_img.size[1] <= 150
        
        finally:
            # 清理临时文件
            try:
                os.unlink(source_path)
                os.unlink(target_path)
            except OSError:
                pass

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_resize_and_save_image_square_aspect_ratio(self, image_processor):
        """测试正方形图片的resize"""
        # 创建正方形图片
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_source:
            img = Image.new('RGB', (300, 300), color='green')
            img.save(tmp_source.name, 'JPEG')
            source_path = tmp_source.name
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_target:
            target_path = tmp_target.name
        
        try:
            # 执行测试
            await image_processor.resize_and_save_image(
                source_path=source_path,
                target_path=target_path,
                max_size=(100, 100)
            )
            
            # 验证目标文件存在
            assert os.path.exists(target_path)
            
            # 验证图片尺寸
            with Image.open(target_path) as resized_img:
                assert resized_img.size == (100, 100)  # 正方形应该保持正方形
        
        finally:
            # 清理临时文件
            try:
                os.unlink(source_path)
                os.unlink(target_path)
            except OSError:
                pass

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_resize_and_save_image_very_small_max_size(self, image_processor, sample_image_path):
        """测试非常小的最大尺寸"""
        # 创建临时目标文件
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_target:
            target_path = tmp_target.name
        
        try:
            # 执行测试 - 原图400x300，最大尺寸50x50
            await image_processor.resize_and_save_image(
                source_path=sample_image_path,
                target_path=target_path,
                max_size=(50, 50)
            )
            
            # 验证目标文件存在
            assert os.path.exists(target_path)
            
            # 验证图片尺寸被正确缩放
            with Image.open(target_path) as resized_img:
                assert resized_img.size[0] <= 50
                assert resized_img.size[1] <= 50
                # 应该保持宽高比
                assert abs(resized_img.size[0] / resized_img.size[1] - 400 / 300) < 0.1
        
        finally:
            # 清理临时文件
            try:
                os.unlink(target_path)
            except OSError:
                pass
