#include "utils/thememanager.h"
#include <QStyleHints>
#include <QPalette>

#ifdef Q_OS_WIN
#include <windows.h>
#include <dwmapi.h>
#endif

ThemeManager* ThemeManager::s_instance = nullptr;

ThemeManager* ThemeManager::instance() {
    if (!s_instance) {
        s_instance = new ThemeManager();
    }
    return s_instance;
}

ThemeManager::ThemeManager(QObject* parent)
    : QObject(parent)
    , m_mode(ThemeMode::Auto)
    , m_isDark(false)
    , m_app(nullptr)
{
}

ThemeManager::~ThemeManager() = default;

void ThemeManager::setThemeMode(ThemeMode mode) {
    if (m_mode != mode) {
        m_mode = mode;
        updateTheme();
    }
}

ThemeMode ThemeManager::currentMode() const {
    return m_mode;
}

bool ThemeManager::isDarkTheme() const {
    return m_isDark;
}

bool ThemeManager::detectSystemDarkMode() {
#ifdef Q_OS_WIN
    // Check Windows registry for dark mode setting
    HKEY hKey;
    DWORD value = 0;
    DWORD size = sizeof(value);
    
    if (RegOpenKeyExW(HKEY_CURRENT_USER,
                      L"Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize",
                      0, KEY_READ, &hKey) == ERROR_SUCCESS) {
        RegQueryValueExW(hKey, L"AppsUseLightTheme", nullptr, nullptr,
                        reinterpret_cast<LPBYTE>(&value), &size);
        RegCloseKey(hKey);
        return value == 0; // 0 means dark mode
    }
#endif
    
    // Fallback to Qt's detection
    if (QGuiApplication::styleHints()) {
        return QGuiApplication::styleHints()->colorScheme() == Qt::ColorScheme::Dark;
    }
    
    return false;
}

void ThemeManager::updateTheme() {
    bool newIsDark = false;
    
    switch (m_mode) {
        case ThemeMode::Light:
            newIsDark = false;
            break;
        case ThemeMode::Dark:
            newIsDark = true;
            break;
        case ThemeMode::Auto:
            newIsDark = detectSystemDarkMode();
            break;
    }
    
    if (m_isDark != newIsDark) {
        m_isDark = newIsDark;
        if (m_app) {
            applyTheme(m_app);
        }
        emit themeChanged(m_isDark);
    }
}

void ThemeManager::registerSystemThemeCallback() {
    // Connect to Qt's color scheme change signal
    if (QGuiApplication::styleHints()) {
        connect(QGuiApplication::styleHints(), &QStyleHints::colorSchemeChanged,
                this, &ThemeManager::onSystemThemeChanged);
    }
}

void ThemeManager::onSystemThemeChanged() {
    if (m_mode == ThemeMode::Auto) {
        updateTheme();
    }
}

