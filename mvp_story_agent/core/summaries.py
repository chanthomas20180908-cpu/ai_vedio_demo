import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def summaries_dir(ws_path: Path) -> Path:
    return ws_path / "summaries"


def summaries_index_path(ws_path: Path) -> Path:
    return summaries_dir(ws_path) / "index.json"


def _safe_label(label: str) -> str:
    label = (label or "").strip()
    label = label.replace("/", "_").replace("\\", "_")
    label = re.sub(r"\s+", "_", label)
    label = re.sub(r"[^\w\u4e00-\u9fff\-.]+", "_", label)
    label = label.strip("_").strip(".")
    return label or "source"


def _source_key(source_id: str) -> str:
    return hashlib.sha1(source_id.encode("utf-8")).hexdigest()[:8]


def _source_dir_name(source_label: str, source_id: str) -> str:
    safe = _safe_label(source_label)
    return f"{safe}__{_source_key(source_id)}"


def ensure_summaries_dir(ws_path: Path) -> None:
    summaries_dir(ws_path).mkdir(parents=True, exist_ok=True)


def load_summaries_index(ws_path: Path) -> Dict[str, Any]:
    ensure_summaries_dir(ws_path)
    idx_path = summaries_index_path(ws_path)
    if not idx_path.exists():
        return {"sources": {}}
    return json.loads(idx_path.read_text(encoding="utf-8"))


def save_summaries_index(ws_path: Path, index: Dict[str, Any]) -> None:
    ensure_summaries_dir(ws_path)
    idx_path = summaries_index_path(ws_path)
    idx_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _next_version(source_dir: Path) -> int:
    max_v = 0
    for fp in source_dir.glob("v*.summary.json"):
        name = fp.stem  # v001.summary -> v001.summary
        if not name.startswith("v"):
            continue
        try:
            v = int(name[1:].split(".")[0])
        except ValueError:
            continue
        max_v = max(max_v, v)
    return max_v + 1


def write_summary(
    *,
    ws_path: Path,
    source_id: str,
    source_label: str,
    source_type: str,
    source_path: Optional[str],
    source_loc: Optional[str],
    source_tags: Iterable[str],
    business: Dict[str, Any],
    model: Optional[str] = None,
) -> Path:
    ensure_summaries_dir(ws_path)
    index = load_summaries_index(ws_path)
    source_key = _source_key(source_id)
    dir_name = _source_dir_name(source_label, source_id)
    source_dir = summaries_dir(ws_path) / "by_source" / dir_name
    source_dir.mkdir(parents=True, exist_ok=True)

    version = _next_version(source_dir)
    summary_id = f"sum_{source_key}_v{version:03d}"

    business_out = {
        "source_label": source_label,
        "source_theme": business.get("source_theme") or "",
        "facts": business.get("facts") or [],
        "motifs": business.get("motifs") or [],
        "conflicts": business.get("conflicts") or [],
    }

    meta_out = {
        "summary_id": summary_id,
        "version": f"v{version:03d}",
        "source_id": source_id,
        "source_label": source_label,
        "source_key": source_key,
        "source_type": source_type,
        "source_path": source_path or "",
        "source_loc": source_loc or "",
        "source_tags": list(source_tags or []),
        "created_at": _now_iso(),
        "model": model or "",
    }

    out = {"business": business_out, "meta": meta_out}
    out_path = source_dir / f"v{version:03d}.summary.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    src_entry = index.setdefault("sources", {}).setdefault(source_key, {})
    src_entry.update(
        {
            "source_id": source_id,
            "source_label": source_label,
            "source_key": source_key,
            "dir": str(source_dir.relative_to(ws_path)),
            "latest_version": f"v{version:03d}",
            "latest_file": str(out_path.relative_to(ws_path)),
        }
    )
    versions = src_entry.setdefault("versions", [])
    versions.append(
        {
            "summary_id": summary_id,
            "version": f"v{version:03d}",
            "file": str(out_path.relative_to(ws_path)),
            "created_at": meta_out["created_at"],
        }
    )
    save_summaries_index(ws_path, index)
    return out_path
