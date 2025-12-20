"""JSON 序列化工具函数"""
import json
from typing import Any, Dict, List
from ..core.models import AppConfig, ThemeMode, DramaInfo, EpisodeInfo


def serialize_config(config: AppConfig) -> str:
    """序列化配置对象为 JSON 字符串"""
    data = {
        "apiTimeout": config.api_timeout,
        "defaultQuality": config.default_quality,
        "themeMode": config.theme_mode.value,
        "lastSearchKeyword": config.last_search_keyword,
        "searchHistory": config.search_history,
        "maxSearchHistory": config.max_search_history,
        "currentProvider": config.current_provider,
        "enableCache": config.enable_cache,
        "cacheTTL": config.cache_ttl,
        "maxRetries": config.max_retries,
        "retryDelay": config.retry_delay
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def deserialize_config(json_str: str) -> AppConfig:
    """反序列化 JSON 字符串为配置对象"""
    data = json.loads(json_str)
    
    return AppConfig(
        api_timeout=data.get("apiTimeout", 10000),
        default_quality=data.get("defaultQuality", "1080p"),
        theme_mode=ThemeMode(data.get("themeMode", "auto")),
        last_search_keyword=data.get("lastSearchKeyword", ""),
        search_history=data.get("searchHistory", []),
        max_search_history=data.get("maxSearchHistory", 20),
        current_provider=data.get("currentProvider", "cenguigui"),
        enable_cache=data.get("enableCache", True),
        cache_ttl=data.get("cacheTTL", 300000),
        max_retries=data.get("maxRetries", 3),
        retry_delay=data.get("retryDelay", 1000)
    )


def serialize_drama(drama: DramaInfo) -> Dict[str, Any]:
    """序列化短剧信息为字典"""
    return {
        "book_id": drama.book_id,
        "title": drama.title,
        "cover": drama.cover,
        "episode_cnt": drama.episode_cnt,
        "intro": drama.intro,
        "type": drama.type,
        "author": drama.author,
        "play_cnt": drama.play_cnt
    }


def deserialize_drama(data: Dict[str, Any]) -> DramaInfo:
    """反序列化字典为短剧信息"""
    return DramaInfo(
        book_id=data.get("book_id", data.get("bookId", "")),
        title=data.get("title", data.get("name", "")),
        cover=data.get("cover", data.get("coverUrl", "")),
        episode_cnt=data.get("episode_cnt", data.get("episodeCount", 0)),
        intro=data.get("intro", data.get("description", "")),
        type=data.get("type", data.get("category", "")),
        author=data.get("author", ""),
        play_cnt=data.get("play_cnt", 0)
    )


def serialize_episode(episode: EpisodeInfo) -> Dict[str, Any]:
    """序列化剧集信息为字典"""
    return {
        "video_id": episode.video_id,
        "title": episode.title,
        "episode_number": episode.episode_number,
        "chapter_word_number": episode.chapter_word_number
    }


def deserialize_episode(data: Dict[str, Any]) -> EpisodeInfo:
    """反序列化字典为剧集信息"""
    return EpisodeInfo(
        video_id=data.get("video_id", data.get("videoId", "")),
        title=data.get("title", ""),
        episode_number=data.get("episode_number", data.get("episodeNumber", 0)),
        chapter_word_number=data.get("chapter_word_number", 0)
    )


def serialize_dramas(dramas: List[DramaInfo]) -> str:
    """序列化短剧列表为 JSON 字符串"""
    return json.dumps([serialize_drama(d) for d in dramas], ensure_ascii=False)


def deserialize_dramas(json_str: str) -> List[DramaInfo]:
    """反序列化 JSON 字符串为短剧列表"""
    data = json.loads(json_str)
    return [deserialize_drama(d) for d in data]
