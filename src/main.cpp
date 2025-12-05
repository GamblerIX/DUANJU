#include <QApplication>
#include "mainwindow.h"
#include "utils/thememanager.h"
#include "utils/configmanager.h"

int main(int argc, char *argv[]) {
    QApplication app(argc, argv);
    
    app.setApplicationName("DuanjuGUI");
    app.setApplicationVersion("1.0.0");
    app.setOrganizationName("DuanjuGUI");
    
    // Load configuration
    ConfigManager::instance()->load();
    
    // Apply theme
    ThemeManager::instance()->applyTheme(&app);
    
    MainWindow window;
    window.show();
    
    return app.exec();
}
