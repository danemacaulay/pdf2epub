from pathlib import Path
from unittest.mock import MagicMock, patch

from pypdf import PdfWriter

from pdf2epub.convert import (
    ConvertOptions,
    build_pandoc_cmd,
    convert_pdf,
    default_out_path,
    find_marker_markdown,
)
from pdf2epub.metadata import BookMeta


def test_default_out_path():
    assert default_out_path(Path("/tmp/Paper.pdf")) == Path("/tmp/Paper.epub")


def test_find_marker_markdown(tmp_path: Path):
    stem = "Paper"
    md = tmp_path / stem / f"{stem}.md"
    md.parent.mkdir()
    md.write_text("# Hi\n", encoding="utf-8")
    assert find_marker_markdown(tmp_path, stem) == md


def test_build_pandoc_cmd_includes_title_page_and_meta(tmp_path: Path):
    md = tmp_path / "x.md"
    md.write_text("# T\n", encoding="utf-8")
    epub = tmp_path / "x.epub"
    cover = tmp_path / "cover.jpg"
    cover.write_bytes(b"fake")
    cmd = build_pandoc_cmd(
        pandoc=Path("/usr/bin/pandoc"),
        md_path=md,
        epub_path=epub,
        meta=BookMeta(title="My Title", author="Ada"),
        cover_path=cover,
    )
    assert cmd[0] == "/usr/bin/pandoc"
    assert str(md) in cmd
    assert str(epub) in cmd
    assert "--toc" in cmd
    assert f"--resource-path={md.parent}" in cmd
    assert "title=My Title" in " ".join(cmd) or any("My Title" in a for a in cmd)
    assert "Ada" in " ".join(cmd)
    assert "--epub-title-page=false" not in cmd
    assert f"--epub-cover-image={cover}" in cmd


def test_convert_pdf_generates_cover_for_pandoc(tmp_path: Path):
    pdf = tmp_path / "Paper.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    with pdf.open("wb") as f:
        writer.write(f)
    work = tmp_path / "work"
    stem = pdf.stem
    md_dir = work / stem
    md_dir.mkdir(parents=True)
    (md_dir / f"{stem}.md").write_text(
        "# **Paper Title**\n\nAda Lovelace\n\n# Intro\n\nHello.\n",
        encoding="utf-8",
    )
    out = tmp_path / "out.epub"
    opts = ConvertOptions(pdf_path=pdf, out_path=out, fast=True, work_dir=work)

    with patch("pdf2epub.convert.check_conversion_deps"):
        with patch("pdf2epub.convert.require_marker_single", return_value=Path("marker_single")):
            with patch("pdf2epub.convert.require_pandoc", return_value=Path("pandoc")):
                with patch("pdf2epub.convert.subprocess.run") as run:

                    def _side_effect(cmd, **kwargs):
                        if Path(cmd[0]).name == "pandoc":
                            out.write_bytes(b"PK\x03\x04")
                        return MagicMock(returncode=0, stdout="", stderr="")

                    run.side_effect = _side_effect
                    convert_pdf(opts)
                    pandoc_cmd = run.call_args_list[1].args[0]

    cover_flags = [a for a in pandoc_cmd if a.startswith("--epub-cover-image=")]
    assert len(cover_flags) == 1
    cover_path = Path(cover_flags[0].split("=", 1)[1])
    assert cover_path.is_file()
    assert cover_path.suffix.lower() in {".jpg", ".jpeg"}


def _run_convert_with_markdown(tmp_path: Path, markdown: str, **opt_overrides):
    pdf = tmp_path / "Paper.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    with pdf.open("wb") as f:
        writer.write(f)
    work = tmp_path / "work"
    md_dir = work / pdf.stem
    md_dir.mkdir(parents=True)
    md_path = md_dir / f"{pdf.stem}.md"
    md_path.write_text(markdown, encoding="utf-8")
    out = tmp_path / "out.epub"
    opts = ConvertOptions(pdf_path=pdf, out_path=out, fast=True, work_dir=work, **opt_overrides)

    with patch("pdf2epub.convert.check_conversion_deps"):
        with patch("pdf2epub.convert.require_marker_single", return_value=Path("marker_single")):
            with patch("pdf2epub.convert.require_pandoc", return_value=Path("pandoc")):
                with patch("pdf2epub.convert.subprocess.run") as run:

                    def _side_effect(cmd, **kwargs):
                        if Path(cmd[0]).name == "pandoc":
                            out.write_bytes(b"PK\x03\x04")
                        return MagicMock(returncode=0, stdout="", stderr="")

                    run.side_effect = _side_effect
                    convert_pdf(opts)
                    pandoc_cmd = run.call_args_list[1].args[0]
    return md_path, Path(pandoc_cmd[1])


CITED_MD = "# **Paper Title**\n\nSee [1].\n\n# References\n\n[1] Levin I. (2024).\n"


def test_convert_pdf_passes_citation_linked_markdown_to_pandoc(tmp_path: Path):
    md_path, pandoc_input = _run_convert_with_markdown(tmp_path, CITED_MD)
    assert pandoc_input != md_path
    assert pandoc_input.parent == md_path.parent
    linked = pandoc_input.read_text(encoding="utf-8")
    assert "(#ref-1)" in linked
    assert "::: {#ref-1" in linked
    assert md_path.read_text(encoding="utf-8") == CITED_MD


def test_convert_pdf_uses_original_markdown_when_nothing_to_link(tmp_path: Path):
    md_path, pandoc_input = _run_convert_with_markdown(tmp_path, "# T\n\nHello.\n")
    assert pandoc_input == md_path


def test_convert_pdf_can_disable_citation_linking(tmp_path: Path):
    md_path, pandoc_input = _run_convert_with_markdown(tmp_path, CITED_MD, link_citations=False)
    assert pandoc_input == md_path


def test_convert_pdf_orchestration(tmp_path: Path):
    pdf = tmp_path / "Paper.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    with pdf.open("wb") as f:
        writer.write(f)
    work = tmp_path / "work"
    stem = pdf.stem
    md_dir = work / stem
    md_dir.mkdir(parents=True)
    (md_dir / f"{stem}.md").write_text(
        "# **Paper Title**\n\nAda Lovelace\n\n# Intro\n\nHello.\n",
        encoding="utf-8",
    )
    out = tmp_path / "out.epub"
    opts = ConvertOptions(pdf_path=pdf, out_path=out, fast=True, work_dir=work)

    with patch("pdf2epub.convert.check_conversion_deps"):
        with patch("pdf2epub.convert.require_marker_single", return_value=Path("marker_single")):
            with patch("pdf2epub.convert.require_pandoc", return_value=Path("pandoc")):
                with patch("pdf2epub.convert.subprocess.run") as run:

                    def _side_effect(cmd, **kwargs):
                        if Path(cmd[0]).name == "pandoc":
                            out.write_bytes(b"PK\x03\x04")
                        return MagicMock(returncode=0, stdout="", stderr="")

                    run.side_effect = _side_effect
                    result = convert_pdf(opts)
                    assert result == out
                    assert out.exists()
                    assert run.call_count == 2
                    marker_cmd = run.call_args_list[0].args[0]
                    assert "--mode" in marker_cmd
                    assert "fast" in marker_cmd
