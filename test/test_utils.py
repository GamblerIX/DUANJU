"""工具函数单元测试

测试 src/core/utils/ 中的工具函数。
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.string_utils import (
    trim, is_blank, split, truncate, 
    sanitize_filename, format_file_size
)


class TestStringUtils:
    """字符串工具函数测试"""
    
    class TestTrim:
        """trim 函数测试"""
        
        def test_trim_whitespace(self):
            """测试去除空白字符"""
            assert trim("  hello  ") == "hello"
            assert trim("\t\nhello\n\t") == "hello"
        
        def test_trim_empty_string(self):
            """测试空字符串"""
            assert trim("") == ""
            assert trim("   ") == ""
    
    class TestIsBlank:
        """is_blank 函数测试"""
        
        def test_is_blank_none(self):
            """测试 None 值"""
            assert is_blank(None) is True
        
        def test_is_blank_empty(self):
            """测试空字符串"""
            assert is_blank("") is True
            assert is_blank("   ") is True
            assert is_blank("\t\n") is True
        
        def test_is_blank_not_blank(self):
            """测试非空字符串"""
            assert is_blank("hello") is False
            assert is_blank("  hello  ") is False
    
    class TestSplit:
        """split 函数测试"""
        
        def test_split_default_delimiter(self):
            """测试默认分隔符"""
            result = split("a, b, c")
            assert result == ["a", "b", "c"]
        
        def test_split_custom_delimiter(self):
            """测试自定义分隔符"""
            result = split("a|b|c", "|")
            assert result == ["a", "b", "c"]
        
        def test_split_empty_parts(self):
            """测试空部分被过滤"""
            result = split("a,,b,  ,c")
            assert result == ["a", "b", "c"]
        
        def test_split_empty_string(self):
            """测试空字符串"""
            result = split("")
            assert result == []
    
    class TestTruncate:
        """truncate 函数测试"""
        
        def test_truncate_short_string(self):
            """测试短字符串不截断"""
            assert truncate("hello", 10) == "hello"
        
        def test_truncate_long_string(self):
            """测试长字符串截断"""
            assert truncate("hello world", 8) == "hello..."
        
        def test_truncate_custom_suffix(self):
            """测试自定义后缀"""
            assert truncate("hello world", 8, "..") == "hello .."
        
        def test_truncate_exact_length(self):
            """测试刚好等于最大长度"""
            assert truncate("hello", 5) == "hello"
    
    class TestSanitizeFilename:
        """sanitize_filename 函数测试"""
        
        def test_sanitize_illegal_chars(self):
            """测试移除非法字符"""
            assert sanitize_filename('file<>:"/\\|?*.txt') == "file_________.txt"
        
        def test_sanitize_normal_filename(self):
            """测试正常文件名不变"""
            assert sanitize_filename("normal_file.txt") == "normal_file.txt"
        
        def test_sanitize_chinese_filename(self):
            """测试中文文件名"""
            assert sanitize_filename("测试文件.txt") == "测试文件.txt"
    
    class TestFormatFileSize:
        """format_file_size 函数测试"""
        
        def test_format_bytes(self):
            """测试字节格式化"""
            assert format_file_size(500) == "500.0 B"
        
        def test_format_kilobytes(self):
            """测试 KB 格式化"""
            assert format_file_size(1024) == "1.0 KB"
            assert format_file_size(1536) == "1.5 KB"
        
        def test_format_megabytes(self):
            """测试 MB 格式化"""
            assert format_file_size(1024 * 1024) == "1.0 MB"
            assert format_file_size(1024 * 1024 * 5) == "5.0 MB"
        
        def test_format_gigabytes(self):
            """测试 GB 格式化"""
            assert format_file_size(1024 * 1024 * 1024) == "1.0 GB"
        
        def test_format_terabytes(self):
            """测试 TB 格式化"""
            assert format_file_size(1024 * 1024 * 1024 * 1024) == "1.0 TB"

