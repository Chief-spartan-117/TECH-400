"""Generate report figures from the current implementation and live output."""

from __future__ import annotations

import json
import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from evaluate_models import evaluate_models, load_sample


BASE = Path(__file__).resolve().parent
OUT = BASE / "screenshots"
OUT.mkdir(exist_ok=True)


def get_font(size: int, bold: bool = False):
    candidates = [
        "/System/Library/Fonts/SFNSMonoBold.ttf" if bold else "/System/Library/Fonts/SFNSMono.ttf",
        "/System/Library/Fonts/Menlo.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


MONO = get_font(21)
MONO_SMALL = get_font(18)
SANS = get_font(24)
BOLD = get_font(26, True)


def run(command: list[str]) -> str:
    completed = subprocess.run(command, cwd=BASE, capture_output=True, text=True, check=True)
    return completed.stdout + completed.stderr


def terminal_image(command: str, output: str, filename: str, width: int = 1550) -> None:
    lines = [f"$ {command}"] + output.rstrip().splitlines()
    image = Image.new("RGB", (width, 88 + 30 * len(lines)), "#0d131a")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width, 52), fill="#27313d")
    for x, color in ((24, "#ff5f56"), (56, "#ffbd2e"), (88, "#27c93f")):
        draw.ellipse((x, 16, x + 19, 35), fill=color)
    y = 67
    for position, line in enumerate(lines):
        draw.text((26, y), line[:120], font=MONO_SMALL, fill="#8be9fd" if position == 0 else "#f1f5f9")
        y += 30
    image.save(OUT / filename)


def source_snapshot(function_name: str, next_name: str, filename: str, title: str) -> None:
    lines = (BASE / "evaluate_models.py").read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(f"def {function_name}"))
    end = next(i for i, line in enumerate(lines[start + 1:], start + 1) if line.startswith(f"def {next_name}"))
    snippet = lines[start:end]
    numbered = [f"{start + offset + 1:>3}  {line}" for offset, line in enumerate(snippet)]
    image = Image.new("RGB", (1700, 95 + 29 * len(numbered)), "#0b1020")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1700, 54), fill="#1e293b")
    draw.text((25, 14), title, font=MONO_SMALL, fill="#e2e8f0")
    y = 69
    for line in numbered:
        color = "#93c5fd" if any(token in line for token in ("def ", "return ", "if ", "for ")) else "#e5e7eb"
        draw.text((22, y), line[:135], font=MONO_SMALL, fill=color)
        y += 29
    image.save(OUT / filename)


def bm25_snapshot() -> None:
    lines = (BASE / "retrieval_models.py").read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("class BM25Model"))
    end = next(i for i, line in enumerate(lines[start + 1:], start + 1) if line.startswith("def create_models"))
    snippet = lines[start:end]
    numbered = [f"{start + offset + 1:>3}  {line}" for offset, line in enumerate(snippet)]
    image = Image.new("RGB", (1750, 100 + 28 * len(numbered)), "#0b1020")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1750, 54), fill="#1e293b")
    draw.text((25, 14), "retrieval_models.py — commented BM25 implementation", font=MONO_SMALL, fill="#e2e8f0")
    y = 69
    for line in numbered:
        color = "#a7f3d0" if any(token in line for token in ("class ", "def ", "idf =", "term_score")) else "#e5e7eb"
        draw.text((22, y), line[:140], font=MONO_SMALL, fill=color)
        y += 28
    image.save(OUT / "code_bm25.png")