void ThemeManager::applyTheme(QApplication* app) {
    m_app = app;
    
    if (!app) return;
    
    QString styleSheet = m_isDark ? darkStyleSheet() : lightStyleSheet();
    app->setStyleSheet(styleSheet);
    
    // Set palette for native widgets
    QPalette palette;
    if (m_isDark) {
        palette.setColor(QPalette::Window, QColor(32, 32, 32));
        palette.setColor(QPalette::WindowText, QColor(255, 255, 255));
        palette.setColor(QPalette::Base, QColor(45, 45, 45));
        palette.setColor(QPalette::AlternateBase, QColor(53, 53, 53));
        palette.setColor(QPalette::ToolTipBase, QColor(45, 45, 45));
        palette.setColor(QPalette::ToolTipText, QColor(255, 255, 255));
        palette.setColor(QPalette::Text, QColor(255, 255, 255));
        palette.setColor(QPalette::Button, QColor(53, 53, 53));
        palette.setColor(QPalette::ButtonText, QColor(255, 255, 255));
        palette.setColor(QPalette::BrightText, QColor(255, 0, 0));
        palette.setColor(QPalette::Link, QColor(42, 130, 218));
        palette.setColor(QPalette::Highlight, QColor(42, 130, 218));
        palette.setColor(QPalette::HighlightedText, QColor(255, 255, 255));
    } else {
        palette.setColor(QPalette::Window, QColor(243, 243, 243));
        palette.setColor(QPalette::WindowText, QColor(0, 0, 0));
        palette.setColor(QPalette::Base, QColor(255, 255, 255));
        palette.setColor(QPalette::AlternateBase, QColor(245, 245, 245));
        palette.setColor(QPalette::ToolTipBase, QColor(255, 255, 255));
        palette.setColor(QPalette::ToolTipText, QColor(0, 0, 0));
        palette.setColor(QPalette::Text, QColor(0, 0, 0));
        palette.setColor(QPalette::Button, QColor(240, 240, 240));
        palette.setColor(QPalette::ButtonText, QColor(0, 0, 0));
        palette.setColor(QPalette::BrightText, QColor(255, 0, 0));
        palette.setColor(QPalette::Link, QColor(0, 102, 204));
        palette.setColor(QPalette::Highlight, QColor(0, 120, 215));
        palette.setColor(QPalette::HighlightedText, QColor(255, 255, 255));
    }
    
    app->setPalette(palette);
    
    // Register for system theme changes
    registerSystemThemeCallback();
}

QString ThemeManager::lightStyleSheet() const {
    return R"(
        /* Windows 11 Fluent Design - Light Theme */
        * {
            font-family: "Segoe UI", sans-serif;
        }
        
        QMainWindow {
            background-color: #f3f3f3;
        }
        
        QWidget {
            background-color: transparent;
            color: #000000;
        }
        
        QPushButton {
            background-color: #ffffff;
            border: 1px solid #d1d1d1;
            border-radius: 4px;
            padding: 6px 16px;
            min-height: 24px;
        }
        
        QPushButton:hover {
            background-color: #f5f5f5;
            border-color: #c1c1c1;
        }
        
        QPushButton:pressed {
            background-color: #e5e5e5;
        }
        
        QPushButton:disabled {
            background-color: #f0f0f0;
            color: #a0a0a0;
        }
        
        QLineEdit {
            background-color: #ffffff;
            border: 1px solid #d1d1d1;
            border-radius: 4px;
            padding: 6px 12px;
            selection-background-color: #0078d4;
        }
        
        QLineEdit:focus {
            border: 2px solid #0078d4;
            padding: 5px 11px;
        }
        
        QListWidget {
            background-color: #ffffff;
            border: 1px solid #d1d1d1;
            border-radius: 8px;
        }
        
        QListWidget::item {
            padding: 8px;
            border-radius: 4px;
        }
        
        QListWidget::item:hover {
            background-color: #f5f5f5;
        }
        
        QListWidget::item:selected {
            background-color: #e5f1fb;
            color: #000000;
        }
        
        QComboBox {
            background-color: #ffffff;
            border: 1px solid #d1d1d1;
            border-radius: 4px;
            padding: 6px 12px;
        }
        
        QComboBox:hover {
            border-color: #c1c1c1;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 24px;
        }
        
        QTextEdit {
            background-color: #ffffff;
            border: 1px solid #d1d1d1;
            border-radius: 8px;
            padding: 8px;
        }
        
        QTabWidget::pane {
            border: 1px solid #d1d1d1;
            border-radius: 8px;
            background-color: #ffffff;
        }
        
        QTabBar::tab {
            background-color: transparent;
            padding: 8px 16px;
            margin-right: 4px;
            border-radius: 4px 4px 0 0;
        }
        
        QTabBar::tab:selected {
            background-color: #ffffff;
            border: 1px solid #d1d1d1;
            border-bottom: none;
        }
        
        QTabBar::tab:hover:!selected {
            background-color: #f5f5f5;
        }
        
        QScrollBar:vertical {
            background-color: transparent;
            width: 12px;
            margin: 0;
        }
        
        QScrollBar::handle:vertical {
            background-color: #c1c1c1;
            border-radius: 6px;
            min-height: 30px;
            margin: 2px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #a1a1a1;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0;
        }
        
        QSlider::groove:horizontal {
            height: 4px;
            background-color: #d1d1d1;
            border-radius: 2px;
        }
        
        QSlider::handle:horizontal {
            background-color: #0078d4;
            width: 16px;
            height: 16px;
            margin: -6px 0;
            border-radius: 8px;
        }
        
        QSlider::sub-page:horizontal {
            background-color: #0078d4;
            border-radius: 2px;
        }
    )";
}

