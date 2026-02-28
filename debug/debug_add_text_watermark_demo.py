"""Minimal demo: batch add a classy corner text watermark to images.

- Default input dir: config.PICTURE_RESULTS_DIR
- Supports single-file input via --input
- Writes outputs into a sibling folder (does NOT overwrite originals)

Examples:
  python debug/debug_add_text_watermark_demo.py \
    --input "/Users/test/Library/Mobile Documents/com~apple~CloudDocs/my_mutimedia/my_images/搞笑老詹/gemini_3_pro_image_preview_1767527799_0.png" \
    --pos tl --text "汤圆" --styles all

  python debug/debug_add_text_watermark_demo.py --pos tl --styles all
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont


def _find_font_path(font_style: str = "round") -> Optional[Path]:
    """Prefer a good-looking Chinese-capable system font on macOS.

    font_style:
      - round: cute/rounded (best for "汤圆")
      - sans: modern
      - serif: classic
    """

    font_style = (font_style or "round").lower()

    # Keep this intentionally simple: just try a few known-good system fonts.
    if font_style == "serif":
        candidates = [
            Path("/System/Library/Fonts/Supplemental/Songti.ttc"),
            Path("/System/Library/Fonts/Supplemental/STSongti-SC-Regular.ttf"),
        ]
    elif font_style == "round":
        # "Round" preference, but must support Chinese glyphs.
        # PingFang SC is not perfectly rounded, but it's clean and always has Chinese.
        candidates = [
            Path("/System/Library/Fonts/Supplemental/PingFang.ttc"),
            Path("/System/Library/Fonts/PingFang.ttc"),
            Path("/Library/Fonts/PingFang.ttc"),
            # Hiragino Sans GB commonly supports Chinese and is a bit softer.
            Path("/System/Library/Fonts/Hiragino Sans GB.ttc"),
            Path("/System/Library/Fonts/Supplemental/Hiragino Sans GB.ttc"),
            # Heiti fallback
            Path("/System/Library/Fonts/STHeiti Medium.ttc"),
            Path("/System/Library/Fonts/STHeiti Light.ttc"),
            # These may NOT include Chinese on some systems; keep late.
            Path("/System/Library/Fonts/Supplemental/Kokonor.ttf"),
            Path("/System/Library/Fonts/Supplemental/Chalkboard.ttc"),
            Path("/System/Library/Fonts/Supplemental/ChalkboardSE.ttc"),
        ]
    else:
        candidates = [
            Path("/System/Library/Fonts/Supplemental/PingFang.ttc"),
            Path("/System/Library/Fonts/PingFang.ttc"),
            Path("/Library/Fonts/PingFang.ttc"),
            Path("/System/Library/Fonts/STHeiti Medium.ttc"),
            Path("/System/Library/Fonts/STHeiti Light.ttc"),
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


def _load_font(
    size: int,
    font_path: Optional[Path],
    font_style: str,
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if font_path is None:
        font_path = _find_font_path(font_style=font_style)
    if font_path is not None:
        try:
            return ImageFont.truetype(str(font_path), size=size)
        except Exception:
            pass
    return ImageFont.load_default()


def _clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))


def _compute_layout(w: int, h: int, font_scale: float = 1.0) -> Tuple[int, int, int, int, int]:
    """Return (margin, font_size, shadow_blur, pad, border_w)."""
    base = min(w, h)

    margin = _clamp(int(base * 0.03), 10, 72)

    # Smaller by default to feel more like a signature/badge.
    font_size = _clamp(int(base * 0.040 * font_scale), 14, 90)

    shadow_blur = _clamp(int(base * 0.004), 1, 6)

    # Badge geometry
    pad = _clamp(int(base * 0.012), 6, 28)
    border_w = _clamp(int(base * 0.006), 2, 10)

    return margin, font_size, shadow_blur, pad, border_w


def _text_bbox(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> Tuple[int, int, int, int]:
    # Pillow >= 8 supports textbbox
    return draw.textbbox((0, 0), text, font=font)


def _position_xy(
    pos: str, w: int, h: int, margin: int, text_w: int, text_h: int
) -> Tuple[int, int]:
    pos = pos.lower()
    if pos == "tl":
        return margin, margin
    if pos == "tr":
        return w - margin - text_w, margin
    if pos == "bl":
        return margin, h - margin - text_h
    if pos == "br":
        return w - margin - text_w, h - margin - text_h
    raise ValueError(f"Unsupported pos: {pos!r} (use tl/tr/bl/br)")


def _draw_text_bold(
    draw: ImageDraw.ImageDraw,
    xy: Tuple[float, float],
    text: str,
    font: ImageFont.ImageFont,
    fill: Tuple[int, int, int, int],
    bold_px: int,
) -> None:
    """Simple fake-bold while keeping readability.

    Strategy: draw faint offsets, then a crisp center glyph.
    Note: xy may be float (we'll round). Pillow accepts float, but rounding avoids fuzz.
    """

    x, y = int(round(xy[0])), int(round(xy[1]))
    if bold_px <= 0:
        draw.text((x, y), text, fill=fill, font=font)
        return

    r, g, b, a = fill
    # Offsets are lighter so we don't "muddy" the glyph.
    offset_fill = (r, g, b, _clamp(int(a * 0.55), 1, 255))

    offsets = [(bold_px, 0), (0, bold_px), (-bold_px, 0), (0, -bold_px)]
    for ox, oy in offsets:
        draw.text((x + ox, y + oy), text, fill=offset_fill, font=font)

    # Crisp center
    draw.text((x, y), text, fill=fill, font=font)


def _render_watermark_layer(
    size: Tuple[int, int],
    text: str,
    pos: str,
    style: int,
    opacity: float,
    font_scale: float,
    font_style: str,
    font_path: Optional[Path] = None,
) -> Image.Image:
    """Create an RGBA layer with the watermark drawn on it."""

    w, h = size
    margin, font_size, shadow_blur, pad, border_w = _compute_layout(w, h, font_scale=font_scale)

    # Draw into a small text canvas first (better control for shadow/blur)
    dummy = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(dummy)
    font = _load_font(font_size, font_path, font_style=font_style)

    l, t, r, b = _text_bbox(d, text, font)
    text_w, text_h = r - l, b - t

    # Badge bbox (for border styles)
    badge_w = text_w + pad * 2
    badge_h = text_h + pad * 2

    x, y = _position_xy(pos, w, h, margin, text_w, text_h)
    bx, by = _position_xy(pos, w, h, margin, badge_w, badge_h)

    # Opacity: weak-mid (0.10~0.14 typical)
    a = int(255 * max(0.0, min(1.0, opacity)))

    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))

    # Styles 4+ use a badge (rounded border). Keep radius conservative.
    radius = _clamp(int(min(badge_w, badge_h) * 0.35), 8, 32)

    # Style 1: plain text
    if style == 1:
        draw = ImageDraw.Draw(layer)
        _draw_text_bold(draw, (x, y), text, font=font, fill=(255, 255, 255, a), bold_px=0)
        return layer

    # Shadow layer (very subtle) used by styles 2/3
    if style in (2, 3):
        shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_alpha = _clamp(int(a * 0.45), 1, 120)
        shadow_offset = _clamp(int(min(w, h) * 0.0025), 1, 4)
        shadow_draw.text(
            (x + shadow_offset, y + shadow_offset),
            text,
            fill=(0, 0, 0, shadow_alpha),
            font=font,
        )
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=shadow_blur))
        layer.alpha_composite(shadow)

        draw = ImageDraw.Draw(layer)

        # Style 2: text + subtle shadow
        if style == 2:
            _draw_text_bold(draw, (x, y), text, font=font, fill=(255, 255, 255, a), bold_px=0)
            return layer

        # Style 3: text + subtle stroke + subtle shadow
        stroke_width = 1
        stroke_fill = (0, 0, 0, _clamp(int(a * 0.35), 1, 90))
        draw.text(
            (x, y),
            text,
            fill=(255, 255, 255, a),
            font=font,
            stroke_width=stroke_width,
            stroke_fill=stroke_fill,
        )
        return layer

    draw = ImageDraw.Draw(layer)

    # Style 4: thick rounded border + centered text (no fill)
    if style == 4:
        border_alpha = _clamp(int(a * 1.25), 10, 255)
        draw.rounded_rectangle(
            (bx, by, bx + badge_w, by + badge_h),
            radius=radius,
            outline=(255, 255, 255, border_alpha),
            width=border_w,
        )

        # Perfect centering using text bbox (handles font ascent/descent offsets).
        cx = bx + badge_w / 2.0
        cy = by + badge_h / 2.0
        tx = cx - (text_w / 2.0) - l
        ty = cy - (text_h / 2.0) - t

        bold_px = 1
        _draw_text_bold(draw, (tx, ty), text, font=font, fill=(255, 255, 255, a), bold_px=bold_px)
        return layer

    # Style 5: filled badge (very light) + thick border + text
    if style == 5:
        fill_alpha = _clamp(int(a * 0.35), 5, 90)
        border_alpha = _clamp(int(a * 1.35), 10, 255)
        draw.rounded_rectangle(
            (bx, by, bx + badge_w, by + badge_h),
            radius=radius,
            fill=(255, 255, 255, fill_alpha),
            outline=(255, 255, 255, border_alpha),
            width=border_w,
        )
        # Switch to dark text if background is filled light (keeps it classy)
        text_alpha = _clamp(int(a * 0.9), 10, 255)
        draw.text((bx + pad, by + pad), text, fill=(0, 0, 0, text_alpha), font=font)
        return layer

    raise ValueError(f"Unsupported style: {style} (use 1/2/3/4/5)")


def add_corner_text_watermark(
    in_path: Path,
    out_path: Path,
    text: str,
    pos: str,
    style: int,
    opacity: float,
    font_scale: float,
    font_style: str,
    font_path: Optional[Path] = None,
) -> None:
    img = Image.open(in_path)

    # Ensure RGBA for compositing
    base = img.convert("RGBA")
    wm = _render_watermark_layer(
        base.size,
        text=text,
        pos=pos,
        style=style,
        opacity=opacity,
        font_scale=font_scale,
        font_style=font_style,
        font_path=font_path,
    )
    out = Image.alpha_composite(base, wm)

    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Keep output simple: PNG always (no EXIF needed per user)
    out.save(out_path.with_suffix(".png"), format="PNG", optimize=True)


def iter_images(root: Path, recursive: bool = True) -> Iterable[Path]:
    exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
    if root.is_file():
        if root.suffix.lower() in exts:
            yield root
        return

    if recursive:
        it = root.rglob("*")
    else:
        it = root.glob("*")

    for p in it:
        if p.is_file() and p.suffix.lower() in exts:
            yield p


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default=None, help="Input image file or directory. Default: config.PICTURE_RESULTS_DIR")
    parser.add_argument("--text", type=str, default="汤圆2060", help="Watermark text")
    parser.add_argument("--pos", type=str, default="tl", choices=["tl", "tr", "bl", "br"], help="Corner position")
    parser.add_argument(
        "--styles",
        type=str,
        default="all",
        help="1,2,3,4,5 or 'all' (default). Example: --styles 4 or --styles 2,5",
    )
    parser.add_argument("--opacity", type=float, default=0.12, help="Opacity in [0,1], e.g. 0.12 (weak-mid)")
    parser.add_argument(
        "--font-scale",
        type=float,
        default=0.75,
        help="Font size scale factor (default 0.75 = smaller signature).",
    )
    parser.add_argument(
        "--font-style",
        type=str,
        default="round",
        choices=["round", "sans", "serif"],
        help="Font style preference: round (Kokonor/Chalkboard), sans (PingFang-like), serif (Songti-like)",
    )
    parser.add_argument("--no-recursive", action="store_true", help="Do not recurse into subfolders when input is a directory")

    args = parser.parse_args()

    # Resolve input
    if args.input is None:
        from config import config as project_config

        input_root = Path(project_config.PICTURE_RESULTS_DIR)
    else:
        input_root = Path(args.input).expanduser()

    # Resolve styles
    if args.styles.strip().lower() == "all":
        styles: List[int] = [1, 2, 3, 4, 5]
    else:
        styles = [int(s) for s in args.styles.split(",") if s.strip()]

    font_path = _find_font_path(font_style=args.font_style)

    # Output dir: sibling folder
    if input_root.is_file():
        base_out_dir = input_root.parent / "_watermark_demo"
    else:
        base_out_dir = input_root / "_watermark_demo"

    paths = list(iter_images(input_root, recursive=not args.no_recursive))
    if not paths:
        print(f"No images found under: {input_root}")
        return 1

    for style in styles:
        out_dir = base_out_dir / f"style_{style}"
        for p in paths:
            # Keep relative structure when input is a directory
            if input_root.is_dir():
                rel = p.relative_to(input_root)
                out_path = out_dir / rel
            else:
                out_path = out_dir / p.name

            add_corner_text_watermark(
                in_path=p,
                out_path=out_path,
                text=args.text,
                pos=args.pos,
                style=style,
                opacity=args.opacity,
                font_scale=args.font_scale,
                font_style=args.font_style,
                font_path=font_path,
            )

    print(f"Done. Output under: {base_out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
