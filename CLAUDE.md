# CLAUDE.md

This file provides guidance to AI assistants (Claude and others) working in this repository.

## Repository Overview

**Name:** Hello-world-bhc
**Remote:** `bertrandhow/Hello-world-bhc`
**Purpose:** This repository is currently in its initial state. This CLAUDE.md was created to establish conventions before further development begins.

## Repository State

As of the creation of this file, the repository is empty (no source files or prior commits). Conventions below should be applied as the project grows.

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

These will be filled in as the project's language and framework are established. Typical things to document here:

- **Language / Runtime:** TBD
- **Formatter / Linter:** TBD
- **Package manager:** TBD
- **Directory structure:** TBD

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
