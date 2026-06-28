"""Email notifications via Resend."""

from __future__ import annotations

import os

import resend


def send_report_email(
    *,
    to_email: str,
    subject: str,
    markdown_body: str,
    source_url: str | None = None,
) -> bool:
    api_key = os.environ.get("RESEND_API_KEY")
    from_email = os.environ.get("RESEND_FROM_EMAIL", "onboarding@resend.dev")
    if not api_key:
        print("RESEND_API_KEY not set — skipping email.")
        return False

    resend.api_key = api_key
    html = f"<h2>{subject}</h2>"
    if source_url:
        html += f'<p><a href="{source_url}">View source</a></p>'
    html += f"<pre style='white-space:pre-wrap;font-family:sans-serif'>{markdown_body[:8000]}</pre>"

    try:
        resend.Emails.send(
            {
                "from": from_email,
                "to": [to_email],
                "subject": subject,
                "html": html,
            }
        )
        return True
    except Exception as exc:
        print(f"Email failed: {exc}")
        return False
