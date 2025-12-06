"""DuanjuApp Debug Version - Application Entry Point

This is the debug version with full logging, detailed error messages,
and development utilities enabled.
"""
import sys
import traceback
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QFont

# Initialize logging system (must be first)
from src.core.utils.log_manager import logger

# Enable high DPI support
if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)


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
        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("DuanjuApp")
        app.setApplicationVersion("1.0.0-debug")
        
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
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        logger.critical(f"Unhandled exception in main: {e}", exc_info=True)
        sys.exit(1)
