from __future__ import annotations

import logging
import os
import re
import webbrowser
from pathlib import Path
from urllib.parse import urlencode

import dropbox
from dropbox.exceptions import ApiError
from dropbox.files import WriteMode

logger = logging.getLogger(__name__)

_ARCHIVE_ROOT = "/Archive"
_UNSAFE_CHARS = re.compile(r"[^\w\s\-.]")
_MULTI_SPACE = re.compile(r"\s+")


def get_dropbox_client(settings) -> dropbox.Dropbox:
    return dropbox.Dropbox(
        oauth2_refresh_token=settings.dropbox_refresh_token,
        app_key=settings.dropbox_app_key,
        app_secret=settings.dropbox_app_secret,
    )


def build_dropbox_path(year: int, subject: str, filename: str) -> str:
    safe_subject = _sanitize(subject) or "Uncategorized"
    safe_filename = _sanitize(filename) or "untitled"
    return f"{_ARCHIVE_ROOT}/{year}/{safe_subject}/{safe_filename}"


def resolve_conflict(dbx: dropbox.Dropbox, path: str) -> str:
    stem, ext = _split_ext(path)
    candidate = path
    for counter in range(1, 100):
        try:
            dbx.files_get_metadata(candidate)
            # File exists — try next name
            candidate = f"{stem} ({counter}){ext}"
        except ApiError as err:
            if err.error.is_path() and err.error.get_path().is_not_found():
                return candidate
            raise
    raise RuntimeError(f"Could not resolve filename conflict after 99 attempts: {path}")


def upload_file(
    dbx: dropbox.Dropbox,
    content: bytes,
    year: int,
    subject: str,
    filename: str,
) -> str:
    path = build_dropbox_path(year, subject, filename)
    final_path = resolve_conflict(dbx, path)
    dbx.files_upload(content, final_path, mode=WriteMode.add)
    logger.info("Uploaded → %s", final_path)
    return final_path


def interactive_auth_setup(settings) -> None:
    import secrets
    import hashlib
    import base64
    import urllib.request

    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b"=").decode()

    auth_url = (
        "https://www.dropbox.com/oauth2/authorize?"
        + urlencode({
            "client_id": settings.dropbox_app_key,
            "response_type": "code",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "token_access_type": "offline",
        })
    )

    print(f"\nOpen this URL in your browser to authorise Dropbox access:\n\n  {auth_url}\n")
    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    auth_code = input("Paste the authorisation code here: ").strip()

    import urllib.parse
    import json

    data = urllib.parse.urlencode({
        "code": auth_code,
        "grant_type": "authorization_code",
        "code_verifier": code_verifier,
        "client_id": settings.dropbox_app_key,
        "client_secret": settings.dropbox_app_secret,
    }).encode()

    req = urllib.request.Request(
        "https://api.dropboxapi.com/oauth2/token",
        data=data,
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        tokens = json.loads(resp.read())

    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        raise RuntimeError(f"No refresh token in response: {tokens}")

    print(f"\nSuccess! Add this to your .env file:\n\n  DROPBOX_REFRESH_TOKEN={refresh_token}\n")


def _sanitize(value: str) -> str:
    value = _UNSAFE_CHARS.sub("_", value)
    value = _MULTI_SPACE.sub(" ", value).strip()
    return value


def _split_ext(path: str) -> tuple[str, str]:
    dot = path.rfind(".")
    slash = path.rfind("/")
    if dot > slash:
        return path[:dot], path[dot:]
    return path, ""
