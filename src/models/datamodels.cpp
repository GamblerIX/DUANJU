#include "models/datamodels.h"

// Theme mode to string conversion
QString themeModeToString(ThemeMode mode) {
    switch (mode) {
        case ThemeMode::Light: return "light";
        case ThemeMode::Dark: return "dark";
        case ThemeMode::Auto: return "auto";
        default: return "auto";
    }
}

// String to theme mode conversion
ThemeMode stringToThemeMode(const QString& str) {
    if (str == "light") return ThemeMode::Light;
    if (str == "dark") return ThemeMode::Dark;
    return ThemeMode::Auto;
}

// Log level to string conversion
QString logLevelToString(LogLevel level) {
    switch (level) {
        case LogLevel::Debug: return "DEBUG";
        case LogLevel::Info: return "INFO";
        case LogLevel::Warning: return "WARNING";
        case LogLevel::Error: return "ERROR";
        default: return "INFO";
    }
}

// Serialize AppConfig to JSON
QJsonObject configToJson(const AppConfig& config) {
    QJsonObject json;
    json["apiTimeout"] = config.apiTimeout;
    json["defaultQuality"] = config.defaultQuality;
    json["themeMode"] = themeModeToString(config.themeMode);
    json["lastSearchKeyword"] = config.lastSearchKeyword;
    
    QJsonArray historyArray;
    for (const QString& keyword : config.searchHistory) {
        historyArray.append(keyword);
    }
    json["searchHistory"] = historyArray;
    
    return json;
}

// Deserialize JSON to AppConfig
AppConfig jsonToConfig(const QJsonObject& json) {
    AppConfig config;
    
    if (json.contains("apiTimeout")) {
        config.apiTimeout = json["apiTimeout"].toInt(10000);
    }
    if (json.contains("defaultQuality")) {
        config.defaultQuality = json["defaultQuality"].toString("1080p");
    }
    if (json.contains("themeMode")) {
        config.themeMode = stringToThemeMode(json["themeMode"].toString());
    }
    if (json.contains("lastSearchKeyword")) {
        config.lastSearchKeyword = json["lastSearchKeyword"].toString();
    }
    if (json.contains("searchHistory")) {
        QJsonArray historyArray = json["searchHistory"].toArray();
        for (const QJsonValue& value : historyArray) {
            config.searchHistory.append(value.toString());
        }
    }
    
    return config;
}

// Parse search result from API response
SearchResult parseSearchResult(const QJsonObject& json) {
    SearchResult result;
    
    result.code = json["code"].toInt();
    result.title = json["title"].toString();
    
    if (json.contains("data") && json["data"].isArray()) {
        QJsonArray dataArray = json["data"].toArray();
        for (const QJsonValue& value : dataArray) {
            QJsonObject item = value.toObject();
            DramaInfo drama;
            drama.bookId = item["book_id"].toString();
            if (drama.bookId.isEmpty()) {
                drama.bookId = QString::number(item["book_id"].toInt());
            }
            drama.name = item["name"].toString();
            drama.coverUrl = item["cover"].toString();
            drama.episodeCount = item["episode_count"].toInt();
            drama.description = item["description"].toString();
            drama.category = item["category"].toString();
            result.data.append(drama);
        }
    }
    
    result.currentPage = json["page"].toInt(1);
    result.totalPages = json["total_pages"].toInt(1);
    
    return result;
}

// Parse episode list from API response
EpisodeList parseEpisodeList(const QJsonObject& json) {
    EpisodeList list;
    
    list.code = json["code"].toInt();
    list.dramaName = json["name"].toString();
    
    if (json.contains("data") && json["data"].isArray()) {
        QJsonArray dataArray = json["data"].toArray();
        for (const QJsonValue& value : dataArray) {
            QJsonObject item = value.toObject();
            EpisodeInfo episode;
            episode.videoId = item["video_id"].toString();
            if (episode.videoId.isEmpty()) {
                episode.videoId = QString::number(item["video_id"].toInt());
            }
            episode.episodeNumber = item["episode"].toInt();
            episode.title = item["title"].toString();
            episode.duration = item["duration"].toString();
            list.episodes.append(episode);
        }
    }
    
    return list;
}

// Parse video info from API response
VideoInfo parseVideoInfo(const QJsonObject& json) {
    VideoInfo info;
    
    info.code = json["code"].toInt();
    info.title = json["title"].toString();
    
    if (json.contains("data") && json["data"].isObject()) {
        QJsonObject data = json["data"].toObject();
        info.videoUrl = data["url"].toString();
        info.coverUrl = data["cover"].toString();
        info.quality = data["quality"].toString();
    } else {
        info.videoUrl = json["url"].toString();
        info.coverUrl = json["cover"].toString();
        info.quality = json["quality"].toString();
    }
    
    return info;
}

// Parse category result from API response
CategoryResult parseCategoryResult(const QJsonObject& json) {
    CategoryResult result;
    
    result.code = json["code"].toInt();
    result.category = json["category"].toString();
    result.offset = json["offset"].toInt(1);
    
    if (json.contains("data") && json["data"].isArray()) {
        QJsonArray dataArray = json["data"].toArray();
        for (const QJsonValue& value : dataArray) {
            QJsonObject item = value.toObject();
            DramaInfo drama;
            drama.bookId = item["book_id"].toString();
            if (drama.bookId.isEmpty()) {
                drama.bookId = QString::number(item["book_id"].toInt());
            }
            drama.name = item["name"].toString();
            drama.coverUrl = item["cover"].toString();
            drama.episodeCount = item["episode_count"].toInt();
            drama.description = item["description"].toString();
            drama.category = item["category"].toString();
            result.data.append(drama);
        }
    }
    
    return result;
}
