import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from config.logging_config import get_logger

logger = get_logger(__name__)


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def ensure_session(ws_path: Path, session_id: str) -> Path:
    session_dir = (ws_path / "sessions" / session_id).resolve()
    (session_dir / "versions").mkdir(parents=True, exist_ok=True)
    state_path = session_dir / "state.json"
    if not state_path.exists():
        state = {
            "session_id": session_id,
            "selected_items": [],
            "selected_summaries": [],
            "story_goal": {
                "style": "",
                "voice": "",
                "length": "",
                "tone": "",
            },
            "constraints": [],
            "next_version": 1,
            "last_outputs": {},
            "history": [],
            "created_at": _now_iso(),
        }
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        logger.info("session created: %s", session_dir)
    return session_dir


def load_state(session_dir: Path) -> Dict[str, Any]:
    state_path = session_dir / "state.json"
    with state_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_state(session_dir: Path, state: Dict[str, Any]) -> None:
    state_path = session_dir / "state.json"
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def allocate_version(state: Dict[str, Any]) -> int:
    v = int(state.get("next_version", 1))
    state["next_version"] = v + 1
    logger.info("allocate version: v%03d", v)
    return v


def version_dir(session_dir: Path, version: int) -> Path:
    vdir = session_dir / "versions" / f"v{version:03d}"
    vdir.mkdir(parents=True, exist_ok=True)
    return vdir


def record_output(
    state: Dict[str, Any],
    *,
    role: str,
    version: int,
    files: Dict[str, str],
    summary: Optional[str] = None,
) -> None:
    state.setdefault("history", []).append(
        {
            "version": version,
            "role": role,
            "files": files,
            "summary": summary or "",
            "created_at": _now_iso(),
        }
    )
    state.setdefault("last_outputs", {})[role] = {"version": version, "files": files}
    logger.info("record output: role=%s version=v%03d files=%s", role, version, files)


def find_latest_file(session_dir: Path, filename: str) -> Optional[Path]:
    versions_dir = session_dir / "versions"
    if not versions_dir.exists():
        return None
    candidates = []
    for vdir in versions_dir.iterdir():
        if not vdir.is_dir() or not vdir.name.startswith("v"):
            continue
        fp = vdir / filename
        if fp.exists():
            try:
                vnum = int(vdir.name[1:])
            except ValueError:
                vnum = -1
            candidates.append((vnum, fp))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    return candidates[-1][1]


def get_last_output_path(
    session_dir: Path,
    state: Dict[str, Any],
    role: str,
    filename: str,
) -> Optional[Path]:
    last = (state.get("last_outputs") or {}).get(role)
    if last:
        v = last.get("version")
        files = last.get("files") or {}
        rel = files.get(filename)
        if v is not None and rel:
            fp = session_dir / rel
            if fp.exists():
                return fp
    return find_latest_file(session_dir, filename)
