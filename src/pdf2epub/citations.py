"""Link numeric in-text citations to their bibliography entries.

Marker emits in-text citations as plain ``[12]`` / ``<sup>12</sup>`` text and
flattens the reference list into run-together paragraphs. This module rewrites
the markdown so pandoc produces ``epub:type="biblioref"`` links pointing at
``epub:type="biblioentry"`` divs, which EPUB readers (Readest, Apple Books, ...)
show as tap-to-view popups.
"""

from __future__ import annotations

import re

from pdf2epub.metadata import strip_md_emphasis

REF_ATTRS = 'epub:type="biblioref" role="doc-biblioref"'
ENTRY_ATTRS = 'epub:type="biblioentry" role="doc-biblioentry"'

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_REF_TITLE_RE = re.compile(
    r"^(?:\d+(?:\.\d+)*\.?\s*)?"
    r"(references|reference list|bibliography|works cited|literature cited)\s*:?$",
    re.I,
)
_ENTRY_MARKER_RE = re.compile(r"\[(\d{1,4})\]")
_NUM_GROUP = r"\d{1,4}(?:\s*[,;\u2013\u2014-]\s*\d{1,4})*"
_BRACKET_CITE_RE = re.compile(rf"\[({_NUM_GROUP})\]")
_SUP_CITE_RE = re.compile(rf"(?<!\d)<sup>({_NUM_GROUP})</sup>")
_NUM_TOKEN_RE = re.compile(r"(\d+)")


def link_citations(markdown: str) -> str:
    """Return ``markdown`` with citations linked to anchored bibliography entries.

    Returns the input unchanged when no numbered references section is found.
    """
    lines = markdown.splitlines(keepends=True)
    section = _find_references_section(lines)
    if section is None:
        return markdown
    heading_idx, body_start, body_end = section

    parsed = _parse_entries("".join(lines[body_start:body_end]))
    if parsed is None:
        return markdown
    preamble, entries = parsed
    known = {n for n, _ in entries}

    before = _link_body("".join(lines[:heading_idx]), known)
    after = _link_body("".join(lines[body_end:]), known)
    heading = lines[heading_idx]
    if not heading.endswith("\n"):
        heading += "\n"
    return before + heading + _render_entries(preamble, entries) + after


def _find_references_section(lines: list[str]) -> tuple[int, int, int] | None:
    """Return (heading index, body start, body end) of the references section."""
    for i, line in enumerate(lines):
        m = _HEADING_RE.match(line.rstrip("\n"))
        if not m:
            continue
        if not _REF_TITLE_RE.match(strip_md_emphasis(m.group(2))):
            continue
        end = len(lines)
        for j in range(i + 1, len(lines)):
            if _HEADING_RE.match(lines[j].rstrip("\n")):
                end = j
                break
        return i, i + 1, end
    return None


def _parse_entries(body: str) -> tuple[str, list[tuple[int, str]]] | None:
    """Split the references body into (preamble, [(number, entry text)]).

    Entries may be split across paragraphs by page breaks, so whitespace is
    normalised first. Only markers that continue the 1, 2, 3, ... sequence
    start a new entry; any other ``[N]`` is treated as part of the entry text.
    """
    text = re.sub(r"\s+", " ", body).strip()
    starts: list[tuple[int, int]] = []
    expected = 1
    for m in _ENTRY_MARKER_RE.finditer(text):
        if int(m.group(1)) == expected:
            starts.append((expected, m.start()))
            expected += 1
    if not starts:
        return None
    preamble = text[: starts[0][1]].strip()
    entries: list[tuple[int, str]] = []
    for idx, (number, pos) in enumerate(starts):
        end = starts[idx + 1][1] if idx + 1 < len(starts) else len(text)
        entries.append((number, text[pos:end].strip()))
    return preamble, entries


def _render_entries(preamble: str, entries: list[tuple[int, str]]) -> str:
    parts = ["\n"]
    if preamble:
        parts.append(f"{preamble}\n\n")
    for number, text in entries:
        parts.append(f"::: {{#ref-{number} {ENTRY_ATTRS}}}\n{text}\n:::\n\n")
    return "".join(parts)


def _link_number(number: str, text: str | None = None) -> str:
    return f"[{text or number}](#ref-{number}){{{REF_ATTRS}}}"


def _link_group(inner: str, known: set[int]) -> str | None:
    """Link every number in a citation group; None if any number is unknown."""
    tokens = _NUM_TOKEN_RE.split(inner)
    numbers = [t for t in tokens if t.isdigit()]
    if any(int(n) not in known for n in numbers):
        return None
    return "".join(_link_number(t) if t.isdigit() else t for t in tokens)


def _link_body(text: str, known: set[int]) -> str:
    if not text:
        return text

    def bracket(m: re.Match[str]) -> str:
        inner = m.group(1)
        if inner.isdigit():
            if int(inner) not in known:
                return m.group(0)
            return _link_number(inner, f"[{inner}]")
        linked = _link_group(inner, known)
        return m.group(0) if linked is None else f"[{linked}]"

    def sup(m: re.Match[str]) -> str:
        linked = _link_group(m.group(1), known)
        return m.group(0) if linked is None else f"<sup>{linked}</sup>"

    text = _BRACKET_CITE_RE.sub(bracket, text)
    return _SUP_CITE_RE.sub(sup, text)
