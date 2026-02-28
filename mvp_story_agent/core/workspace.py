import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_WORKSPACE_ROOT = Path(
    "/Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/story_results"
)


@dataclass(frozen=True)
class Workspace:
    path: Path

    @property
    def kb_dir(self) -> Path:
        return self.path / "kb"

    @property
    def draft_dir(self) -> Path:
        return self.path / "draft"

    @property
    def sessions_dir(self) -> Path:
        return self.path / "sessions"

    @property
    def runs_dir(self) -> Path:
        return self.path / "runs"

    @property
    def workspace_json(self) -> Path:
        return self.path / "workspace.json"


def resolve_workspace(ws: str) -> Path:
    p = Path(ws).expanduser().resolve()
    if not p.exists():
        raise SystemExit(f"Workspace not found: {p}")
    if not (p / "workspace.json").exists():
        raise SystemExit(f"Not a workspace (missing workspace.json): {p}")
    return p


def read_workspace_meta(ws_path: Path) -> dict[str, Any]:
    with (ws_path / "workspace.json").open("r", encoding="utf-8") as f:
        return json.load(f)


def init_workspace(
    *,
    root: Path,
    name: str,
    title: Any,
    default_profile: Any,
    overwrite: bool,
) -> Path:
    root = root.expanduser().resolve()
    ws_path = (root / name).resolve()

    if ws_path.exists() and not overwrite:
        raise SystemExit(f"Workspace already exists: {ws_path} (use --overwrite)")

    # Create dirs
    (ws_path / "kb").mkdir(parents=True, exist_ok=True)
    (ws_path / "draft").mkdir(parents=True, exist_ok=True)
    (ws_path / "sessions").mkdir(parents=True, exist_ok=True)
    (ws_path / "runs").mkdir(parents=True, exist_ok=True)

    # Initialize empty JSONL files
    for rel in [
        "kb/sources.jsonl",
        "kb/passages.jsonl",
        "kb/derived.jsonl",
    ]:
        fp = ws_path / rel
        fp.parent.mkdir(parents=True, exist_ok=True)
        if overwrite or not fp.exists():
            fp.write_text("", encoding="utf-8")

    # Seed brief + input placeholders
    brief_path = ws_path / "draft/brief.md"
    if overwrite or not brief_path.exists():
        brief_path.write_text(
            "# brief\n\n用一句话写清楚你想混搭成什么故事（可选）。\n",
            encoding="utf-8",
        )

    input_path = ws_path / "draft/input.md"
    if overwrite or not input_path.exists():
        input_path.write_text(
            "# input\n\n（运行 compose 后生成：尽量保留原文的故事正文 + 证据列表）\n",
            encoding="utf-8",
        )

    meta = {
        "name": name,
        "title": title or name,
        "default_profile": default_profile,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "schema_version": 1,
    }
    (ws_path / "workspace.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    return ws_path
