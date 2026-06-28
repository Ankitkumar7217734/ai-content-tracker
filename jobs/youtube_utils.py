"""YouTube channel helpers — RSS-based, no API key required."""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

import feedparser
import requests

RSS_TEMPLATE = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


def extract_channel_id(channel_url: str) -> str | None:
    """Resolve a YouTube channel URL or @handle to a channel_id (UC...)."""
    url = channel_url.strip()
    if url.startswith("@"):
        url = f"https://www.youtube.com/{url}"

    if "/channel/" in url:
        match = re.search(r"/channel/(UC[\w-]+)", url)
        return match.group(1) if match else None

    if "/@" in url or "youtube.com/@" in url:
        handle = url.split("/@")[-1].split("/")[0].split("?")[0]
        return _resolve_handle_to_channel_id(handle)

    return None


def _resolve_handle_to_channel_id(handle: str) -> str | None:
    """Fetch channel page and extract channel_id from HTML meta tags."""
    page_url = f"https://www.youtube.com/@{handle}"
    try:
        response = requests.get(page_url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        match = re.search(r'"channelId":"(UC[\w-]+)"', response.text)
        if match:
            return match.group(1)
        match = re.search(r'<meta itemprop="channelId" content="(UC[\w-]+)"', response.text)
        if match:
            return match.group(1)
    except requests.RequestException:
        return None
    return None


def fetch_latest_videos(channel_id: str, limit: int = 5) -> list[dict]:
    """Return recent videos from a channel RSS feed."""
    feed = feedparser.parse(RSS_TEMPLATE.format(channel_id=channel_id))
    videos = []
    for entry in feed.entries[:limit]:
        video_id = _entry_video_id(entry)
        if not video_id:
            continue
        videos.append(
            {
                "video_id": video_id,
                "title": entry.get("title", ""),
                "video_url": f"https://www.youtube.com/watch?v={video_id}",
                "published": entry.get("published", ""),
            }
        )
    return videos


def _entry_video_id(entry) -> str | None:
    link = entry.get("link", "")
    if "v=" in link:
        return parse_qs(urlparse(link).query).get("v", [None])[0]
    video_id = entry.get("yt_videoid")
    return video_id
