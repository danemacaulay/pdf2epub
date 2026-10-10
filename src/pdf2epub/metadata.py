from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

_EMPHASIS_RE = re.compile(r"[*_`]+")
_GARBAGE_TITLE_RE = re.compile(
    r"^(untitled|document1|microsoft word\b.*|adobe photoshop\b.*)$",
    re.I,
)


@dataclass(frozen=True)
class BookMeta:
    title: str
    author: str | None


def strip_md_emphasis(text: str) -> str:
    return _EMPHASIS_RE.sub("", text).strip()


def is_garbage_pdf_field(value: str | None) -> bool:
    if value is None:
        return True
    cleaned = value.strip()
    if not cleaned:
        return True
    return bool(_GARBAGE_TITLE_RE.match(cleaned))


def parse_markdown_heuristics(markdown: str) -> BookMeta:
    lines = markdown.splitlines()
    title: str | None = None
    author: str | None = None
    for i, raw in enumerate(lines):
        line = raw.strip()
        if title is None and line.startswith("# "):
            title = strip_md_emphasis(line[2:].strip())
            for j in range(i + 1, min(i + 6, len(lines))):
                cand = strip_md_emphasis(lines[j].strip())
                if not cand:
                    continue
                if cand.startswith("#"):
                    break
                if _looks_like_author_line(cand):
                    author = _normalize_author_line(cand)
                break
            break
    if not title:
        title = "Untitled"
    return BookMeta(title=title, author=author)


def _looks_like_author_line(line: str) -> bool:
    if len(line) > 180:
        return False
    if line.lower().startswith("abstract"):
        return False
    return bool(re.search(r"[A-Za-z].*[A-Za-z]", line)) and (
        "," in line
        or " and " in line.lower()
        or re.search(r"\b(university|institute|laboratory|lab)\b", line, re.I)
        or bool(re.match(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z.\-]+)+", line))
    )


def _normalize_author_line(line: str) -> str:
    for sep in ("*", " - ", " – ", " — "):
        if sep in line:
            left = line.split(sep, 1)[0].strip()
            if left and ("," in left or " " in left):
                line = left
                break
    return re.sub(r"\s+", " ", line).strip()


def read_pdf_info(pdf_path: Path) -> BookMeta:
    reader = PdfReader(str(pdf_path))
    info = reader.metadata or {}
    title = info.get("/Title") if info else None
    author = info.get("/Author") if info else None
    title_s = str(title).strip() if title else ""
    author_s = str(author).strip() if author else ""
    return BookMeta(
        title="" if is_garbage_pdf_field(title_s) else title_s,
        author=None if is_garbage_pdf_field(author_s) else author_s,
    )


def resolve_metadata(
    *,
    pdf_path: Path,
    markdown: str,
    title_override: str | None = None,
    author_override: str | None = None,
) -> BookMeta:
    pdf_meta = read_pdf_info(pdf_path)
    md_meta = parse_markdown_heuristics(markdown)

    if title_override:
        title = title_override
    elif pdf_meta.title:
        title = pdf_meta.title
    elif md_meta.title and md_meta.title != "Untitled":
        title = md_meta.title
    else:
        title = pdf_path.stem

    if author_override:
        author = author_override
    elif pdf_meta.author:
        author = pdf_meta.author
    else:
        author = md_meta.author

    return BookMeta(title=title.strip(), author=author.strip() if author else None)
