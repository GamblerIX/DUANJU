"""时间格式化工具函数"""


def format_duration(milliseconds: int) -> str:
    """
    格式化毫秒为时间字符串
    
    Args:
        milliseconds: 时间（毫秒）
        
    Returns:
        格式化字符串，小于1小时返回 "MM:SS"，否则返回 "HH:MM:SS"
        
    Examples:
        >>> format_duration(150000)
        '02:30'
        >>> format_duration(3661000)
        '01:01:01'
        >>> format_duration(-1000)
        '00:00'
    """
    if milliseconds < 0:
        milliseconds = 0
    
    total_seconds = milliseconds // 1000
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def parse_duration(time_str: str) -> int:
    """
    解析时间字符串为毫秒
    
    Args:
        time_str: 时间字符串，支持 "MM:SS" 或 "HH:MM:SS" 格式
        
    Returns:
        毫秒数，解析失败返回 -1
        
    Examples:
        >>> parse_duration('02:30')
        150000
        >>> parse_duration('01:01:01')
        3661000
        >>> parse_duration('invalid')
        -1
    """
    if not time_str:
        return -1
    
    parts = time_str.split(':')
    if len(parts) not in (2, 3):
        return -1
    
    try:
        parts_int = [int(p) for p in parts]
        if any(p < 0 for p in parts_int):
            return -1
            
        if len(parts_int) == 2:
            minutes, seconds = parts_int
            hours = 0
        else:
            hours, minutes, seconds = parts_int
            
        return ((hours * 3600) + (minutes * 60) + seconds) * 1000
    except ValueError:
        return -1
