#include <gtest/gtest.h>
#include "api/apiclient.h"
#include <QUrl>
#include <QUrlQuery>

class ApiClientTest : public ::testing::Test {
protected:
    void SetUp() override {
        client = new ApiClient();
    }
    
    void TearDown() override {
        delete client;
    }
    
    ApiClient* client;
};

// **Feature: duanju-gui, Property 1: Search Request Formation**
// **Validates: Requirements 1.1**
TEST_F(ApiClientTest, BuildSearchUrl_ContainsNameParameter) {
    QString keyword = "总裁";
    QUrl url = client->buildSearchUrl(keyword);
    
    QUrlQuery query(url);
    EXPECT_TRUE(query.hasQueryItem("name"));
    EXPECT_EQ(query.queryItemValue("name"), keyword);
}

TEST_F(ApiClientTest, BuildSearchUrl_ContainsPageParameter) {
    QString keyword = "test";
    int page = 3;
    QUrl url = client->buildSearchUrl(keyword, page);
    
    QUrlQuery query(url);
    EXPECT_TRUE(query.hasQueryItem("page"));
    EXPECT_EQ(query.queryItemValue("page"), QString::number(page));
}

TEST_F(ApiClientTest, BuildSearchUrl_NoPageForFirstPage) {
    QString keyword = "test";
    QUrl url = client->buildSearchUrl(keyword, 1);
    
    QUrlQuery query(url);
    // Page parameter should not be present for page 1
    EXPECT_FALSE(query.hasQueryItem("page"));
}

// **Feature: duanju-gui, Property 7: Video Quality Parameter**
// **Validates: Requirements 4.2**
TEST_F(ApiClientTest, BuildVideoUrl_ContainsQualityParameter) {
    QString videoId = "12345";
    QString quality = "720p";
    QUrl url = client->buildVideoUrl(videoId, quality);
    
    QUrlQuery query(url);
    EXPECT_TRUE(query.hasQueryItem("level"));
    EXPECT_EQ(query.queryItemValue("level"), quality);
}

TEST_F(ApiClientTest, BuildVideoUrl_AllQualityLevels) {
    QStringList qualities = {"360p", "480p", "720p", "1080p", "2160p"};
    QString videoId = "12345";
    
    for (const QString& quality : qualities) {
        QUrl url = client->buildVideoUrl(videoId, quality);
        QUrlQuery query(url);
        EXPECT_EQ(query.queryItemValue("level"), quality);
    }
}

TEST_F(ApiClientTest, BuildVideoUrl_ContainsVideoId) {
    QString videoId = "67890";
    QUrl url = client->buildVideoUrl(videoId, "1080p");
    
    QUrlQuery query(url);
    EXPECT_TRUE(query.hasQueryItem("video_id"));
    EXPECT_EQ(query.queryItemValue("video_id"), videoId);
}

// **Feature: duanju-gui, Property 5: Category API Request Formation**
// **Validates: Requirements 2.2**
TEST_F(ApiClientTest, BuildCategoryUrl_ContainsClassnameParameter) {
    QString category = "甜宠";
    QUrl url = client->buildCategoryUrl(category);
    
    QUrlQuery query(url);
    EXPECT_TRUE(query.hasQueryItem("classname"));
    EXPECT_EQ(query.queryItemValue("classname"), category);
}

TEST_F(ApiClientTest, BuildCategoryUrl_ContainsOffsetParameter) {
    QString category = "穿越";
    int offset = 5;
    QUrl url = client->buildCategoryUrl(category, offset);
    
    QUrlQuery query(url);
    EXPECT_TRUE(query.hasQueryItem("offset"));
    EXPECT_EQ(query.queryItemValue("offset"), QString::number(offset));
}

TEST_F(ApiClientTest, BuildCategoryUrl_NoOffsetForFirstPage) {
    QString category = "虐恋";
    QUrl url = client->buildCategoryUrl(category, 1);
    
    QUrlQuery query(url);
    EXPECT_FALSE(query.hasQueryItem("offset"));
}

// Test timeout configuration
TEST_F(ApiClientTest, SetTimeout) {
    client->setTimeout(5000);
    EXPECT_EQ(client->timeout(), 5000);
    
    client->setTimeout(30000);
    EXPECT_EQ(client->timeout(), 30000);
}
