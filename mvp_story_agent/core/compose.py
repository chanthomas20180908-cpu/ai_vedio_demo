from __future__ import annotations

import hashlib
from pathlib import Path

from mvp_story_agent.core.kb import get_passages_by_ids
from mvp_story_agent.core.workspace import read_workspace_meta


def _sha1_text(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def compose_input(
    *,
    ws_path: Path,
    passage_ids: list[str],
    brief,
    no_glue: bool,
    output_relpath: Path,
) -> None:
    meta = read_workspace_meta(ws_path)
    title = (brief or meta.get("title") or meta.get("name") or "story").strip()

    passages = get_passages_by_ids(ws_path, passage_ids)

    # Body: keep as much original text as possible.
    body_parts: list[str] = []
    glue = "\n\n（转场：承接上文，故事继续。）\n\n"
    for idx, p in enumerate(passages):
        text = (p.get("text") or "").rstrip()
        if not text:
            continue
        if idx > 0 and not no_glue:
            body_parts.append(glue)
        body_parts.append(text)

    body = "\n\n".join([part for part in body_parts if part.strip()])

    # Evidence section: make grounding explicit.
    evidence_lines: list[str] = []
    for p in passages:
        pid = p.get("passage_id")
        sid = p.get("source_id")
        loc = p.get("loc")
        tags = p.get("tags") or []
        text = (p.get("text") or "").strip()
        excerpt = text.replace("\n", " ")
        if len(excerpt) > 120:
            excerpt = excerpt[:120] + "…"
        evidence_lines.append(
            f"- {pid} (source={sid}{', loc=' + loc if loc else ''}{', tags=' + ','.join(tags) if tags else ''}): {excerpt}"
        )

    out = []
    out.append(f"# {title}\n")
    out.append("## 故事正文\n")
    out.append(body + "\n" if body.strip() else "（暂无正文：请先添加 passages 再 compose）\n")
    out.append("\n## 引用原文证据\n")
    out.append("\n".join(evidence_lines) + "\n")

    out_text = "\n".join(out).rstrip() + "\n"

    out_path = (ws_path / output_relpath).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(out_text, encoding="utf-8")

    # Write a tiny sidecar for traceability (optional, but cheap).
    sidecar = out_path.with_suffix(out_path.suffix + ".meta.json")
    sidecar.write_text(
        (
            "{\n"
            f"  \"title\": {title!r},\n"
            f"  \"passage_ids\": {passage_ids!r},\n"
            f"  \"content_sha1\": {_sha1_text(out_text)!r}\n"
            "}\n"
        ),
        encoding="utf-8",
    )
