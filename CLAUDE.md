# CLAUDE.md

This file provides guidance to AI assistants (Claude and others) working in this repository.

## Repository Overview

**Name:** Hello-world-bhc
**Remote:** `bertrandhow/Hello-world-bhc`
**Purpose:** This repository is currently in its initial state. This CLAUDE.md was created to establish conventions before further development begins.

## Repository State

This repository contains a Python CLI tool that archives Outlook/Office 365 emails and attachments to Dropbox, classified by year and subject using the Claude API.

## Git Workflow

### Branch Conventions
- Feature/AI branches follow the pattern: `claude/<short-description>-<session-id>`
- Development happens on feature branches; `main` (or `master`) is the stable branch
- Always push with tracking: `git push -u origin <branch-name>`

### Commit Messages
- Use the imperative mood: "Add feature" not "Added feature"
- Keep the subject line under 72 characters
- Reference issues or context in the body when relevant

### Pushing Changes
- Never force-push to `main`/`master`
- On network failure, retry up to 4 times with exponential backoff (2s, 4s, 8s, 16s)

## Development Workflows

### Starting Work
1. Ensure you are on the correct feature branch before making changes
2. Pull the latest changes from the remote before starting: `git pull origin <branch>`
3. Make changes, then commit with a clear message

### Making Changes
- Prefer editing existing files over creating new ones
- Avoid over-engineering: implement only what is directly requested
- Do not add comments, docstrings, or type annotations to unchanged code
- Keep solutions simple and focused

### Testing
- Run tests before committing (add test commands here once the project has a test suite)
- Do not skip pre-commit hooks (`--no-verify`)

## Code Conventions

- **Language / Runtime:** Python 3.11+
- **Formatter / Linter:** `black`, `ruff`
- **Package manager:** `pip` / `requirements.txt`

### Directory Structure

```
Hello-world-bhc/
├── archiver/
│   ├── config.py          # load & validate all env vars (Settings dataclass)
│   ├── auth.py            # MSAL token acquisition (device code / client credentials)
│   ├── graph.py           # Microsoft Graph API: list messages, fetch attachments
│   ├── extractor.py       # text extraction from HTML, PDF, DOCX, images (OCR)
│   ├── classifier.py      # Claude API → ClassificationResult(year, subject)
│   ├── dropbox_client.py  # Dropbox upload, path sanitization, conflict resolution
│   └── state.py           # JSON state file for incremental processing
├── main.py                # Click CLI: `run` and `setup-dropbox` commands
├── requirements.txt
├── .env.example           # all required environment variables documented
└── CLAUDE.md
```

### Setup & Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env — fill in AZURE_TENANT_ID, AZURE_CLIENT_ID, ANTHROPIC_API_KEY,
#              DROPBOX_APP_KEY, DROPBOX_APP_SECRET

# 3. One-time Dropbox auth (get refresh token)
python main.py setup-dropbox
# Follow the browser prompt, then paste DROPBOX_REFRESH_TOKEN into .env

# 4. Run the archiver
python main.py run                       # process all new emails
python main.py run --dry-run             # classify only, no Dropbox upload
python main.py run --max-emails 50       # process at most 50 emails
python main.py run --reset-state         # reprocess all (ignore state file)
python main.py run --mailbox user@co.com # override mailbox (client_credentials flow)
```

### Dropbox Folder Structure

Emails and attachments land at:

```
/Archive/{year}/{subject}/{filename}
```

Examples:
```
/Archive/2024/Invoice/email-a1b2c3d4.txt
/Archive/2024/Invoice/Q1-Vendor-Invoice.pdf
/Archive/2023/Tax Return/1099-INT-Form.pdf
```

### Key Design Decisions

| Concern | Approach |
|---|---|
| Auth | Device code for user mailboxes; client credentials for service accounts |
| Classification model | `claude-3-5-haiku-20241022` at `temperature=0` for deterministic JSON output |
| Incremental processing | `.archiver_state.json` tracks processed message IDs; saved after each message |
| Conflict resolution | Append `(1)`, `(2)`… to filename if Dropbox path already exists |
| Error isolation | Per-message errors are caught, logged, and skipped (retried on next run) |
| Rate limiting | `tenacity` retry with exponential backoff for Graph API, Claude, and Dropbox |

### Environment Variables

See `.env.example` for the full list. Key variables:

- `GRAPH_AUTH_FLOW` — `device_code` (interactive) or `client_credentials` (service account)
- `MAILBOX_USER_ID` — `me` for the authenticated user, or a UPN/GUID for a shared mailbox
- `MAX_EMAILS` — `0` means no limit; set to a positive integer to cap a run
- `BATCH_SIZE` — Graph API page size (default 20)

## Security

- Never commit secrets, credentials, `.env` files, or API keys
- Validate input at system boundaries (user input, external APIs)
- Follow OWASP top-10 guidance: avoid SQL injection, XSS, command injection, etc.

## AI Assistant Instructions

- Read relevant files before suggesting modifications
- Do not create files unless strictly necessary
- Do not add unrequested features, refactors, or "improvements"
- Match the scope of changes to what was actually requested
- When an action is hard to reverse or affects shared state, confirm with the user first

## Updating This File

Update this file whenever:
- A new language, framework, or toolchain is introduced
- Key architectural decisions are made
- New development workflows or conventions are established
- Test or build commands change
