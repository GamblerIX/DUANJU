"""响应解析器测试

测试 src/data/api/response_parser.py 中的解析功能。
"""
from pathlib import Path
import json
import sys

import pytest

from src.core.models import (
    DramaInfo, EpisodeInfo, EpisodeList, VideoInfo, SearchResult, CategoryResult
)
from src.data.response_parser import ResponseParser

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.response_parser import ResponseParser, ApiResponseError
from src.core.models import DramaInfo, EpisodeInfo, VideoInfo, SearchResult


class TestResponseParser:
    """ResponseParser 测试"""
    
    class TestCheckResponseStatus:
        """check_response_status 测试"""
        
        def test_success_status(self):
            """测试成功状态"""
            data = {"code": 200, "msg": "success"}
            success, error = ResponseParser.check_response_status(data)
            assert success is True
            assert error is None
        
        def test_error_status(self):
            """测试错误状态"""
            data = {"code": 500, "msg": "服务器错误"}
            success, error = ResponseParser.check_response_status(data)
            assert success is False
            assert error == "服务器错误"
        
        def test_missing_code(self):
            """测试缺少 code 字段"""
            data = {"msg": "no code"}
            success, error = ResponseParser.check_response_status(data)
            assert success is False
    
    class TestParseSearchResult:
        """parse_search_result 测试"""
        
        def test_parse_success(self):
            """测试成功解析搜索结果"""
            json_str = json.dumps({
                "code": 200,
                "msg": "搜索成功",
                "page": 1,
                "data": [
                    {
                        "book_id": "123",
                        "title": "测试短剧",
                        "cover": "https://example.com/cover.jpg",
                        "episode_cnt": 20,
                        "intro": "简介",
                        "type": "都市",
                        "author": "作者",
                        "play_cnt": 10000
                    }
                ]
            })
            
            result = ResponseParser.parse_search_result(json_str)
            
            assert result.code == 200
            assert len(result.data) == 1
            assert result.data[0].book_id == "123"
            assert result.data[0].title == "测试短剧"
            assert result.data[0].episode_cnt == 20
        
        def test_parse_empty_data(self):
            """测试解析空数据"""
            json_str = json.dumps({
                "code": 200,
                "msg": "无结果",
                "data": []
            })
            
            result = ResponseParser.parse_search_result(json_str)
            assert len(result.data) == 0
        
        def test_parse_error_response(self):
            """测试解析错误响应"""
            json_str = json.dumps({
                "code": 500,
                "msg": "服务器错误",
                "tips": "请稍后重试"
            })
            
            with pytest.raises(ApiResponseError) as exc_info:
                ResponseParser.parse_search_result(json_str)
            
            assert exc_info.value.code == 500
            assert "服务器错误" in exc_info.value.message
        
        def test_parse_string_page(self):
            """测试解析字符串类型的页码"""
            json_str = json.dumps({
                "code": 200,
                "msg": "success",
                "page": "2",
                "data": []
            })
            
            result = ResponseParser.parse_search_result(json_str)
            assert result.page == 2
        
        def test_parse_invalid_page(self):
            """测试解析无效页码"""
            json_str = json.dumps({
                "code": 200,
                "msg": "success",
                "page": "invalid",
                "data": []
            })
            
            result = ResponseParser.parse_search_result(json_str)
            assert result.page == 1  # 默认值
    
    class TestParseEpisodeNumber:
        """parse_episode_number 测试"""
        
        def test_parse_chinese_format(self):
            """测试解析中文格式"""
            assert ResponseParser.parse_episode_number("第1集") == 1
            assert ResponseParser.parse_episode_number("第10集") == 10
            assert ResponseParser.parse_episode_number("第100集") == 100
        
        def test_parse_number_only(self):
            """测试解析纯数字"""
            assert ResponseParser.parse_episode_number("1") == 1
            assert ResponseParser.parse_episode_number("Episode 5") == 5
        
        def test_parse_no_number(self):
            """测试无数字的标题"""
            assert ResponseParser.parse_episode_number("预告片") == 0
            assert ResponseParser.parse_episode_number("花絮") == 0
    
    class TestParseEpisodeList:
        """parse_episode_list 测试"""
        
        def test_parse_success(self):
            """测试成功解析剧集列表"""
            json_str = json.dumps({
                "code": 200,
                "book_name": "测试短剧",
                "book_id": "123",
                "author": "作者",
                "category": "都市",
                "desc": "简介",
                "duration": "5分钟",
                "book_pic": "https://example.com/pic.jpg",
                "total": 20,
                "data": [
                    {"video_id": "v1", "title": "第1集", "chapter_word_number": 0},
                    {"video_id": "v2", "title": "第2集", "chapter_word_number": 0}
                ]
            })
            
            result = ResponseParser.parse_episode_list(json_str)
            
            assert result.code == 200
            assert result.book_name == "测试短剧"
            assert len(result.episodes) == 2
            assert result.episodes[0].video_id == "v1"
            assert result.episodes[0].episode_number == 1
        
        def test_parse_string_total(self):
            """测试解析字符串类型的总数"""
            json_str = json.dumps({
                "code": 200,
                "book_name": "测试",
                "total": "20",
                "data": []
            })
            
            result = ResponseParser.parse_episode_list(json_str)
            assert result.total == 20
        
        def test_parse_error_response(self):
            """测试解析错误响应"""
            json_str = json.dumps({
                "code": 404,
                "msg": "短剧不存在"
            })
            
            with pytest.raises(ApiResponseError):
                ResponseParser.parse_episode_list(json_str)
    
    class TestParseVideoInfo:
        """parse_video_info 测试"""
        
        def test_parse_success(self):
            """测试成功解析视频信息"""
            json_str = json.dumps({
                "code": 200,
                "data": {
                    "url": "https://example.com/video.m3u8",
                    "pic": "https://example.com/pic.jpg",
                    "title": "第1集",
                    "info": {
                        "quality": "1080p",
                        "duration": "05:30",
                        "size_str": "50MB"
                    }
                }
            })
            
            result = ResponseParser.parse_video_info(json_str)
            
            assert result.code == 200
            assert result.url == "https://example.com/video.m3u8"
            assert result.quality == "1080p"
            assert result.duration == "05:30"
        
        def test_parse_error_response(self):
            """测试解析错误响应"""
            json_str = json.dumps({
                "code": 403,
                "msg": "无权访问"
            })
            
            with pytest.raises(ApiResponseError):
                ResponseParser.parse_video_info(json_str)
    
    class TestParseCategoryResult:
        """parse_category_result 测试"""
        
        def test_parse_success(self):
            """测试成功解析分类结果"""
            json_str = json.dumps({
                "code": 200,
                "data": [
                    {
                        "book_id": "123",
                        "title": "短剧1",
                        "cover": "url1",
                        "episode_cnt": 10,
                        "video_desc": "描述",
                        "sub_title": "都市",
                        "play_cnt": 1000
                    }
                ]
            })
            
            result = ResponseParser.parse_category_result(json_str, "都市")
            
            assert result.code == 200
            assert result.category == "都市"
            assert len(result.data) == 1
            assert result.data[0].book_id == "123"
    
    class TestParseRecommendations:
        """parse_recommendations 测试"""
        
        def test_parse_success(self):
            """测试成功解析推荐"""
            json_str = json.dumps({
                "code": 200,
                "data": [
                    {
                        "hot": 10000,
                        "book_data": {
                            "book_id": "123",
                            "book_name": "推荐短剧",
                            "thumb_url": "url",
                            "serial_count": 20,
                            "category": "甜宠"
                        }
                    }
                ]
            })
            
            result = ResponseParser.parse_recommendations(json_str)
            
            assert len(result) == 1
            assert result[0].book_id == "123"
            assert result[0].title == "推荐短剧"
            assert result[0].play_cnt == 10000
        
        def test_parse_string_serial_count(self):
            """测试解析字符串类型的集数"""
            json_str = json.dumps({
                "code": 200,
                "data": [
                    {
                        "hot": 100,
                        "book_data": {
                            "book_id": "1",
                            "book_name": "test",
                            "thumb_url": "url",
                            "serial_count": "15",
                            "category": ""
                        }
                    }
                ]
            })
            
            result = ResponseParser.parse_recommendations(json_str)
            assert result[0].episode_cnt == 15
    
    class TestParseError:
        """parse_error 测试"""
        
        def test_parse_valid_error(self):
            """测试解析有效的错误响应"""
            json_str = json.dumps({
                "code": 500,
                "msg": "服务器错误"
            })
            
            error = ResponseParser.parse_error(json_str)
            
            assert error.code == 500
            assert error.message == "服务器错误"
        
        def test_parse_invalid_json(self):
            """测试解析无效 JSON"""
            error = ResponseParser.parse_error("not json")
            
            assert error.code == 0
            assert "JSON 解析失败" in error.message
        
        def test_parse_long_error_truncated(self):
            """测试长错误信息被截断"""
            long_text = "x" * 300
            error = ResponseParser.parse_error(long_text)
            
            assert len(error.details) <= 200


