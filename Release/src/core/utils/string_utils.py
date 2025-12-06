from typing import List, Optional
import re


def trim(s: str) -> str:
    return s.strip()


def is_blank(s: Optional[str]) -> bool:
    return s is None or s.strip() == ""


def split(s: str, delimiter: str = ",") -> List[str]:
    return [part.strip() for part in s.split(delimiter) if part.strip()]


def truncate(s: str, max_length: int, suffix: str = "...") -> str:
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix


def sanitize_filename(filename: str) -> str:
    illegal_chars = r'[<>:"/\\|?*]'
    return re.sub(illegal_chars, '_', filename)


def format_file_size(size_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
