# Basic Information Retrieval System

A small Boolean Information Retrieval system built for a course assignment.
It ingests a collection of text documents, builds a dictionary and an
inverted index, and answers Boolean queries (`AND`, `OR`, `NOT`, with
parentheses) over that index.

## Contents

```
ir-system/
├── docs/                 sample 8-document collection (.txt)
├── ir_system.py          IRSystem class: index build + Boolean search
├── demo.py               builds the index and runs sample queries
├── test_ir_system.py     unit tests
├── make_screenshots.py   generates the report's terminal screenshots
├── screenshots/          PNG screenshots used in the report
├── report.docx           write-up: design choices, results, screenshots
└── README.md             this file
```

## Requirements

Python 3.9+, no third-party packages needed to run the IR system itself.

## Usage

Run the demo (builds the index from `docs/` and runs sample Boolean queries):

```bash
python3 demo.py
```

Use it in your own script:

```python
from ir_system import IRSystem

ir = IRSystem()
ir.add_documents_from_folder("docs")

print(ir.get_dictionary())          # all distinct terms
print(ir.get_postings("python"))    # doc ids containing "python"
print(ir.search("python OR java"))  # Boolean query
print(ir.search("(python OR java) AND NOT javascript"))
```

Run the tests:

```bash
python3 -m unittest test_ir_system.py -v
```

## Boolean query syntax

- `term1 AND term2`
- `term1 OR term2`
- `NOT term1`
- `term1 AND NOT term2`
- `(term1 OR term2) AND term3`

Operators (`AND`/`OR`/`NOT`) are case-insensitive; everything else is treated
as a single query term. Precedence: `NOT` > `AND` > `OR`, parentheses
override precedence.

## Report

`report.docx` explains the design and implementation choices (tokenization,
data structures, index construction, Boolean query parsing), includes
screenshots of the program running, and walks through sample queries and
results.
