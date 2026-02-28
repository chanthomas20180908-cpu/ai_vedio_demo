"""Batch add a classy corner badge watermark (finalized style) to images.

Defaults:
- Input dir: config.PICTURE_RESULTS_DIR
- Non-recursive (only files directly under the directory)
- Output: PNG written back into the same directory, with a timestamp suffix to avoid name collisions

Example:
  python3 tools/add_watermark.py

Test on a specific folder:
  python3 tools/add_watermark.py --input-dir "/path/to/images" --pos tl

Notes:
- This intentionally keeps implementation simple.
- Does NOT overwrite originals.
- Does not preserve EXIF (outputs PNG).
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

# Allow running as: python3 tools/add_watermark.py
# (ensures project root is on sys.path so `from config import config` works)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PIL import Image, ImageDraw, ImageFilter, ImageFont


# =========================
# IDE-friendly config block
# Edit these in your IDE, then run the script.
# CLI args (if provided) will override these values.
# =========================

# Set to a path string (or Path) to override defaults, e.g. "/path/to/input"
# INPUT_DIR = '/Users/test/Library/Mobile Documents/com~apple~CloudDocs/my_mutimedia/my_images/一比一角色形象图/NBA'
INPUT_DIR = '/Users/test/Library/Mobile Documents/com~apple~CloudDocs/BEAST_BEING/my_mutimedia/my_images/input'
# If None, defaults to (config.PICTURE_RESULTS_DIR / "_watermark_out")
# OUTPUT_DIR = '/Users/test/Library/Mobile Documents/com~apple~CloudDocs/BEAST_BEING/my_mutimedia/my_scripts/NBA/戈登与谷爱凌合体/原图/水印图'

# Default watermark params
DEFAULT_TEXT = "汤圆2060"
DEFAULT_POS = "tl"  # tl/tr/bl/br
DEFAULT_OPACITY = 0.3
DEFAULT_FONT_SCALE = 0.9


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


def _clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))


def _find_font_path_round() -> Optional[Path]:
    """Pick a Chinese-capable, slightly softer system font on macOS.

    Avoid fonts that may lack Chinese glyphs (which would render as tofu boxes).
    """

    candidates = [
        # Chinese-capable defaults
        Path("/System/Library/Fonts/Supplemental/PingFang.ttc"),
        Path("/System/Library/Fonts/PingFang.ttc"),
        Path("/Library/Fonts/PingFang.ttc"),
        # Often softer looking
        Path("/System/Library/Fonts/Hiragino Sans GB.ttc"),
        Path("/System/Library/Fonts/Supplemental/Hiragino Sans GB.ttc"),
        # Heiti fallback
        Path("/System/Library/Fonts/STHeiti Medium.ttc"),
        Path("/System/Library/Fonts/STHeiti Light.ttc"),
        # May or may not contain Chinese glyphs; keep late
        Path("/System/Library/Fonts/Supplemental/Kokonor.ttf"),
        Path("/System/Library/Fonts/Supplemental/Chalkboard.ttc"),
        Path("/System/Library/Fonts/Supplemental/ChalkboardSE.ttc"),
    ]

    # Common open fonts (if user installed)
    candidates += [
        Path("/Library/Fonts/NotoSansCJK-Regular.ttc"),
        Path("/Library/Fonts/NotoSansCJKsc-Regular.otf"),
    ]

    for p in candidates:
        if p.exists():
            return p
    return None


def _load_font(size: int, font_path: Optional[Path]) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if font_path is None:
        font_path = _find_font_path_round()
    if font_path is not None:
        try:
            return ImageFont.truetype(str(font_path), size=size)
        except Exception:
            pass
    return ImageFont.load_default()


def _compute_layout(w: int, h: int, font_scale: float) -> Tuple[int, int, int, int, int]:
    """Return (margin, font_size, shadow_blur, pad, border_w)."""

    base = min(w, h)

    margin = _clamp(int(base * 0.03), 10, 72)
    font_size = _clamp(int(base * 0.040 * font_scale), 14, 90)
    shadow_blur = _clamp(int(base * 0.004), 1, 6)
    pad = _clamp(int(base * 0.012), 6, 28)
    border_w = _clamp(int(base * 0.006), 2, 10)

    return margin, font_size, shadow_blur, pad, border_w


def _position_xy(pos: str, w: int, h: int, margin: int, box_w: int, box_h: int) -> Tuple[int, int]:
    pos = pos.lower()
    if pos == "tl":
        return margin, margin
    if pos == "tr":
        return w - margin - box_w, margin
    if pos == "bl":
        return margin, h - margin - box_h
    if pos == "br":
        return w - margin - box_w, h - margin - box_h
    raise ValueError(f"Unsupported pos: {pos!r} (use tl/tr/bl/br)")


def _draw_text_slight_bold(
    draw: ImageDraw.ImageDraw,
    xy: Tuple[float, float],
    text: str,
    font: ImageFont.ImageFont,
    fill: Tuple[int, int, int, int],
    bold_px: int = 1,
) -> None:
    x, y = int(round(xy[0])), int(round(xy[1]))
    if bold_px <= 0:
        draw.text((x, y), text, fill=fill, font=font)
        return

    r, g, b, a = fill
    offset_fill = (r, g, b, _clamp(int(a * 0.55), 1, 255))

    for ox, oy in [(bold_px, 0), (0, bold_px), (-bold_px, 0), (0, -bold_px)]:
        draw.text((x + ox, y + oy), text, fill=offset_fill, font=font)
    draw.text((x, y), text, fill=fill, font=font)


def add_badge_watermark(
    in_path: Path,
    out_path: Path,
    text: str,
    pos: str,
    opacity: float,
    font_scale: float,
    font_path: Optional[Path] = None,
) -> None:
    img = Image.open(in_path)
    base = img.convert("RGBA")

    w, h = base.size
    margin, font_size, shadow_blur, pad, border_w = _compute_layout(w, h, font_scale=font_scale)
    font = _load_font(font_size, font_path)

    # Measure text bbox for accurate centering.
    tmp = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dtmp = ImageDraw.Draw(tmp)
    l, t, r, b = dtmp.textbbox((0, 0), text, font=font)
    text_w, text_h = r - l, b - t

    badge_w = text_w + pad * 2
    badge_h = text_h + pad * 2

    bx, by = _position_xy(pos, w, h, margin, badge_w, badge_h)

    a = int(255 * max(0.0, min(1.0, opacity)))

    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))

    # Optional very subtle shadow behind the badge border.
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    shadow_alpha = _clamp(int(a * 0.18), 1, 80)
    shadow_offset = _clamp(int(min(w, h) * 0.0020), 1, 3)
    radius = _clamp(int(min(badge_w, badge_h) * 0.35), 8, 32)
    sdraw.rounded_rectangle(
        (bx + shadow_offset, by + shadow_offset, bx + badge_w + shadow_offset, by + badge_h + shadow_offset),
        radius=radius,
        outline=(0, 0, 0, shadow_alpha),
        width=border_w,
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=shadow_blur))
    layer.alpha_composite(shadow)

    draw = ImageDraw.Draw(layer)

    border_alpha = _clamp(int(a * 1.25), 10, 255)
    draw.rounded_rectangle(
        (bx, by, bx + badge_w, by + badge_h),
        radius=radius,
        outline=(255, 255, 255, border_alpha),
        width=border_w,
    )

    # Perfect centering inside badge
    cx = bx + badge_w / 2.0
    cy = by + badge_h / 2.0
    tx = cx - (text_w / 2.0) - l
    ty = cy - (text_h / 2.0) - t

    _draw_text_slight_bold(draw, (tx, ty), text, font=font, fill=(255, 255, 255, a), bold_px=1)

    out = Image.alpha_composite(base, layer)
    out.save(out_path, format="PNG", optimize=True)


def _unique_out_path(output_dir: Path, in_file: Path, ts: str) -> Path:
    stem = in_file.stem
    base = output_dir / f"{stem}__wm_{ts}.png"
    if not base.exists():
        return base
    # extremely simple collision handling
    for i in range(1, 1000):
        p = output_dir / f"{stem}__wm_{ts}_{i:02d}.png"
        if not p.exists():
            return p
    raise RuntimeError(f"Could not find a unique output path for {in_file.name}")


def _resolve_dir_value(v) -> Optional[Path]:
    if v is None:
        return None
    if isinstance(v, Path):
        return v
    return Path(str(v)).expanduser()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-dir",
        type=str,
        default=None,
        help="Directory of images. Overrides INPUT_DIR. Default: config.PICTURE_RESULTS_DIR",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help='Output directory. Overrides OUTPUT_DIR. Default: config.PICTURE_RESULTS_DIR / "_watermark_out"',
    )
    parser.add_argument("--text", type=str, default=None, help="Watermark text")
    parser.add_argument("--pos", type=str, default=None, choices=["tl", "tr", "bl", "br"], help="Corner position")
    parser.add_argument("--opacity", type=float, default=None, help="Opacity in [0,1], e.g. 0.12")
    parser.add_argument("--font-scale", type=float, default=None, help="Font size scale factor")

    args = parser.parse_args()

    from config import config as project_config

    # Resolve input dir (CLI > IDE config > project default)
    input_dir = (
        Path(args.input_dir).expanduser()
        if args.input_dir is not None
        else (_resolve_dir_value(INPUT_DIR) or Path(project_config.PICTURE_RESULTS_DIR))
    )

    if not input_dir.exists() or not input_dir.is_dir():
        raise SystemExit(f"input-dir must be an existing directory: {input_dir}")

    # Resolve output dir (CLI > IDE config > default under results dir)
    output_dir = (
        Path(args.output_dir).expanduser()
        if args.output_dir is not None
        else ((Path(project_config.PICTURE_RESULTS_DIR) / "_watermark_out"))
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    # Resolve watermark params (CLI > IDE defaults)
    text = args.text if args.text is not None else DEFAULT_TEXT
    pos = args.pos if args.pos is not None else DEFAULT_POS
    opacity = args.opacity if args.opacity is not None else DEFAULT_OPACITY
    font_scale = args.font_scale if args.font_scale is not None else DEFAULT_FONT_SCALE

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    font_path = _find_font_path_round()

    # Non-recursive: only process direct children
    files = [p for p in sorted(input_dir.iterdir()) if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
    if not files:
        print(f"No images found in: {input_dir}")
        return 1

    ok = 0
    failed = []
    for p in files:
        try:
            out_path = _unique_out_path(output_dir, p, ts)
            add_badge_watermark(
                in_path=p,
                out_path=out_path,
                text=text,
                pos=pos,
                opacity=opacity,
                font_scale=font_scale,
                font_path=font_path,
            )
            ok += 1
        except Exception as e:
            failed.append((p, str(e)))

    print(f"Done. input={input_dir} output={output_dir} total={len(files)} ok={ok} failed={len(failed)}")
    if failed:
        for p, msg in failed[:20]:
            print(f"  FAIL {p.name}: {msg}")
        if len(failed) > 20:
            print(f"  ... and {len(failed) - 20} more")

    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
