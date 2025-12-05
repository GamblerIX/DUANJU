#ifndef DATAMODELS_H
#define DATAMODELS_H

#include <QString>
#include <QList>
#include <QJsonObject>
#include <QJsonArray>
#include <QJsonDocument>

// Log level enumeration
enum class LogLevel {
    Debug,
    Info,
    Warning,
    Error
};

// Theme mode enumeration
enum class ThemeMode {
    Light,
    Dark,
    Auto
};

// Playback state enumeration
enum class PlaybackState {
    Stopped,
    Playing,
    Paused,
    Buffering,
    Error
};

// Drama information structure
struct DramaInfo {
    QString bookId;
    QString name;
    QString coverUrl;
    int episodeCount = 0;
    QString description;
    QString category;
    
    bool operator==(const DramaInfo& other) const {
        return bookId == other.bookId &&
               name == other.name &&
               coverUrl == other.coverUrl &&
               episodeCount == other.episodeCount &&
               description == other.description &&
               category == other.category;
    }
};

// Search result structure
struct SearchResult {
    int code = 0;
    QString title;
    QList<DramaInfo> data;
    int currentPage = 1;
    int totalPages = 1;
};

// Episode information structure
struct EpisodeInfo {
    QString videoId;
    int episodeNumber = 0;
    QString title;
    QString duration;
    
    bool operator==(const EpisodeInfo& other) const {
        return videoId == other.videoId &&
               episodeNumber == other.episodeNumber &&
               title == other.title &&
               duration == other.duration;
    }
};

// Episode list structure
struct EpisodeList {
    int code = 0;
    QString dramaName;
    QList<EpisodeInfo> episodes;
};

// Video information structure
struct VideoInfo {
    int code = 0;
    QString videoUrl;
    QString coverUrl;
    QString quality;
    QString title;
};

// Category result structure
struct CategoryResult {
    int code = 0;
    QString category;
    QList<DramaInfo> data;
    int offset = 1;
};

// API error structure
struct ApiError {
    int code = 0;
    QString message;
    QString details;
};

// Application configuration structure
struct AppConfig {
    int apiTimeout = 10000;
    QString defaultQuality = "1080p";
    ThemeMode themeMode = ThemeMode::Auto;
    QString lastSearchKeyword;
    QStringList searchHistory;
    
    bool operator==(const AppConfig& other) const {
        return apiTimeout == other.apiTimeout &&
               defaultQuality == other.defaultQuality &&
               themeMode == other.themeMode &&
               lastSearchKeyword == other.lastSearchKeyword &&
               searchHistory == other.searchHistory;
    }
};

// JSON serialization functions
QJsonObject configToJson(const AppConfig& config);
AppConfig jsonToConfig(const QJsonObject& json);

// API response parsing functions
SearchResult parseSearchResult(const QJsonObject& json);
EpisodeList parseEpisodeList(const QJsonObject& json);
VideoInfo parseVideoInfo(const QJsonObject& json);
CategoryResult parseCategoryResult(const QJsonObject& json);

// Helper functions
QString themeModeToString(ThemeMode mode);
ThemeMode stringToThemeMode(const QString& str);
QString logLevelToString(LogLevel level);

#endif // DATAMODELS_H
