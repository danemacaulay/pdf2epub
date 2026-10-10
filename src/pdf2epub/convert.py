from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from pdf2epub.deps import (
    check_conversion_deps,
    require_marker_single,
    require_pandoc,
)
from pdf2epub.metadata import BookMeta, resolve_metadata


@dataclass(frozen=True)
class ConvertOptions:
    pdf_path: Path
    out_path: Path | None = None
    title: str | None = None
    author: str | None = None
    fast: bool = False
    keep: bool = False
    work_dir: Path | None = None


def default_out_path(pdf_path: Path) -> Path:
    return pdf_path.with_suffix(".epub")


def find_marker_markdown(marker_out_dir: Path, pdf_stem: str) -> Path:
    candidate = marker_out_dir / pdf_stem / f"{pdf_stem}.md"
    if candidate.is_file():
        return candidate
    matches = list(marker_out_dir.rglob("*.md"))
    if len(matches) == 1:
        return matches[0]
    raise FileNotFoundError(
        f"Marker markdown not found under {marker_out_dir} (expected {candidate})"
    )


def build_pandoc_cmd(
    *,
    pandoc: Path,
    md_path: Path,
    epub_path: Path,
    meta: BookMeta,
) -> list[str]:
    cmd = [
        str(pandoc),
        str(md_path),
        "-o",
        str(epub_path),
        "--toc",
        "--toc-depth=3",
        f"--resource-path={md_path.parent}",
        f"--metadata=title:{meta.title}",
    ]
    if meta.author:
        cmd.append(f"--metadata=author:{meta.author}")
    return cmd


def convert_pdf(opts: ConvertOptions) -> Path:
    pdf_path = opts.pdf_path.expanduser().resolve()
    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    check_conversion_deps(fast=opts.fast)
    marker = require_marker_single()
    pandoc = require_pandoc()
    out_path = (opts.out_path or default_out_path(pdf_path)).expanduser().resolve()

    def _run(work: Path) -> Path:
        work.mkdir(parents=True, exist_ok=True)
        mode = "fast" if opts.fast else "balanced"
        marker_cmd = [
            str(marker),
            str(pdf_path),
            "--output_dir",
            str(work),
            "--output_format",
            "markdown",
            "--mode",
            mode,
        ]
        proc = subprocess.run(marker_cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(
                f"marker_single failed ({proc.returncode}):\n{proc.stderr or proc.stdout}"
            )

        md_path = find_marker_markdown(work, pdf_path.stem)
        markdown = md_path.read_text(encoding="utf-8")
        meta = resolve_metadata(
            pdf_path=pdf_path,
            markdown=markdown,
            title_override=opts.title,
            author_override=opts.author,
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        pandoc_cmd = build_pandoc_cmd(
            pandoc=pandoc, md_path=md_path, epub_path=out_path, meta=meta
        )
        proc2 = subprocess.run(pandoc_cmd, capture_output=True, text=True)
        if proc2.returncode != 0:
            raise RuntimeError(
                f"pandoc failed ({proc2.returncode}):\n{proc2.stderr or proc2.stdout}"
            )
        if not out_path.is_file():
            raise RuntimeError(f"pandoc reported success but EPUB missing: {out_path}")
        return out_path

    if opts.keep:
        keep_root = opts.work_dir or (pdf_path.parent / f"{pdf_path.stem}.pdf2epub")
        return _run(keep_root)

    if opts.work_dir is not None:
        return _run(opts.work_dir)

    with tempfile.TemporaryDirectory(prefix="pdf2epub-") as tmp:
        return _run(Path(tmp))
