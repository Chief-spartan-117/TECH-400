"""
make_screenshots.py
--------------------
Renders sections of the real demo.py output as terminal-style PNG images,
used as the "snapshots" embedded in the report.
"""

from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_SIZE = 15
PAD = 18
LINE_SPACING = 5
BG = (30, 30, 34)
BAR = (52, 52, 58)
FG = (223, 225, 227)
TITLE_FG = (140, 220, 140)
DOT_COLORS = [(255, 95, 86), (255, 189, 46), (39, 201, 63)]


def render_terminal_shot(lines, out_path, title="claude@ir-system: python3 demo.py"):
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    title_font = ImageFont.truetype(FONT_PATH, 13)

    dummy = Image.new("RGB", (10, 10))
    d = ImageDraw.Draw(dummy)
    line_height = FONT_SIZE + LINE_SPACING
    max_width = 0
    for line in lines:
        bbox = d.textbbox((0, 0), line, font=font)
        max_width = max(max_width, bbox[2] - bbox[0])

    bar_h = 34
    width = max_width + PAD * 2
    height = bar_h + PAD * 2 + line_height * len(lines)

    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)

    # title bar
    draw.rectangle([0, 0, width, bar_h], fill=BAR)
    for i, color in enumerate(DOT_COLORS):
        draw.ellipse([16 + i * 22, bar_h // 2 - 6, 16 + i * 22 + 12, bar_h // 2 + 6], fill=color)
    draw.text((width / 2, bar_h / 2), title, font=title_font, fill=(200, 200, 205), anchor="mm")

    y = bar_h + PAD
    for line in lines:
        color = TITLE_FG if line.startswith("=") or line.isupper() and line.strip() else FG
        draw.text((PAD, y), line, font=font, fill=color)
        y += line_height

    img.save(out_path)
    print(f"wrote {out_path} ({width}x{height})")


def read_section(all_lines, start_marker, end_marker=None):
    lines = all_lines
    start = next(i for i, l in enumerate(lines) if start_marker in l)
    if end_marker:
        end = next(i for i, l in enumerate(lines) if end_marker in l and i > start)
    else:
        end = len(lines)
    return [l.rstrip("\n") for l in lines[start:end]]


if __name__ == "__main__":
    with open("demo_output.txt") as f:
        all_lines = f.readlines()

    collection = read_section(all_lines, "DOCUMENT COLLECTION", "DICTIONARY")
    render_terminal_shot(collection, "screenshots/01_document_collection.png")

    index_section = read_section(all_lines, "INVERTED INDEX", "BOOLEAN QUERIES")
    # trim to a readable excerpt for the screenshot (full index is long)
    index_excerpt = index_section[:3] + index_section[3:28]
    render_terminal_shot(index_excerpt, "screenshots/02_inverted_index.png")

    queries = read_section(all_lines, "BOOLEAN QUERIES")
    render_terminal_shot(queries, "screenshots/03_boolean_queries.png")
