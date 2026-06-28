"""Daily YouTube channel check — run via GitHub Actions or cron."""

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
from jobs.worker import process_video_and_notify
from jobs.youtube_utils import fetch_latest_videos


def main() -> None:
    if not os.environ.get("ENCRYPTION_KEY"):
        raise SystemExit("ENCRYPTION_KEY required to decrypt user API keys.")

    client = get_supabase_service()
    channels = client.table("youtube_channels").select("*").execute().data or []
    print(f"Checking {len(channels)} channel(s)...")

    for channel in channels:
        channel_id = channel["channel_id"]
        user_id = channel["user_id"]
        row_id = channel["id"]

        profile = (
            client.table("profiles")
            .select("notification_email")
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        email = profile.data.get("notification_email") if profile.data else None
        if not email:
            print(f"  Skip channel {channel_id}: no notification email")
            continue

        if not load_user_api_key_for_worker(user_id):
            print(f"  Skip channel {channel_id}: user has no saved API key for automation")
            continue

        processed = (
            client.table("processed_videos")
            .select("video_id")
            .eq("channel_id", row_id)
            .execute()
        )
        known_ids = {r["video_id"] for r in (processed.data or [])}

        for video in fetch_latest_videos(channel_id, limit=3):
            if video["video_id"] in known_ids:
                continue
            print(f"  New video: {video['title']}")
            try:
                process_video_and_notify(
                    user_id=user_id,
                    notification_email=email,
                    video_url=video["video_url"],
                    video_id=video["video_id"],
                    title=video["title"],
                    channel_row_id=row_id,
                )
            except Exception as exc:
                print(f"  Error processing {video['video_id']}: {exc}")

    print("YouTube check complete.", datetime.now(timezone.utc).isoformat())


if __name__ == "__main__":
    main()
