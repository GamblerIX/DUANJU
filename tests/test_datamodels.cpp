#include <gtest/gtest.h>
#include "models/datamodels.h"

// Test theme mode conversion
TEST(DataModels, ThemeModeToString) {
    EXPECT_EQ(themeModeToString(ThemeMode::Light), "light");
    EXPECT_EQ(themeModeToString(ThemeMode::Dark), "dark");
    EXPECT_EQ(themeModeToString(ThemeMode::Auto), "auto");
}

TEST(DataModels, StringToThemeMode) {
    EXPECT_EQ(stringToThemeMode("light"), ThemeMode::Light);
    EXPECT_EQ(stringToThemeMode("dark"), ThemeMode::Dark);
    EXPECT_EQ(stringToThemeMode("auto"), ThemeMode::Auto);
    EXPECT_EQ(stringToThemeMode("invalid"), ThemeMode::Auto); // Default
}

// Test log level conversion
TEST(DataModels, LogLevelToString) {
    EXPECT_EQ(logLevelToString(LogLevel::Debug), "DEBUG");
    EXPECT_EQ(logLevelToString(LogLevel::Info), "INFO");
    EXPECT_EQ(logLevelToString(LogLevel::Warning), "WARNING");
    EXPECT_EQ(logLevelToString(LogLevel::Error), "ERROR");
}

// Test config serialization
TEST(DataModels, ConfigToJson) {
    AppConfig config;
    config.apiTimeout = 15000;
    config.defaultQuality = "720p";
    config.themeMode = ThemeMode::Dark;
    config.lastSearchKeyword = "test";
    config.searchHistory = {"a", "b", "c"};
    
    QJsonObject json = configToJson(config);
    
    EXPECT_EQ(json["apiTimeout"].toInt(), 15000);
    EXPECT_EQ(json["defaultQuality"].toString(), "720p");
    EXPECT_EQ(json["themeMode"].toString(), "dark");
    EXPECT_EQ(json["lastSearchKeyword"].toString(), "test");
    EXPECT_EQ(json["searchHistory"].toArray().size(), 3);
}

TEST(DataModels, JsonToConfig) {
    QJsonObject json;
    json["apiTimeout"] = 20000;
    json["defaultQuality"] = "480p";
    json["themeMode"] = "light";
    json["lastSearchKeyword"] = "drama";
    
    QJsonArray history;
    history.append("x");
    history.append("y");
    json["searchHistory"] = history;
    
    AppConfig config = jsonToConfig(json);
    
    EXPECT_EQ(config.apiTimeout, 20000);
    EXPECT_EQ(config.defaultQuality, "480p");
    EXPECT_EQ(config.themeMode, ThemeMode::Light);
    EXPECT_EQ(config.lastSearchKeyword, "drama");
    EXPECT_EQ(config.searchHistory.size(), 2);
}

// Test search result parsing
TEST(DataModels, ParseSearchResult) {
    QJsonObject json;
    json["code"] = 200;
    json["title"] = "Success";
    json["page"] = 1;
    json["total_pages"] = 5;
    
    QJsonArray data;
    QJsonObject drama;
    drama["book_id"] = "123";
    drama["name"] = "Test Drama";
    drama["cover"] = "http://example.com/cover.jpg";
    drama["episode_count"] = 20;
    drama["description"] = "A test drama";
    drama["category"] = "甜宠";
    data.append(drama);
    json["data"] = data;
    
    SearchResult result = parseSearchResult(json);
    
    EXPECT_EQ(result.code, 200);
    EXPECT_EQ(result.title, "Success");
    EXPECT_EQ(result.currentPage, 1);
    EXPECT_EQ(result.totalPages, 5);
    EXPECT_EQ(result.data.size(), 1);
    EXPECT_EQ(result.data[0].bookId, "123");
    EXPECT_EQ(result.data[0].name, "Test Drama");
    EXPECT_EQ(result.data[0].episodeCount, 20);
}

// Test episode list parsing
TEST(DataModels, ParseEpisodeList) {
    QJsonObject json;
    json["code"] = 200;
    json["name"] = "Test Drama";
    
    QJsonArray data;
    QJsonObject episode;
    episode["video_id"] = "456";
    episode["episode"] = 1;
    episode["title"] = "Episode 1";
    episode["duration"] = "10:30";
    data.append(episode);
    json["data"] = data;
    
    EpisodeList list = parseEpisodeList(json);
    
    EXPECT_EQ(list.code, 200);
    EXPECT_EQ(list.dramaName, "Test Drama");
    EXPECT_EQ(list.episodes.size(), 1);
    EXPECT_EQ(list.episodes[0].videoId, "456");
    EXPECT_EQ(list.episodes[0].episodeNumber, 1);
}

// Test video info parsing
TEST(DataModels, ParseVideoInfo) {
    QJsonObject json;
    json["code"] = 200;
    json["title"] = "Episode 1";
    json["url"] = "http://example.com/video.mp4";
    json["cover"] = "http://example.com/cover.jpg";
    json["quality"] = "1080p";
    
    VideoInfo info = parseVideoInfo(json);
    
    EXPECT_EQ(info.code, 200);
    EXPECT_EQ(info.title, "Episode 1");
    EXPECT_EQ(info.videoUrl, "http://example.com/video.mp4");
    EXPECT_EQ(info.quality, "1080p");
}

// Test category result parsing
TEST(DataModels, ParseCategoryResult) {
    QJsonObject json;
    json["code"] = 200;
    json["category"] = "甜宠";
    json["offset"] = 2;
    
    QJsonArray data;
    QJsonObject drama;
    drama["book_id"] = "789";
    drama["name"] = "Sweet Drama";
    drama["episode_count"] = 30;
    data.append(drama);
    json["data"] = data;
    
    CategoryResult result = parseCategoryResult(json);
    
    EXPECT_EQ(result.code, 200);
    EXPECT_EQ(result.category, "甜宠");
    EXPECT_EQ(result.offset, 2);
    EXPECT_EQ(result.data.size(), 1);
    EXPECT_EQ(result.data[0].bookId, "789");
}
