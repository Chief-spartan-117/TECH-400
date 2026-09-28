"""
make_screenshots.py
--------------------
Renders sections of the real scoring.py output as terminal-style PNG images,
used as the screenshots embedded in the report.
"""

from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/System/Library/Fonts/SFNSMono.ttf"
FONT_SIZE = 15
PAD = 18
LINE_SPACING = 5
BG = (30, 30, 34)
BAR = (52, 52, 58)
FG = (223, 225, 227)
TITLE_FG = (140, 220, 140)
DOT_COLORS = [(255, 95, 86), (255, 189, 46), (39, 201, 63)]


def render_terminal_shot(lines, out_path, title="claude@bm25-lm-scoring: python3 scoring.py"):
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

    draw.rectangle([0, 0, width, bar_h], fill=BAR)
    for i, color in enumerate(DOT_COLORS):
        draw.ellipse([16 + i * 22, bar_h // 2 - 6, 16 + i * 22 + 12, bar_h // 2 + 6], fill=color)
    draw.text((width / 2, bar_h / 2), title, font=title_font, fill=(200, 200, 205), anchor="mm")

    y = bar_h + PAD
    for line in lines:
        color = TITLE_FG if line.startswith("=") or (line.isupper() and line.strip()) else FG
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

    stats = read_section(all_lines, "CORPUS STATS", 'QUERY: "machine learning')
    render_terminal_shot(stats, "screenshots/01_corpus_stats.png")

    q1 = read_section(all_lines, 'QUERY: "machine learning', 'QUERY: "space exploration')
    render_terminal_shot(q1, "screenshots/02_query_ml.png")

    q2 = read_section(all_lines, 'QUERY: "space exploration', 'QUERY: "football basketball')
    render_terminal_shot(q2, "screenshots/03_query_space.png")

    q3 = read_section(all_lines, 'QUERY: "football basketball')
    render_terminal_shot(q3, "screenshots/04_query_sports.png")
