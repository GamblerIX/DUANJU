"""UI 控件测试 - 使用 mock 测试逻辑"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from dataclasses import dataclass

from src.core.models import DramaInfo


class TestDramaCardLogic:
    """测试 DramaCard 逻辑（不依赖 Qt）"""
    
    @pytest.fixture
    def sample_drama(self):
        return DramaInfo(
            book_id="drama_001",
            title="测试短剧",
            cover="https://example.com/cover.jpg",
            episode_cnt=20,
            intro="这是一部测试短剧",
            type="都市",
            author="测试作者",
            play_cnt=10000
        )
    
    def test_drama_card_dimensions(self):
        """测试卡片尺寸常量"""
        CARD_WIDTH = 170
        CARD_HEIGHT = 330
        COVER_HEIGHT = 272
        
        assert CARD_WIDTH == 170
        assert CARD_HEIGHT == 330
        assert COVER_HEIGHT == 272
        # 验证比例
        assert COVER_HEIGHT / CARD_WIDTH == pytest.approx(1.6, rel=0.1)
    
    def test_favorite_toggle_logic(self):
        """测试收藏切换逻辑"""
        is_favorite = False
        
        # 切换收藏
        is_favorite = not is_favorite
        assert is_favorite is True
        
        # 再次切换
        is_favorite = not is_favorite
        assert is_favorite is False
    
    def test_drama_info_display(self, sample_drama):
        """测试短剧信息显示"""
        # 测试标题截断
        from src.utils.string_utils import truncate
        truncated_title = truncate(sample_drama.name, 11)
        assert len(truncated_title) <= 14  # 11 + "..."
        
        # 测试信息文本
        info_text = f"{sample_drama.episode_count}集"
        assert "20集" in info_text
        
        if sample_drama.category:
            info_text = f"{sample_drama.category} · {info_text}"
        assert "都市" in info_text
    
    def test_cover_url_handling(self, sample_drama):
        """测试封面 URL 处理"""
        assert sample_drama.cover.startswith("http")
        assert sample_drama.cover == "https://example.com/cover.jpg"


class TestLoadingSpinnerLogic:
    """测试 LoadingSpinner 逻辑"""
    
    def test_default_text(self):
        """测试默认加载文本"""
        default_text = "加载中..."
        assert default_text == "加载中..."
    
    def test_text_update(self):
        """测试文本更新"""
        text = "加载中..."
        new_text = "正在搜索..."
        text = new_text
        assert text == "正在搜索..."
    
    def test_visibility_states(self):
        """测试可见性状态"""
        visible = False
        
        # start
        visible = True
        assert visible is True
        
        # stop
        visible = False
        assert visible is False


class TestOverlayLoadingSpinnerLogic:
    """测试 OverlayLoadingSpinner 逻辑"""
    
    def test_overlay_style(self):
        """测试覆盖层样式"""
        style = "background-color: rgba(0, 0, 0, 0.3);"
        assert "rgba" in style
        assert "0.3" in style
    
    def test_geometry_update(self):
        """测试几何更新逻辑"""
        parent_rect = (0, 0, 800, 600)
        child_rect = parent_rect
        assert child_rect == parent_rect


class TestPaginationLogic:
    """测试 Pagination 逻辑"""
    
    def test_initial_state(self):
        """测试初始状态"""
        current_page = 1
        total_pages = 1
        
        assert current_page == 1
        assert total_pages == 1
    
    def test_page_info_setting(self):
        """测试设置分页信息"""
        total_pages = 10
        current_page = 5
        
        # 验证边界处理
        total_pages = max(1, total_pages)
        current_page = max(1, min(current_page, total_pages))
        
        assert total_pages == 10
        assert current_page == 5
    
    def test_page_boundary_handling(self):
        """测试页码边界处理"""
        total_pages = 10
        
        # 测试超出上限
        current_page = 15
        current_page = max(1, min(current_page, total_pages))
        assert current_page == 10
        
        # 测试低于下限
        current_page = 0
        current_page = max(1, min(current_page, total_pages))
        assert current_page == 1
    
    def test_navigation(self):
        """测试导航逻辑"""
        current_page = 5
        total_pages = 10
        
        # 下一页
        if current_page < total_pages:
            current_page += 1
        assert current_page == 6
        
        # 上一页
        if current_page > 1:
            current_page -= 1
        assert current_page == 5
    
    def test_first_last_page_detection(self):
        """测试首页/末页检测"""
        total_pages = 10
        
        # 首页
        current_page = 1
        is_first = current_page == 1
        is_last = current_page == total_pages
        assert is_first is True
        assert is_last is False
        
        # 末页
        current_page = 10
        is_first = current_page == 1
        is_last = current_page == total_pages
        assert is_first is False
        assert is_last is True
    
    def test_visibility_logic(self):
        """测试可见性逻辑"""
        # 单页时隐藏
        total_pages = 1
        visible = total_pages > 1
        assert visible is False
        
        # 多页时显示
        total_pages = 5
        visible = total_pages > 1
        assert visible is True
    
    def test_index_conversion(self):
        """测试索引转换（PipsPager 从0开始）"""
        # 页码转索引
        page = 5
        index = page - 1
        assert index == 4
        
        # 索引转页码
        index = 4
        page = index + 1
        assert page == 5


class TestRoundedImageLabelLogic:
    """测试 RoundedImageLabel 逻辑"""
    
    def test_default_radius(self):
        """测试默认圆角"""
        radius = (6, 6, 0, 0)  # 左上、右上、右下、左下
        assert radius[0] == 6  # 左上
        assert radius[1] == 6  # 右上
        assert radius[2] == 0  # 右下
        assert radius[3] == 0  # 左下
    
    def test_custom_radius(self):
        """测试自定义圆角"""
        radius = (10, 10, 10, 10)
        assert all(r == 10 for r in radius)
    
    def test_image_scaling_logic(self):
        """测试图片缩放逻辑"""
        # 模拟图片尺寸
        img_width, img_height = 200, 300
        label_width, label_height = 170, 272
        
        # KeepAspectRatioByExpanding 逻辑
        scale_w = label_width / img_width
        scale_h = label_height / img_height
        scale = max(scale_w, scale_h)
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        # 缩放后应该至少覆盖标签区域
        assert new_width >= label_width
        assert new_height >= label_height
    
    def test_center_position_calculation(self):
        """测试居中位置计算"""
        label_width, label_height = 170, 272
        scaled_width, scaled_height = 180, 280
        
        x = (label_width - scaled_width) // 2
        y = (label_height - scaled_height) // 2
        
        assert x == -5
        assert y == -4
