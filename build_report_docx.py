"""Builds REPORT.docx from the content in REPORT.md, with screenshots embedded."""

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

from vsm import build_similarity_matrix

names, vocab, tfidf_vectors, sim_matrix = build_similarity_matrix("docs")
short = [f"d{i+1}" for i in range(len(names))]

doc = Document()

doc.add_heading("Document Similarity Using a Vector Space Model", level=0)
meta = doc.add_paragraph()
meta.add_run("Course: ").bold = True
meta.add_run("Information Retrieval / Text Analytics\n")
meta.add_run("Assignment: ").bold = True
meta.add_run("Document Similarity Scoring with a Vector Space Model")

doc.add_heading("1. Introduction", level=1)
doc.add_paragraph(
    "Measuring similarity between text documents is a core problem in "
    "information retrieval, used in applications such as search ranking, "
    "plagiarism detection, and document clustering. This assignment "
    "implements the Vector Space Model (VSM), one of the foundational "
    "approaches to this problem, and applies it to a small corpus of "
    "publicly available documents. Each document is represented as a "
    "weighted term vector using TF-IDF, and similarity between document "
    "pairs is computed using cosine similarity."
)

doc.add_heading("2. Corpus", level=1)
doc.add_paragraph(
    "A total of 8 documents were collected for this assignment, "
    "satisfying the requirement of 5-10 publicly accessible documents. "
    "The corpus was drawn from Wikipedia, a freely accessible and "
    "citable source (content licensed under CC BY-SA), and saved as "
    "plain .txt files in the docs/ directory."
)
doc.add_paragraph(
    "The topics were selected in related pairs so that the correctness "
    "of the similarity results could be verified against expectation: "
    "two articles on AI/ML, one AI-adjacent article, two on space "
    "exploration, two on team sports, and one on climate. If the model "
    "performs correctly, documents within the same topic pair should "
    "receive noticeably higher similarity scores than documents from "
    "unrelated pairs."
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
    "Documents were retrieved using Wikipedia's REST API "
    "(action=query&prop=extracts&explaintext=1), which returns clean "
    "plain text without HTML markup, navigation elements, or infobox "
    "content. Each file is approximately 1.2 KB and includes a Title: / "
    "Source: header identifying its origin."
)
doc.add_paragraph("Figure 1 — Document collection loaded by the program:")
doc.add_picture("screenshots/01_document_collection.png", width=Inches(5.5))

doc.add_heading("3. Methodology", level=1)
doc.add_paragraph(
    "The VSM pipeline was implemented from first principles in vsm.py, "
    "without relying on pre-built vectorizers such as scikit-learn's "
    "TfidfVectorizer. numpy is used only for vector arithmetic (dot "
    "products and norms), not for any part of the weighting algorithm. "
    "The pipeline consists of the following stages:"
)
steps = [
    "Tokenization and normalization. Text is lowercased and split into "
    "alphabetic tokens using the regular expression [a-z]+. A stopword "
    "list is applied to remove common function words, and tokens of "
    "length 2 or fewer are discarded. No stemming or lemmatization is "
    "applied.",
    "Vocabulary construction. The vocabulary is the union of all terms "
    "across the corpus. For this dataset, the vocabulary contains 601 "
    "unique terms.",
    "Term Frequency (TF). For a term t and document d: "
    "tf(t, d) = count(t in d) / len(d). Raw term counts are normalized "
    "by document length so that longer documents do not receive "
    "inflated scores.",
    "Inverse Document Frequency (IDF). For a term t: "
    "idf(t) = log(N / df(t)), where N is the total number of documents "
    "and df(t) is the number of documents containing t. IDF down-"
    "weights terms that occur across most or all documents (e.g. "
    "\"system\", \"data\") and up-weights terms that are distinctive to "
    "a small subset of documents (e.g. \"neural\", \"mars\", "
    "\"goalkeeper\").",
    "TF-IDF weighting. The final weight for each term in each document "
    "is tfidf(t, d) = tf(t, d) * idf(t). Each document is thus "
    "represented as a vector in a 601-dimensional space, with one "
    "dimension per vocabulary term.",
    "Cosine similarity. For two document vectors A and B: "
    "similarity(A, B) = (A · B) / (‖A‖ * ‖B‖). Cosine similarity "
    "measures the angle between two vectors rather than their "
    "magnitude, making it independent of document length. As all "
    "TF-IDF weights are non-negative, the resulting score is bounded in "
    "the range [0, 1].",
]
for s in steps:
    doc.add_paragraph(s, style="List Number")

doc.add_heading("3.1 Implementation", level=2)
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
    "The complete implementation, including document loading and the "
    "pairwise similarity computation, is provided in vsm.py (see GitHub "
    "repository)."
)

doc.add_heading("4. Results", level=1)
doc.add_paragraph("Figure 2 — Program output: cosine similarity matrix")
doc.add_picture("screenshots/02_similarity_matrix.png", width=Inches(5.5))

doc.add_paragraph("Table 1 — Full pairwise cosine similarity matrix")
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
doc.add_paragraph("Figure 3 — Similarity matrix as a heatmap")
doc.add_picture("screenshots/04_similarity_heatmap.png", width=Inches(5.5))

doc.add_paragraph()
doc.add_paragraph("Figure 4 — Most and least similar document pairs")
doc.add_picture("screenshots/03_similar_pairs.png", width=Inches(5.5))

doc.add_paragraph("Table 2 — Top 3 most similar pairs")
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

doc.add_paragraph()
doc.add_paragraph("Table 3 — Bottom 3 least similar pairs")
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