def architecture() -> None:
    image = Image.new("RGB", (1700, 710), "#f8fafc")
    draw = ImageDraw.Draw(image)
    draw.text((55, 35), "Controlled Model-Evaluation Pipeline", font=BOLD, fill="#0f172a")
    stages = [
        ("CISI corpus", "documents • queries • judgments", "#dbeafe"),
        ("Shared processing", "normalize • filter • stem", "#dcfce7"),
        ("Same test queries", "no model-specific changes", "#fef3c7"),
    ]
    for x, (title, subtitle, color) in zip((70, 600, 1130), stages):
        draw.rounded_rectangle((x, 135, x + 440, 265), radius=18, fill=color, outline="#334155", width=3)
        draw.text((x + 24, 165), title, font=BOLD, fill="#0f172a")
        draw.text((x + 24, 215), subtitle, font=MONO_SMALL, fill="#334155")
    for x in (525, 1055):
        draw.line((x, 200, x + 55, 200), fill="#2563eb", width=6)
        draw.polygon([(x + 55, 188), (x + 73, 200), (x + 55, 212)], fill="#2563eb")
    models = [("Binary overlap", "#e0e7ff"), ("TF–IDF cosine", "#fce7f3"), ("BM25", "#cffafe")]
    for x, (name, color) in zip((120, 655, 1190), models):
        draw.rounded_rectangle((x, 395, x + 385, 505), radius=18, fill=color, outline="#334155", width=3)
        draw.text((x + 26, 430), name, font=BOLD, fill="#0f172a")
    draw.line((1350, 280, 1350, 340), fill="#64748b", width=4)
    draw.line((310, 340, 1385, 340), fill="#64748b", width=4)
    for x in (310, 845, 1385):
        draw.line((x, 340, x, 380), fill="#64748b", width=4)
    draw.rounded_rectangle((450, 585, 1250, 675), radius=18, fill="#ffedd5", outline="#334155", width=3)
    draw.text((495, 615), "P@k • R@k • MAP • MRR • nDCG@k • latency", font=BOLD, fill="#0f172a")
    for x in (310, 845, 1385):
        draw.line((x, 520, x, 550), fill="#64748b", width=3)
        draw.line((x, 550, 850, 550), fill="#64748b", width=3)
    draw.line((850, 550, 850, 575), fill="#64748b", width=3)
    image.save(OUT / "evaluation_architecture.png")


def comparison_chart(payload: dict) -> None:
    models = list(payload["models"])
    metrics = [("precision", "P@5"), ("recall", "R@5"), ("ap", "MAP"), ("rr", "MRR"), ("ndcg", "nDCG@5")]
    colors = ["#2563eb", "#db2777", "#0891b2"]
    image = Image.new("RGB", (1550, 800), "white")
    draw = ImageDraw.Draw(image)
    draw.text((55, 30), "Aggregate Retrieval Effectiveness by Model", font=BOLD, fill="#0f172a")
    draw.text((55, 72), "Eight-query offline demonstration; higher is better", font=MONO_SMALL, fill="#475569")
    left, top, bottom = 110, 150, 660
    draw.line((left, top, left, bottom), fill="#334155", width=3)
    draw.line((left, bottom, 1490, bottom), fill="#334155", width=3)
    for tick in range(6):
        value = tick / 5
        y = bottom - int(value * (bottom - top))
        draw.line((left - 8, y, 1490, y), fill="#e2e8f0", width=2)
        draw.text((45, y - 10), f"{value:.1f}", font=MONO_SMALL, fill="#64748b")
    group_width = 250
    for metric_index, (key, label) in enumerate(metrics):
        center = 200 + metric_index * group_width
        for model_index, model in enumerate(models):
            value = payload["models"][model]["mean"][key]
            x = center + model_index * 48
            y = bottom - int(value * (bottom - top))
            draw.rectangle((x, y, x + 38, bottom), fill=colors[model_index])
        draw.text((center, bottom + 20), label, font=MONO_SMALL, fill="#0f172a")
    for index, (model, color) in enumerate(zip(models, colors)):
        x = 170 + index * 430
        draw.rectangle((x, 730, x + 30, 755), fill=color)
        draw.text((x + 42, 729), model, font=MONO_SMALL, fill="#0f172a")
    image.save(OUT / "model_comparison.png")


