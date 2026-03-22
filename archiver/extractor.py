from __future__ import annotations

import base64
import html.parser
import io
import logging

logger = logging.getLogger(__name__)

_MAX_CHARS = 4000


class _HTMLStripper(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_text(self) -> str:
        return " ".join(self._parts)


def _strip_html(html_text: str) -> str:
    stripper = _HTMLStripper()
    stripper.feed(html_text)
    return stripper.get_text()


def extract_email_text(message: dict) -> str:
    body = message.get("body", {})
    content = body.get("content", "")
    if body.get("contentType", "").lower() == "html":
        content = _strip_html(content)
    return content[:_MAX_CHARS]


def extract_attachment_text(attachment: dict) -> str:
    content_type = attachment.get("contentType", "").lower()
    raw = base64.b64decode(attachment.get("contentBytes", ""))

    try:
        if content_type == "application/pdf":
            return _extract_pdf(raw)[:_MAX_CHARS]

        if content_type in (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
        ):
            return _extract_docx(raw)[:_MAX_CHARS]

        if content_type in ("image/png", "image/jpeg", "image/jpg", "image/tiff"):
            return _extract_image_ocr(raw)[:_MAX_CHARS]

    except Exception as exc:
        logger.warning("Failed to extract text from attachment %r: %s",
                       attachment.get("name"), exc)

    return ""


def _extract_pdf(content: bytes) -> str:
    import pdfplumber

    with pdfplumber.open(io.BytesIO(content)) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
    return "\n".join(pages)


def _extract_docx(content: bytes) -> str:
    import docx

    doc = docx.Document(io.BytesIO(content))
    return "\n".join(para.text for para in doc.paragraphs)


def _extract_image_ocr(content: bytes) -> str:
    import pytesseract
    from PIL import Image

    image = Image.open(io.BytesIO(content))
    return pytesseract.image_to_string(image)
