"""DuanjuApp Debug Version - Application Entry Point

This is the debug version with full logging, detailed error messages,
and development utilities enabled.
"""
import sys
import os
import signal
import shutil
import traceback
import atexit

# 最早期的调试输出 - 写入文件以便在 PyAppify 环境中查看
def _write_debug_log(msg: str):
    """写入调试日志到文件"""
    try:
        log_path = os.path.join(os.getcwd(), "startup_debug.log")
        with open(log_path, "a", encoding="utf-8") as f:
            import datetime
            f.write(f"[{datetime.datetime.now()}] {msg}\n")
    except:
        pass

_write_debug_log(f"=== Application Starting ===")
_write_debug_log(f"Python: {sys.version}")
_write_debug_log(f"Executable: {sys.executable}")
_write_debug_log(f"CWD: {os.getcwd()}")
_write_debug_log(f"__file__: {__file__ if '__file__' in dir() else 'N/A'}")
_write_debug_log(f"sys.path: {sys.path[:5]}")

# 检测 PyAppify 环境并修复 GUI 显示问题
def _fix_pyappify_gui():
    """修复 PyAppify 环境下 GUI 无法显示的问题"""
    try:
        # 检测是否在 PyAppify 环境中
        cwd = os.getcwd()
        if "AppData" in cwd and "Local" in cwd:
            _write_debug_log("Detected PyAppify environment, applying GUI fixes...")
            
            # 设置 Qt 平台插件路径（如果需要）
            python_dir = os.path.join(cwd, "python")
            if os.path.exists(python_dir):
                # 查找 Qt 插件目录
                for root, dirs, files in os.walk(python_dir):
                    if "platforms" in dirs and "qwindows.dll" in os.listdir(os.path.join(root, "platforms")):
                        plugin_path = root
                        os.environ["QT_PLUGIN_PATH"] = plugin_path
                        _write_debug_log(f"Set QT_PLUGIN_PATH: {plugin_path}")
                        break
            
            # 确保 QT_QPA_PLATFORM 设置正确
            if "QT_QPA_PLATFORM" not in os.environ:
                os.environ["QT_QPA_PLATFORM"] = "windows"
                _write_debug_log("Set QT_QPA_PLATFORM: windows")
            
            return True
    except Exception as e:
        _write_debug_log(f"Error in _fix_pyappify_gui: {e}")
    return False

_fix_pyappify_gui()

# 确保 src 模块可以被导入
# 对于 PyAppify 环境，工作目录就是应用目录
app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# 同时确保当前工作目录也在路径中（PyAppify 环境）
cwd = os.getcwd()
if cwd not in sys.path:
    sys.path.insert(0, cwd)

_write_debug_log(f"Updated sys.path: {sys.path[:5]}")

# 早期错误捕获 - 在导入任何依赖之前
def early_error_handler(error_msg: str, details: str = ""):
    """早期错误处理，在 Qt 初始化之前使用"""
    _write_debug_log(f"EARLY ERROR: {error_msg}")
    _write_debug_log(f"Details: {details}")
    try:
        import ctypes
        full_msg = f"{error_msg}\n\n{details}" if details else error_msg
        ctypes.windll.user32.MessageBoxW(0, full_msg, "DuanjuApp 启动错误", 0x10)
    except:
        pass
    sys.exit(1)

try:
    _write_debug_log("Importing PySide6...")
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication, QMessageBox
    from PySide6.QtGui import QFont
    _write_debug_log(f"PySide6 imported successfully, version: {__import__('PySide6').__version__}")
except ImportError as e:
    early_error_handler(
        "无法加载 PySide6 模块",
        f"错误详情: {e}\n\n请确保 PySide6 已正确安装。"
    )

try:
    _write_debug_log("Importing log_manager...")
    # Initialize logging system (must be first)
    from src.utils.log_manager import logger
    _write_debug_log("log_manager imported successfully")
except ImportError as e:
    early_error_handler(
        "无法加载日志模块",
        f"错误详情: {e}\n\n工作目录: {os.getcwd()}\nPython路径: {sys.path[:3]}"
    )


