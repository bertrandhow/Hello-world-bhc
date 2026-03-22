from __future__ import annotations

import logging
import time
from collections.abc import Iterator

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

logger = logging.getLogger(__name__)

_GRAPH_BASE = "https://graph.microsoft.com/v1.0"
_MESSAGE_SELECT = "id,subject,receivedDateTime,body,from,hasAttachments"


class GraphAPIError(Exception):
    pass


def list_messages(
    token: str,
    user_id: str,
    batch_size: int,
    skip_ids: set[str],
    max_emails: int = 0,
) -> Iterator[dict]:
    base = "me" if user_id == "me" else f"users/{user_id}"
    url = f"{_GRAPH_BASE}/{base}/messages"
    params = {
        "$select": _MESSAGE_SELECT,
        "$top": batch_size,
        "$orderby": "receivedDateTime desc",
    }

    count = 0
    while url:
        data = _get(url, token, params)
        params = None  # only used on first request; nextLink carries its own params

        for msg in data.get("value", []):
            if msg["id"] in skip_ids:
                continue
            yield msg
            count += 1
            if max_emails and count >= max_emails:
                return

        url = data.get("@odata.nextLink")


def get_attachments(token: str, user_id: str, message_id: str) -> list[dict]:
    base = "me" if user_id == "me" else f"users/{user_id}"
    url = f"{_GRAPH_BASE}/{base}/messages/{message_id}/attachments"
    data = _get(url, token)
    return [
        att for att in data.get("value", [])
        if att.get("@odata.type") == "#microsoft.graph.fileAttachment"
    ]


@retry(
    retry=retry_if_exception_type((requests.Timeout, requests.ConnectionError)),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(5),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
def _get(url: str, token: str, params: dict | None = None) -> dict:
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        params=params,
        timeout=30,
    )

    if response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", "10"))
        logger.warning("Rate limited by Graph API. Waiting %ds.", retry_after)
        time.sleep(retry_after)
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=30,
        )

    if not response.ok:
        raise GraphAPIError(
            f"Graph API error {response.status_code}: {response.text[:500]}"
        )

    return response.json()
