import argparse
import json
from pathlib import Path
from config.logging_config import get_logger, setup_logging

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


def main(argv=None) -> int:
    setup_logging()
    p = argparse.ArgumentParser(prog="story_select")
    p.add_argument("--ws", required=True, help="Workspace path")
    p.add_argument("--session", required=True, help="Session id")
    p.add_argument("--add", help="Comma-separated items to add (passage_id or file path)")
    p.add_argument("--remove", help="Comma-separated items to remove")
    p.add_argument("--set", help="Comma-separated items to set (overwrite)")
    p.add_argument("--list", action="store_true", help="List current selected items")
    args = p.parse_args(argv)

    ws = resolve_workspace(args.ws)
    session_dir = ensure_session(Path(ws), args.session)
    state = load_state(session_dir)
    logger.info("select | session=%s", args.session)

    changed = False
    selected = list(state.get("selected_items") or [])

    if args.set:
        selected = _parse_items(args.set)
        changed = True

    if args.add:
        for item in _parse_items(args.add):
            if item not in selected:
                selected.append(item)
                changed = True

    if args.remove:
        remove_set = set(_parse_items(args.remove))
        if remove_set:
            new_selected = [x for x in selected if x not in remove_set]
            if new_selected != selected:
                selected = new_selected
                changed = True

    if args.list and not changed:
        logger.info("select | list only | selected_items=%s", len(selected))
        print(json.dumps({"selected_items": selected}, ensure_ascii=False, indent=2))
        return 0

    if changed:
        state["selected_items"] = selected
        version = allocate_version(state)
        vdir = version_dir(session_dir, version)
        out_path = vdir / "selection.json"
        out_path.write_text(
            json.dumps({"selected_items": selected}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        record_output(
            state,
            role="select",
            version=version,
            files={"selection.json": str(out_path.relative_to(session_dir))},
            summary=f"selected_items={len(selected)}",
        )
        save_state(session_dir, state)
        logger.info("select | wrote %s", out_path)
        print(str(out_path))
        return 0
    logger.info("select | no changes | selected_items=%s", len(selected))

    print(json.dumps({"selected_items": selected}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
