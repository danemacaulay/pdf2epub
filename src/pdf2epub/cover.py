from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Calibre-like portrait cover (half of Calibre's default 1200x1600).
COVER_WIDTH = 600
COVER_HEIGHT = 800

# Soft blue Blocks-style palette inspired by Calibre's default cover.
_TOP = (90, 122, 168)
_BOTTOM = (45, 62, 92)
_TEXT = (255, 255, 255)
_RULE = (230, 236, 245)


def _load_font(size: int, bold: bool = False) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    candidates = []
    if bold:
        candidates.extend(
            [
                "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
                "/Library/Fonts/Arial Bold.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
            ]
        )
    candidates.extend(
        [
            "/System/Library/Fonts/Supplemental/Georgia.ttf",
            "/Library/Fonts/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
        ]
    )
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont | ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _draw_centered_block(
    draw: ImageDraw.ImageDraw,
    *,
    lines: list[str],
    font: ImageFont.ImageFont | ImageFont.FreeTypeFont,
    top: int,
    fill: tuple[int, int, int],
    line_gap: int,
) -> int:
    y = top
    for line in lines:
        width = int(draw.textlength(line, font=font))
        x = (COVER_WIDTH - width) // 2
        draw.text((x, y), line, font=font, fill=fill)
        bbox = draw.textbbox((0, 0), line, font=font)
        y += (bbox[3] - bbox[1]) + line_gap
    return y


def generate_cover_image(
    out_path: Path,
    *,
    title: str,
    author: str | None,
) -> Path:
    """Write a Calibre-style title/author cover JPEG and return its path."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGB", (COVER_WIDTH, COVER_HEIGHT), _TOP)
    draw = ImageDraw.Draw(img)
    split_y = (COVER_HEIGHT * 2) // 3
    draw.rectangle((0, split_y, COVER_WIDTH, COVER_HEIGHT), fill=_BOTTOM)

    margin = int(COVER_WIDTH * 0.1)
    max_text_width = COVER_WIDTH - 2 * margin

    title_font = _load_font(42, bold=True)
    title_lines = _wrap_text(draw, title.strip() or "Untitled", title_font, max_text_width)
    # Cap very long titles so they stay in the upper band.
    title_lines = title_lines[:6]

    title_top = int(COVER_HEIGHT * 0.18)
    title_bottom = _draw_centered_block(
        draw,
        lines=title_lines,
        font=title_font,
        top=title_top,
        fill=_TEXT,
        line_gap=10,
    )

    if author and author.strip():
        rule_y = min(title_bottom + 28, split_y - 40)
        rule_half = int(COVER_WIDTH * 0.12)
        draw.line(
            (COVER_WIDTH // 2 - rule_half, rule_y, COVER_WIDTH // 2 + rule_half, rule_y),
            fill=_RULE,
            width=2,
        )
        author_font = _load_font(28, bold=False)
        author_lines = _wrap_text(draw, author.strip(), author_font, max_text_width)[:3]
        author_top = split_y + int((COVER_HEIGHT - split_y - 40) * 0.35)
        _draw_centered_block(
            draw,
            lines=author_lines,
            font=author_font,
            top=author_top,
            fill=_TEXT,
            line_gap=8,
        )

    img.save(out_path, format="JPEG", quality=90, optimize=True)
    return out_path
