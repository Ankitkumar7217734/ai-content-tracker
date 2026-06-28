"""Send a test Hello World email via Resend (onboarding example).

Run from the project root:

    python jobs/send_test_email.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

import resend


def main() -> None:
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key or api_key == "re_xxxxxxxxx":
        raise SystemExit(
            "Set RESEND_API_KEY in .env — replace re_xxxxxxxxx with your real API key."
        )

    resend.api_key = api_key

    result = resend.Emails.send(
        {
            "from": "onboarding@resend.dev",
            "to": ["ak7217734@gmail.com"],
            "subject": "Hello World",
            "html": "<p>Congrats on sending your <strong>first email</strong>!</p>",
        }
    )
    print("Email sent:", result)


if __name__ == "__main__":
    main()
