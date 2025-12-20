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

# 确保 src 模块可以被导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QFont

# Initialize logging system (must be first)
from src.utils.log_manager import logger


def cleanup_on_exit():
    """程序退出时清理临时文件夹"""
    app_dir = os.path.dirname(os.path.abspath(__file__))
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
        # 注册信号处理器，支持 Ctrl+C 优雅退出
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("DuanjuApp")
        app.setApplicationVersion("1.0.0-debug")

        # 确保最后一个窗口关闭时应用退出
        app.setQuitOnLastWindowClosed(True)

        # Setup Qt exception hook for debugging
        logger.setup_qt_exception_hook()
        logger.info("Application initializing (Debug Mode)...")

        # Set default font
        font = QFont("Microsoft YaHei", 10)
        app.setFont(font)

        # Create and show main window
        try:
            from src.ui.windows.main_window import MainWindow
            logger.debug("Creating main window...")
            window = MainWindow()
            logger.debug("Main window created successfully")
            window.show()
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

        # 确保所有线程都已停止
        app.closeAllWindows()
        
        # 清理临时文件夹
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
