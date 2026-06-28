"""Supabase authentication helpers for Streamlit."""

from __future__ import annotations

import streamlit as st
from supabase import Client

from app.db import get_supabase_anon


def init_session_state() -> None:
    defaults = {
        "authenticated": False,
        "user_id": None,
        "access_token": None,
        "refresh_token": None,
        "user_email": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_authed_client() -> Client | None:
    if not st.session_state.get("access_token"):
        return None
    client = get_supabase_anon()
    client.postgrest.auth(st.session_state["access_token"])
    return client


def sign_up(email: str, password: str, display_name: str = "") -> tuple[bool, str]:
    client = get_supabase_anon()
    try:
        options = {"data": {"display_name": display_name}} if display_name else {}
        response = client.auth.sign_up(
            {"email": email, "password": password, "options": options}
        )
        if response.session:
            _set_session(response.session)
            return True, "Account created successfully."
        return True, "Check your email to confirm your account."
    except Exception as exc:
        return False, str(exc)


def sign_in(email: str, password: str) -> tuple[bool, str]:
    client = get_supabase_anon()
    try:
        response = client.auth.sign_in_with_password({"email": email, "password": password})
        if response.session:
            _set_session(response.session)
            return True, "Signed in."
        return False, "No session returned."
    except Exception as exc:
        return False, str(exc)


def sign_out() -> None:
    try:
        get_supabase_anon().auth.sign_out()
    except Exception:
        pass
    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.access_token = None
    st.session_state.refresh_token = None
    st.session_state.user_email = None


def _set_session(session) -> None:
    st.session_state.authenticated = True
    st.session_state.user_id = session.user.id
    st.session_state.access_token = session.access_token
    st.session_state.refresh_token = session.refresh_token
    st.session_state.user_email = session.user.email


def render_auth_form() -> bool:
    """Render login/signup. Returns True if user is authenticated."""
    init_session_state()
    if st.session_state.authenticated:
        return True

    st.title("AI Content Tracker")
    st.caption("Sign in to generate reports and track YouTube channels & websites.")

    tab_login, tab_signup = st.tabs(["Login", "Sign up"])
    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login", key="login_btn"):
            ok, msg = sign_in(email, password)
            if ok and st.session_state.authenticated:
                st.rerun()
            st.error(msg) if not ok else st.success(msg)

    with tab_signup:
        su_email = st.text_input("Email", key="signup_email")
        su_name = st.text_input("Display name", key="signup_name")
        su_password = st.text_input("Password", type="password", key="signup_password")
        if st.button("Create account", key="signup_btn"):
            ok, msg = sign_up(su_email, su_password, su_name)
            if ok and st.session_state.authenticated:
                st.rerun()
            st.error(msg) if not ok else st.info(msg)

    return False
