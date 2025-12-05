#include <gtest/gtest.h>
#include "widgets/searchwidget.h"

// **Feature: duanju-gui, Property 3: Empty Input Validation**
// **Validates: Requirements 1.5**
class SearchValidationTest : public ::testing::Test {
};

TEST_F(SearchValidationTest, EmptyStringIsInvalid) {
    EXPECT_FALSE(SearchWidget::isValidSearchInput(""));
}

TEST_F(SearchValidationTest, WhitespaceOnlyIsInvalid) {
    EXPECT_FALSE(SearchWidget::isValidSearchInput("   "));
    EXPECT_FALSE(SearchWidget::isValidSearchInput("\t"));
    EXPECT_FALSE(SearchWidget::isValidSearchInput("\n"));
    EXPECT_FALSE(SearchWidget::isValidSearchInput("\r"));
    EXPECT_FALSE(SearchWidget::isValidSearchInput(" \t\n\r "));
}

TEST_F(SearchValidationTest, NonEmptyStringIsValid) {
    EXPECT_TRUE(SearchWidget::isValidSearchInput("test"));
    EXPECT_TRUE(SearchWidget::isValidSearchInput("总裁"));
    EXPECT_TRUE(SearchWidget::isValidSearchInput("a"));
}

TEST_F(SearchValidationTest, StringWithLeadingWhitespaceIsValid) {
    EXPECT_TRUE(SearchWidget::isValidSearchInput("  test"));
    EXPECT_TRUE(SearchWidget::isValidSearchInput("\ttest"));
}

TEST_F(SearchValidationTest, StringWithTrailingWhitespaceIsValid) {
    EXPECT_TRUE(SearchWidget::isValidSearchInput("test  "));
    EXPECT_TRUE(SearchWidget::isValidSearchInput("test\t"));
}

TEST_F(SearchValidationTest, StringWithMiddleWhitespaceIsValid) {
    EXPECT_TRUE(SearchWidget::isValidSearchInput("test keyword"));
    EXPECT_TRUE(SearchWidget::isValidSearchInput("霸道 总裁"));
}

TEST_F(SearchValidationTest, ChineseCharactersAreValid) {
    EXPECT_TRUE(SearchWidget::isValidSearchInput("穿越"));
    EXPECT_TRUE(SearchWidget::isValidSearchInput("甜宠剧"));
    EXPECT_TRUE(SearchWidget::isValidSearchInput("霸道总裁爱上我"));
}

TEST_F(SearchValidationTest, MixedContentIsValid) {
    EXPECT_TRUE(SearchWidget::isValidSearchInput("test123"));
    EXPECT_TRUE(SearchWidget::isValidSearchInput("总裁123"));
    EXPECT_TRUE(SearchWidget::isValidSearchInput("drama_name"));
}

TEST_F(SearchValidationTest, SpecialCharactersAreValid) {
    EXPECT_TRUE(SearchWidget::isValidSearchInput("test!"));
    EXPECT_TRUE(SearchWidget::isValidSearchInput("test@#$"));
    EXPECT_TRUE(SearchWidget::isValidSearchInput("《总裁》"));
}
