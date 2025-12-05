#include "utils/configmanager.h"
#include <QFile>
#include <QJsonDocument>
#include <QStandardPaths>
#include <QDir>

ConfigManager* ConfigManager::s_instance = nullptr;

ConfigManager* ConfigManager::instance() {
    if (!s_instance) {
        s_instance = new ConfigManager();
    }
    return s_instance;
}

ConfigManager::ConfigManager(QObject* parent)
    : QObject(parent)
{
    // Default config path
    QString configDir = QStandardPaths::writableLocation(QStandardPaths::AppConfigLocation);
    QDir().mkpath(configDir);
    m_configPath = configDir + "/config.json";
}

ConfigManager::~ConfigManager() = default;

int ConfigManager::apiTimeout() const {
    return m_config.apiTimeout;
}

QString ConfigManager::defaultQuality() const {
    return m_config.defaultQuality;
}

ThemeMode ConfigManager::themeMode() const {
    return m_config.themeMode;
}

QString ConfigManager::lastSearchKeyword() const {
    return m_config.lastSearchKeyword;
}

QStringList ConfigManager::searchHistory() const {
    return m_config.searchHistory;
}

void ConfigManager::setApiTimeout(int ms) {
    if (m_config.apiTimeout != ms) {
        m_config.apiTimeout = ms;
        emit settingsChanged();
    }
}

void ConfigManager::setDefaultQuality(const QString& quality) {
    if (m_config.defaultQuality != quality) {
        m_config.defaultQuality = quality;
        emit settingsChanged();
    }
}

void ConfigManager::setThemeMode(ThemeMode mode) {
    if (m_config.themeMode != mode) {
        m_config.themeMode = mode;
        emit themeModeChanged(mode);
        emit settingsChanged();
    }
}

void ConfigManager::setLastSearchKeyword(const QString& keyword) {
    if (m_config.lastSearchKeyword != keyword) {
        m_config.lastSearchKeyword = keyword;
        emit settingsChanged();
    }
}

void ConfigManager::addToSearchHistory(const QString& keyword) {
    if (!keyword.isEmpty() && !m_config.searchHistory.contains(keyword)) {
        m_config.searchHistory.prepend(keyword);
        // Keep only last 20 searches
        while (m_config.searchHistory.size() > 20) {
            m_config.searchHistory.removeLast();
        }
        emit settingsChanged();
    }
}

void ConfigManager::clearSearchHistory() {
    if (!m_config.searchHistory.isEmpty()) {
        m_config.searchHistory.clear();
        emit settingsChanged();
    }
}

void ConfigManager::save() {
    QFile file(m_configPath);
    if (!file.open(QIODevice::WriteOnly)) {
        return;
    }
    
    QJsonObject json = configToJson(m_config);
    QJsonDocument doc(json);
    file.write(doc.toJson(QJsonDocument::Indented));
    file.close();
}

void ConfigManager::load() {
    QFile file(m_configPath);
    if (!file.open(QIODevice::ReadOnly)) {
        return;
    }
    
    QByteArray data = file.readAll();
    file.close();
    
    QJsonDocument doc = QJsonDocument::fromJson(data);
    if (doc.isNull() || !doc.isObject()) {
        return;
    }
    
    ThemeMode oldTheme = m_config.themeMode;
    m_config = jsonToConfig(doc.object());
    
    if (oldTheme != m_config.themeMode) {
        emit themeModeChanged(m_config.themeMode);
    }
    emit settingsChanged();
}

AppConfig ConfigManager::config() const {
    return m_config;
}

void ConfigManager::setConfig(const AppConfig& config) {
    ThemeMode oldTheme = m_config.themeMode;
    m_config = config;
    
    if (oldTheme != m_config.themeMode) {
        emit themeModeChanged(m_config.themeMode);
    }
    emit settingsChanged();
}

QString ConfigManager::configFilePath() const {
    return m_configPath;
}

void ConfigManager::setConfigFilePath(const QString& path) {
    m_configPath = path;
}
