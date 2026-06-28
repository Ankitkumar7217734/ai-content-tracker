"""Supabase client helpers."""

import os
from functools import lru_cache

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()


@lru_cache
def get_supabase_anon() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_ANON_KEY"]
    return create_client(url, key)


def get_supabase_with_token(access_token: str) -> Client:
    client = get_supabase_anon()
    client.postgrest.auth(access_token)
    return client


@lru_cache
def get_supabase_service() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, key)
