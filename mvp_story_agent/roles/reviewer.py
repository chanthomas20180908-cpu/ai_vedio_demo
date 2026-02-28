import argparse
import json
from pathlib import Path
from config.logging_config import get_logger, setup_logging

from mvp_story_agent.core.llm_adapter import call_role_json
from mvp_story_agent.core.session_state import (
    allocate_version,
    ensure_session,
    get_last_output_path,
    load_state,
    record_output,
    save_state,
    version_dir,
)
from mvp_story_agent.core.workspace import resolve_workspace
logger = get_logger(__name__)


def main(argv=None) -> int:
    setup_logging()
    p = argparse.ArgumentParser(prog="story_reviewer")
    p.add_argument("--ws", required=True, help="Workspace path")
    p.add_argument("--session", required=True, help="Session id")
    p.add_argument("--model-type", default="gemini")
    p.add_argument("--model", default="gemini-3-pro-preview")
    p.add_argument("--api-key-env")
    p.add_argument("--thinking-level")
    args = p.parse_args(argv)

    ws = resolve_workspace(args.ws)
    ws_path = Path(ws)
    session_dir = ensure_session(ws_path, args.session)
    state = load_state(session_dir)
    logger.info("reviewer | session=%s", args.session)

    story_path = get_last_output_path(session_dir, state, "writer", "story.md")
    if not story_path:
        raise SystemExit("No story.md found. Run writer first.")
    logger.info("reviewer | story=%s", story_path)

    payload = {
        "story": story_path.read_text(encoding="utf-8"),
        "story_goal": state.get("story_goal") or {},
        "constraints": state.get("constraints") or [],
    }

    review = call_role_json(
        role="reviewer",
        payload=payload,
        model_type=args.model_type,
        model=args.model,
        api_key_env=args.api_key_env,
        thinking_level=args.thinking_level,
    )

    out_obj = {
        "issues": (review.get("issues") or [])[:3],
        "suggestions": (review.get("suggestions") or [])[:3],
    }

    version = allocate_version(state)
    vdir = version_dir(session_dir, version)
    out_path = vdir / "review.json"
    out_path.write_text(json.dumps(out_obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    logger.info(
        "reviewer | issues=%s suggestions=%s -> %s",
        len(out_obj["issues"]),
        len(out_obj["suggestions"]),
        out_path,
    )

    record_output(
        state,
        role="reviewer",
        version=version,
        files={"review.json": str(out_path.relative_to(session_dir))},
        summary=f"issues={len(out_obj['issues'])}",
    )
    save_state(session_dir, state)

    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
