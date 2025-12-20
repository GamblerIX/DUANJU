"""API 响应解析器模块

根据短剧 API 文档解析各种响应格式，将 JSON 响应转换为数据模型对象。
"""
import json
import re
from typing import List, Optional, Tuple

from ..core.models import (
    DramaInfo, 
    EpisodeInfo, 
    EpisodeList, 
    VideoInfo, 
    SearchResult, 
    CategoryResult,
    ApiError
)


class ApiResponseError(Exception):
    """API 响应错误异常"""
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class ResponseParser:
    """API 响应解析器"""
    
    @staticmethod
    def check_response_status(data: dict) -> Tuple[bool, Optional[str]]:
        """检查 API 响应状态码"""
        code = data.get("code", 0)
        if code == 200:
            return True, None
        else:
            msg = data.get("msg", "未知错误")
            return False, msg
    
    @staticmethod
    def parse_search_result(json_str: str) -> SearchResult:
        """解析搜索响应"""
        data = json.loads(json_str)
        
        # 检查 API 返回的错误码
        code = data.get("code", 0)
        if code != 200:
            msg = data.get("msg", "未知错误")
            tips = data.get("tips", "")
            error_msg = msg
            if tips:
                error_msg = f"{msg}\n{tips}"
            raise ApiResponseError(code, error_msg)
        
        dramas = []
        for item in data.get("data", []):
            dramas.append(DramaInfo(
                book_id=str(item.get("book_id", "")),
                title=item.get("title", ""),
                cover=item.get("cover", ""),
                episode_cnt=int(item.get("episode_cnt", 0)),
                intro=item.get("intro", ""),
                type=item.get("type", ""),
                author=item.get("author", ""),
                play_cnt=int(item.get("play_cnt", 0))
            ))
        
        page = data.get("page", 1)
        if isinstance(page, str):
            page = int(page) if page.isdigit() else 1
        
        return SearchResult(
            code=code,
            msg=data.get("msg", ""),
            data=dramas,
            page=page
        )
    
    @staticmethod
    def parse_episode_number(title: str) -> int:
        """从标题中解析集数编号"""
        match = re.search(r'第(\d+)集', title)
        if match:
            return int(match.group(1))
        match = re.search(r'(\d+)', title)
        if match:
            return int(match.group(1))
        return 0

    @staticmethod
    def parse_episode_list(json_str: str) -> EpisodeList:
        """解析剧集列表响应"""
        data = json.loads(json_str)
        
        # 检查 API 返回的错误码
        code = data.get("code", 0)
        if code != 200:
            msg = data.get("msg", "未知错误")
            tips = data.get("tips", "")
            error_msg = msg
            if tips:
                error_msg = f"{msg}\n{tips}"
            raise ApiResponseError(code, error_msg)
        
        episodes = []
        for item in data.get("data", []):
            title = item.get("title", "")
            episodes.append(EpisodeInfo(
                video_id=str(item.get("video_id", "")),
                title=title,
                episode_number=ResponseParser.parse_episode_number(title),
                chapter_word_number=int(item.get("chapter_word_number", 0))
            ))
        
        total = data.get("total", 0)
        if isinstance(total, str):
            total = int(total) if total.isdigit() else 0
        
        return EpisodeList(
            code=code,
            book_name=data.get("book_name", ""),
            episodes=episodes,
            total=total,
            book_id=str(data.get("book_id", "")),
            author=data.get("author", ""),
            category=data.get("category", ""),
            desc=data.get("desc", ""),
            duration=data.get("duration", ""),
            book_pic=data.get("book_pic", "")
        )
    
    @staticmethod
    def parse_video_info(json_str: str) -> VideoInfo:
        """解析视频信息响应"""
        data = json.loads(json_str)
        
        # 检查 API 返回的错误码
        code = data.get("code", 0)
        if code != 200:
            msg = data.get("msg", "未知错误")
            tips = data.get("tips", "")
            error_msg = msg
            if tips:
                error_msg = f"{msg}\n{tips}"
            raise ApiResponseError(code, error_msg)
        
        video_data = data.get("data", {})
        info = video_data.get("info", {})
        
        return VideoInfo(
            code=code,
            url=video_data.get("url", ""),
            pic=video_data.get("pic", ""),
            quality=info.get("quality", ""),
            title=video_data.get("title", ""),
            duration=info.get("duration", ""),
            size_str=info.get("size_str", "")
        )
    
    @staticmethod
    def parse_category_result(json_str: str, category: str = "") -> CategoryResult:
        """解析分类响应"""
        data = json.loads(json_str)
        
        # 检查 API 返回的错误码
        code = data.get("code", 0)
        if code != 200:
            msg = data.get("msg", "未知错误")
            tips = data.get("tips", "")
            error_msg = msg
            if tips:
                error_msg = f"{msg}\n{tips}"
            raise ApiResponseError(code, error_msg)
        
        dramas = []
        for item in data.get("data", []):
            dramas.append(DramaInfo(
                book_id=str(item.get("book_id", "")),
                title=item.get("title", ""),
                cover=item.get("cover", ""),
                episode_cnt=int(item.get("episode_cnt", 0)),
                intro=item.get("video_desc", ""),
                type=item.get("sub_title", category),
                author="",
                play_cnt=int(item.get("play_cnt", 0))
            ))
        
        return CategoryResult(
            code=code,
            category=category,
            data=dramas,
            offset=1
        )
    
    @staticmethod
    def parse_recommendations(json_str: str) -> List[DramaInfo]:
        """解析推荐响应"""
        data = json.loads(json_str)
        
        # 检查 API 返回的错误码
        code = data.get("code", 0)
        if code != 200:
            msg = data.get("msg", "未知错误")
            tips = data.get("tips", "")
            error_msg = msg
            if tips:
                error_msg = f"{msg}\n{tips}"
            raise ApiResponseError(code, error_msg)
        
        dramas = []
        for item in data.get("data", []):
            book_data = item.get("book_data", {})
            
            serial_count = book_data.get("serial_count", 0)
            if isinstance(serial_count, str):
                serial_count = int(serial_count) if serial_count.isdigit() else 0
            
            dramas.append(DramaInfo(
                book_id=str(book_data.get("book_id", "")),
                title=book_data.get("book_name", ""),
                cover=book_data.get("thumb_url", ""),
                episode_cnt=serial_count,
                intro="",
                type=book_data.get("category", ""),
                author="",
                play_cnt=int(item.get("hot", 0))
            ))
        
        return dramas
    
    @staticmethod
    def parse_error(json_str: str) -> ApiError:
        """解析错误响应"""
        try:
            data = json.loads(json_str)
            return ApiError(
                code=data.get("code", 0),
                message=data.get("msg", "未知错误"),
                details=""
            )
        except json.JSONDecodeError:
            return ApiError(
                code=0,
                message="JSON 解析失败",
                details=json_str[:200] if len(json_str) > 200 else json_str
            )
