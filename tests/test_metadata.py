from pathlib import Path

import pytest
from pypdf import PdfWriter

from pdf2epub.metadata import (
    BookMeta,
    is_garbage_pdf_field,
    parse_markdown_heuristics,
    read_pdf_info,
    resolve_metadata,
    strip_md_emphasis,
)

FIXTURE = Path(__file__).parent / "fixtures" / "cognification_head.md"


def test_strip_md_emphasis():
    assert strip_md_emphasis("**Hello**") == "Hello"
    assert strip_md_emphasis("*Hello*") == "Hello"


def test_parse_markdown_heuristics_title_and_author():
    md = FIXTURE.read_text(encoding="utf-8")
    meta = parse_markdown_heuristics(md)
    assert meta.title == "Reimagining Culture Through AI: The Cognification Phenomenon"
    assert meta.author is not None
    assert "Ilya Levin" in meta.author
    assert "Konstantin" in meta.author


def test_garbage_pdf_fields():
    assert is_garbage_pdf_field(None)
    assert is_garbage_pdf_field("")
    assert is_garbage_pdf_field("untitled")
    assert is_garbage_pdf_field("Microsoft Word - Document1")
    assert not is_garbage_pdf_field("Real Title")


def test_read_pdf_info(tmp_path: Path):
    pdf = tmp_path / "sample.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.add_metadata({"/Title": "PDF Title", "/Author": "PDF Author"})
    with pdf.open("wb") as f:
        writer.write(f)
    meta = read_pdf_info(pdf)
    assert meta.title == "PDF Title"
    assert meta.author == "PDF Author"


def test_resolve_priority_cli_over_pdf_over_md(tmp_path: Path):
    pdf = tmp_path / "fallback-name.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.add_metadata({"/Title": "PDF Title", "/Author": "PDF Author"})
    with pdf.open("wb") as f:
        writer.write(f)
    md = FIXTURE.read_text(encoding="utf-8")

    cli = resolve_metadata(
        pdf_path=pdf, markdown=md, title_override="CLI Title", author_override="CLI Author"
    )
    assert cli == BookMeta(title="CLI Title", author="CLI Author")

    from_pdf = resolve_metadata(pdf_path=pdf, markdown=md)
    assert from_pdf.title == "PDF Title"
    assert from_pdf.author == "PDF Author"

    empty_pdf = tmp_path / "paper.pdf"
    w2 = PdfWriter()
    w2.add_blank_page(width=200, height=200)
    with empty_pdf.open("wb") as f:
        w2.write(f)
    from_md = resolve_metadata(pdf_path=empty_pdf, markdown=md)
    assert "Cognification" in from_md.title
    assert from_md.author and "Ilya" in from_md.author

    from_name = resolve_metadata(pdf_path=empty_pdf, markdown="# No author here\n\nBody.\n")
    assert from_name.title == "No author here"
    assert from_name.author is None
