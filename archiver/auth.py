from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import msal

logger = logging.getLogger(__name__)

_GRAPH_SCOPES_DELEGATED = [
    "https://graph.microsoft.com/Mail.Read",
    "https://graph.microsoft.com/User.Read",
]
_GRAPH_SCOPES_APP = ["https://graph.microsoft.com/.default"]
_TOKEN_CACHE_PATH = ".msal_cache.json"


def _load_token_cache() -> msal.SerializableTokenCache:
    cache = msal.SerializableTokenCache()
    if Path(_TOKEN_CACHE_PATH).exists():
        cache.deserialize(Path(_TOKEN_CACHE_PATH).read_text())
    return cache


def _save_token_cache(cache: msal.SerializableTokenCache) -> None:
    if cache.has_state_changed:
        Path(_TOKEN_CACHE_PATH).write_text(cache.serialize())


def get_token_device_code(settings) -> str:
    cache = _load_token_cache()
    app = msal.PublicClientApplication(
        client_id=settings.azure_client_id,
        authority=f"https://login.microsoftonline.com/{settings.azure_tenant_id}",
        token_cache=cache,
    )

    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(_GRAPH_SCOPES_DELEGATED, account=accounts[0])
        if result and "access_token" in result:
            _save_token_cache(cache)
            return result["access_token"]

    flow = app.initiate_device_flow(scopes=_GRAPH_SCOPES_DELEGATED)
    if "user_code" not in flow:
        raise RuntimeError(f"Failed to initiate device flow: {flow.get('error_description')}")

    print("\n" + flow["message"])
    result = app.acquire_token_by_device_flow(flow)

    if "access_token" not in result:
        raise RuntimeError(
            f"Authentication failed: {result.get('error_description', result.get('error'))}"
        )

    _save_token_cache(cache)
    return result["access_token"]


def get_token_client_credentials(settings) -> str:
    app = msal.ConfidentialClientApplication(
        client_id=settings.azure_client_id,
        client_credential=settings.azure_client_secret,
        authority=f"https://login.microsoftonline.com/{settings.azure_tenant_id}",
    )

    result = app.acquire_token_for_client(scopes=_GRAPH_SCOPES_APP)

    if "access_token" not in result:
        raise RuntimeError(
            f"Authentication failed: {result.get('error_description', result.get('error'))}"
        )

    return result["access_token"]


def get_access_token(settings) -> str:
    if settings.graph_auth_flow == "device_code":
        return get_token_device_code(settings)
    return get_token_client_credentials(settings)
