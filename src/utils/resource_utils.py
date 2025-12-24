import os
import sys


def is_pyappify_env() -> bool:
    """检测是否在 PyAppify 打包环境中运行"""
    # PyAppify 通常将应用安装在 AppData/Local/{AppName} 目录
    # 并且工作目录就是应用目录
    cwd = os.getcwd()
    # 检查是否在 AppData/Local 目录下
    if "AppData" in cwd and "Local" in cwd:
        # 检查是否存在 Python 环境目录（PyAppify 特征）
        python_dir = os.path.join(cwd, "python")
        if os.path.exists(python_dir):
            return True
    return False


def get_resource_path(relative_path: str) -> str:
    """
    Get the absolute path to a resource, works for dev, PyInstaller and PyAppify
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # PyAppify: 工作目录就是应用目录，资源在 src 子目录或当前目录
        if is_pyappify_env():
            # PyAppify 环境下，资源文件在工作目录
            base_path = os.getcwd()
            # 如果资源在 src 目录下，尝试从 src 目录查找
            src_path = os.path.join(base_path, "src", relative_path)
            if os.path.exists(src_path):
                return src_path
        else:
            base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def get_app_path(relative_path: str = "") -> str:
    """Get path relative to the application executable (or script in dev)"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 环境
        base_path = os.path.dirname(sys.executable)
    elif is_pyappify_env():
        # PyAppify 环境：工作目录就是应用目录
        base_path = os.getcwd()
    else:
        # 开发环境
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


def get_script_dir() -> str:
    """获取当前脚本所在目录，适用于所有环境"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    elif is_pyappify_env():
        return os.getcwd()
    else:
        return os.path.dirname(os.path.abspath(__file__))
