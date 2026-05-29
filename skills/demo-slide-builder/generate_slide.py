"""
Demo Slide Builder — generate a .pptx from a JSON spec.

Usage:
    python generate_slide.py --input data.json
    python generate_slide.py --input data.json --output C:\\tmp\\my_deck.pptx
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from PIL import Image as PILImage
    _PIL_OK = True
except ImportError:
    _PIL_OK = False

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt, Emu

# ── Color palette ──────────────────────────────────────────────────────────────
NAVY   = RGBColor(0x1E, 0x3A, 0x5F)
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
LGRAY  = RGBColor(0xF2, 0xF2, 0xF2)
DGRAY  = RGBColor(0x44, 0x44, 0x44)
ACCENT = RGBColor(0x2E, 0x75, 0xB6)   # lighter blue for bullets

# ── Slide dimensions (widescreen 16:9) ────────────────────────────────────────
SLIDE_W = Inches(13.33)
SLIDE_H = Inches(7.5)


def _rgb(color: RGBColor):
    """Return fill XML helper — set solid fill on a shape."""
    return color


def set_bg(slide, color: RGBColor):
    from pptx.oxml.ns import qn
    from lxml import etree
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_textbox(slide, text, left, top, width, height,
                font_size=18, bold=False, color=WHITE,
                align=PP_ALIGN.LEFT, wrap=True):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = "Calibri"
    return txBox


def add_colored_rect(slide, color: RGBColor, left, top, width, height):
    shape = slide.shapes.add_shape(
        1,  # MSO_SHAPE_TYPE.RECTANGLE
        left, top, width, height
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    return shape


# ── Slide builders ─────────────────────────────────────────────────────────────

def build_title_slide(prs, title, date, team):
    layout = prs.slide_layouts[6]  # blank
    slide = prs.slides.add_slide(layout)
    set_bg(slide, NAVY)

    # Subtle decorative bar on left edge
    add_colored_rect(slide, ACCENT, Inches(0), Inches(0), Inches(0.08), SLIDE_H)

    # Title text
    add_textbox(
        slide, title,
        left=Inches(1), top=Inches(1.8),
        width=Inches(11.3), height=Inches(2.2),
        font_size=44, bold=True, color=WHITE, align=PP_ALIGN.CENTER
    )

    # Separator line (thin rect)
    add_colored_rect(slide, ACCENT, Inches(4), Inches(4.3), Inches(5.3), Inches(0.04))

    # Date + team
    subtitle = f"{date}  ·  {team}" if team else date
    add_textbox(
        slide, subtitle,
        left=Inches(1), top=Inches(4.5),
        width=Inches(11.3), height=Inches(0.6),
        font_size=16, bold=False, color=RGBColor(0xCC, 0xD9, 0xEA),
        align=PP_ALIGN.CENTER
    )


def build_agenda_slide(prs, feature_names, sections=None):
    """
    Clean agenda: left navy panel with section labels, right white area with numbered items.
    sections: optional list of dicts {'title': str, 'items': [str]}.
    If not given, feature_names are listed as a flat numbered list.
    """
    layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(layout)
    set_bg(slide, WHITE)

    # Left navy panel
    PANEL_W = Inches(2.8)
    add_colored_rect(slide, NAVY, Inches(0), Inches(0), PANEL_W, SLIDE_H)

    # "Agenda" title on navy panel
    add_textbox(
        slide, "Agenda",
        left=Inches(0.3), top=Inches(0.5),
        width=Inches(3.0), height=Inches(0.9),
        font_size=36, bold=True, color=WHITE
    )
    # Accent underline
    add_colored_rect(slide, ACCENT, Inches(0.3), Inches(1.45), Inches(1.2), Inches(0.06))

    # Subtitle on panel
    add_textbox(
        slide, "Nội dung trình bày hôm nay",
        left=Inches(0.3), top=Inches(1.65),
        width=Inches(3.0), height=Inches(0.7),
        font_size=13, bold=False, color=RGBColor(0xCC, 0xD9, 0xEA)
    )

    # Section list on navy panel (if sections provided)
    if sections:
        sec_colors = [
            RGBColor(0x5B, 0x9B, 0xD5),  # light blue
            RGBColor(0x70, 0xAD, 0x47),  # green
            RGBColor(0xED, 0x7D, 0x31),  # orange
            RGBColor(0xFF, 0xC0, 0x00),  # yellow
        ]
        for si, sec in enumerate(sections):
            top = Inches(2.6) + si * Inches(1.05)
            dot_color = sec_colors[si % len(sec_colors)]
            add_colored_rect(slide, dot_color,
                             Inches(0.3), top + Inches(0.14),
                             Inches(0.18), Inches(0.18))
            add_textbox(
                slide, sec.get("title", ""),
                left=Inches(0.6), top=top,
                width=Inches(2.8), height=Inches(0.45),
                font_size=14, bold=True, color=WHITE
            )
            count = len(sec.get("items", []))
            add_textbox(
                slide, f"{count} mục",
                left=Inches(0.6), top=top + Inches(0.38),
                width=Inches(2.8), height=Inches(0.3),
                font_size=11, bold=False, color=RGBColor(0xAA, 0xBB, 0xCC)
            )

    # Right content area — numbered items
    RIGHT_X = PANEL_W + Inches(0.4)
    RIGHT_W = SLIDE_W - PANEL_W - Inches(0.5)

    sec_colors = [
        RGBColor(0x5B, 0x9B, 0xD5),
        RGBColor(0x70, 0xAD, 0x47),
        RGBColor(0xED, 0x7D, 0x31),
        RGBColor(0xFF, 0xC0, 0x00),
    ]
    if sections:
        # Flatten items — each item may be str or {"text":…,"desc":…}
        all_items = []
        for si, sec in enumerate(sections):
            for item in sec.get("items", []):
                if isinstance(item, dict):
                    text = item.get("text", "")
                    desc = item.get("desc", "")
                else:
                    text = item
                    desc = ""
                all_items.append((text, desc, sec_colors[si % len(sec_colors)]))
    else:
        all_items = [(name, "", ACCENT) for name in feature_names]

    n = len(all_items)
    # Distribute evenly — max 5 per column, 2 columns if needed
    if n <= 5:
        cols = [(all_items, RIGHT_X)]
        col_item_w = RIGHT_W - Inches(0.65)
    else:
        mid = (n + 1) // 2
        col_item_w = RIGHT_W / 2 - Inches(0.8)
        cols = [
            (all_items[:mid], RIGHT_X),
            (all_items[mid:], RIGHT_X + RIGHT_W / 2 + Inches(0.1)),
        ]

    # Fill slide evenly — spread items across available height
    max_col_len = max(len(c) for c, _ in cols)
    MARGIN_TOP = Inches(0.55)
    MARGIN_BOT = Inches(0.4)
    avail_h = SLIDE_H - MARGIN_TOP - MARGIN_BOT
    row_h = avail_h / max_col_len
    start_top = MARGIN_TOP

    BADGE_SIZE = Inches(0.52)
    ITEM_FONT  = 14

    for col_items, col_x in cols:
        for i, (name, desc, dot_color) in enumerate(col_items):
            global_num = next(
                idx + 1 for idx, (t, d, c) in enumerate(all_items)
                if t == name and d == desc and c == dot_color
            )
            top = start_top + i * row_h
            # vertically center badge within row
            badge_top = top + (row_h - BADGE_SIZE) / 2

            # Number badge
            add_colored_rect(slide, dot_color,
                             col_x, badge_top,
                             BADGE_SIZE, BADGE_SIZE)
            add_textbox(
                slide, str(global_num),
                left=col_x, top=badge_top,
                width=BADGE_SIZE, height=BADGE_SIZE,
                font_size=16, bold=True, color=WHITE, align=PP_ALIGN.CENTER
            )

            # Item label + optional description
            item_x = col_x + BADGE_SIZE + Inches(0.18)
            item_w = col_item_w - Inches(0.18)
            if desc:
                label_top = badge_top - Inches(0.06)
                add_textbox(
                    slide, name,
                    left=item_x, top=label_top,
                    width=item_w, height=Inches(0.38),
                    font_size=ITEM_FONT, bold=True, color=RGBColor(0x22, 0x22, 0x22)
                )
                add_textbox(
                    slide, desc,
                    left=item_x, top=label_top + Inches(0.36),
                    width=item_w, height=Inches(0.42),
                    font_size=11, bold=False, color=RGBColor(0x66, 0x66, 0x66)
                )
            else:
                add_textbox(
                    slide, name,
                    left=item_x, top=badge_top - Inches(0.04),
                    width=item_w, height=BADGE_SIZE + Inches(0.08),
                    font_size=ITEM_FONT, bold=False, color=RGBColor(0x22, 0x22, 0x22)
                )

            # Divider at bottom of row (except last)
            if i < len(col_items) - 1:
                add_colored_rect(
                    slide, RGBColor(0xE0, 0xE0, 0xE0),
                    col_x, top + row_h - Inches(0.04),
                    item_w + BADGE_SIZE + Inches(0.15), Inches(0.015)
                )


def build_feature_slide(prs, feature):
    layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(layout)
    set_bg(slide, WHITE)

    name        = feature.get("name", "Feature")
    description = feature.get("description", "")
    bullets     = feature.get("bullets", [])
    image_path  = feature.get("image_path")

    has_image = bool(image_path and os.path.isfile(image_path))

    # Header bar
    add_colored_rect(slide, NAVY, Inches(0), Inches(0), SLIDE_W, Inches(1.1))
    add_textbox(
        slide, name,
        left=Inches(0.4), top=Inches(0.12),
        width=Inches(12.5), height=Inches(0.85),
        font_size=26, bold=True, color=WHITE
    )

    # Layout: text on left 5.0", image on right 7.8"
    text_w = Inches(5.0) if has_image else Inches(12.5)

    # Description
    if description:
        add_textbox(
            slide, description,
            left=Inches(0.4), top=Inches(1.25),
            width=text_w, height=Inches(0.6),
            font_size=13, bold=False, color=RGBColor(0x55, 0x55, 0x55)
        )

    # Bullet points — tighter spacing to leave room
    bullet_top_start = Inches(1.95) if description else Inches(1.4)
    for i, bullet in enumerate(bullets[:5]):
        top = bullet_top_start + i * Inches(0.95)
        add_colored_rect(slide, ACCENT, Inches(0.4), top + Inches(0.22), Inches(0.1), Inches(0.1))
        add_textbox(
            slide, bullet,
            left=Inches(0.65), top=top,
            width=text_w - Inches(0.25), height=Inches(0.85),
            font_size=15, bold=False, color=DGRAY
        )

    # Image — large right panel
    img_left  = Inches(5.3)
    img_top   = Inches(1.2)
    img_w     = Inches(7.7)
    img_h     = Inches(6.0)

    if has_image:
        try:
            _add_picture_fit(slide, image_path, img_left, img_top, img_w, img_h)
        except Exception as e:
            _add_placeholder(slide, img_left, img_top, img_w, img_h, f"[Image load error:\n{e}]")
    elif image_path:
        _add_placeholder(slide, img_left, img_top, img_w, img_h, f"[Screenshot placeholder:\n{image_path}]")


def _add_picture_fit(slide, image_path, left, top, max_w, max_h):
    """Insert image scaled to fit within (max_w × max_h) while keeping aspect ratio, centered."""
    if _PIL_OK:
        with PILImage.open(image_path) as img:
            px_w, px_h = img.size
    else:
        # Fallback: read dimensions from file header without PIL
        # Try basic PNG/JPEG dimension sniff
        import struct
        with open(image_path, "rb") as f:
            header = f.read(24)
        if header[:8] == b'\x89PNG\r\n\x1a\n':
            px_w, px_h = struct.unpack('>II', header[16:24])
        else:
            px_w, px_h = 1440, 900  # safe default for our screenshots

    img_aspect = px_w / px_h        # e.g. 1.6 for 1440×900
    box_aspect = max_w / max_h

    if img_aspect >= box_aspect:
        # wider than box — constrain by width
        actual_w = max_w
        actual_h = Emu(int(max_w / img_aspect))
    else:
        # taller than box — constrain by height
        actual_h = max_h
        actual_w = Emu(int(max_h * img_aspect))

    # Center within allocated box
    offset_x = (max_w - actual_w) / 2
    offset_y = (max_h - actual_h) / 2

    slide.shapes.add_picture(image_path, left + offset_x, top + offset_y, actual_w, actual_h)


def _add_placeholder(slide, left, top, width, height, label="[Screenshot]"):
    rect = add_colored_rect(slide, LGRAY, left, top, width, height)
    add_textbox(
        slide, label,
        left=left + Inches(0.1), top=top + height / 2 - Inches(0.4),
        width=width - Inches(0.2), height=Inches(0.8),
        font_size=12, bold=False, color=RGBColor(0x99, 0x99, 0x99),
        align=PP_ALIGN.CENTER
    )


def build_qa_slide(prs, next_steps):
    layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(layout)
    set_bg(slide, NAVY)

    add_colored_rect(slide, ACCENT, Inches(0), Inches(0), Inches(0.08), SLIDE_H)

    add_textbox(
        slide, "Q&A",
        left=Inches(1), top=Inches(1.0),
        width=Inches(11.3), height=Inches(1.4),
        font_size=52, bold=True, color=WHITE, align=PP_ALIGN.CENTER
    )

    if next_steps:
        add_textbox(
            slide, "Next Steps",
            left=Inches(1.5), top=Inches(2.8),
            width=Inches(10), height=Inches(0.6),
            font_size=20, bold=True, color=ACCENT
        )
        for i, step in enumerate(next_steps):
            top = Inches(3.5) + i * Inches(0.65)
            add_colored_rect(slide, ACCENT, Inches(1.5), top + Inches(0.18), Inches(0.12), Inches(0.12))
            add_textbox(
                slide, step,
                left=Inches(1.8), top=top,
                width=Inches(9.5), height=Inches(0.6),
                font_size=16, bold=False, color=RGBColor(0xCC, 0xD9, 0xEA)
            )


# ── Main ───────────────────────────────────────────────────────────────────────

def build_presentation(data: dict, output_path: str):
    prs = Presentation()
    prs.slide_width  = SLIDE_W
    prs.slide_height = SLIDE_H

    title      = data.get("title", "Demo Presentation")
    date       = data.get("date", "")
    team       = data.get("team", "")
    features   = data.get("features", [])
    next_steps = data.get("next_steps", [])

    sections   = data.get("agenda_sections")

    build_title_slide(prs, title, date, team)
    if features:
        feature_names = [f.get("name", f"Feature {i+1}") for i, f in enumerate(features)]
        build_agenda_slide(prs, feature_names, sections=sections)
    for feature in features:
        build_feature_slide(prs, feature)
    build_qa_slide(prs, next_steps)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out))
    return str(out), len(prs.slides)


def main():
    parser = argparse.ArgumentParser(description="Generate demo .pptx from JSON spec")
    parser.add_argument("--input",  required=True, help="Path to JSON input file")
    parser.add_argument("--output", default=r"C:\tmp\demo_slides.pptx",
                        help="Output .pptx path (default: C:\\tmp\\demo_slides.pptx)")
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)

    output_path, slide_count = build_presentation(data, args.output)
    print(f"OK Saved {slide_count} slides -> {output_path}")


if __name__ == "__main__":
    main()
