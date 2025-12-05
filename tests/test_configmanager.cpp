#include <gtest/gtest.h>
#include "utils/configmanager.h"
#include <QTemporaryFile>
#include <QDir>

class ConfigManagerTest : public ::testing::Test {
protected:
    void SetUp() override {
        // Use a temporary file for testing
        tempFile = new QTemporaryFile();
        tempFile->open();
        tempPath = tempFile->fileName();
        tempFile->close();
        
        ConfigManager::instance()->setConfigFilePath(tempPath);
    }
    
    void TearDown() override {
        delete tempFile;
        QFile::remove(tempPath);
    }
    
    QTemporaryFile* tempFile;
    QString tempPath;
};

// **Feature: duanju-gui, Property 6: Theme Setting Persistence Round-Trip**
// **Validates: Requirements 3.5, 9.2, 9.3**
TEST_F(ConfigManagerTest, ThemeModePersistence_Light) {
    ConfigManager::instance()->setThemeMode(ThemeMode::Light);
    ConfigManager::instance()->save();
    
    // Reset and reload
    ConfigManager::instance()->setThemeMode(ThemeMode::Auto);
    ConfigManager::instance()->load();
    
    EXPECT_EQ(ConfigManager::instance()->themeMode(), ThemeMode::Light);
}

TEST_F(ConfigManagerTest, ThemeModePersistence_Dark) {
    ConfigManager::instance()->setThemeMode(ThemeMode::Dark);
    ConfigManager::instance()->save();
    
    ConfigManager::instance()->setThemeMode(ThemeMode::Light);
    ConfigManager::instance()->load();
    
    EXPECT_EQ(ConfigManager::instance()->themeMode(), ThemeMode::Dark);
}

TEST_F(ConfigManagerTest, ThemeModePersistence_Auto) {
    ConfigManager::instance()->setThemeMode(ThemeMode::Auto);
    ConfigManager::instance()->save();
    
    ConfigManager::instance()->setThemeMode(ThemeMode::Dark);
    ConfigManager::instance()->load();
    
    EXPECT_EQ(ConfigManager::instance()->themeMode(), ThemeMode::Auto);
}

// Test API timeout persistence
TEST_F(ConfigManagerTest, ApiTimeoutPersistence) {
    ConfigManager::instance()->setApiTimeout(25000);
    ConfigManager::instance()->save();
    
    ConfigManager::instance()->setApiTimeout(10000);
    ConfigManager::instance()->load();
    
    EXPECT_EQ(ConfigManager::instance()->apiTimeout(), 25000);
}

// Test default quality persistence
TEST_F(ConfigManagerTest, DefaultQualityPersistence) {
    ConfigManager::instance()->setDefaultQuality("720p");
    ConfigManager::instance()->save();
    
    ConfigManager::instance()->setDefaultQuality("1080p");
    ConfigManager::instance()->load();
    
    EXPECT_EQ(ConfigManager::instance()->defaultQuality(), "720p");
}

// Test search history
TEST_F(ConfigManagerTest, SearchHistoryManagement) {
    ConfigManager::instance()->clearSearchHistory();
    
    ConfigManager::instance()->addToSearchHistory("keyword1");
    ConfigManager::instance()->addToSearchHistory("keyword2");
    ConfigManager::instance()->addToSearchHistory("keyword3");
    
    QStringList history = ConfigManager::instance()->searchHistory();
    EXPECT_EQ(history.size(), 3);
    EXPECT_EQ(history[0], "keyword3"); // Most recent first
    EXPECT_EQ(history[1], "keyword2");
    EXPECT_EQ(history[2], "keyword1");
}

TEST_F(ConfigManagerTest, SearchHistoryNoDuplicates) {
    ConfigManager::instance()->clearSearchHistory();
    
    ConfigManager::instance()->addToSearchHistory("keyword");
    ConfigManager::instance()->addToSearchHistory("keyword");
    
    EXPECT_EQ(ConfigManager::instance()->searchHistory().size(), 1);
}

TEST_F(ConfigManagerTest, SearchHistoryPersistence) {
    ConfigManager::instance()->clearSearchHistory();
    ConfigManager::instance()->addToSearchHistory("test1");
    ConfigManager::instance()->addToSearchHistory("test2");
    ConfigManager::instance()->save();
    
    ConfigManager::instance()->clearSearchHistory();
    ConfigManager::instance()->load();
    
    QStringList history = ConfigManager::instance()->searchHistory();
    EXPECT_EQ(history.size(), 2);
}
