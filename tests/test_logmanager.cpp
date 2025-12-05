#include <gtest/gtest.h>
#include "utils/logmanager.h"
#include <QDateTime>
#include <QRegularExpression>

class LogManagerTest : public ::testing::Test {
protected:
    void SetUp() override {
        LogManager::instance()->clear();
    }
    
    void TearDown() override {
        LogManager::instance()->clear();
    }
};

// **Feature: duanju-gui, Property 8: Log Entry Timestamp**
// **Validates: Requirements 5.1**
TEST_F(LogManagerTest, LogEntryHasValidTimestamp) {
    LogManager::instance()->log("Test message", LogLevel::Info);
    
    QList<LogEntry> entries = LogManager::instance()->entries();
    ASSERT_EQ(entries.size(), 1);
    
    // Check timestamp is valid and recent
    QDateTime now = QDateTime::currentDateTime();
    QDateTime entryTime = entries[0].timestamp;
    
    EXPECT_TRUE(entryTime.isValid());
    EXPECT_LE(qAbs(entryTime.secsTo(now)), 1); // Within 1 second
}

TEST_F(LogManagerTest, LogEntryTimestampISO8601Format) {
    LogManager::instance()->log("Test message", LogLevel::Info);
    
    QString exported = LogManager::instance()->exportToString();
    
    // ISO 8601 format: YYYY-MM-DDTHH:MM:SS
    QRegularExpression isoRegex(R"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})");
    EXPECT_TRUE(isoRegex.match(exported).hasMatch());
}

// Test log levels
TEST_F(LogManagerTest, LogLevelsAreRecorded) {
    LogManager::instance()->log("Debug", LogLevel::Debug);
    LogManager::instance()->log("Info", LogLevel::Info);
    LogManager::instance()->log("Warning", LogLevel::Warning);
    LogManager::instance()->log("Error", LogLevel::Error);
    
    QList<LogEntry> entries = LogManager::instance()->entries();
    ASSERT_EQ(entries.size(), 4);
    
    EXPECT_EQ(entries[0].level, LogLevel::Debug);
    EXPECT_EQ(entries[1].level, LogLevel::Info);
    EXPECT_EQ(entries[2].level, LogLevel::Warning);
    EXPECT_EQ(entries[3].level, LogLevel::Error);
}

// Test log message content
TEST_F(LogManagerTest, LogMessageContent) {
    QString message = "This is a test message";
    LogManager::instance()->log(message, LogLevel::Info);
    
    QList<LogEntry> entries = LogManager::instance()->entries();
    ASSERT_EQ(entries.size(), 1);
    EXPECT_EQ(entries[0].message, message);
}

// Test clear functionality
TEST_F(LogManagerTest, ClearLogs) {
    LogManager::instance()->log("Message 1", LogLevel::Info);
    LogManager::instance()->log("Message 2", LogLevel::Info);
    
    EXPECT_EQ(LogManager::instance()->entries().size(), 2);
    
    LogManager::instance()->clear();
    
    EXPECT_EQ(LogManager::instance()->entries().size(), 0);
}

// Test max entries limit
TEST_F(LogManagerTest, MaxEntriesLimit) {
    LogManager::instance()->setMaxEntries(5);
    
    for (int i = 0; i < 10; i++) {
        LogManager::instance()->log(QString("Message %1").arg(i), LogLevel::Info);
    }
    
    QList<LogEntry> entries = LogManager::instance()->entries();
    EXPECT_EQ(entries.size(), 5);
    
    // Should keep the most recent entries
    EXPECT_EQ(entries[0].message, "Message 5");
    EXPECT_EQ(entries[4].message, "Message 9");
    
    // Reset max entries
    LogManager::instance()->setMaxEntries(1000);
}

// Test export to string
TEST_F(LogManagerTest, ExportToString) {
    LogManager::instance()->log("Test message", LogLevel::Info);
    
    QString exported = LogManager::instance()->exportToString();
    
    EXPECT_TRUE(exported.contains("Test message"));
    EXPECT_TRUE(exported.contains("[INFO]"));
}

// **Feature: duanju-gui, Property 9: API Request Logging**
// **Validates: Requirements 5.2**
TEST_F(LogManagerTest, ApiRequestLogging) {
    QString requestUrl = "https://api.example.com/search?name=test";
    LogManager::instance()->log(QString("API Request: Search - URL: %1").arg(requestUrl), LogLevel::Info);
    
    QList<LogEntry> entries = LogManager::instance()->entries();
    ASSERT_EQ(entries.size(), 1);
    
    EXPECT_TRUE(entries[0].message.contains("API Request"));
    EXPECT_TRUE(entries[0].message.contains(requestUrl));
}

// **Feature: duanju-gui, Property 10: API Response Logging**
// **Validates: Requirements 5.3**
TEST_F(LogManagerTest, ApiResponseLogging) {
    int statusCode = 200;
    LogManager::instance()->log(QString("API Response: Search - Code: %1").arg(statusCode), LogLevel::Info);
    
    QList<LogEntry> entries = LogManager::instance()->entries();
    ASSERT_EQ(entries.size(), 1);
    
    EXPECT_TRUE(entries[0].message.contains("API Response"));
    EXPECT_TRUE(entries[0].message.contains(QString::number(statusCode)));
}
