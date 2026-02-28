import argparse
import json
from pathlib import Path
from config.logging_config import get_logger, setup_logging

from mvp_story_agent.core.llm_adapter import call_role_json
from mvp_story_agent.core.summaries import load_summaries_index
from mvp_story_agent.core.session_state import (
    allocate_version,
    ensure_session,
    load_state,
    record_output,
    save_state,
    version_dir,
)
from mvp_story_agent.core.workspace import resolve_workspace
logger = get_logger(__name__)


def _parse_items(s: str) -> list[str]:
    return [x.strip() for x in (s or "").split(",") if x.strip()]


def _list_summaries(index: dict) -> list[dict]:
    items = []
    for key, info in (index.get("sources") or {}).items():
        items.append(
            {
                "source_key": key,
                "source_label": info.get("source_label") or "",
                "source_id": info.get("source_id") or "",
                "latest_version": info.get("latest_version") or "",
                "latest_file": info.get("latest_file") or "",
            }
        )
    return items


def _match_sources(index: dict, tokens: list[str]) -> list[str]:
    sources = index.get("sources") or {}
    if not tokens:
        return []
    if len(tokens) == 1 and tokens[0] in {"all", "*"}:
        return list(sources.keys())
    matched = []
    for token in tokens:
        for key, info in sources.items():
            if token in {key, info.get("source_label"), info.get("source_id")}:
                if key not in matched:
                    matched.append(key)
    if not matched:
        labels = [info.get("source_label") for info in sources.values()]
        raise SystemExit(f"No summaries matched. Available: {labels}")
    return matched


def main(argv=None) -> int:
    setup_logging()
    p = argparse.ArgumentParser(prog="story_ideator")
    p.add_argument("--ws", required=True, help="Workspace path")
    p.add_argument("--session", required=True, help="Session id")
    p.add_argument("--count", type=int, default=3, help="Number of ideas")
    p.add_argument("--summaries", help="Comma-separated summaries to use (source_label/source_id/source_key)")
    p.add_argument("--list-summaries", action="store_true", help="List available summaries")
    p.add_argument("--model-type", default="gemini")
    p.add_argument("--model", default="gemini-3-pro-preview")
    p.add_argument("--api-key-env")
    p.add_argument("--thinking-level")
    args = p.parse_args(argv)

    ws = resolve_workspace(args.ws)
    ws_path = Path(ws)
    session_dir = ensure_session(ws_path, args.session)
    state = load_state(session_dir)
    logger.info("ideator | session=%s", args.session)

    index = load_summaries_index(ws_path)
    if args.list_summaries:
        print(json.dumps({"summaries": _list_summaries(index)}, ensure_ascii=False, indent=2))
        return 0

    selected_keys = []
    if args.summaries:
        selected_keys = _match_sources(index, _parse_items(args.summaries))
        state["selected_summaries"] = selected_keys
        save_state(session_dir, state)
    else:
        selected_keys = list(state.get("selected_summaries") or [])

    if not selected_keys:
        raise SystemExit("No summaries selected. Use --summaries or --list-summaries.")

    summaries = []
    for key in selected_keys:
        info = (index.get("sources") or {}).get(key) or {}
        latest_file = info.get("latest_file")
        if not latest_file:
            continue
        fp = (ws_path / latest_file).resolve()
        if not fp.exists():
            raise SystemExit(f"Summary file not found: {fp}")
        data = json.loads(fp.read_text(encoding="utf-8"))
        summaries.append(data.get("business") or {})
    if not summaries:
        raise SystemExit("Selected summaries resolved to empty list.")
    logger.info("ideator | summaries=%s selected=%s", len(summaries), len(selected_keys))
    payload = {
        "summaries": summaries,
        "story_goal": state.get("story_goal") or {},
        "constraints": state.get("constraints") or [],
        "count": args.count,
    }

    ideas = call_role_json(
        role="ideator",
        payload=payload,
        model_type=args.model_type,
        model=args.model,
        api_key_env=args.api_key_env,
        thinking_level=args.thinking_level,
    )

    out_obj = {"ideas": ideas.get("ideas") or []}
    version = allocate_version(state)
    vdir = version_dir(session_dir, version)
    out_path = vdir / "ideas.json"
    out_path.write_text(json.dumps(out_obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    logger.info("ideator | ideas=%s -> %s", len(out_obj["ideas"]), out_path)

    record_output(
        state,
        role="ideator",
        version=version,
        files={"ideas.json": str(out_path.relative_to(session_dir))},
        summary=f"ideas={len(out_obj['ideas'])}",
    )
    save_state(session_dir, state)

    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