doc.add_heading("5. Analysis", level=1)
doc.add_paragraph(
    "The results are consistent with the topic groupings defined in "
    "Section 2, indicating that the model correctly captures topical "
    "similarity from term distributions alone."
)
doc.add_paragraph(
    "The highest similarity score (0.207) was observed between the "
    "Artificial Intelligence and Machine Learning documents. This is "
    "expected, as Machine Learning is a subfield of Artificial "
    "Intelligence and both articles share substantial vocabulary, "
    "including terms such as \"learning,\" \"model,\" \"neural,\" and "
    "\"data.\""
)
doc.add_paragraph(
    "The second-highest score (0.127) was observed between the "
    "Association Football and Basketball documents. Both are team-sport "
    "articles that share terms such as \"team,\" \"player,\" \"game,\" "
    "and \"league.\""
)
doc.add_paragraph(
    "All document pairs spanning unrelated topic clusters (for example, "
    "sports versus climate, or space versus sports) scored close to "
    "zero, correctly indicating no meaningful topical overlap."
)
doc.add_paragraph(
    "One notable result is that the Large Language Model document "
    "correlates more strongly with the Artificial Intelligence document "
    "(0.067) than with the Machine Learning document (0.059), despite "
    "the technical proximity between LLMs and machine learning. A "
    "plausible explanation is that the Artificial Intelligence article "
    "uses framing vocabulary (e.g. \"intelligence,\" \"reasoning,\" "
    "\"perception\") that is also present in discussions of large "
    "language models."
)
doc.add_paragraph(
    "The IDF component of the weighting scheme is primarily responsible "
    "for these results. Without IDF, high-frequency scaffolding words "
    "common to nearly every document would dominate the term vectors, "
    "and all document pairs would score close to 1.0 regardless of "
    "topic. IDF suppresses these ubiquitous terms, allowing the "
    "vocabulary distinctive to each topic to drive the cosine "
    "similarity score."
)

doc.add_heading("6. Conclusion", level=1)
doc.add_paragraph(
    "This assignment demonstrated a complete Vector Space Model "
    "pipeline -- tokenization, TF-IDF weighting, and cosine similarity "
    "-- applied to an 8-document corpus gathered from publicly "
    "available sources. The resulting similarity scores correctly "
    "identified topically related document pairs (AI/Machine Learning, "
    "Football/Basketball) and assigned near-zero scores to unrelated "
    "pairs, confirming that the model is functioning as intended. The "
    "results also illustrate the importance of IDF weighting in "
    "distinguishing topic-specific vocabulary from common language "
    "patterns shared across all documents."
)

doc.add_heading("7. GitHub Repository", level=1)
doc.add_paragraph(
    "Full source code, documents, and this report are published at: "
    "https://github.com/Chief-spartan-117/TECH-400/tree/vsm-document-similarity"
)

doc.add_heading("8. How to Reproduce", level=1)
repro = '''pip install -r requirements.txt
python3 vsm.py                 # prints similarity matrix + top/bottom pairs
python3 make_heatmap.py        # writes screenshots/04_similarity_heatmap.png
python3 make_screenshots.py    # re-renders terminal-style snapshot PNGs'''
p = doc.add_paragraph()
run = p.add_run(repro)
run.font.name = "Courier New"
run.font.size = Pt(9)

doc.add_heading("9. References", level=1)
references = [
    "Salton, G., Wong, A., & Yang, C. S. (1975). A vector space model for "
    "automatic indexing. Communications of the ACM, 18(11), 613-620.",
    "Manning, C. D., Raghavan, P., & Schutze, H. (2008). Introduction to "
    "Information Retrieval. Cambridge University Press. (Chapters 6-7: "
    "term weighting, TF-IDF, and the vector space model.)",
    "Wikipedia contributors. \"Artificial intelligence.\" Wikipedia, The "
    "Free Encyclopedia. https://en.wikipedia.org/wiki/Artificial_intelligence",
    "Wikipedia contributors. \"Machine learning.\" Wikipedia, The Free "
    "Encyclopedia. https://en.wikipedia.org/wiki/Machine_learning",
    "Wikipedia contributors. \"Large language model.\" Wikipedia, The Free "
    "Encyclopedia. https://en.wikipedia.org/wiki/Large_language_model",
    "Wikipedia contributors. \"NASA.\" Wikipedia, The Free Encyclopedia. "
    "https://en.wikipedia.org/wiki/NASA",
    "Wikipedia contributors. \"Mars.\" Wikipedia, The Free Encyclopedia. "
    "https://en.wikipedia.org/wiki/Mars",
    "Wikipedia contributors. \"Association football.\" Wikipedia, The Free "
    "Encyclopedia. https://en.wikipedia.org/wiki/Association_football",
    "Wikipedia contributors. \"Basketball.\" Wikipedia, The Free "
    "Encyclopedia. https://en.wikipedia.org/wiki/Basketball",
    "Wikipedia contributors. \"Climate change.\" Wikipedia, The Free "
    "Encyclopedia. https://en.wikipedia.org/wiki/Climate_change",
    "Wikimedia Foundation. MediaWiki Action API -- prop=extracts. "
    "https://www.mediawiki.org/wiki/API:Query#Additional_notes (used to "
    "retrieve plain-text article extracts, Section 2).",
    "Harris, C.R. et al. (2020). Array programming with NumPy. Nature, "
    "585, 357-362. https://numpy.org (used for vector arithmetic in vsm.py).",
]
for r in references:
    doc.add_paragraph(r, style="List Number")
doc.add_paragraph(
    "All Wikipedia content is licensed under Creative Commons "
    "Attribution-ShareAlike 4.0 (CC BY-SA 4.0)."
)

doc.save("REPORT.docx")
print("wrote REPORT.docx")
