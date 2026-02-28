import argparse
import json
from pathlib import Path
from config.logging_config import get_logger, setup_logging

from mvp_story_agent.core.kb import get_passages_by_ids
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
from mvp_story_agent.core.summaries import summaries_index_path, write_summary
from mvp_story_agent.core.workspace import resolve_workspace
logger = get_logger(__name__)


def _parse_items(s: str) -> list[str]:
    return [x.strip() for x in (s or "").split(",") if x.strip()]


def _resolve_file(ws_path: Path, item: str) -> Path:
    p = Path(item).expanduser()
    if not p.is_absolute():
        p = (ws_path / p).resolve()
    return p


def _source_label(item: dict) -> str:
    if item.get("type") == "file" and item.get("path"):
        return Path(item["path"]).stem
    if item.get("source_path"):
        return Path(item["source_path"]).stem
    return item.get("source_id") or item.get("id") or "source"


def main(argv=None) -> int:
    setup_logging()
    p = argparse.ArgumentParser(prog="story_reader")
    p.add_argument("--ws", required=True, help="Workspace path")
    p.add_argument("--session", required=True, help="Session id")
    p.add_argument("--items", help="Comma-separated items (passage_id or file path)")
    p.add_argument("--mode", choices=["materials", "summary"], default="materials")
    p.add_argument(
        "--use-last-materials",
        action="store_true",
        help="In summary mode, write summaries from latest materials.json by_source without LLM",
    )
    p.add_argument("--model-type", default="gemini")
    p.add_argument("--model", default="gemini-3-pro-preview")
    p.add_argument("--api-key-env")
    p.add_argument("--thinking-level")
    args = p.parse_args(argv)

    ws = resolve_workspace(args.ws)
    ws_path = Path(ws)
    session_dir = ensure_session(ws_path, args.session)
    state = load_state(session_dir)
    logger.info("reader | session=%s", args.session)

    selected = list(state.get("selected_items") or [])
    if args.items:
        selected = _parse_items(args.items)
        state["selected_items"] = selected

    if not selected and not (args.mode == "summary" and args.use_last_materials):
        raise SystemExit("No selected items. Use story_select to add items first.")
    logger.info("reader | selected_items=%s", len(selected))

    passage_ids = [x for x in selected if x.startswith("pas_")]
    file_items = [x for x in selected if not x.startswith("pas_")]

    items = []
    if passage_ids:
        passages = get_passages_by_ids(ws_path, passage_ids)
        logger.info("reader | passage_ids=%s", len(passages))
        for psg in passages:
            items.append(
                {
                    "id": psg.get("passage_id"),
                    "type": "passage",
                    "text": psg.get("text") or "",
                    "source_id": psg.get("source_id"),
                    "loc": psg.get("loc"),
                    "tags": psg.get("tags") or [],
                }
            )

    for item in file_items:
        fp = _resolve_file(ws_path, item)
        if not fp.exists():
            raise SystemExit(f"File not found: {fp}")
        logger.info("reader | file=%s", fp)
        items.append(
            {
                "id": item,
                "type": "file",
                "path": str(fp),
                "text": fp.read_text(encoding="utf-8"),
            }
        )
    if args.mode == "summary":
        summaries_written = []
        if args.use_last_materials:
            materials_path = get_last_output_path(session_dir, state, "reader", "materials.json")
            if not materials_path:
                raise SystemExit("No materials.json found. Run reader (materials mode) first.")
            materials = json.loads(materials_path.read_text(encoding="utf-8"))
            by_source = materials.get("by_source") or []
            if not by_source:
                raise SystemExit("materials.json missing by_source. Re-run reader to generate it.")
            for entry in by_source:
                label = _source_label(entry)
                out_path = write_summary(
                    ws_path=ws_path,
                    source_id=entry.get("source_id") or "",
                    source_label=label,
                    source_type=entry.get("source_type") or "file",
                    source_path=entry.get("source_path"),
                    source_loc=entry.get("source_loc"),
                    source_tags=entry.get("source_tags") or [],
                    business={
                        "source_theme": entry.get("source_theme") or "",
                        "facts": entry.get("facts") or [],
                        "motifs": entry.get("motifs") or [],
                        "conflicts": entry.get("conflicts") or [],
                    },
                    model=args.model,
                )
                summaries_written.append(out_path)
        else:
            for idx, item in enumerate(items, start=1):
                label = _source_label(item)
                logger.info("reader | summary item=%s/%s label=%s", idx, len(items), label)
                payload = {"text": item.get("text") or "", "source_label": label}
                materials = call_role_json(
                    role="reader",
                    payload=payload,
                    model_type=args.model_type,
                    model=args.model,
                    api_key_env=args.api_key_env,
                    thinking_level=args.thinking_level,
                )
                out_path = write_summary(
                    ws_path=ws_path,
                    source_id=item.get("id") or "",
                    source_label=label,
                    source_type=item.get("type") or "file",
                    source_path=item.get("path"),
                    source_loc=item.get("loc"),
                    source_tags=item.get("tags") or [],
                    business={
                        "source_theme": materials.get("source_theme") or "",
                        "facts": materials.get("facts") or [],
                        "motifs": materials.get("motifs") or [],
                        "conflicts": materials.get("conflicts") or [],
                    },
                    model=args.model,
                )
                summaries_written.append(out_path)

        idx_path = summaries_index_path(ws_path)
        logger.info("reader | summaries_written=%s -> %s", len(summaries_written), idx_path)
        print(
            json.dumps(
                {
                    "summaries_written": [str(p) for p in summaries_written],
                    "index": str(idx_path),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    by_source = []
    for idx, item in enumerate(items, start=1):
        logger.info("reader | map item=%s/%s id=%s", idx, len(items), item.get("id"))
        label = _source_label(item)
        payload = {"text": item.get("text") or "", "source_label": label}
        materials = call_role_json(
            role="reader",
            payload=payload,
            model_type=args.model_type,
            model=args.model,
            api_key_env=args.api_key_env,
            thinking_level=args.thinking_level,
        )
        entry = {
            "source_id": item.get("id"),
            "source_type": item.get("type"),
            "source_path": item.get("path"),
            "source_loc": item.get("loc"),
            "source_tags": item.get("tags") or [],
            "source_theme": materials.get("source_theme") or "",
            "facts": materials.get("facts") or [],
            "motifs": materials.get("motifs") or [],
            "conflicts": materials.get("conflicts") or [],
        }
        logger.info(
            "reader | map done id=%s facts=%s motifs=%s conflicts=%s",
            entry["source_id"],
            len(entry["facts"]),
            len(entry["motifs"]),
            len(entry["conflicts"]),
        )
        by_source.append(entry)

    out_obj = {
        "facts": [x for s in by_source for x in s["facts"]],
        "motifs": [x for s in by_source for x in s["motifs"]],
        "conflicts": [x for s in by_source for x in s["conflicts"]],
        "sources": [i.get("id") for i in items],
        "by_source": by_source,
    }

    version = allocate_version(state)
    vdir = version_dir(session_dir, version)
    out_path = vdir / "materials.json"
    out_path.write_text(json.dumps(out_obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    logger.info(
        "reader | materials facts=%s motifs=%s conflicts=%s -> %s",
        len(out_obj["facts"]),
        len(out_obj["motifs"]),
        len(out_obj["conflicts"]),
        out_path,
    )

    record_output(
        state,
        role="reader",
        version=version,
        files={"materials.json": str(out_path.relative_to(session_dir))},
        summary=f"materials facts={len(out_obj['facts'])}",
    )
    save_state(session_dir, state)

    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
