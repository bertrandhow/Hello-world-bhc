from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime

import anthropic
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

logger = logging.getLogger(__name__)

_MODEL = "claude-3-5-haiku-20241022"

_SYSTEM_PROMPT = """You are a document archiving assistant. Your only task is to classify \
documents and emails into a year and a subject category for filing purposes.

You MUST respond with a single JSON object and nothing else. No explanation, no markdown \
fences, no extra text. The JSON must have exactly two keys:

  "year":    an integer representing the most relevant year for this document.
             Use the document's own date if present; otherwise use the received date provided.
             If genuinely uncertain, use the received year.
  "subject": a short, filesystem-safe category string (2-5 words, title case, no slashes,
             no special characters). Examples: "Invoice", "Legal Contract", "HR Onboarding",
             "Bank Statement", "Project Proposal", "Meeting Notes", "Tax Return"

If the document is an email, classify based on its topic, not the act of emailing."""

_USER_TEMPLATE = """\
Received date: {received_date}
Filename (if attachment): {filename}

Content:
{text}"""


@dataclass
class ClassificationResult:
    year: int
    subject: str


@retry(
    retry=retry_if_exception_type(anthropic.RateLimitError),
    wait=wait_exponential(multiplier=1, min=5, max=60),
    stop=stop_after_attempt(4),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
def classify(
    client: anthropic.Anthropic,
    text: str,
    received_date: str,
    filename: str = "",
) -> ClassificationResult:
    received_year = _parse_year(received_date)

    user_content = _USER_TEMPLATE.format(
        received_date=received_date,
        filename=filename or "(email body)",
        text=text or "(no extractable text)",
    )

    response = client.messages.create(
        model=_MODEL,
        max_tokens=100,
        temperature=0,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )

    raw = response.content[0].text.strip()
    try:
        data = json.loads(raw)
        year = int(data["year"])
        subject = str(data["subject"]).strip() or "Uncategorized"
        return ClassificationResult(year=year, subject=subject)
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        logger.warning("Classification parse failed (%s). Raw response: %r. Using fallback.", exc, raw)
        return ClassificationResult(year=received_year, subject="Uncategorized")


def _parse_year(received_date: str) -> int:
    try:
        return datetime.fromisoformat(received_date.replace("Z", "+00:00")).year
    except (ValueError, AttributeError):
        return datetime.now().year
