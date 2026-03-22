from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    azure_tenant_id: str
    azure_client_id: str
    azure_client_secret: str
    graph_auth_flow: str
    mailbox_user_id: str
    anthropic_api_key: str
    dropbox_app_key: str
    dropbox_app_secret: str
    dropbox_refresh_token: str
    state_file_path: str
    batch_size: int
    max_emails: int
    log_level: str


def load_settings() -> Settings:
    settings = Settings(
        azure_tenant_id=os.getenv("AZURE_TENANT_ID", ""),
        azure_client_id=os.getenv("AZURE_CLIENT_ID", ""),
        azure_client_secret=os.getenv("AZURE_CLIENT_SECRET", ""),
        graph_auth_flow=os.getenv("GRAPH_AUTH_FLOW", "device_code"),
        mailbox_user_id=os.getenv("MAILBOX_USER_ID", "me"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        dropbox_app_key=os.getenv("DROPBOX_APP_KEY", ""),
        dropbox_app_secret=os.getenv("DROPBOX_APP_SECRET", ""),
        dropbox_refresh_token=os.getenv("DROPBOX_REFRESH_TOKEN", ""),
        state_file_path=os.getenv("STATE_FILE_PATH", ".archiver_state.json"),
        batch_size=int(os.getenv("BATCH_SIZE", "20")),
        max_emails=int(os.getenv("MAX_EMAILS", "0")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
    settings.validate()
    return settings


def validate(self: Settings) -> None:
    missing = []

    for field in ("azure_tenant_id", "azure_client_id", "anthropic_api_key",
                  "dropbox_app_key", "dropbox_app_secret"):
        if not getattr(self, field):
            missing.append(field.upper())

    if self.graph_auth_flow == "client_credentials" and not self.azure_client_secret:
        missing.append("AZURE_CLIENT_SECRET")

    if self.graph_auth_flow not in ("device_code", "client_credentials"):
        raise EnvironmentError(
            f"GRAPH_AUTH_FLOW must be 'device_code' or 'client_credentials', "
            f"got: {self.graph_auth_flow!r}"
        )

    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            "Copy .env.example to .env and fill in the values."
        )


Settings.validate = validate
