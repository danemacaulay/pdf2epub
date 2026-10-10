from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pdf2epub.convert import ConvertOptions, convert_pdf
from pdf2epub.deps import MissingDependencyError


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pdf2epub",
        description="Convert a PDF to a reflowable EPUB via Marker + Pandoc.",
    )
    p.add_argument("pdf", type=Path, help="Input PDF path")
    p.add_argument("--out", type=Path, default=None, help="Output EPUB path")
    p.add_argument("--title", default=None, help="Override title")
    p.add_argument("--author", default=None, help="Override author")
    p.add_argument(
        "--fast",
        action="store_true",
        help="Use Marker fast mode (skip llama-server; lower quality)",
    )
    p.add_argument(
        "--keep",
        action="store_true",
        help="Keep intermediate Marker markdown/images beside the PDF",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        return int(e.code) if e.code is not None else 2

    opts = ConvertOptions(
        pdf_path=args.pdf,
        out_path=args.out,
        title=args.title,
        author=args.author,
        fast=args.fast,
        keep=args.keep,
    )
    try:
        out = convert_pdf(opts)
    except MissingDependencyError as e:
        print(str(e), file=sys.stderr)
        return 2
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Conversion failed: {e}", file=sys.stderr)
        return 1
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
