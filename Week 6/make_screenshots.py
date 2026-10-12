"""Generate report figures from the current source code and executable output."""

from __future__ import annotations

import json
import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


BASE = Path(__file__).resolve().parent
OUT = BASE / "screenshots"
OUT.mkdir(exist_ok=True)


def font(size: int, bold: bool = False):
    choices = [
        "/System/Library/Fonts/SFNSMono.ttf",
        "/System/Library/Fonts/Menlo.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ]
    if bold:
        choices.insert(0, "/System/Library/Fonts/SFNSMonoBold.ttf")
    for path in choices:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


MONO = font(23)
MONO_SMALL = font(20)
SANS = font(25)
SANS_BOLD = font(27, bold=True)


def terminal_image(command: str, output: str, filename: str, width: int = 1500) -> None:
    lines = [f"$ {command}"] + output.rstrip().splitlines()
    height = 90 + len(lines) * 31
    image = Image.new("RGB", (width, height), "#10151c")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width, 54), fill="#27313d")
    for x, color in ((25, "#ff5f56"), (58, "#ffbd2e"), (91, "#27c93f")):
        draw.ellipse((x, 17, x + 20, 37), fill=color)
    y = 70
    for i, line in enumerate(lines):
        color = "#8be9fd" if i == 0 else "#f1f5f9"
        draw.text((28, y), line[:115], font=MONO_SMALL, fill=color)
        y += 31
    image.save(OUT / filename)


def code_image() -> None:
    source = (BASE / "ir_system.py").read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(source) if line.startswith("def preprocess"))
    end = next(i for i, line in enumerate(source[start + 1:], start + 1) if line.startswith("def parse_cisi_records"))
    snippet = source[start:end]
    numbered = [f"{start + i + 1:>3}  {line}" for i, line in enumerate(snippet)]
    width, height = 1600, 100 + len(numbered) * 32
    image = Image.new("RGB", (width, height), "#0b1020")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width, 58), fill="#1e293b")
    draw.text((26, 15), "ir_system.py — preprocessing pipeline", font=MONO_SMALL, fill="#e2e8f0")
    y = 75
    keywords = ("def ", "return ", "normalized =", "tokens =")
    for line in numbered:
        color = "#93c5fd" if any(word in line for word in keywords) else "#e5e7eb"
        draw.text((24, y), line, font=MONO, fill=color)
        y += 32
    image.save(OUT / "code_preprocessing.png")


def architecture_image() -> None:
    width, height = 1700, 720
    image = Image.new("RGB", (width, height), "#f8fafc")
    draw = ImageDraw.Draw(image)
    draw.text((55, 35), "TF–IDF Information Retrieval Architecture", font=SANS_BOLD, fill="#0f172a")

    boxes = [
        ("CISI documents", "title + author + abstract", "#dbeafe"),
        ("Preprocessing", "normalize • tokenize • filter • stem", "#dcfce7"),
        ("Inverted index", "term → document frequency / tf", "#fef3c7"),
        ("TF–IDF vectors", "log tf • smooth idf • L2 norm", "#fce7f3"),
    ]
    x_positions = [55, 455, 855, 1255]
    for x, (title, subtitle, color) in zip(x_positions, boxes):
        draw.rounded_rectangle((x, 145, x + 345, 275), radius=18, fill=color, outline="#334155", width=3)
        draw.text((x + 22, 172), title, font=SANS_BOLD, fill="#0f172a")
        for i, line in enumerate(textwrap.wrap(subtitle, 26)):
            draw.text((x + 22, 215 + 25 * i), line, font=MONO_SMALL, fill="#334155")
    for x in (410, 810, 1210):
        draw.line((x, 210, x + 34, 210), fill="#2563eb", width=6)
        draw.polygon([(x + 34, 198), (x + 52, 210), (x + 34, 222)], fill="#2563eb")

    draw.rounded_rectangle((250, 440, 605, 575), radius=18, fill="#e0e7ff", outline="#334155", width=3)
    draw.text((275, 468), "User query", font=SANS_BOLD, fill="#0f172a")
    draw.text((275, 518), "same preprocessing", font=MONO_SMALL, fill="#334155")
    draw.rounded_rectangle((735, 440, 1090, 575), radius=18, fill="#cffafe", outline="#334155", width=3)
    draw.text((760, 468), "Cosine scoring", font=SANS_BOLD, fill="#0f172a")
    draw.text((760, 518), "accumulate postings", font=MONO_SMALL, fill="#334155")
    draw.rounded_rectangle((1220, 440, 1575, 575), radius=18, fill="#ffedd5", outline="#334155", width=3)
    draw.text((1245, 468), "Ranked top-k", font=SANS_BOLD, fill="#0f172a")
    draw.text((1245, 518), "ID • score • title", font=MONO_SMALL, fill="#334155")
    for x in (620, 1105):
        draw.line((x, 507, x + 95, 507), fill="#2563eb", width=6)
        draw.polygon([(x + 95, 495), (x + 113, 507), (x + 95, 519)], fill="#2563eb")
    draw.line((1428, 290, 1428, 405), fill="#64748b", width=4)
    draw.line((1428, 405, 913, 405), fill="#64748b", width=4)
    draw.line((913, 405, 913, 430), fill="#64748b", width=4)
    image.save(OUT / "architecture.png")


