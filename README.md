# pdf2epub

Convert PDFs to reflowable EPUBs using [Marker](https://github.com/datalab-to/marker) (layout-aware markdown) and [Pandoc](https://pandoc.org/) (EPUB + title page + TOC).

## Requirements

| Dependency | Install | Notes |
|------------|---------|-------|
| Python 3.11+ | — | |
| `pdf2epub` + `marker-pdf` | `pip install .` | Marker models download on first balanced run |
| `pandoc` | `brew install pandoc` | EPUB packaging |
| `llama-server` | `brew install llama.cpp` | Required for default **balanced** mode |

Use `--fast` to skip `llama-server` (lower quality).

## Install

```bash
git clone <this-repo> && cd pdf2epub
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
brew install pandoc llama.cpp   # once per machine
```

## Usage

```bash
pdf2epub paper.pdf
pdf2epub paper.pdf --out ~/Books/paper.epub
pdf2epub paper.pdf --title "My Title" --author "Ada Lovelace"
pdf2epub paper.pdf --fast
pdf2epub paper.pdf --keep   # keeps Marker markdown beside the PDF
```

Metadata priority: `--title`/`--author` → PDF info → first-page heuristics → filename.

## Tests

```bash
pytest -v
```

Unit tests mock Marker/Pandoc and do not download models.

## Phase 2

Calibre plugin (thin wrapper around this CLI) — not included yet. See `DESIGN.md`.
