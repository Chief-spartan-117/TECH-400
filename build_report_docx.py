"""Builds REPORT.docx: an APA-formatted 2-3 page report on document
ranking scoring functions (Okapi BM25 vs. Language Model with
Jelinek-Mercer smoothing), with screenshots embedded."""

from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()

# APA basics: 12pt Times New Roman, double spacing
style = doc.styles["Normal"]
style.font.name = "Times New Roman"
style.font.size = Pt(12)
style.paragraph_format.line_spacing = 2.0


def add_code(text, size=9):
    """Adds a single-spaced, non-double-spaced code block."""
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run(text)
    run.font.name = "Courier New"
    run.font.size = Pt(size)
    return p

title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = title.add_run("Document Ranking Scoring Functions:\nOkapi BM25 and the Language Model with Jelinek-Mercer Smoothing")
r.bold = True
r.font.size = Pt(14)

meta = doc.add_paragraph()
meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
meta.add_run("Information Retrieval\nWeek 4 Assignment")

doc.add_heading("Introduction", level=1)
doc.add_paragraph(
    "Ranking documents by relevance is the central problem an information "
    "retrieval (IR) system must solve once candidate documents have been "
    "retrieved. A scoring function assigns each document a numeric value "
    "for a query so the most relevant documents can be presented first. "
    "This report examines two scoring functions from different "
    "theoretical families: Okapi BM25, a probabilistic relevance model, "
    "and a unigram Language Model (LM) with Jelinek-Mercer (JM) "
    "smoothing, a statistical language-modeling approach. Both were "
    "implemented from first principles in Python and applied to a shared "
    "eight-document corpus so their practical behavior could be "
    "compared directly."
)

doc.add_heading("Corpus and Setup", level=1)
doc.add_paragraph(
    "The evaluation corpus consists of eight public Wikipedia documents "
    "(artificial intelligence, machine learning, large language models, "
    "NASA, Mars, association football, basketball, and climate change), "
    "the same corpus used in the Week 3 vector space model assignment. "
    "Text was lowercased, tokenized with the regular expression [a-z]+, "
    "and filtered through a stopword list, yielding a vocabulary of 601 "
    "terms and an average document length of 123.8 tokens. Figure 1 "
    "shows the program's corpus summary."
)
doc.add_paragraph("Figure 1")
doc.add_paragraph("Corpus Statistics Reported by scoring.py").italic = True
doc.add_picture("screenshots/01_corpus_stats.png", width=Inches(5.5))

doc.add_heading("Okapi BM25", level=1)
doc.add_paragraph(
    "BM25 (Robertson & Zaragon, 2009) scores a document d against a "
    "query q as a sum, over query terms t, of an inverse document "
    "frequency (IDF) weight multiplied by a saturating term-frequency "
    "component:"
)
add_code(
    "score(q, d) = sum_t IDF(t) * [ f(t,d)*(k1+1) ] / "
    "[ f(t,d) + k1*(1 - b + b*|d|/avgdl) ]",
    size=10,
)
doc.add_paragraph(
    "IDF(t) = ln[ (N - df(t) + 0.5) / (df(t) + 0.5) + 1 ] down-weights "
    "terms that occur in most documents. f(t,d) is the raw frequency of "
    "term t in document d, k1 controls how quickly additional "
    "occurrences of a term stop adding to the score (term-frequency "
    "saturation), and b controls how strongly document length is "
    "normalized against the average document length (avgdl). This "
    "implementation uses the standard defaults k1 = 1.5 and b = 0.75."
)
doc.add_paragraph(
    "Two properties of BM25 are important in practice. First, term "
    "frequency saturates: a term appearing 10 times contributes far less "
    "than 10 times the score of a single occurrence, which prevents "
    "keyword stuffing from dominating the ranking. Second, a document "
    "that shares no vocabulary with the query scores exactly 0, since "
    "every summed term contributes nothing -- BM25 has no mechanism to "
    "distinguish between two completely non-matching documents."
)

