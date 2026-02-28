import argparse
import sys
from pathlib import Path

from mvp_story_agent.core.compose import compose_input
from mvp_story_agent.core.kb import add_passage, add_source
from mvp_story_agent.core.workspace import DEFAULT_WORKSPACE_ROOT, init_workspace, resolve_workspace


def _cmd_init_workspace(args: argparse.Namespace) -> int:
    ws_path = init_workspace(
        root=Path(args.root) if args.root else DEFAULT_WORKSPACE_ROOT,
        name=args.name,
        title=args.title,
        default_profile=args.default_profile,
        overwrite=args.overwrite,
    )
    print(str(ws_path))
    return 0


def _cmd_kb_add_source(args: argparse.Namespace) -> int:
    ws = resolve_workspace(args.ws)
    source_id = add_source(
        ws_path=ws,
        title=args.title,
        author=args.author,
        url=args.url,
        license=args.license,
        notes=args.notes,
    )
    print(source_id)
    return 0


def _cmd_kb_add_passage(args: argparse.Namespace) -> int:
    ws = resolve_workspace(args.ws)
    tags = [t.strip() for t in (args.tags or "").split(",") if t.strip()]
    passage_id = add_passage(
        ws_path=ws,
        source_id=args.source_id,
        text=args.text,
        loc=args.loc,
        tags=tags,
        notes=args.notes,
    )
    print(passage_id)
    return 0


def _cmd_compose(args: argparse.Namespace) -> int:
    ws = resolve_workspace(args.ws)
    passage_ids = [p.strip() for p in args.passage_ids.split(",") if p.strip()]
    if not passage_ids:
        raise SystemExit("--passage-ids is empty")

    compose_input(
        ws_path=ws,
        passage_ids=passage_ids,
        brief=args.brief,
        no_glue=args.no_glue,
        output_relpath=Path("draft/input.md"),
    )
    print(str(ws / "draft/input.md"))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="mvp_story_agent",
        description="MVP Story Agent CLI (workspace + original-text KB + mix-and-match compose)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init-workspace", help="Create a new story workspace")
    p_init.add_argument("name", help="Workspace name (directory name)")
    p_init.add_argument("--root", help=f"Workspace root dir (default: {DEFAULT_WORKSPACE_ROOT})")
    p_init.add_argument("--title", help="Workspace title")
    p_init.add_argument("--default-profile", help="Optional default render profile")
    p_init.add_argument("--overwrite", action="store_true", help="Allow overwriting an existing workspace")
    p_init.set_defaults(fn=_cmd_init_workspace)

    p_src = sub.add_parser("kb-add-source", help="Append one source record into kb/sources.jsonl")
    p_src.add_argument("--ws", required=True, help="Workspace path")
    p_src.add_argument("--title", required=True)
    p_src.add_argument("--author")
    p_src.add_argument("--url")
    p_src.add_argument("--license")
    p_src.add_argument("--notes")
    p_src.set_defaults(fn=_cmd_kb_add_source)

    p_pas = sub.add_parser("kb-add-passage", help="Append one passage record into kb/passages.jsonl")
    p_pas.add_argument("--ws", required=True, help="Workspace path")
    p_pas.add_argument("--source-id", required=True)
    p_pas.add_argument("--text", required=True, help="Original text passage (keep as-is)")
    p_pas.add_argument("--loc", help="Location hint, e.g. chapter/page")
    p_pas.add_argument("--tags", help="Comma-separated tags")
    p_pas.add_argument("--notes")
    p_pas.set_defaults(fn=_cmd_kb_add_passage)

    p_cmp = sub.add_parser("compose", help="Compose draft/input.md by mixing selected passages")
    p_cmp.add_argument("--ws", required=True, help="Workspace path")
    p_cmp.add_argument("--passage-ids", required=True, help="Comma-separated passage ids, in desired order")
    p_cmp.add_argument("--brief", help="Optional one-line brief to guide glue text")
    p_cmp.add_argument("--no-glue", action="store_true", help="Do not add any glue text")
    p_cmp.set_defaults(fn=_cmd_compose)

    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.fn(args))
    except BrokenPipeError:
        return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
