# pdf2epub

Convert PDFs to reflowable EPUBs using Marker + Pandoc.

## Install

```bash
pip install .
# native tools (not bundled):
brew install pandoc llama.cpp
```

## Usage

```bash
pdf2epub paper.pdf
pdf2epub paper.pdf --title "My Title" --author "Ada Lovelace"
pdf2epub paper.pdf --fast
```
