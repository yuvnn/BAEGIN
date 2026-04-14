import json
import logging
import re
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

STATE_FILE = Path("/app/reports/seen_papers.json")
MAX_SEEN = 10_000

_ARXIV_ID_RE = re.compile(r"\d{4}\.\d{4,5}")


def load_state() -> dict:
    """Load last_run datetime and seen_ids set from state file."""
    if not STATE_FILE.exists():
        return {"last_run": None, "seen_ids": set()}
    try:
        raw = json.loads(STATE_FILE.read_text())
        last_run = None
        if raw.get("last_run"):
            last_run = datetime.fromisoformat(raw["last_run"])
        return {"last_run": last_run, "seen_ids": set(raw.get("seen_ids", []))}
    except Exception as exc:
        logger.warning("Failed to load seen_papers state: %s", exc)
        return {"last_run": None, "seen_ids": set()}


def save_state(state: dict) -> None:
    """Serialize state to file, capping seen_ids at MAX_SEEN."""
    seen_ids: set = state.get("seen_ids", set())
    if len(seen_ids) > MAX_SEEN:
        trimmed = list(seen_ids)[-(MAX_SEEN):]
        seen_ids = set(trimmed)

    last_run = state.get("last_run")
    payload = {
        "last_run": last_run.isoformat() if isinstance(last_run, datetime) else last_run,
        "seen_ids": list(seen_ids),
    }
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(payload, indent=2))
    except Exception as exc:
        logger.warning("Failed to save seen_papers state: %s", exc)


def is_new(canonical_id: str, state: dict) -> bool:
    return canonical_id not in state.get("seen_ids", set())


def mark_seen(canonical_id: str, state: dict) -> None:
    state.setdefault("seen_ids", set()).add(canonical_id)


def to_canonical_id(paper: dict) -> str:
    """Return a canonical ID for cross-source deduplication.

    - arXiv papers       → ``arxiv:XXXX.XXXXX``
    - HF papers backed by arXiv → same ``arxiv:`` prefix
    - HF-only papers     → ``hf:{paper_id}``
    """
    source = paper.get("source", "")
    raw_id = paper.get("paper_id", "")

    if source == "arxiv":
        match = _ARXIV_ID_RE.search(raw_id)
        if match:
            return f"arxiv:{match.group()}"
        return f"arxiv:{raw_id}"

    # huggingface
    arxiv_id = paper.get("arxiv_id")
    if arxiv_id:
        match = _ARXIV_ID_RE.search(arxiv_id)
        if match:
            return f"arxiv:{match.group()}"

    # HF paper whose id looks like an arXiv ID (e.g. "2404.12345")
    hf_id = raw_id.removeprefix("hf-")
    if _ARXIV_ID_RE.fullmatch(hf_id):
        return f"arxiv:{hf_id}"

    return f"hf:{hf_id}"
