def format_duration(milliseconds: int) -> str:
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