def result_chart(metrics_path: Path) -> None:
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))["mean"]
    labels = ["P@5", "R@5", "MAP", "MRR", "nDCG@5"]
    values = [metrics[name] for name in ("precision", "recall", "ap", "rr", "ndcg")]
    width, height = 1300, 720
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text((55, 30), "Offline demonstration: mean effectiveness", font=SANS_BOLD, fill="#0f172a")
    draw.text((55, 75), "Eight manually judged queries over 18 records — not a full CISI benchmark", font=MONO_SMALL, fill="#475569")
    left, top, bottom = 110, 145, 610
    draw.line((left, top, left, bottom), fill="#334155", width=3)
    draw.line((left, bottom, 1240, bottom), fill="#334155", width=3)
    for tick in range(6):
        value = tick / 5
        y = bottom - int(value * (bottom - top))
        draw.line((left - 8, y, 1240, y), fill="#e2e8f0", width=2)
        draw.text((45, y - 12), f"{value:.1f}", font=MONO_SMALL, fill="#64748b")
    colors = ["#2563eb", "#16a34a", "#7c3aed", "#ea580c", "#0891b2"]
    for i, (label, value, color) in enumerate(zip(labels, values, colors)):
        x = 180 + i * 210
        y = bottom - int(value * (bottom - top))
        draw.rounded_rectangle((x, y, x + 115, bottom), radius=9, fill=color)
        draw.text((x + 18, y - 38), f"{value:.3f}", font=MONO_SMALL, fill="#0f172a")
        draw.text((x + 17, bottom + 18), label, font=SANS, fill="#0f172a")
    image.save(OUT / "metrics_chart.png")


def run(command: list[str]) -> str:
    completed = subprocess.run(command, cwd=BASE, check=True, capture_output=True, text=True)
    return completed.stdout + completed.stderr


def main() -> None:
    demo = run(["python3", "demo.py"])
    evaluation = run(["python3", "evaluate.py", "--sample", "--top-k", "5", "--json", str(OUT / "metrics.json")])
    tests = run(["python3", "-m", "unittest", "discover", "-s", "tests", "-v"])
    terminal_image("python3 demo.py", demo, "demo_results.png")
    terminal_image("python3 evaluate.py --sample --top-k 5", evaluation, "evaluation.png")
    terminal_image("python3 -m unittest discover -s tests -v", tests, "tests.png")
    code_image()
    architecture_image()
    result_chart(OUT / "metrics.json")
    print(f"Generated report figures in {OUT}")


if __name__ == "__main__":
    main()

