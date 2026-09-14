const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, BorderStyle, ImageRun, AlignmentType, ShadingType, PageBreak
} = require("docx");
const fs = require("fs");

const PAGE_WIDTH = 12240; // US Letter, DXA
const PAGE_HEIGHT = 15840;

function h1(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_1, spacing: { before: 300, after: 150 } });
}
function h2(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_2, spacing: { before: 240, after: 120 } });
}
function p(text, opts = {}) {
  return new Paragraph({ children: [new TextRun({ text, ...opts })], spacing: { after: 160 } });
}
function bullet(text) {
  return new Paragraph({ text, bullet: { level: 0 }, spacing: { after: 60 } });
}
function code(text) {
  const lines = text.split("\n");
  return lines.map((line, i) =>
    new Paragraph({
      children: [new TextRun({ text: line || " ", font: "Consolas", size: 19 })],
      spacing: { after: i === lines.length - 1 ? 160 : 0 },
      shading: { type: ShadingType.CLEAR, fill: "F2F2F2" },
    })
  );
}
function imageParagraph(path, width, height) {
  const data = fs.readFileSync(path);
  return new Paragraph({
    children: [new ImageRun({ data, transformation: { width, height }, type: "png" })],
    alignment: AlignmentType.CENTER,
    spacing: { after: 100 },
  });
}
function caption(text) {
  return new Paragraph({
    children: [new TextRun({ text, italics: true, size: 19, color: "555555" })],
    alignment: AlignmentType.CENTER,
    spacing: { after: 260 },
  });
}

function cell(text, opts = {}) {
  return new TableCell({
    children: [new Paragraph({ children: [new TextRun({ text, bold: !!opts.bold })] })],
    width: { size: opts.width || 2000, type: WidthType.DXA },
    shading: opts.shade ? { type: ShadingType.CLEAR, fill: "E7E7E7" } : undefined,
  });
}

const sampleRows = [
  ["python", "1", "Only doc1 mentions Python by name."],
  ["language", "4", "doc1-doc4 each describe a programming language."],
  ["python OR java", "2", "Union of Python and Java postings."],
  ["language AND retrieval", "0", "No document uses both words -- languages and IR are discussed in disjoint documents."],
  ["programming AND NOT java", "2", "Documents about programming, excluding the one about Java."],
  ["boolean AND retrieval", "2", "Both terms co-occur only in doc7 and doc8."],
  ["(python OR java) AND language", "2", "Parenthesised sub-query evaluated first."],
  ["machine AND learning", "1", "Only doc8 mentions machine learning."],
];

const queryTable = new Table({
  width: { size: 9350, type: WidthType.DXA },
  columnWidths: [4200, 1300, 3850],
  rows: [
    new TableRow({
      children: [
        cell("Query", { bold: true, width: 4200, shade: true }),
        cell("# Results", { bold: true, width: 1300, shade: true }),
        cell("Why", { bold: true, width: 3850, shade: true }),
      ],
    }),
    ...sampleRows.map(([q, n, why]) =>
      new TableRow({
        children: [cell(q, { width: 4200 }), cell(n, { width: 1300 }), cell(why, { width: 3850 })],
      })
    ),
  ],
});

