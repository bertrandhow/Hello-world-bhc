from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class State:
    processed_ids: set[str] = field(default_factory=set)
    last_run: str | None = None


def load_state(path: str) -> State:
    p = Path(path)
    if not p.exists():
        return State()
    try:
        data = json.loads(p.read_text())
        return State(
            processed_ids=set(data.get("processed_ids", [])),
            last_run=data.get("last_run"),
        )
    except (json.JSONDecodeError, OSError):
        return State()


def save_state(path: str, state: State) -> None:
    state.last_run = datetime.now(timezone.utc).isoformat()
    data = {
        "processed_ids": list(state.processed_ids),
        "last_run": state.last_run,
    }
    p = Path(path)
    fd, tmp = tempfile.mkstemp(dir=p.parent, prefix=".archiver_state_tmp_")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, path)
    except Exception:
        os.unlink(tmp)
        raise


def mark_processed(state: State, message_id: str) -> None:
    state.processed_ids.add(message_id)
