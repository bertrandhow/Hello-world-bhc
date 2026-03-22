from __future__ import annotations

import base64
import logging
import sys

import anthropic
import click

from archiver import auth, classifier, dropbox_client, extractor, graph, state
from archiver.config import load_settings


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option("--mailbox", default=None, help="Override MAILBOX_USER_ID from .env")
@click.option("--max-emails", default=None, type=int, help="Limit number of emails to process")
@click.option("--dry-run", is_flag=True, help="Classify but do not upload to Dropbox")
@click.option("--reset-state", is_flag=True, help="Ignore existing state and reprocess all emails")
def run(mailbox: str | None, max_emails: int | None, dry_run: bool, reset_state: bool) -> None:
    settings = load_settings()
    _configure_logging(settings.log_level)
    logger = logging.getLogger(__name__)

    user_id = mailbox or settings.mailbox_user_id
    effective_max = max_emails if max_emails is not None else settings.max_emails

    current_state = state.State() if reset_state else state.load_state(settings.state_file_path)
    skip_ids = current_state.processed_ids

    logger.info("Acquiring Microsoft Graph token...")
    token = auth.get_access_token(settings)

    dbx = None
    if not dry_run:
        logger.info("Connecting to Dropbox...")
        dbx = dropbox_client.get_dropbox_client(settings)

    anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    total_emails = 0
    total_attachments = 0
    total_errors = 0

    logger.info("Starting archive run (dry_run=%s, max_emails=%s)...", dry_run, effective_max or "unlimited")

    for message in graph.list_messages(token, user_id, settings.batch_size, skip_ids, effective_max):
        msg_id = message["id"]
        subject = message.get("subject", "(no subject)")
        received = message.get("receivedDateTime", "")

        try:
            body_text = extractor.extract_email_text(message)
            result = classifier.classify(anthropic_client, body_text, received, filename="")

            logger.info(
                "[email] %r → %d / %s",
                subject[:60],
                result.year,
                result.subject,
            )

            if not dry_run:
                email_filename = f"email-{msg_id[:8]}.txt"
                dropbox_client.upload_file(
                    dbx,
                    body_text.encode("utf-8"),
                    result.year,
                    result.subject,
                    email_filename,
                )

            total_emails += 1

            if message.get("hasAttachments"):
                attachments = graph.get_attachments(token, user_id, msg_id)
                for att in attachments:
                    att_name = att.get("name", "attachment")
                    try:
                        att_text = extractor.extract_attachment_text(att)
                        att_result = classifier.classify(
                            anthropic_client, att_text, received, filename=att_name
                        )

                        logger.info(
                            "  [attachment] %r → %d / %s",
                            att_name[:60],
                            att_result.year,
                            att_result.subject,
                        )

                        if not dry_run:
                            raw_bytes = base64.b64decode(att.get("contentBytes", ""))
                            dropbox_client.upload_file(
                                dbx,
                                raw_bytes,
                                att_result.year,
                                att_result.subject,
                                att_name,
                            )

                        total_attachments += 1

                    except Exception as exc:
                        logger.warning("Error processing attachment %r: %s", att_name, exc)
                        total_errors += 1

            state.mark_processed(current_state, msg_id)
            state.save_state(settings.state_file_path, current_state)

        except Exception as exc:
            logger.warning("Error processing message %r (%s): %s", subject[:60], msg_id[:8], exc)
            total_errors += 1

    logger.info(
        "Done. Emails processed: %d, Attachments: %d, Errors: %d",
        total_emails,
        total_attachments,
        total_errors,
    )
    if dry_run:
        logger.info("(dry run — nothing was uploaded to Dropbox)")


@cli.command("setup-dropbox")
def setup_dropbox() -> None:
    settings = load_settings()
    dropbox_client.interactive_auth_setup(settings)


def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


if __name__ == "__main__":
    cli()