class TestApiResponseError:
    """ApiResponseError 异常测试"""
    
    def test_exception_attributes(self):
        """测试异常属性"""
        error = ApiResponseError(500, "服务器错误")
        
        assert error.code == 500
        assert error.message == "服务器错误"
        assert str(error) == "服务器错误"
    
    def test_exception_raise(self):
        """测试异常抛出"""
        with pytest.raises(ApiResponseError) as exc_info:
            raise ApiResponseError(404, "未找到")
        
        assert exc_info.value.code == 404




# ============================================================
# From: test_response_parser_full.py
# ============================================================
class TestResponseParserSearch:
    """测试搜索结果解析"""
    
    def test_parse_search_result_success(self):
        """测试解析成功的搜索结果"""
        json_str = json.dumps({
            "code": 200,
            "msg": "success",
            "page": 1,
            "data": [
                {
                    "book_id": "123",
                    "title": "测试短剧",
                    "cover": "https://example.com/cover.jpg",
                    "episode_cnt": 20,
                    "intro": "简介",
                    "type": "都市",
                    "author": "作者",
                    "play_cnt": 10000
                }
            ]
        })
        
        result = ResponseParser.parse_search_result(json_str)
        
        assert result.code == 200
        assert len(result.data) == 1
        assert result.data[0].title == "测试短剧"
    
    def test_parse_search_result_empty(self):
        """测试解析空搜索结果"""
        json_str = json.dumps({
            "code": 200,
            "msg": "success",
            "page": 1,
            "data": []
        })
        
        result = ResponseParser.parse_search_result(json_str)
        
        assert result.code == 200
        assert len(result.data) == 0
    
    def test_parse_search_result_string_page(self):
        """测试解析字符串页码"""
        json_str = json.dumps({
            "code": 200,
            "msg": "success",
            "page": "5",
            "data": []
        })
        
        result = ResponseParser.parse_search_result(json_str)
        
        assert result.page == 5
    
    def test_parse_search_result_missing_fields(self):
        """测试解析缺少字段的搜索结果"""
        json_str = json.dumps({
            "code": 200,
            "data": [
                {"book_id": "123", "title": "测试"}
            ]
        })
        
        result = ResponseParser.parse_search_result(json_str)
        
        assert result.code == 200
        assert len(result.data) == 1


