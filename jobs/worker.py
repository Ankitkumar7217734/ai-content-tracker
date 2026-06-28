"""Shared worker: run crew, save report, send email."""

from __future__ import annotations

from datetime import datetime, timezone

from app.db import get_supabase_service
from app.user_secrets import load_user_api_key_for_worker
from crew.factory import run_video_crew, run_website_crew
from jobs.email_utils import send_report_email


def save_report(
    *,
    user_id: str,
    source_type: str,
    source_url: str,
    topic: str,
    markdown: str,
) -> str | None:
    client = get_supabase_service()
    row = {
        "user_id": user_id,
        "source_type": source_type,
        "source_url": source_url,
        "topic": topic,
        "markdown": markdown,
    }
    result = client.table("reports").insert(row).execute()
    if result.data:
        return result.data[0]["id"]
    return None


def _require_user_api_key(user_id: str) -> str:
    api_key = load_user_api_key_for_worker(user_id)
    if not api_key:
        raise RuntimeError(
            f"User {user_id} has no saved API key for scheduled jobs. "
            "They must save one in Settings → API key."
        )
    return api_key


def process_video_and_notify(
    *,
    user_id: str,
    notification_email: str,
    video_url: str,
    video_id: str,
    title: str,
    topic: str | None = None,
    channel_row_id: str | None = None,
    openai_api_key: str | None = None,
) -> str:
    api_key = openai_api_key or _require_user_api_key(user_id)
    report_topic = topic or title
    markdown = run_video_crew(
        openai_api_key=api_key,
        video_url=video_url,
        topic=report_topic,
    )
    save_report(
        user_id=user_id,
        source_type="youtube",
        source_url=video_url,
        topic=report_topic,
        markdown=markdown,
    )
    if channel_row_id:
        client = get_supabase_service()
        client.table("processed_videos").insert(
            {
                "channel_id": channel_row_id,
                "video_id": video_id,
                "title": title,
                "video_url": video_url,
                "emailed_at": datetime.now(timezone.utc).isoformat(),
            }
        ).execute()

    send_report_email(
        to_email=notification_email,
        subject=f"New video report: {title}",
        markdown_body=markdown,
        source_url=video_url,
    )
    return markdown


def process_article_and_notify(
    *,
    user_id: str,
    notification_email: str,
    article_url: str,
    title: str,
    content_hash: str,
    tracked_url_id: str,
    topic: str | None = None,
    openai_api_key: str | None = None,
) -> str:
    api_key = openai_api_key or _require_user_api_key(user_id)
    report_topic = topic or title
    markdown = run_website_crew(
        openai_api_key=api_key,
        website_url=article_url,
        topic=report_topic,
    )
    save_report(
        user_id=user_id,
        source_type="website",
        source_url=article_url,
        topic=report_topic,
        markdown=markdown,
    )
    client = get_supabase_service()
    client.table("processed_articles").insert(
        {
            "tracked_url_id": tracked_url_id,
            "content_hash": content_hash,
            "title": title,
            "article_url": article_url,
            "emailed_at": datetime.now(timezone.utc).isoformat(),
        }
    ).execute()

    send_report_email(
        to_email=notification_email,
        subject=f"New article report: {title}",
        markdown_body=markdown,
        source_url=article_url,
    )
    return markdown
