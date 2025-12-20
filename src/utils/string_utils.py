"""字符串处理工具函数"""
from typing import List, Optional
import re


def trim(s: str) -> str:
    """去除字符串首尾空白字符"""
    return s.strip()


def is_blank(s: Optional[str]) -> bool:
    """检查字符串是否为空白（None、空字符串或仅包含空白字符）"""
    return s is None or s.strip() == ""


def split(s: str, delimiter: str = ",") -> List[str]:
    """分割字符串并去除每个部分的空白"""
    return [part.strip() for part in s.split(delimiter) if part.strip()]


def truncate(s: str, max_length: int, suffix: str = "...") -> str:
    """截断字符串到指定长度"""
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix


def sanitize_filename(filename: str) -> str:
    """清理文件名，移除非法字符"""
    illegal_chars = r'[<>:"/\\|?*]'
    return re.sub(illegal_chars, '_', filename)


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
