"""Weekly website URL check — run via GitHub Actions or cron."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from app.db import get_supabase_service
from app.user_secrets import load_user_api_key_for_worker
from jobs.website_utils import fetch_page_links, page_content_hash
from jobs.worker import process_article_and_notify


def main() -> None:
    if not os.environ.get("ENCRYPTION_KEY"):
        raise SystemExit("ENCRYPTION_KEY required to decrypt user API keys.")

    client = get_supabase_service()
    urls = client.table("tracked_urls").select("*").execute().data or []
    print(f"Checking {len(urls)} URL(s)...")

    for tracked in urls:
        user_id = tracked["user_id"]
        row_id = tracked["id"]
        site_url = tracked["url"]
        site_name = tracked.get("site_name", site_url)

        profile = (
            client.table("profiles")
            .select("notification_email")
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        email = profile.data.get("notification_email") if profile.data else None
        if not email:
            print(f"  Skip {site_name}: no notification email")
            continue

        if not load_user_api_key_for_worker(user_id):
            print(f"  Skip {site_name}: user has no saved API key for automation")
            continue

        processed = (
            client.table("processed_articles")
            .select("content_hash")
            .eq("tracked_url_id", row_id)
            .execute()
        )
        known_hashes = {r["content_hash"] for r in (processed.data or [])}

        try:
            articles = fetch_page_links(site_url)
            if not articles:
                content_hash = page_content_hash(site_url)
                articles = [
                    {
                        "title": site_name,
                        "article_url": site_url,
                        "content_hash": content_hash,
                    }
                ]

            for article in articles:
                if article["content_hash"] in known_hashes:
                    continue
                print(f"  New content: {article['title']}")
                try:
                    process_article_and_notify(
                        user_id=user_id,
                        notification_email=email,
                        article_url=article["article_url"],
                        title=article["title"],
                        content_hash=article["content_hash"],
                        tracked_url_id=row_id,
                        topic=article["title"],
                    )
                except Exception as exc:
                    print(f"  Error processing {article['article_url']}: {exc}")

            client.table("tracked_urls").update(
                {"last_checked_at": datetime.now(timezone.utc).isoformat()}
            ).eq("id", row_id).execute()

        except Exception as exc:
            print(f"  Error fetching {site_url}: {exc}")

    print("Website check complete.", datetime.now(timezone.utc).isoformat())


if __name__ == "__main__":
    main()