doc.add_heading("Language Model with Jelinek-Mercer Smoothing", level=1)
doc.add_paragraph(
    "The language-modeling approach (Zhai & Lafferty, 2001; Ponte & "
    "Croft, 1998) treats each document as having generated a probability "
    "distribution over words, and ranks documents by the likelihood that "
    "their language model would generate the query. The raw maximum-"
    "likelihood estimate P(w|d) = c(w,d)/|d| assigns zero probability to "
    "any query term absent from d, which would make the whole query "
    "probability zero the moment a single term is missing. Jelinek-"
    "Mercer smoothing fixes this by linearly interpolating the "
    "document model with the collection model:"
)
add_code(
    "P(w|d) = (1 - lambda) * c(w,d)/|d|  +  lambda * c(w,C)/|C|\n"
    "score(q, d) = sum_w log P(w|d)",
    size=10,
)
doc.add_paragraph(
    "c(w,C)/|C| is the term's relative frequency across the whole "
    "collection C, and lambda in [0,1] controls the smoothing strength. "
    "Following Zhai and Lafferty's (2001) finding that short, keyword-"
    "style queries perform best with light smoothing, this "
    "implementation uses lambda = 0.1: document evidence dominates the "
    "score, and the collection model only prevents a missing term from "
    "producing an undefined log(0)."
)

doc.add_heading("Implementation", level=1)
code = '''def bm25_score(corpus, query_terms, doc_name, k1=1.5, b=0.75):
    for term in query_terms:
        f = corpus.counts[doc_name].get(term, 0)
        if f == 0: continue
        idf = bm25_idf(corpus, term)
        num = f * (k1 + 1)
        den = f + k1 * (1 - b + b * corpus.doc_len[doc_name] / corpus.avg_dl)
        score += idf * (num / den)

def lm_jm_score(corpus, query_terms, doc_name, lam=0.1):
    for term in query_terms:
        p_doc = corpus.counts[doc_name].get(term, 0) / corpus.doc_len[doc_name]
        p_coll = corpus.collection_counts.get(term, 0) / corpus.collection_len
        p = (1 - lam) * p_doc + lam * p_coll
        score += math.log(p) if p > 0 else math.log(1e-12)'''
add_code(code)
doc.add_paragraph(
    "The full implementation, including corpus loading and the ranking "
    "helper, is provided in scoring.py."
)

doc.add_heading("Results", level=1)
doc.add_paragraph(
    "Three test queries were run against the corpus to probe different "
    "topic clusters: a machine-learning query, a space-exploration "
    "query, and a team-sports query. Each was scored with both BM25 and "
    "LM-JM and the top-ranked documents compared."
)

doc.add_paragraph("Figure 2")
doc.add_paragraph('Ranking for the Query "machine learning neural network"').italic = True
doc.add_picture("screenshots/02_query_ml.png", width=Inches(6.0))

doc.add_paragraph("Figure 3")
doc.add_paragraph('Ranking for the Query "space exploration mars mission"').italic = True
doc.add_picture("screenshots/03_query_space.png", width=Inches(6.0))

doc.add_paragraph("Figure 4")
doc.add_paragraph('Ranking for the Query "football basketball team player"').italic = True
doc.add_picture("screenshots/04_query_sports.png", width=Inches(6.0))

