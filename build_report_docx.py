"""Builds REPORT.docx from the content in REPORT.md, with screenshots embedded."""

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

from vsm import build_similarity_matrix

names, vocab, tfidf_vectors, sim_matrix = build_similarity_matrix("docs")
short = [f"d{i+1}" for i in range(len(names))]

doc = Document()

title = doc.add_heading("Document Similarity via Vector Space Model", level=0)

doc.add_heading("1. Objective", level=1)
doc.add_paragraph(
    "Compute pairwise similarity scores between a set of documents using a "
    "Vector Space Model (VSM) with TF-IDF term weighting and cosine similarity."
)

doc.add_heading("2. Document Collection", level=1)
doc.add_paragraph(
    "8 documents were gathered from Wikipedia (public, freely accessible content, "
    "CC BY-SA) and saved as plain .txt files in docs/. Topics were chosen in four "
    "related pairs so the similarity results are easy to sanity check: two AI/ML "
    "topics, one AI-adjacent topic, two space topics, two sports topics, and one "
    "climate topic."
)

table_data = [
    ("d1", "Artificial Intelligence", "https://en.wikipedia.org/wiki/Artificial_intelligence"),
    ("d2", "Machine Learning", "https://en.wikipedia.org/wiki/Machine_learning"),
    ("d3", "Large Language Model", "https://en.wikipedia.org/wiki/Large_language_model"),
    ("d4", "NASA", "https://en.wikipedia.org/wiki/NASA"),
    ("d5", "Mars", "https://en.wikipedia.org/wiki/Mars"),
    ("d6", "Association Football", "https://en.wikipedia.org/wiki/Association_football"),
    ("d7", "Basketball", "https://en.wikipedia.org/wiki/Basketball"),
    ("d8", "Climate Change", "https://en.wikipedia.org/wiki/Climate_change"),
]
t = doc.add_table(rows=1, cols=3)
t.style = "Light Grid Accent 1"
hdr = t.rows[0].cells
hdr[0].text, hdr[1].text, hdr[2].text = "ID", "Topic", "Source"
for id_, topic, src in table_data:
    row = t.add_row().cells
    row[0].text, row[1].text, row[2].text = id_, topic, src

doc.add_paragraph()
doc.add_paragraph("Snapshot — document collection loaded:")
doc.add_picture("screenshots/01_document_collection.png", width=Inches(5.5))

doc.add_heading("3. Method: Vector Space Model", level=1)
doc.add_paragraph(
    "Implemented from scratch in vsm.py (numpy used only for vector arithmetic, "
    "not for the algorithm itself):"
)
steps = [
    "Tokenize & normalize — lowercase, strip to alphabetic tokens with a regex "
    "([a-z]+), drop a small stopword list, drop tokens ≤ 2 chars.",
    "Build vocabulary — union of all terms across all documents (601 unique "
    "terms across the 8-document collection).",
    "Term Frequency (TF) — tf(t, d) = count(t in d) / len(d), raw count "
    "normalized by document length.",
    "Inverse Document Frequency (IDF) — idf(t) = log(N / df(t)), where N is "
    "the number of documents and df(t) is the number of documents containing "
    "term t. Down-weights terms common across documents, up-weights distinctive terms.",
    "TF-IDF vector — tfidf(t, d) = tf(t, d) * idf(t), one scalar per "
    "vocabulary term, giving each document an N-dimensional vector.",
    "Cosine similarity — similarity(A, B) = (A · B) / (‖A‖ * ‖B‖). Scale-"
    "invariant, bounded in [0, 1] since TF-IDF weights are non-negative.",
]
for s in steps:
    doc.add_paragraph(s, style="List Number")

doc.add_paragraph("Core code:")
code = '''def compute_tf(tokens, vocab):
    counts = Counter(tokens)
    total = len(tokens) or 1
    return np.array([counts.get(term, 0) / total for term in vocab])

def compute_idf(tokenized_docs, vocab):
    n_docs = len(tokenized_docs)
    df = np.zeros(len(vocab))
    for i, term in enumerate(vocab):
        df[i] = sum(1 for tokens in tokenized_docs.values() if term in tokens)
    return np.log(n_docs / (df + 1e-9)) + 1e-9

def cosine_similarity(v1, v2):
    dot = np.dot(v1, v2)
    norm = np.linalg.norm(v1) * np.linalg.norm(v2)
    return float(dot / norm) if norm > 0 else 0.0'''
