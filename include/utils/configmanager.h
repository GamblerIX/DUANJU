#ifndef CONFIGMANAGER_H
#define CONFIGMANAGER_H

#include <QObject>
#include <QString>
#include "models/datamodels.h"

class ConfigManager : public QObject {
    Q_OBJECT

public:
    static ConfigManager* instance();
    
    // Settings getters
    int apiTimeout() const;
    QString defaultQuality() const;
    ThemeMode themeMode() const;
    QString lastSearchKeyword() const;
    QStringList searchHistory() const;
    
    // Settings setters
    void setApiTimeout(int ms);
    void setDefaultQuality(const QString& quality);
    void setThemeMode(ThemeMode mode);
    void setLastSearchKeyword(const QString& keyword);
    void addToSearchHistory(const QString& keyword);
    void clearSearchHistory();
    
    // Persistence
    void save();
    void load();
    
    // Get full config
    AppConfig config() const;
    void setConfig(const AppConfig& config);
    
    // Config file path
    QString configFilePath() const;
    void setConfigFilePath(const QString& path);

signals:
    void settingsChanged();
    void themeModeChanged(ThemeMode mode);

private:
    explicit ConfigManager(QObject* parent = nullptr);
    ~ConfigManager();
    
    static ConfigManager* s_instance;
    AppConfig m_config;
    QString m_configPath;
};

#endif // CONFIGMANAGER_H
