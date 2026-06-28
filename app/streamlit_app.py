"""AI Content Tracker — Streamlit entrypoint."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from app.auth import get_authed_client, render_auth_form, sign_out
from app.pdf_utils import markdown_to_pdf_bytes
from app.user_secrets import (
    delete_user_api_key,
    get_user_secrets_row,
    load_user_api_key_for_client,
    save_user_api_key,
    user_has_saved_api_key,
    user_scheduling_enabled,
)
from crew.factory import run_video_crew, run_website_crew, topic_to_filename
from jobs.youtube_utils import extract_channel_id

st.set_page_config(page_title="AI Content Tracker", page_icon="📡", layout="wide")


def _require_env() -> bool:
    missing = []
    for key in ("SUPABASE_URL", "SUPABASE_ANON_KEY", "ENCRYPTION_KEY"):
        import os

        if not os.environ.get(key):
            missing.append(key)
    if missing:
        st.error(f"Missing environment variables: {', '.join(missing)}")
        st.info("Add them to `.env` or Streamlit Cloud secrets.")
        return False
    return True


def _automation_key_banner(client) -> None:
    if not user_scheduling_enabled(client, user_id=st.session_state.user_id):
        st.warning(
            "Save your OpenAI API key in **Settings** and enable scheduled reports "
            "to receive automatic summaries by email when new content is detected."
        )


def page_generate_report() -> None:
    st.header("Generate Report")
    st.caption("Paste a YouTube or website URL and topic. Uses your saved API key or a one-time key.")

    client = get_authed_client()
    if not client:
        return

    has_saved = user_has_saved_api_key(client, user_id=st.session_state.user_id)
    if has_saved:
        st.info("Using your saved OpenAI API key from Settings (or paste a different key below).")

    api_key = st.text_input(
        "OpenAI API Key (optional if saved)",
        type="password",
        placeholder="sk-..." if has_saved else "Required",
    )
    save_key = False
    if api_key.strip():
        save_key = st.checkbox("Save this API key for automatic scheduled reports", value=False)

    video_url = st.text_input("YouTube Video URL", placeholder="https://www.youtube.com/watch?v=...")
    topic = st.text_input("Topic", placeholder="e.g. AI vs ML vs Data Science")
    source_type = st.radio("Source type", ["YouTube video", "Website URL"], horizontal=True)

    website_url = ""
    if source_type == "Website URL":
        website_url = st.text_input("Website URL", placeholder="https://openai.com/news/...")

    effective_key = api_key.strip() or (load_user_api_key_for_client(client, user_id=st.session_state.user_id) if has_saved else "")
    can_generate = bool(effective_key and topic)

    if st.button("Generate Report", type="primary", disabled=not can_generate):
        if source_type == "YouTube video" and not video_url:
            st.warning("Please enter a YouTube video URL.")
            return
        if source_type == "Website URL" and not website_url:
            st.warning("Please enter a website URL.")
            return

        if save_key and api_key.strip():
            try:
                save_user_api_key(
                    client,
                    user_id=st.session_state.user_id,
                    openai_api_key=api_key.strip(),
                    allow_scheduled_jobs=True,
                )
                st.toast("API key saved for automation.")
            except Exception as exc:
                st.error(f"Could not save API key: {exc}")
                return

        with st.spinner("Running CrewAI agents… this may take 1–2 minutes."):
            try:
                if source_type == "YouTube video":
                    report = run_video_crew(
                        openai_api_key=effective_key,
                        video_url=video_url,
                        topic=topic,
                    )
                    source_url = video_url
                    db_type = "manual"
                else:
                    report = run_website_crew(
                        openai_api_key=effective_key,
                        website_url=website_url,
                        topic=topic,
                    )
                    source_url = website_url
                    db_type = "website"

                st.session_state["last_report"] = report
                st.session_state["last_topic"] = topic

                client.table("reports").insert(
                    {
                        "user_id": st.session_state.user_id,
                        "source_type": db_type,
                        "source_url": source_url,
                        "topic": topic,
                        "markdown": report,
                    }
                ).execute()
            except Exception as exc:
                st.error(f"Report generation failed: {exc}")
                return

        st.success("Report generated!")

    if st.session_state.get("last_report"):
        st.markdown("---")
        st.subheader("Report")
        st.markdown(st.session_state["last_report"])
        report = st.session_state["last_report"]
        filename = topic_to_filename(st.session_state.get("last_topic", "report"))
        st.download_button("Download Markdown", report, file_name=filename, mime="text/markdown")
        try:
            pdf_bytes = markdown_to_pdf_bytes(report, st.session_state.get("last_topic", "Report"))
            st.download_button(
                "Download PDF",
                pdf_bytes,
                file_name=filename.replace(".md", ".pdf"),
                mime="application/pdf",
            )
        except Exception as exc:
            st.warning(f"PDF export failed: {exc}")


def page_track_youtube() -> None:
    st.header("Track YouTube Channels")
    st.caption("Checked every 24 hours. You'll receive an email when a new video is published.")

    client = get_authed_client()
    if not client:
        return

    _automation_key_banner(client)

    with st.form("add_channel"):
        channel_url = st.text_input(
            "Channel URL",
            placeholder="https://www.youtube.com/@krishnaik06",
        )
        channel_name = st.text_input("Label (optional)", placeholder="Krish Naik")
        if st.form_submit_button("Add channel"):
            channel_id = extract_channel_id(channel_url)
            if not channel_id:
                st.error("Could not resolve channel ID. Use a full channel URL or @handle.")
            else:
                try:
                    client.table("youtube_channels").insert(
                        {
                            "user_id": st.session_state.user_id,
                            "channel_id": channel_id,
                            "channel_url": channel_url,
                            "channel_name": channel_name or channel_id,
                        }
                    ).execute()
                    st.success(f"Added channel ({channel_id})")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    channels = (
        client.table("youtube_channels")
        .select("*")
        .eq("user_id", st.session_state.user_id)
        .order("created_at", desc=True)
        .execute()
    )
    for ch in channels.data or []:
        col1, col2 = st.columns([4, 1])
        col1.write(f"**{ch.get('channel_name', ch['channel_id'])}** — `{ch['channel_url']}`")
        if col2.button("Delete", key=f"del_ch_{ch['id']}"):
            client.table("youtube_channels").delete().eq("id", ch["id"]).execute()
            st.rerun()


def page_track_websites() -> None:
    st.header("Track Websites")
    st.caption("Checked weekly. Examples: OpenAI News, Anthropic Research, Anthropic Engineering.")

    client = get_authed_client()
    if not client:
        return

    _automation_key_banner(client)

    with st.form("add_url"):
        site_name = st.text_input("Site name", placeholder="OpenAI News")
        url = st.text_input("URL", placeholder="https://openai.com/news/")
        if st.form_submit_button("Add URL"):
            try:
                client.table("tracked_urls").insert(
                    {
                        "user_id": st.session_state.user_id,
                        "site_name": site_name or url,
                        "url": url,
                        "url_type": "website",
                    }
                ).execute()
                st.success("URL added.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    urls = (
        client.table("tracked_urls")
        .select("*")
        .eq("user_id", st.session_state.user_id)
        .order("created_at", desc=True)
        .execute()
    )
    for row in urls.data or []:
        col1, col2 = st.columns([4, 1])
        checked = row.get("last_checked_at") or "never"
        col1.write(f"**{row['site_name']}** — `{row['url']}` (last checked: {checked})")
        if col2.button("Delete", key=f"del_url_{row['id']}"):
            client.table("tracked_urls").delete().eq("id", row["id"]).execute()
            st.rerun()


def page_report_history() -> None:
    st.header("Report History")

    client = get_authed_client()
    if not client:
        return

    reports = (
        client.table("reports")
        .select("*")
        .eq("user_id", st.session_state.user_id)
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )
    if not reports.data:
        st.info("No reports yet.")
        return

    for rep in reports.data:
        with st.expander(f"{rep.get('topic', 'Report')} — {rep.get('created_at', '')[:10]}"):
            st.caption(f"Source: {rep.get('source_url', 'N/A')} ({rep.get('source_type', '')})")
            st.markdown(rep["markdown"])
            md_name = topic_to_filename(rep.get("topic") or "report")
            st.download_button(
                "Download .md",
                rep["markdown"],
                file_name=md_name,
                mime="text/markdown",
                key=f"md_{rep['id']}",
            )
            try:
                pdf = markdown_to_pdf_bytes(rep["markdown"], rep.get("topic") or "Report")
                st.download_button(
                    "Download .pdf",
                    pdf,
                    file_name=md_name.replace(".md", ".pdf"),
                    mime="application/pdf",
                    key=f"pdf_{rep['id']}",
                )
            except Exception:
                pass


def page_settings() -> None:
    st.header("Settings")
    client = get_authed_client()
    if not client:
        return

    profile = (
        client.table("profiles")
        .select("*")
        .eq("user_id", st.session_state.user_id)
        .single()
        .execute()
    )
    current_email = profile.data.get("notification_email", "") if profile.data else ""
    secrets_row = get_user_secrets_row(client, user_id=st.session_state.user_id)
    has_key = bool(secrets_row and secrets_row.get("openai_api_key_encrypted"))
    scheduling_on = bool(secrets_row and secrets_row.get("allow_scheduled_jobs"))

    st.subheader("Profile")
    with st.form("settings_form"):
        notification_email = st.text_input("Notification email", value=current_email)
        display_name = st.text_input(
            "Display name",
            value=profile.data.get("display_name", "") if profile.data else "",
        )
        if st.form_submit_button("Save profile"):
            client.table("profiles").update(
                {
                    "notification_email": notification_email,
                    "display_name": display_name,
                }
            ).eq("user_id", st.session_state.user_id).execute()
            st.success("Profile saved.")

    st.subheader("OpenAI API key (for automation)")
    st.caption(
        "Your key is encrypted and used by scheduled jobs to generate reports and email you "
        "when new YouTube videos or website content appear — without you visiting the app."
    )

    if has_key:
        st.success("API key saved." + (" Scheduled reports enabled." if scheduling_on else " Scheduled reports disabled."))
        if st.button("Remove saved API key"):
            delete_user_api_key(client, user_id=st.session_state.user_id)
            st.success("API key removed.")
            st.rerun()

    with st.form("api_key_form"):
        new_key = st.text_input(
            "OpenAI API key",
            type="password",
            placeholder="sk-..." if not has_key else "Enter new key to replace",
        )
        allow_scheduled = st.checkbox(
            "Enable automatic scheduled reports (YouTube daily, websites weekly)",
            value=scheduling_on if has_key else True,
        )
        if st.form_submit_button("Save API key"):
            if not new_key.strip():
                st.error("Enter an API key.")
            else:
                try:
                    save_user_api_key(
                        client,
                        user_id=st.session_state.user_id,
                        openai_api_key=new_key.strip(),
                        allow_scheduled_jobs=allow_scheduled,
                    )
                    st.success("API key saved.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not save key: {exc}")


def main() -> None:
    if not _require_env():
        return
    if not render_auth_form():
        return

    with st.sidebar:
        st.write(f"Signed in as **{st.session_state.user_email}**")
        page = st.radio(
            "Navigation",
            [
                "Generate Report",
                "Track YouTube",
                "Track Websites",
                "Report History",
                "Settings",
            ],
        )
        if st.button("Sign out"):
            sign_out()
            st.rerun()

    pages = {
        "Generate Report": page_generate_report,
        "Track YouTube": page_track_youtube,
        "Track Websites": page_track_websites,
        "Report History": page_report_history,
        "Settings": page_settings,
    }
    pages[page]()


if __name__ == "__main__":
    main()