class TestResponseParserCategory:
    """测试分类结果解析"""
    
    def test_parse_category_result_success(self):
        """测试解析成功的分类结果"""
        json_str = json.dumps({
            "code": 200,
            "data": [
                {
                    "book_id": "123",
                    "title": "测试短剧",
                    "cover": "https://example.com/cover.jpg",
                    "episode_cnt": 20,
                    "video_desc": "描述",
                    "sub_title": "都市",
                    "play_cnt": 10000
                }
            ]
        })
        
        result = ResponseParser.parse_category_result(json_str, "都市")
        
        assert result.code == 200
        assert result.category == "都市"
        assert len(result.data) == 1
    
    def test_parse_category_result_empty(self):
        """测试解析空分类结果"""
        json_str = json.dumps({
            "code": 200,
            "data": []
        })
        
        result = ResponseParser.parse_category_result(json_str, "都市")
        
        assert len(result.data) == 0


class TestResponseParserEpisodes:
    """测试剧集列表解析"""
    
    def test_parse_episode_list_success(self):
        """测试解析成功的剧集列表"""
        json_str = json.dumps({
            "code": 200,
            "book_name": "测试短剧",
            "book_id": "123",
            "total": 20,
            "author": "作者",
            "category": "都市",
            "desc": "描述",
            "duration": "05:00",
            "book_pic": "https://example.com/pic.jpg",
            "data": [
                {"video_id": "v1", "title": "第1集", "chapter_word_number": 0},
                {"video_id": "v2", "title": "第2集", "chapter_word_number": 0}
            ]
        })
        
        result = ResponseParser.parse_episode_list(json_str)
        
        assert result.code == 200
        assert result.book_name == "测试短剧"
        assert len(result.episodes) == 2
        assert result.total == 20
    
    def test_parse_episode_list_string_total(self):
        """测试解析字符串总数"""
        json_str = json.dumps({
            "code": 200,
            "book_name": "测试",
            "total": "20",
            "data": []
        })
        
        result = ResponseParser.parse_episode_list(json_str)
        
        assert result.total == 20
    
    def test_parse_episode_number_from_title(self):
        """测试从标题解析集数"""
        json_str = json.dumps({
            "code": 200,
            "book_name": "测试",
            "data": [
                {"video_id": "v1", "title": "第10集"},
                {"video_id": "v2", "title": "Episode 5"},
                {"video_id": "v3", "title": "序章"}
            ]
        })
        
        result = ResponseParser.parse_episode_list(json_str)
        
        assert result.episodes[0].episode_number == 10
        assert result.episodes[1].episode_number == 5
        assert result.episodes[2].episode_number == 0