QString ThemeManager::darkStyleSheet() const {
    return R"(
        /* Windows 11 Fluent Design - Dark Theme */
        * {
            font-family: "Segoe UI", sans-serif;
        }
        
        QMainWindow {
            background-color: #202020;
        }
        
        QWidget {
            background-color: transparent;
            color: #ffffff;
        }
        
        QPushButton {
            background-color: #2d2d2d;
            border: 1px solid #3d3d3d;
            border-radius: 4px;
            padding: 6px 16px;
            min-height: 24px;
            color: #ffffff;
        }
        
        QPushButton:hover {
            background-color: #3d3d3d;
            border-color: #4d4d4d;
        }
        
        QPushButton:pressed {
            background-color: #4d4d4d;
        }
        
        QPushButton:disabled {
            background-color: #2a2a2a;
            color: #6d6d6d;
        }
        
        QLineEdit {
            background-color: #2d2d2d;
            border: 1px solid #3d3d3d;
            border-radius: 4px;
            padding: 6px 12px;
            color: #ffffff;
            selection-background-color: #0078d4;
        }
        
        QLineEdit:focus {
            border: 2px solid #0078d4;
            padding: 5px 11px;
        }
        
        QListWidget {
            background-color: #2d2d2d;
            border: 1px solid #3d3d3d;
            border-radius: 8px;
        }
        
        QListWidget::item {
            padding: 8px;
            border-radius: 4px;
            color: #ffffff;
        }
        
        QListWidget::item:hover {
            background-color: #3d3d3d;
        }
        
        QListWidget::item:selected {
            background-color: #0078d4;
            color: #ffffff;
        }
        
        QComboBox {
            background-color: #2d2d2d;
            border: 1px solid #3d3d3d;
            border-radius: 4px;
            padding: 6px 12px;
            color: #ffffff;
        }
        
        QComboBox:hover {
            border-color: #4d4d4d;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 24px;
        }
        
        QComboBox QAbstractItemView {
            background-color: #2d2d2d;
            border: 1px solid #3d3d3d;
            selection-background-color: #0078d4;
        }
        
        QTextEdit {
            background-color: #2d2d2d;
            border: 1px solid #3d3d3d;
            border-radius: 8px;
            padding: 8px;
            color: #ffffff;
        }
        
        QTabWidget::pane {
            border: 1px solid #3d3d3d;
            border-radius: 8px;
            background-color: #2d2d2d;
        }
        
        QTabBar::tab {
            background-color: transparent;
            padding: 8px 16px;
            margin-right: 4px;
            border-radius: 4px 4px 0 0;
            color: #ffffff;
        }
        
        QTabBar::tab:selected {
            background-color: #2d2d2d;
            border: 1px solid #3d3d3d;
            border-bottom: none;
        }
        
        QTabBar::tab:hover:!selected {
            background-color: #3d3d3d;
        }
        
        QScrollBar:vertical {
            background-color: transparent;
            width: 12px;
            margin: 0;
        }
        
        QScrollBar::handle:vertical {
            background-color: #5d5d5d;
            border-radius: 6px;
            min-height: 30px;
            margin: 2px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #7d7d7d;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0;
        }
        
        QSlider::groove:horizontal {
            height: 4px;
            background-color: #4d4d4d;
            border-radius: 2px;
        }
        
        QSlider::handle:horizontal {
            background-color: #0078d4;
            width: 16px;
            height: 16px;
            margin: -6px 0;
            border-radius: 8px;
        }
        
        QSlider::sub-page:horizontal {
            background-color: #0078d4;
            border-radius: 2px;
        }
    )";
}
