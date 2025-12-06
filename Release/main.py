import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QFont

if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)


def show_error_dialog(title: str, message: str) -> None:
    try:
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec()
    except Exception:
        print(f"ERROR: {title}\n{message}")


def main() -> int:
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("DuanjuApp")
        app.setApplicationVersion("1.0.0")
        font = QFont("Microsoft YaHei", 10)
        app.setFont(font)
        
        try:
            from src.ui.windows.main_window import MainWindow
            window = MainWindow()
            window.show()
            window.start_initialization()
        except Exception as e:
            show_error_dialog("启动错误", f"无法创建主窗口: {e}")
            return 1
        
        return app.exec()
    except Exception as e:
        show_error_dialog("致命错误", f"应用启动失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
