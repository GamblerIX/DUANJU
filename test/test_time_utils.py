"""时间工具测试

测试 src/core/utils/time_utils.py 中的时间处理功能。
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.time_utils import format_duration, parse_duration


class TestFormatDuration:
    """format_duration 测试"""
    
    def test_format_seconds_only(self):
        """测试只有秒"""
        assert format_duration(30000) == "00:30"
        assert format_duration(59000) == "00:59"
    
    def test_format_minutes_and_seconds(self):
        """测试分钟和秒"""
        assert format_duration(60000) == "01:00"
        assert format_duration(90000) == "01:30"
        assert format_duration(150000) == "02:30"
        assert format_duration(599000) == "09:59"
    
    def test_format_hours(self):
        """测试小时"""
        assert format_duration(3600000) == "01:00:00"
        assert format_duration(3661000) == "01:01:01"
        assert format_duration(7200000) == "02:00:00"
    
    def test_format_zero(self):
        """测试零"""
        assert format_duration(0) == "00:00"
    
    def test_format_negative(self):
        """测试负数"""
        assert format_duration(-1000) == "00:00"
        assert format_duration(-100000) == "00:00"
    
    def test_format_large_value(self):
        """测试大值"""
        # 10小时
        assert format_duration(36000000) == "10:00:00"
        # 99小时59分59秒
        assert format_duration(359999000) == "99:59:59"
    
    def test_format_milliseconds_precision(self):
        """测试毫秒精度（向下取整）"""
        assert format_duration(1500) == "00:01"  # 1.5秒 -> 1秒
        assert format_duration(999) == "00:00"   # 0.999秒 -> 0秒


class TestParseDuration:
    """parse_duration 测试"""
    
    def test_parse_minutes_seconds(self):
        """测试解析分:秒格式"""
        assert parse_duration("00:30") == 30000
        assert parse_duration("01:00") == 60000
        assert parse_duration("02:30") == 150000
        assert parse_duration("59:59") == 3599000
    
    def test_parse_hours_minutes_seconds(self):
        """测试解析时:分:秒格式"""
        assert parse_duration("01:00:00") == 3600000
        assert parse_duration("01:01:01") == 3661000
        assert parse_duration("10:30:45") == 37845000
    
    def test_parse_zero(self):
        """测试解析零"""
        assert parse_duration("00:00") == 0
        assert parse_duration("00:00:00") == 0
    
    def test_parse_invalid_format(self):
        """测试无效格式"""
        assert parse_duration("invalid") == -1
        assert parse_duration("1:2:3:4") == -1
        assert parse_duration("abc:def") == -1
        assert parse_duration("") == -1
        assert parse_duration("12") == -1
    
    def test_parse_negative_values(self):
        """测试负值"""
        assert parse_duration("-01:00") == -1
        assert parse_duration("01:-30") == -1
    
    def test_parse_single_digit(self):
        """测试单位数"""
        assert parse_duration("1:30") == 90000
        assert parse_duration("1:1:1") == 3661000


class TestDurationRoundtrip:
    """时间格式化往返测试"""
    
    def test_roundtrip_minutes_seconds(self):
        """测试分:秒往返"""
        original = 150000  # 2:30
        formatted = format_duration(original)
        parsed = parse_duration(formatted)
        assert parsed == original
    
    def test_roundtrip_hours(self):
        """测试小时往返"""
        original = 3661000  # 1:01:01
        formatted = format_duration(original)
        parsed = parse_duration(formatted)
        assert parsed == original
    
    def test_roundtrip_various_values(self):
        """测试各种值往返"""
        test_values = [
            0,
            1000,
            60000,
            3600000,
            7261000,
            36000000,
        ]
        
        for value in test_values:
            formatted = format_duration(value)
            parsed = parse_duration(formatted)
            assert parsed == value, f"Failed for {value}: {formatted} -> {parsed}"

