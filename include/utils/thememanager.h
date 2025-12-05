#ifndef THEMEMANAGER_H
#define THEMEMANAGER_H

#include <QObject>
#include <QApplication>
#include "models/datamodels.h"

class ThemeManager : public QObject {
    Q_OBJECT

public:
    static ThemeManager* instance();
    
    void setThemeMode(ThemeMode mode);
    ThemeMode currentMode() const;
    bool isDarkTheme() const;
    
    void applyTheme(QApplication* app);
    
    QString lightStyleSheet() const;
    QString darkStyleSheet() const;

signals:
    void themeChanged(bool isDark);

private:
    explicit ThemeManager(QObject* parent = nullptr);
    ~ThemeManager();
    
    void registerSystemThemeCallback();
    void onSystemThemeChanged();
    void updateTheme();
    bool detectSystemDarkMode();
    
    static ThemeManager* s_instance;
    ThemeMode m_mode;
    bool m_isDark;
    QApplication* m_app;
};

#endif // THEMEMANAGER_H
