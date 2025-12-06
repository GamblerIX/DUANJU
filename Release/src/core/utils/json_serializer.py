import json
from typing import Any, Dict, List
from ..models import AppConfig, ThemeMode, DramaInfo, EpisodeInfo


def serialize_config(config: AppConfig) -> str:
    data = {
        "apiTimeout": config.api_timeout,
        "defaultQuality": config.default_quality,
        "themeMode": config.theme_mode.value,
        "lastSearchKeyword": config.last_search_keyword,
        "searchHistory": config.search_history,
        "maxSearchHistory": config.max_search_history
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def deserialize_config(json_str: str) -> AppConfig:
    data = json.loads(json_str)
    return AppConfig(
        api_timeout=data.get("apiTimeout", 10000),
        default_quality=data.get("defaultQuality", "1080p"),
        theme_mode=ThemeMode(data.get("themeMode", "auto")),
        last_search_keyword=data.get("lastSearchKeyword", ""),
        search_history=data.get("searchHistory", []),
        max_search_history=data.get("maxSearchHistory", 20)
    )


def serialize_drama(drama: DramaInfo) -> Dict[str, Any]:
    return {
        "book_id": drama.book_id, "title": drama.title, "cover": drama.cover,
        "episode_cnt": drama.episode_cnt, "intro": drama.intro, "type": drama.type,
        "author": drama.author, "play_cnt": drama.play_cnt
    }


def deserialize_drama(data: Dict[str, Any]) -> DramaInfo:
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
    return {
        "video_id": episode.video_id, "title": episode.title,
        "episode_number": episode.episode_number, "chapter_word_number": episode.chapter_word_number
    }


def deserialize_episode(data: Dict[str, Any]) -> EpisodeInfo:
    return EpisodeInfo(
        video_id=data.get("video_id", data.get("videoId", "")),
        title=data.get("title", ""),
        episode_number=data.get("episode_number", data.get("episodeNumber", 0)),
        chapter_word_number=data.get("chapter_word_number", 0)
    )


def serialize_dramas(dramas: List[DramaInfo]) -> str:
    return json.dumps([serialize_drama(d) for d in dramas], ensure_ascii=False)


def deserialize_dramas(json_str: str) -> List[DramaInfo]:
    data = json.loads(json_str)
    return [deserialize_drama(d) for d in data]
