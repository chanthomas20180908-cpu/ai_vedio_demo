"""Refill SRT text from a reference spoken transcript.

Goal:
- Keep the original SRT timing (start/end).
- Replace each cue's text using the provided reference text (spoken script).

This is designed for the pipeline:
- Timing comes from ASR/forced alignment (stable, no drift)
- Text should match the TTS spoken input (0 typos)

Heuristics:
- Normalize by removing whitespace + punctuation for matching.
- Walk forward in the reference with a pointer to keep monotonic order.
- For each cue, take a reference slice with length ~= normalized cue length.
- Optionally resync within a small lookahead window using difflib longest match.

Usage:
  /path/to/venv/bin/python3 tools/srt_refill_from_spoken.py \
    --ref_txt /abs/path/spoken.txt \
    --in_srt /abs/path/asr_short.srt \
    --out_srt /abs/path/asr_short_refill.srt
"""

from __future__ import annotations

import argparse
import difflib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


_WS_RE = re.compile(r"\s+")


def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")


def _strip_ws(s: str) -> str:
    return _WS_RE.sub("", s or "")


def _is_punc(ch: str) -> bool:
    # Minimal but practical punctuation set for zh/en.
    # We intentionally treat quotes/brackets as punctuation as well.
    return ch in (
        "，。！？；：、,.!?;:"
        "“”‘’'\""
        "（）()【】[]《》<>"
        "—-…"
        "~·`")


def _normalize_for_match(s: str) -> str:
    s = _strip_ws(s)
    if not s:
        return ""
    out = []
    for ch in s:
        if _is_punc(ch):
            continue
        out.append(ch)
    return "".join(out)


def _wrap_2lines(text: str, *, max_line: int = 16, max_lines: int = 2) -> str:
    """Wrap text into up to 2 lines by char count.

    We keep punctuation as-is; whitespace is removed.
    """
    t = _strip_ws(text)
    if not t:
        return ""
    lines: list[str] = []
    while t and len(lines) < max_lines:
        lines.append(t[:max_line])
        t = t[max_line:]
    if t and lines:
        lines[-1] = (lines[-1] + t)[:max_line]
    return "\n".join(lines)


@dataclass
class SrtCue:
    start_end: str  # keep original time line
    text: str


def _parse_srt(s: str) -> list[SrtCue]:
    blocks = re.split(r"\n\s*\n", (s or "").strip(), flags=re.M)
    cues: list[SrtCue] = []
    for b in blocks:
        lines = [ln.rstrip("\r") for ln in b.splitlines() if ln.strip() != ""]
        if len(lines) < 2:
            continue
        # tolerate optional leading index
        if re.fullmatch(r"\d+", lines[0]):
            if len(lines) < 3:
                continue
            time_line = lines[1]
            text_lines = lines[2:]
        else:
            time_line = lines[0]
            text_lines = lines[1:]
        text = "\n".join(text_lines).strip()
        cues.append(SrtCue(start_end=time_line.strip(), text=text))
    return cues


def _format_srt(cues: Iterable[SrtCue]) -> str:
    out: list[str] = []
    for i, c in enumerate(cues, 1):
        out.append(str(i))
        out.append(c.start_end)
        out.append(c.text or "")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def _build_ref_index(ref_raw: str) -> tuple[str, list[int]]:
    """Return (ref_norm, norm2raw_idx).

    ref_norm removes whitespace + punctuation.
    norm2raw_idx maps each char position in ref_norm to an index in ref_raw.
    """
    ref_norm_chars: list[str] = []
    norm2raw: list[int] = []
    for i, ch in enumerate(ref_raw or ""):
        if ch.isspace():
            continue
        if _is_punc(ch):
            continue
        ref_norm_chars.append(ch)
        norm2raw.append(i)
    return "".join(ref_norm_chars), norm2raw