p = doc.add_paragraph()
run = p.add_run(code)
run.font.name = "Courier New"
run.font.size = Pt(9)

doc.add_paragraph("Full implementation: vsm.py (see GitHub repository).")

doc.add_heading("4. Results", level=1)
doc.add_paragraph("Snapshot — cosine similarity matrix (terminal output):")
doc.add_picture("screenshots/02_similarity_matrix.png", width=Inches(5.5))

doc.add_paragraph("Full similarity matrix:")
mt = doc.add_table(rows=1, cols=len(short) + 1)
mt.style = "Light Grid Accent 1"
mt.rows[0].cells[0].text = ""
for j, s in enumerate(short):
    mt.rows[0].cells[j + 1].text = s
for i, row_vals in enumerate(sim_matrix):
    row = mt.add_row().cells
    row[0].text = short[i]
    for j, v in enumerate(row_vals):
        row[j + 1].text = f"{v:.3f}"

doc.add_paragraph()
doc.add_paragraph("Snapshot — heatmap:")
doc.add_picture("screenshots/04_similarity_heatmap.png", width=Inches(5.5))

doc.add_paragraph()
doc.add_paragraph("Snapshot — top/bottom similar pairs:")
doc.add_picture("screenshots/03_similar_pairs.png", width=Inches(5.5))

doc.add_heading("Top 3 most similar pairs", level=2)
top_table = doc.add_table(rows=1, cols=2)
top_table.style = "Light Grid Accent 1"
top_table.rows[0].cells[0].text = "Score"
top_table.rows[0].cells[1].text = "Pair"
for score, a, b in [
    (0.207, "Artificial Intelligence", "Machine Learning"),
    (0.127, "Association Football", "Basketball"),
    (0.067, "Artificial Intelligence", "Large Language Model"),
]:
    row = top_table.add_row().cells
    row[0].text = f"{score:.3f}"
    row[1].text = f"{a} ↔ {b}"

doc.add_heading("Bottom 3 least similar pairs", level=2)
bot_table = doc.add_table(rows=1, cols=2)
bot_table.style = "Light Grid Accent 1"
bot_table.rows[0].cells[0].text = "Score"
bot_table.rows[0].cells[1].text = "Pair"
for score, a, b in [
    (0.002, "Machine Learning", "Basketball"),
    (0.002, "Association Football", "Climate Change"),
    (0.000, "Mars", "Basketball"),
]:
    row = bot_table.add_row().cells
    row[0].text = f"{score:.3f}"
    row[1].text = f"{a} ↔ {b}"

doc.add_heading("5. Discussion", level=1)
discussion = [
    "AI ↔ Machine Learning (0.207) is the highest score — expected, since ML "
    "is a subfield of AI and the two articles share heavy vocabulary overlap "
    "(learning, model, neural, data).",
    "Football ↔ Basketball (0.127) is the second-highest — both are team "
    "sports articles sharing terms like team, player, game, league.",
    "Cross-cluster pairs (e.g. sports vs. climate, space vs. sports) all "
    "score near 0, correctly showing the model finds no meaningful topical "
    "overlap between unrelated documents.",
    "Large Language Model correlates with AI (0.067) more than with ML "
    "(0.059), consistent with LLMs being described in AI-article terms as "
    "well as ML terms.",
]
for d in discussion:
    doc.add_paragraph(d, style="List Bullet")
doc.add_paragraph(
    "TF-IDF weighting is what makes this work: without IDF down-weighting, "
    "common English scaffolding words would dominate every vector and "
    "flatten all similarity scores toward 1.0. IDF suppresses ubiquitous "
    "terms and lets the distinctive vocabulary of each topic drive the "
    "cosine score."
)

doc.add_heading("6. How to Reproduce", level=1)
repro = '''pip install -r requirements.txt
python3 vsm.py                 # prints similarity matrix + top/bottom pairs
python3 make_heatmap.py        # writes screenshots/04_similarity_heatmap.png
python3 make_screenshots.py    # re-renders terminal-style snapshot PNGs'''
p = doc.add_paragraph()
run = p.add_run(repro)
run.font.name = "Courier New"
run.font.size = Pt(9)

doc.add_heading("7. GitHub Repository", level=1)
doc.add_paragraph(
    "Full source code, documents, and this report are published at: "
    "[GitHub link — see submission]"
)

doc.save("REPORT.docx")
print("wrote REPORT.docx")
