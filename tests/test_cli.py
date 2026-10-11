from pathlib import Path
from unittest.mock import patch

from pdf2epub.cli import main
from pdf2epub.convert import ConvertOptions
from pdf2epub.deps import MissingDependencyError


def test_cli_parses_flags(tmp_path: Path):
    pdf = tmp_path / "a.pdf"
    pdf.write_bytes(b"%PDF")
    out = tmp_path / "out.epub"
    with patch("pdf2epub.cli.convert_pdf", return_value=out) as conv:
        code = main(
            [str(pdf), "--out", str(out), "--title", "T", "--author", "A", "--fast", "--keep"]
        )
    assert code == 0
    opts: ConvertOptions = conv.call_args.args[0]
    assert opts.title == "T"
    assert opts.author == "A"
    assert opts.fast is True
    assert opts.keep is True
    assert opts.out_path == out
    assert opts.link_citations is True


def test_cli_no_link_citations_flag(tmp_path: Path):
    pdf = tmp_path / "a.pdf"
    pdf.write_bytes(b"%PDF")
    with patch("pdf2epub.cli.convert_pdf", return_value=tmp_path / "a.epub") as conv:
        code = main([str(pdf), "--no-link-citations"])
    assert code == 0
    opts: ConvertOptions = conv.call_args.args[0]
    assert opts.link_citations is False


def test_cli_missing_dep_prints_hint(tmp_path: Path, capsys):
    pdf = tmp_path / "a.pdf"
    pdf.write_bytes(b"%PDF")
    with patch(
        "pdf2epub.cli.convert_pdf",
        side_effect=MissingDependencyError("pandoc", "Install with: brew install pandoc"),
    ):
        code = main([str(pdf)])
    assert code == 2
    err = capsys.readouterr().err
    assert "brew install pandoc" in err


def test_cli_requires_pdf_arg():
    code = main([])
    assert code == 2
