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
    "This assignment looks at how well a classic information retrieval "
    "technique -- the Vector Space Model (VSM) -- picks up on topical "
    "relationships between documents based purely on word usage, with no "
    "machine learning training involved. The approach combines TF-IDF "
    "term weighting with cosine similarity, computed between every pair "
    "of documents in a small collection."
)

doc.add_heading("2. Document Collection", level=1)
doc.add_paragraph(
    "The task called for 5-10 real, publicly available documents, so 8 "
    "articles were pulled from Wikipedia (public content, CC BY-SA "
    "licensed) and saved as plain .txt files in docs/. Rather than picking "
    "random topics, they were deliberately grouped into related pairs -- "
    "two AI/ML articles, one AI-adjacent article, two about space, two "
    "about team sports, and one on climate. The reasoning: if the model "
    "works, related topics should score noticeably higher than unrelated "
    "ones, which makes the results easy to sanity-check."
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
doc.add_paragraph(
    "To keep the text clean (no HTML, no nav bars, no infobox clutter), "
    "each article was pulled through Wikipedia's REST API using "
    "action=query&prop=extracts&explaintext=1 instead of scraping the "
    "rendered page. Each file ended up around 1.2 KB, with a short Title: / "
    "Source: header on top so the origin stays traceable."
)
doc.add_paragraph("Snapshot — document collection loaded:")
doc.add_picture("screenshots/01_document_collection.png", width=Inches(5.5))

doc.add_heading("3. Method: Vector Space Model", level=1)
doc.add_paragraph(
    "The pipeline was built from scratch in vsm.py -- no scikit-learn, no "
    "pre-built TF-IDF vectorizer. numpy is used only for the actual vector "
    "math (dot products, norms), not for any part of the algorithm itself. "
    "Here's roughly how it works, in the order the code runs it:"
)
steps = [
    "Tokenize & normalize. Lowercase everything, pull out alphabetic tokens "
    "with a simple regex ([a-z]+), strip a small stopword list, and drop "
    "anything 2 characters or shorter. No stemming or lemmatization -- just "
    "enough cleanup to stop noise words from swamping the vectors.",
    "Build the vocabulary. Union of every term across all 8 documents. For "
    "this collection that came out to 601 unique terms.",
    "Term Frequency (TF). tf(t, d) = count(t in d) / len(d) -- how often a "
    "term shows up in a document, normalized by document length so longer "
    "documents don't automatically score higher.",
    "Inverse Document Frequency (IDF). idf(t) = log(N / df(t)), where N is "
    "the total number of documents and df(t) is how many of them contain "
    "term t. This is the important part -- it pushes down words that "
    "show up everywhere (things like \"system\" or \"data\") and gives more "
    "weight to words distinctive to just a few documents (like \"neural\", "
    "\"mars\", or \"goalkeeper\").",
    "TF-IDF vector. Multiply the two together -- tfidf(t, d) = tf(t, d) * "
    "idf(t) -- and each document ends up represented as a point in a "
    "601-dimensional space, one axis per vocabulary term.",
    "Cosine similarity. similarity(A, B) = (A · B) / (‖A‖ * ‖B‖). This is "
    "the cosine of the angle between the vectors. It doesn't care how long "
    "the documents are (already handled by the TF normalization above), "
    "and since none of the TF-IDF weights are negative, the score always "
    "lands somewhere in [0, 1].",
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

doc.add_paragraph(
    "Full implementation is in vsm.py (see GitHub repository), including "
    "document loading and the driving loop that builds the pairwise matrix."
)

doc.add_heading("4. Results", level=1)
doc.add_paragraph("Snapshot — cosine similarity matrix (terminal output):")
doc.add_picture("screenshots/02_similarity_matrix.png", width=Inches(5.5))

doc.add_paragraph("Full matrix, for reference:")
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
doc.add_paragraph(
    "Plotted as a heatmap, the pattern is a lot easier to spot than in the "
    "raw numbers:"
)
doc.add_picture("screenshots/04_similarity_heatmap.png", width=Inches(5.5))

doc.add_paragraph()
doc.add_paragraph("And the top/bottom pairs, pulled straight from the script's own output:")
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
doc.add_paragraph(
    "The results line up with what the topic groupings would suggest, "
    "which is a good sign the model is capturing something real and not "
    "just noise:"
)
discussion = [
    "AI ↔ Machine Learning came out on top at 0.207, which makes sense -- ML "
    "is basically a subfield of AI, so the two articles share a lot of "
    "vocabulary (learning, model, neural, data all show up in both).",
    "Football ↔ Basketball was second at 0.127. Both are team-sport "
    "articles, so words like team, player, game, and league overlap heavily.",
    "Every pair that crosses topic clusters -- sports vs. climate, space "
    "vs. sports, and so on -- scores close to zero. That correctly "
    "reflects no real topical connection between them.",
    "One notable result: Large Language Model correlates more with AI "
    "(0.067) than with Machine Learning (0.059), even though ML and LLMs "
    "might be expected to be closer. A likely explanation is that the AI "
    "article uses more of the same framing language (\"intelligence\", "
    "\"reasoning\", \"perception\") that also shows up when LLMs are "
    "described.",
]
for d in discussion:
    doc.add_paragraph(d, style="List Bullet")
doc.add_paragraph(
    "The IDF term is doing most of the heavy lifting here. Without it, "
    "common scaffolding words that appear in basically every article "
    "would dominate the vectors and every pair would score close to 1.0, "
    "regardless of topic. IDF suppresses those and lets the words "
    "actually distinctive to each topic drive the cosine score."
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
