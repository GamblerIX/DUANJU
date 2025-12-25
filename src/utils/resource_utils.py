import os
import sys


def get_resource_path(relative_path: str) -> str:
    """
    Get the absolute path to a resource, works for dev and PyInstaller
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def get_app_path(relative_path: str = "") -> str:
    """Get path relative to the application executable (or script in dev)"""
    if getattr(sys, 'frozen', False):
        # PyInstaller/Nuitka 环境
        base_path = os.path.dirname(sys.executable)
    else:
        # 开发环境
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


def get_script_dir() -> str:
    """获取当前脚本所在目录，适用于所有环境"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))
