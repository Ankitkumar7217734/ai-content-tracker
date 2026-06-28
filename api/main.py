"""FastAPI backend for report generation and encrypted API key storage."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from api.auth import AuthedUser, get_current_user
from app.db import get_supabase_with_token
from app.pdf_utils import markdown_to_pdf_bytes
from app.user_secrets import (
    delete_user_api_key,
    load_user_api_key_for_client,
    save_user_api_key,
    user_has_saved_api_key,
)
from crew.factory import run_video_crew, run_website_crew, topic_to_filename
from fastapi.responses import Response
from jobs.youtube_utils import extract_channel_id

app = FastAPI(title="AI Content Tracker API", version="1.0.0")

_default_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
_extra_origins = [
    origin.strip()
    for origin in os.environ.get("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_default_origins + _extra_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateReportRequest(BaseModel):
    source_type: str = Field(..., pattern="^(youtube|website)$")
    source_url: str
    topic: str
    openai_api_key: str | None = None
    save_api_key: bool = False


class ApiKeyRequest(BaseModel):
    openai_api_key: str
    allow_scheduled_jobs: bool = True


class ResolveChannelRequest(BaseModel):
    channel_url: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/youtube/resolve-channel")
def resolve_youtube_channel(
    body: ResolveChannelRequest,
    user: AuthedUser = Depends(get_current_user),
) -> dict[str, str]:
    channel_id = extract_channel_id(body.channel_url)
    if not channel_id:
        raise HTTPException(
            status_code=400,
            detail="Could not resolve channel ID. Use a full channel URL or @handle.",
        )
    return {"channel_id": channel_id}


@app.post("/reports/generate")
def generate_report(
    body: GenerateReportRequest,
    user: AuthedUser = Depends(get_current_user),
) -> dict:
    client = get_supabase_with_token(user.access_token)
    api_key = body.openai_api_key.strip() if body.openai_api_key else None
    if not api_key and user_has_saved_api_key(client, user_id=user.user_id):
        api_key = load_user_api_key_for_client(client, user_id=user.user_id)
    if not api_key:
        raise HTTPException(status_code=400, detail="OpenAI API key is required")

    if body.save_api_key and body.openai_api_key:
        save_user_api_key(
            client,
            user_id=user.user_id,
            openai_api_key=body.openai_api_key.strip(),
            allow_scheduled_jobs=True,
        )

    try:
        if body.source_type == "youtube":
            markdown = run_video_crew(
                openai_api_key=api_key,
                video_url=body.source_url,
                topic=body.topic,
            )
            db_type = "manual"
        else:
            markdown = run_website_crew(
                openai_api_key=api_key,
                website_url=body.source_url,
                topic=body.topic,
            )
            db_type = "website"
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    result = (
        client.table("reports")
        .insert(
            {
                "user_id": user.user_id,
                "source_type": db_type,
                "source_url": body.source_url,
                "topic": body.topic,
                "markdown": markdown,
            }
        )
        .execute()
    )
    report_id = result.data[0]["id"] if result.data else None
    return {
        "id": report_id,
        "topic": body.topic,
        "markdown": markdown,
        "filename": topic_to_filename(body.topic),
    }


@app.post("/settings/api-key")
def save_api_key(
    body: ApiKeyRequest,
    user: AuthedUser = Depends(get_current_user),
) -> dict[str, str]:
    client = get_supabase_with_token(user.access_token)
    if not body.openai_api_key.strip():
        raise HTTPException(status_code=400, detail="API key cannot be empty")
    save_user_api_key(
        client,
        user_id=user.user_id,
        openai_api_key=body.openai_api_key.strip(),
        allow_scheduled_jobs=body.allow_scheduled_jobs,
    )
    return {"status": "saved"}


@app.delete("/settings/api-key")
def remove_api_key(user: AuthedUser = Depends(get_current_user)) -> dict[str, str]:
    client = get_supabase_with_token(user.access_token)
    delete_user_api_key(client, user_id=user.user_id)
    return {"status": "removed"}


@app.get("/reports/{report_id}/pdf")
def download_pdf(
    report_id: str,
    user: AuthedUser = Depends(get_current_user),
) -> Response:
    client = get_supabase_with_token(user.access_token)
    result = (
        client.table("reports")
        .select("*")
        .eq("id", report_id)
        .eq("user_id", user.user_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Report not found")

    report = result.data
    try:
        pdf_bytes = markdown_to_pdf_bytes(
            report["markdown"],
            report.get("topic") or "Report",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    filename = topic_to_filename(report.get("topic") or "report").replace(".md", ".pdf")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
