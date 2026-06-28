"""Website monitoring helpers."""

from __future__ import annotations

import hashlib
import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AIContentTracker/1.0)",
}


def fetch_page_links(url: str, same_domain: bool = True) -> list[dict]:
    """Fetch a page and return candidate article links with content hashes."""
    response = requests.get(url, timeout=20, headers=DEFAULT_HEADERS)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    base_domain = urlparse(url).netloc
    articles = []

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if not href or href.startswith("#") or href.startswith("mailto:"):
            continue
        full_url = urljoin(url, href)
        if same_domain and urlparse(full_url).netloc != base_domain:
            continue
        title = anchor.get_text(strip=True)
        if not title or len(title) < 10:
            continue
        if not _looks_like_article(full_url, title):
            continue
        content_hash = hashlib.sha256(full_url.encode()).hexdigest()[:16]
        articles.append(
            {
                "title": title[:200],
                "article_url": full_url,
                "content_hash": content_hash,
            }
        )

    # Deduplicate by URL
    seen = set()
    unique = []
    for item in articles:
        if item["article_url"] in seen:
            continue
        seen.add(item["article_url"])
        unique.append(item)
    return unique[:20]


def _looks_like_article(url: str, title: str) -> bool:
    lower = url.lower()
    skip_ext = (".png", ".jpg", ".pdf", ".css", ".js", "/login", "/signup")
    if any(ext in lower for ext in skip_ext):
        return False
    if len(title.split()) < 3:
        return False
    return True


def page_content_hash(url: str) -> str:
    """Hash main text content of a page for change detection."""
    response = requests.get(url, timeout=20, headers=DEFAULT_HEADERS)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = re.sub(r"\s+", " ", soup.get_text(separator=" ", strip=True))
    return hashlib.sha256(text[:5000].encode()).hexdigest()[:16]