def cleanup_on_exit():
    """程序退出时清理临时文件夹"""
    # 使用工作目录（PyAppify 环境）或脚本目录
    app_dir = os.getcwd()
    folders_to_delete = ["cache", "config"]
    
    for folder in folders_to_delete:
        folder_path = os.path.join(app_dir, folder)
        if os.path.exists(folder_path):
            try:
                shutil.rmtree(folder_path)
                print(f"已清理: {folder}")
            except Exception as e:
                print(f"清理 {folder} 失败: {e}")


def signal_handler(sig, frame):
    """处理 Ctrl+C 信号，优雅退出"""
    logger.info("收到退出信号，正在关闭应用...")
    cleanup_on_exit()
    app = QApplication.instance()
    if app:
        app.quit()
    sys.exit(0)


def show_error_dialog(title: str, message: str, details: str = "") -> None:
    """Display error dialog with detailed information for debugging."""
    try:
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        if details:
            msg_box.setDetailedText(details)
        msg_box.exec()
    except Exception:
        print(f"ERROR: {title}\n{message}\n{details}")


def main() -> int:
    """Application main entry point."""
    try:
        _write_debug_log("main() started")
        
        # 注册信号处理器，支持 Ctrl+C 优雅退出
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        _write_debug_log("Creating QApplication...")
        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("DuanjuApp")
        app.setApplicationVersion("1.0.0-debug")

        # 确保最后一个窗口关闭时应用退出
        app.setQuitOnLastWindowClosed(True)
        
        _write_debug_log(f"QApplication created, platform: {app.platformName()}")

        # Setup Qt exception hook for debugging
        logger.setup_qt_exception_hook()
        logger.info("Application initializing (Debug Mode)...")
        _write_debug_log("QApplication created, setting up UI...")

        # Set default font
        font = QFont("Microsoft YaHei", 10)
        app.setFont(font)

        # Create and show main window
        try:
            _write_debug_log("Importing MainWindow...")
            from src.ui.windows.main_window import MainWindow
            _write_debug_log("Creating MainWindow instance...")
            logger.debug("Creating main window...")
            window = MainWindow()
            logger.debug("Main window created successfully")
            _write_debug_log(f"MainWindow created, geometry: {window.geometry()}")
            
            # 确保窗口可见
            window.setWindowFlags(window.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            window.show()
            window.setWindowFlags(window.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
            window.show()
            window.raise_()
            window.activateWindow()
            
            logger.info("Main window displayed")
            _write_debug_log(f"MainWindow shown, visible: {window.isVisible()}, geometry: {window.geometry()}")

            # Start initialization process
            window.start_initialization()
            _write_debug_log("Initialization started")
        except Exception as e:
            _write_debug_log(f"ERROR creating main window: {e}")
            _write_debug_log(traceback.format_exc())
            logger.critical(f"Failed to create main window: {e}", exc_info=True)
            show_error_dialog(
                "启动错误",
                "无法创建主窗口",
                traceback.format_exc()
            )
            return 1

        # Run application
        logger.info("Application started, entering event loop")
        _write_debug_log("Entering event loop...")
        exit_code = app.exec()
        _write_debug_log(f"Event loop exited with code: {exit_code}")
        logger.info(f"Application exiting with code: {exit_code}")

        # 确保所有线程都已停止
        app.closeAllWindows()
        
        # 清理临时文件夹
        cleanup_on_exit()

        return exit_code

    except Exception as e:
        _write_debug_log(f"FATAL ERROR: {e}")
        _write_debug_log(traceback.format_exc())
        logger.critical(f"Fatal error during startup: {e}", exc_info=True)
        show_error_dialog(
            "致命错误",
            f"应用启动失败: {e}",
            traceback.format_exc()
        )
        return 1


if __name__ == "__main__":
    # 注册退出时清理函数
    atexit.register(cleanup_on_exit)
    
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("用户中断，退出应用")
        cleanup_on_exit()
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Unhandled exception in main: {e}", exc_info=True)
        cleanup_on_exit()
        sys.exit(1)
