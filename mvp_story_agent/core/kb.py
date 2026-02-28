import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Optional


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _append_jsonl(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(obj, ensure_ascii=False)
    with path.open("a", encoding="utf-8") as f:
        f.write(line)
        f.write("\n")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            rows.append(json.loads(ln))
    return rows


def _find_by_id(
    rows: Iterable[dict[str, Any]], key: str, value: str
) -> Optional[dict[str, Any]]:
    for r in rows:
        if r.get(key) == value:
            return r
    return None


def add_source(
    *,
    ws_path: Path,
    title: str,
    author: Optional[str],
    url: Optional[str],
    license: Optional[str],
    notes: Optional[str],
) -> str:
    source_id = f"src_{uuid.uuid4().hex[:12]}"
    obj = {
        "source_id": source_id,
        "title": title,
        "author": author,
        "url": url,
        "license": license,
        "notes": notes,
        "created_at": _now_iso(),
    }
    _append_jsonl(ws_path / "kb/sources.jsonl", obj)
    return source_id


def add_passage(
    *,
    ws_path: Path,
    source_id: str,
    text: str,
    loc: Optional[str],
    tags: list[str],
    notes: Optional[str],
) -> str:
    sources = _read_jsonl(ws_path / "kb/sources.jsonl")
    if not _find_by_id(sources, "source_id", source_id):
        raise SystemExit(f"Unknown --source-id: {source_id} (add it via kb-add-source first)")

    passage_id = f"pas_{uuid.uuid4().hex[:12]}"
    obj = {
        "passage_id": passage_id,
        "source_id": source_id,
        "text": text,
        "loc": loc,
        "tags": tags,
        "notes": notes,
        "created_at": _now_iso(),
    }
    _append_jsonl(ws_path / "kb/passages.jsonl", obj)
    return passage_id


def get_passages_by_ids(ws_path: Path, passage_ids: list[str]) -> list[dict[str, Any]]:
    rows = _read_jsonl(ws_path / "kb/passages.jsonl")
    by_id = {r.get("passage_id"): r for r in rows if r.get("passage_id")}

    missing = [pid for pid in passage_ids if pid not in by_id]
    if missing:
        raise SystemExit(f"Unknown passage_id(s): {', '.join(missing)}")

    return [by_id[pid] for pid in passage_ids]