doc.add_heading("Analysis", level=1)
doc.add_paragraph(
    "Across all three queries, BM25 and LM-JM agree on document "
    "ordering: doc2 (Machine Learning) tops the ML query, doc4 (NASA) "
    "tops the space query, and doc6/doc7 (football/basketball) top the "
    "sports query, in the same relative order under both functions. This "
    "agreement is expected -- both functions grow with how often query "
    "terms occur in a document relative to the collection -- but the two "
    "scores are not interchangeable."
)
doc.add_paragraph(
    "The clearest difference is how each function treats non-matching "
    "documents. BM25 assigns exactly 0.000 to every document that shares "
    "no term with the query (ranks 4-8 in Figure 3), so it cannot rank "
    "them relative to each other; ties must be broken arbitrarily. LM-JM "
    "instead falls back to the collection-wide probability of each query "
    "term (-32.812 for those same documents), which keeps the score "
    "finite and, in corpora where non-matching documents differ in how "
    "much they otherwise share with near-miss query terms, still lets "
    "LM-JM discriminate where BM25's flat zero cannot."
)
doc.add_paragraph(
    "Scale also differs. BM25 scores are additive, unbounded above, and "
    "directly readable as relative match strength (6.612 vs. 3.453 for "
    "the ML query shows doc2 matching nearly twice as strongly as doc3). "
    "LM-JM scores are log-probabilities that shrink toward negative "
    "infinity as query length grows, since each extra query term "
    "multiplies in another probability below 1, making raw scores harder "
    "to compare across queries of different lengths."
)
doc.add_paragraph(
    "The functions normalize document length differently as well. BM25 "
    "applies an explicit, tunable factor (1 - b + b*|d|/avgdl) that "
    "penalizes long documents unless their term frequency is "
    "proportionally high. LM-JM normalizes only implicitly, through the "
    "ratio c(w,d)/|d|; its one parameter, lambda, instead controls "
    "collection-versus-document weighting. With document lengths fairly "
    "close in this corpus (avg. 123.8 tokens), the effect was small here "
    "but would matter more with wide length variance."
)
doc.add_paragraph(
    "In short, BM25 suits keyword-style retrieval where a tunable, "
    "interpretable saturation curve is useful, while LM-JM's smoothing "
    "gives it a principled probability distribution that composes well "
    "with other probabilistic techniques, such as relevance models or "
    "query expansion."
)

doc.add_heading("Conclusion", level=1)
doc.add_paragraph(
    "This assignment implemented Okapi BM25 and a Jelinek-Mercer "
    "smoothed language model from first principles and applied both to "
    "an eight-document corpus across three queries. Both functions "
    "produced the same top-ranked document for every query, confirming "
    "that they are both valid relevance signals, but they diverge in "
    "how they treat non-matching documents, in the interpretability and "
    "scale of their scores, and in how they normalize for document "
    "length. Understanding these differences is important when choosing "
    "a scoring function for a real system: BM25 remains a strong, "
    "tunable default for general-purpose search, while LM-JM's "
    "probabilistic foundation makes it preferable when scores need to "
    "compose with other probabilistic components."
)

doc.add_heading("How to Reproduce", level=1)
add_code(
    "pip install -r requirements.txt\n"
    "python3 scoring.py             # corpus stats + BM25/LM-JM rankings\n"
    "python3 make_screenshots.py    # re-renders terminal-style PNGs"
)

doc.add_heading("References", level=1)
references = [
    "Ponte, J. M., & Croft, W. B. (1998). A language modeling approach "
    "to information retrieval. Proceedings of the 21st Annual "
    "International ACM SIGIR Conference on Research and Development in "
    "Information Retrieval, 275-281.",
    "Robertson, S., & Zaragoza, H. (2009). The probabilistic relevance "
    "framework: BM25 and beyond. Foundations and Trends in Information "
    "Retrieval, 3(4), 333-389.",
    "Zhai, C., & Lafferty, J. (2001). A study of smoothing methods for "
    "language models applied to ad hoc information retrieval. "
    "Proceedings of the 24th Annual International ACM SIGIR Conference "
    "on Research and Development in Information Retrieval, 334-342.",
    "Manning, C. D., Raghavan, P., & Schutze, H. (2008). Introduction to "
    "information retrieval. Cambridge University Press. (Chapters 11-12: "
    "probabilistic IR and language models for IR.)",
    "Wikipedia contributors. Articles used as the evaluation corpus: "
    "Artificial intelligence, Machine learning, Large language model, "
    "NASA, Mars, Association football, Basketball, Climate change. "
    "Wikipedia, The Free Encyclopedia. Licensed under CC BY-SA 4.0.",
]
for r in references:
    p = doc.add_paragraph(r)
    p.paragraph_format.first_line_indent = Inches(-0.5)
    p.paragraph_format.left_indent = Inches(0.5)

doc.save("REPORT.docx")
print("wrote REPORT.docx")
