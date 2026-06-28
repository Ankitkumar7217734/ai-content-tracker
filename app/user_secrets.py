"""Per-user OpenAI API key storage (encrypted)."""

from __future__ import annotations

from datetime import datetime, timezone

from supabase import Client

from app.crypto_utils import decrypt_api_key, encrypt_api_key
from app.db import get_supabase_service


def save_user_api_key(
    client: Client,
    *,
    user_id: str,
    openai_api_key: str,
    allow_scheduled_jobs: bool = True,
) -> None:
    encrypted = encrypt_api_key(openai_api_key.strip())
    client.table("user_secrets").upsert(
        {
            "user_id": user_id,
            "openai_api_key_encrypted": encrypted,
            "allow_scheduled_jobs": allow_scheduled_jobs,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    ).execute()


def delete_user_api_key(client: Client, *, user_id: str) -> None:
    client.table("user_secrets").delete().eq("user_id", user_id).execute()


def get_user_secrets_row(client: Client, *, user_id: str) -> dict | None:
    result = client.table("user_secrets").select("*").eq("user_id", user_id).execute()
    if result.data:
        return result.data[0]
    return None


def user_has_saved_api_key(client: Client, *, user_id: str) -> bool:
    row = get_user_secrets_row(client, user_id=user_id)
    return bool(row and row.get("openai_api_key_encrypted"))


def user_scheduling_enabled(client: Client, *, user_id: str) -> bool:
    row = get_user_secrets_row(client, user_id=user_id)
    return bool(row and row.get("openai_api_key_encrypted") and row.get("allow_scheduled_jobs"))


def load_user_api_key_for_client(client: Client, *, user_id: str) -> str | None:
    row = get_user_secrets_row(client, user_id=user_id)
    if not row or not row.get("openai_api_key_encrypted"):
        return None
    return decrypt_api_key(row["openai_api_key_encrypted"])


def load_user_api_key_for_worker(user_id: str) -> str | None:
    """Used by scheduled jobs — service role + must have scheduling enabled."""
    client = get_supabase_service()
    row = get_user_secrets_row(client, user_id=user_id)
    if not row or not row.get("allow_scheduled_jobs"):
        return None
    encrypted = row.get("openai_api_key_encrypted")
    if not encrypted:
        return None
    return decrypt_api_key(encrypted)
