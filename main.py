"""DuanjuApp - Application Entry Point"""
import sys
import os
import signal
import shutil
import traceback
import atexit

# 确保 src 模块可以被导入
app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# 早期错误捕获 - 在导入任何依赖之前
def early_error_handler(error_msg: str, details: str = ""):
    """早期错误处理，在 Qt 初始化之前使用"""
    try:
        import ctypes
        full_msg = f"{error_msg}\n\n{details}" if details else error_msg
        ctypes.windll.user32.MessageBoxW(0, full_msg, "DuanjuApp 启动错误", 0x10)
    except:
        pass
    sys.exit(1)

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication, QMessageBox
    from PySide6.QtGui import QFont
except ImportError as e:
    early_error_handler(
        "无法加载 PySide6 模块",
        f"错误详情: {e}\n\n请确保 PySide6 已正确安装。"
    )

try:
    from src.utils.log_manager import logger
except ImportError as e:
    early_error_handler(
        "无法加载日志模块",
        f"错误详情: {e}\n\n工作目录: {os.getcwd()}\nPython路径: {sys.path[:3]}"
    )


def cleanup_on_exit():
    """程序退出时清理临时文件夹"""
    app_dir = os.path.dirname(os.path.abspath(__file__))
    folders_to_delete = ["cache", "config"]
    
    for folder in folders_to_delete:
        folder_path = os.path.join(app_dir, folder)
        if os.path.exists(folder_path):
            try:
                shutil.rmtree(folder_path)
            except Exception:
                pass


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
        # 注册信号处理器，支持 Ctrl+C 优雅退出
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("DuanjuApp")
        app.setApplicationVersion("1.0.0")
        app.setQuitOnLastWindowClosed(True)

        # Setup Qt exception hook for debugging
        logger.setup_qt_exception_hook()
        logger.info("Application initializing...")

        # Set default font
        font = QFont("Microsoft YaHei", 10)
        app.setFont(font)

        # Create and show main window
        try:
            from src.ui.windows.main_window import MainWindow
            logger.debug("Creating main window...")
            window = MainWindow()
            window.show()
            window.raise_()
            window.activateWindow()
            logger.info("Main window displayed")

            # Start initialization process
            window.start_initialization()
        except Exception as e:
            logger.critical(f"Failed to create main window: {e}", exc_info=True)
            show_error_dialog(
                "启动错误",
                "无法创建主窗口",
                traceback.format_exc()
            )
            return 1

        # Run application
        logger.info("Application started, entering event loop")
        exit_code = app.exec()
        logger.info(f"Application exiting with code: {exit_code}")

        app.closeAllWindows()
        cleanup_on_exit()

        return exit_code

    except Exception as e:
        logger.critical(f"Fatal error during startup: {e}", exc_info=True)
        show_error_dialog(
            "致命错误",
            f"应用启动失败: {e}",
            traceback.format_exc()
        )
        return 1


if __name__ == "__main__":
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