def cutoff_chart(cutoffs: dict) -> None:
    models = list(next(iter(cutoffs.values()))["models"])
    colors = ["#2563eb", "#db2777", "#0891b2"]
    image = Image.new("RGB", (1450, 760), "white")
    draw = ImageDraw.Draw(image)
    draw.text((55, 30), "Recall as the Result Cut-off Increases", font=BOLD, fill="#0f172a")
    draw.text((55, 72), "Mean Recall@k for k = 1, 3, 5, 10", font=MONO_SMALL, fill="#475569")
    left, top, right, bottom = 120, 145, 1360, 625
    draw.line((left, top, left, bottom), fill="#334155", width=3)
    draw.line((left, bottom, right, bottom), fill="#334155", width=3)
    for tick in range(6):
        value = tick / 5
        y = bottom - int(value * (bottom - top))
        draw.line((left, y, right, y), fill="#e2e8f0", width=2)
        draw.text((48, y - 10), f"{value:.1f}", font=MONO_SMALL, fill="#64748b")
    ks = [1, 3, 5, 10]
    xs = [200, 550, 900, 1250]
    for x, k in zip(xs, ks):
        draw.text((x - 8, bottom + 22), str(k), font=MONO, fill="#0f172a")
    draw.text((700, bottom + 60), "cut-off k", font=MONO_SMALL, fill="#475569")
    for model_index, model in enumerate(models):
        points = []
        for x, k in zip(xs, ks):
            value = cutoffs[str(k)]["models"][model]["mean"]["recall"]
            points.append((x, bottom - int(value * (bottom - top))))
        draw.line(points, fill=colors[model_index], width=6)
        for x, y in points:
            draw.ellipse((x - 9, y - 9, x + 9, y + 9), fill=colors[model_index])
    for index, (model, color) in enumerate(zip(models, colors)):
        x = 190 + index * 390
        draw.line((x, 710, x + 48, 710), fill=color, width=6)
        draw.text((x + 60, 700), model, font=MONO_SMALL, fill="#0f172a")
    image.save(OUT / "recall_cutoffs.png")


def per_query_ap(payload: dict) -> None:
    models = list(payload["models"])
    queries = [row["query_id"] for row in payload["models"][models[0]]["rows"]]
    image = Image.new("RGB", (1350, 650), "white")
    draw = ImageDraw.Draw(image)
    draw.text((55, 30), "Average Precision by Query", font=BOLD, fill="#0f172a")
    draw.text((55, 72), "Darker cells indicate higher AP", font=MONO_SMALL, fill="#475569")
    left, top = 310, 135
    cell_w, cell_h = 115, 105
    for column, query in enumerate(queries):
        draw.text((left + column * cell_w + 37, 102), query, font=MONO_SMALL, fill="#0f172a")
    for row_index, model in enumerate(models):
        draw.text((40, top + row_index * cell_h + 35), model, font=MONO_SMALL, fill="#0f172a")
        for column, row in enumerate(payload["models"][model]["rows"]):
            value = row["ap"]
            shade = int(245 - 130 * value)
            color = (shade, min(250, shade + 45), 245)
            x = left + column * cell_w
            y = top + row_index * cell_h
            draw.rectangle((x, y, x + cell_w - 5, y + cell_h - 5), fill=color, outline="#cbd5e1", width=2)
            draw.text((x + 22, y + 36), f"{value:.3f}", font=MONO_SMALL, fill="#0f172a")
    image.save(OUT / "per_query_ap.png")


def main() -> None:
    metrics_file = OUT / "metrics.json"
    output = run(["python3", "evaluate_models.py", "--sample", "--top-k", "5", "--timing-runs", "500", "--json", str(metrics_file)])
    terminal_image("python3 evaluate_models.py --sample --top-k 5", output, "evaluation_output.png")
    terminal_image("python3 demo.py", run(["python3", "demo.py"]), "ranking_output.png")
    terminal_image("python3 -m unittest discover -s tests -v", run(["python3", "-m", "unittest", "discover", "-s", "tests", "-v"]), "tests_output.png")
    source_snapshot("calculate_metrics", "evaluate_models", "code_metrics.png", "evaluate_models.py — metric calculation")
    bm25_snapshot()
    architecture()

    payload = json.loads(metrics_file.read_text(encoding="utf-8"))
    comparison_chart(payload)
    per_query_ap(payload)

    documents, queries, judgments = load_sample(BASE)
    cutoff_payload = {}
    for k in (1, 3, 5, 10):
        results, corpus = evaluate_models(documents, queries, judgments, k=k, timing_runs=1)
        cutoff_payload[str(k)] = {"models": results, "vocabulary": corpus.vocabulary_size}
    (OUT / "cutoffs.json").write_text(json.dumps(cutoff_payload, indent=2), encoding="utf-8")
    cutoff_chart(cutoff_payload)
    print(f"Generated Week 7 report figures in {OUT}")


if __name__ == "__main__":
    main()