def refill_srt_text(
    *,
    ref_txt: str,
    in_srt: str,
    max_line: int = 16,
    max_lines: int = 2,
    lookahead: int = 2000,
    match_min_ratio: float = 0.5,
) -> tuple[str, dict]:
    ref_raw = ref_txt or ""
    ref_norm, norm2raw = _build_ref_index(ref_raw)
    cues = _parse_srt(in_srt)
    if not cues:
        raise ValueError("未解析到任何 SRT cues")
    if not ref_norm:
        raise ValueError("ref_txt 为空或无法归一化（全是空白/标点？）")

    pos = 0
    used_match = 0
    used_fallback = 0
    total = 0

    out_cues: list[SrtCue] = []
    for c in cues:
        total += 1
        asr_norm = _normalize_for_match(c.text)
        want = max(1, len(asr_norm))

        # window
        w_start = pos
        w_end = min(len(ref_norm), pos + max(lookahead, want * 6))
        window = ref_norm[w_start:w_end]

        slice_start = pos

        # attempt resync when cue has enough content
        if asr_norm and len(asr_norm) >= 6 and window:
            m = difflib.SequenceMatcher(None, window, asr_norm).find_longest_match(
                0, len(window), 0, len(asr_norm)
            )
            # m.size is the longest common contiguous match length
            ratio = (m.size / max(1, len(asr_norm)))
            if m.size >= 4 and ratio >= match_min_ratio:
                # Align starts: window[m.a] corresponds to asr_norm[m.b]
                candidate = w_start + m.a - m.b
                if candidate < pos:
                    candidate = pos
                slice_start = candidate
                used_match += 1
            else:
                used_fallback += 1
        else:
            used_fallback += 1

        slice_end = min(len(ref_norm), slice_start + want)
        if slice_end <= slice_start:
            slice_end = min(len(ref_norm), slice_start + 1)

        # Map back to raw to optionally keep punctuation inside the span.
        if slice_start >= len(norm2raw):
            raw_piece = ""
        else:
            rs = norm2raw[slice_start]
            re_ = norm2raw[slice_end - 1] + 1 if (slice_end - 1) < len(norm2raw) else (norm2raw[-1] + 1)
            raw_piece = ref_raw[rs:re_]
        raw_piece = _strip_ws(raw_piece)
        out_text = _wrap_2lines(raw_piece, max_line=max_line, max_lines=max_lines)
        out_cues.append(SrtCue(start_end=c.start_end, text=out_text))

        pos = slice_end
        if pos >= len(ref_norm):
            # reference exhausted; keep remaining cues empty to avoid hallucinating
            pos = len(ref_norm)

    meta = {
        "cues": len(cues),
        "ref_norm_len": len(ref_norm),
        "used_match": used_match,
        "used_fallback": used_fallback,
        "match_min_ratio": match_min_ratio,
        "lookahead": lookahead,
        "max_line": max_line,
        "max_lines": max_lines,
    }
    return _format_srt(out_cues), meta


def main() -> int:
    ap = argparse.ArgumentParser(description="Refill SRT text from spoken transcript (keep timing)")
    ap.add_argument("--ref_txt", required=True, help="参考口播稿 txt 路径（正确文字来源）")
    ap.add_argument("--in_srt", required=True, help="输入 srt（时间轴来源）")
    ap.add_argument("--out_srt", required=True, help="输出 srt（时间轴不变、文字替换）")
    ap.add_argument("--max_line", type=int, default=16)
    ap.add_argument("--max_lines", type=int, default=2)
    ap.add_argument("--lookahead", type=int, default=2000)
    ap.add_argument("--match_min_ratio", type=float, default=0.5)
    args = ap.parse_args()

    ref_path = Path(args.ref_txt).expanduser().resolve()
    in_srt_path = Path(args.in_srt).expanduser().resolve()
    out_srt_path = Path(args.out_srt).expanduser().resolve()

    if not ref_path.exists():
        raise FileNotFoundError(str(ref_path))
    if not in_srt_path.exists():
        raise FileNotFoundError(str(in_srt_path))

    out_srt_path.parent.mkdir(parents=True, exist_ok=True)

    out_text, meta = refill_srt_text(
        ref_txt=_read_text(ref_path),
        in_srt=_read_text(in_srt_path),
        max_line=int(args.max_line),
        max_lines=int(args.max_lines),
        lookahead=int(args.lookahead),
        match_min_ratio=float(args.match_min_ratio),
    )
    out_srt_path.write_text(out_text, encoding="utf-8")

    print(f"OK: {out_srt_path}")
    print(f"meta: {meta}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