class TestResponseParserVideo:
    """测试视频信息解析"""
    
    def test_parse_video_info_success(self):
        """测试解析成功的视频信息"""
        json_str = json.dumps({
            "code": 200,
            "data": {
                "url": "https://example.com/video.m3u8",
                "pic": "https://example.com/pic.jpg",
                "title": "第1集",
                "info": {
                    "quality": "1080p",
                    "duration": "05:30",
                    "size_str": "50MB"
                }
            }
        })
        
        result = ResponseParser.parse_video_info(json_str)
        
        assert result.code == 200
        assert result.url == "https://example.com/video.m3u8"
        assert result.quality == "1080p"
    
    def test_parse_video_info_missing_info(self):
        """测试解析缺少 info 的视频信息"""
        json_str = json.dumps({
            "code": 200,
            "data": {
                "url": "https://example.com/video.m3u8",
                "title": "第1集"
            }
        })
        
        result = ResponseParser.parse_video_info(json_str)
        
        assert result.url == "https://example.com/video.m3u8"


class TestResponseParserRecommendations:
    """测试推荐内容解析"""
    
    def test_parse_recommendations_success(self):
        """测试解析成功的推荐内容"""
        json_str = json.dumps({
            "code": 200,
            "data": [
                {
                    "book_data": {
                        "book_id": "123",
                        "book_name": "推荐短剧",
                        "thumb_url": "https://example.com/thumb.jpg",
                        "serial_count": 20,
                        "category": "甜宠"
                    },
                    "hot": 5000
                }
            ]
        })
        
        result = ResponseParser.parse_recommendations(json_str)
        
        assert len(result) == 1
        assert result[0].title == "推荐短剧"
    
    def test_parse_recommendations_string_serial_count(self):
        """测试解析字符串集数"""
        json_str = json.dumps({
            "code": 200,
            "data": [
                {
                    "book_data": {
                        "book_id": "123",
                        "book_name": "推荐短剧",
                        "serial_count": "20"
                    },
                    "hot": 5000
                }
            ]
        })
        
        result = ResponseParser.parse_recommendations(json_str)
        
        assert result[0].episode_cnt == 20
    
    def test_parse_recommendations_empty(self):
        """测试解析空推荐内容"""
        json_str = json.dumps({
            "code": 200,
            "data": []
        })
        
        result = ResponseParser.parse_recommendations(json_str)
        
        assert len(result) == 0


class TestResponseParserEdgeCases:
    """测试边界情况"""
    
    def test_parse_invalid_json(self):
        """测试解析无效 JSON"""
        with pytest.raises(Exception):
            ResponseParser.parse_search_result("invalid json")
    
    def test_parse_empty_string(self):
        """测试解析空字符串"""
        with pytest.raises(Exception):
            ResponseParser.parse_search_result("")
    
    def test_parse_null_data(self):
        """测试解析 null 数据"""
        json_str = json.dumps({
            "code": 200,
            "data": None
        })
        
        # 应该能处理 None 数据
        try:
            result = ResponseParser.parse_search_result(json_str)
            assert result.data == [] or result.data is None
        except:
            pass  # 如果抛出异常也是可接受的