const doc = new Document({
  sections: [
    {
      properties: { page: { size: { width: PAGE_WIDTH, height: PAGE_HEIGHT } } },
      children: [
        new Paragraph({
          children: [new TextRun({ text: "A Basic Information Retrieval System", bold: true, size: 44 })],
          alignment: AlignmentType.CENTER,
          spacing: { after: 100 },
        }),
        new Paragraph({
          children: [new TextRun({ text: "Inverted Index Construction and Boolean Retrieval over a Small Document Collection", size: 26, color: "444444" })],
          alignment: AlignmentType.CENTER,
          spacing: { after: 400 },
        }),
        new Paragraph({
          children: [new TextRun({ text: "Sagar", size: 22 })],
          alignment: AlignmentType.CENTER,
          spacing: { after: 60 },
        }),
        new Paragraph({
          children: [new TextRun({ text: "Information Retrieval -- Course Assignment", size: 22, color: "666666" })],
          alignment: AlignmentType.CENTER,
          spacing: { after: 60 },
        }),
        new Paragraph({
          children: [new TextRun({ text: "GitHub repository: <add your repo link here before submitting>", size: 22, color: "666666", italics: true })],
          alignment: AlignmentType.CENTER,
          spacing: { after: 400 },
        }),

        h1("1. Introduction"),
        p("This report describes a basic Information Retrieval (IR) system built for a small collection of eight text documents. The system supports three core capabilities that underlie most classical IR engines: (1) ingesting documents into a collection, (2) building a dictionary and an inverted index over that collection, and (3) answering Boolean queries (AND, OR, NOT, and parenthesised combinations of these) against the index. The goal of the assignment was not raw performance but a hands-on, traceable implementation: every design decision below favours clarity and easy manual verification over sophistication."),

        h1("2. Objectives"),
        bullet("Represent a document collection and add new documents to it programmatically."),
        bullet("Build a dictionary: the set of all distinct terms appearing across the collection."),
        bullet("Build an inverted index mapping each term to the documents that contain it."),
        bullet("Implement Boolean retrieval (AND, OR, NOT, parentheses) over that index."),
        bullet("Verify the system with a demo run and a small automated test suite."),

        h1("3. Document Collection"),
        p("The collection consists of eight short documents (doc1.txt - doc8.txt), stored as plain text files in a docs/ folder. Four documents describe individual programming languages (Python, Java, C, JavaScript), and four describe Information Retrieval concepts (IR in general, inverted indexes, Boolean retrieval, and a mention of machine learning in ranking). This mix was chosen deliberately: some terms (e.g. \"language\", \"programming\") appear across many documents, while others (e.g. \"python\", \"boolean\") are distinctive -- which makes the Boolean query results easy to reason about and sanity-check by eye."),
        imageParagraph("screenshots/01_document_collection.png", 470, 172),
        caption("Figure 1. The eight documents loaded into the system, with a preview of each."),

        h1("4. Design and Implementation Choices"),
        h2("4.1 Data structures"),
        p("Documents are stored in a dictionary mapping an integer doc_id to its raw text (Dict[int, str]), assigned in insertion order starting at 0. The inverted index is a dictionary mapping each term to a Python set of document ids (Dict[str, Set[int]]). Sets were chosen over lists because Boolean AND / OR / NOT map directly onto set intersection, union, and difference -- this keeps the retrieval logic short and its correctness easy to argue."),
        h2("4.2 Tokenization and normalization"),
        p("Text is lowercased, punctuation is stripped, and the remaining text is split into alphanumeric tokens with a simple regular expression. Two common IR preprocessing steps were deliberately left out for this assignment:"),
        bullet("Stopword removal -- omitted so the index stays a faithful, complete record of every word in the source text, which makes it easier to verify against the raw documents by hand."),
        bullet("Stemming / lemmatization -- omitted to avoid obscuring the mapping between a query word and the exact surface form stored in the index."),
        p("Both would be straightforward additions (see Section 7, Limitations and Future Work) and are noted there rather than built in, to keep the core index-and-retrieval logic the focus of the assignment."),
        h2("4.3 Building the dictionary and inverted index"),
        p("Whenever a document is added, it is tokenized and every distinct term found is added to that term's posting set together with the new document's id. The dictionary is simply the sorted list of keys of the inverted index -- it does not need to be stored separately, since it can always be derived from the index. This keeps the two structures consistent by construction: there is no way for a term to appear in the dictionary but not the index, or vice versa."),
        h2("4.4 Boolean query evaluation"),
        p("Queries are parsed with a small recursive-descent parser with three precedence levels, matching conventional Boolean IR semantics: NOT binds tightest, then AND, then OR, and parentheses override precedence. A NOT term is evaluated as (all document ids) minus (postings for term), which requires knowing the full document set -- a minor but deliberate trade-off of the simple design, since a truly web-scale index would avoid ever materialising a \"NOT\" result directly this way."),
        ...code("query:  (python OR java) AND language\nparse:  AND( OR(python, java), language )\neval:   ({0} | {1}) & {0,1,2,3}  =  {0, 1}"),

        h1("5. Sample Queries and Results"),
        p("The table below summarises a representative set of queries run against the demo collection (see Figure 3 for the full program output)."),
        queryTable,
        new Paragraph({ text: "", spacing: { after: 200 } }),
        imageParagraph("screenshots/03_boolean_queries.png", 470, 121),
        caption("Figure 2. Boolean queries executed against the index, with matching document ids and filenames."),

        h1("6. Inverted Index (excerpt)"),
        p("The full dictionary contains 118 distinct terms after tokenizing all eight documents. An excerpt of the printed inverted index is shown below; the complete index is produced by running demo.py or ir_system.py directly."),
        imageParagraph("screenshots/02_inverted_index.png", 380, 415),
        caption("Figure 3. Excerpt of the inverted index: each term with its sorted list of document ids."),

        h1("7. Testing"),
        p("A unit test suite (test_ir_system.py) exercises the dictionary, the posting lists, and each Boolean operator (AND, OR, NOT) individually as well as in combination with parentheses, plus case-insensitivity of query terms. All seven tests pass:"),
        ...code("$ python3 -m unittest test_ir_system.py -v\ntest_and_query ... ok\ntest_case_insensitivity ... ok\ntest_combined_query_with_parentheses ... ok\ntest_dictionary_contains_expected_terms ... ok\ntest_not_query ... ok\ntest_or_query ... ok\ntest_postings_are_correct ... ok\n\nRan 7 tests in 0.001s\nOK"),

        h1("8. Limitations and Future Work"),
        bullet("No ranking: results are an unordered set of matching documents, as expected of a pure Boolean model rather than a ranked (vector-space / probabilistic) model."),
        bullet("No stemming or stopword removal, as discussed in Section 4.2 -- adding a stopword list or a stemmer (e.g. Porter stemmer) would reduce the dictionary size and let morphological variants of a word match each other."),
        bullet("Single-word query terms only: phrase queries (\"exact phrase\") and wildcard queries (comp*) are not supported, since they require positional or permuterm indexes beyond this assignment's scope."),
        bullet("In-memory only: the index is rebuilt from the docs/ folder each run rather than persisted to disk, which is adequate at this collection size but would not scale to a larger corpus."),

        h1("9. Conclusion"),
        p("This assignment implements the core building blocks of a classical Boolean IR system -- document ingestion, dictionary construction, inverted index construction, and Boolean query evaluation with AND / OR / NOT and parentheses -- over a small, hand-inspectable collection of eight documents. The set-based design keeps the mapping from Boolean query semantics to code direct and easy to verify, and the accompanying tests and demo output confirm the system behaves as expected on the sample queries."),

        h1("10. Source Code"),
        p("The full source code, sample documents, tests, and this report are available at:"),
        new Paragraph({
          children: [new TextRun({ text: "<add your GitHub repository link here>", italics: true, color: "1155CC" })],
          spacing: { after: 200 },
        }),
        p("Repository layout:"),
        ...code("ir-system/\n  docs/                 sample 8-document collection (.txt)\n  ir_system.py          IRSystem class: index build + Boolean search\n  demo.py               builds the index and runs sample queries\n  test_ir_system.py     unit tests\n  make_screenshots.py   generates the report's terminal screenshots\n  screenshots/          PNG screenshots used in this report\n  report.docx           this report\n  README.md             usage instructions"),
      ],
    },
  ],
});

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync("report.docx", buffer);
  console.log("wrote report.docx");
});
