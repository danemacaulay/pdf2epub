from pdf2epub.citations import REF_ATTRS, link_citations

ENTRY_ATTRS = 'epub:type="biblioentry" role="doc-biblioentry"'


def _link(n: int, text: str | None = None) -> str:
    return f"[{text or n}](#ref-{n}){{{REF_ATTRS}}}"


BIB = (
    "# **6. References**\n\n"
    "[1] Levin I. (2024). Cultural transformations. [2] Kelly, K. (2016). "
    "The Inevitable. [3] Harari, Y. (2017). Homo Deus.\n"
)


def test_returns_unchanged_without_references_section():
    md = "# Intro\n\nSee [1] for details.\n"
    assert link_citations(md) == md


def test_wraps_each_reference_entry_in_anchored_div():
    out = link_citations(BIB)
    assert f"::: {{#ref-1 {ENTRY_ATTRS}}}\n[1] Levin I. (2024). Cultural transformations.\n:::" in out
    assert f"::: {{#ref-2 {ENTRY_ATTRS}}}\n[2] Kelly, K. (2016). The Inevitable.\n:::" in out
    assert f"::: {{#ref-3 {ENTRY_ATTRS}}}\n[3] Harari, Y. (2017). Homo Deus.\n:::" in out


def test_entry_split_across_paragraphs_is_rejoined():
    md = (
        "# References\n\n"
        "[1] Levin I. (2024). Cultural\n\n"
        "transformations of society. [2] Kelly, K. (2016).\n"
    )
    out = link_citations(md)
    assert "[1] Levin I. (2024). Cultural transformations of society.\n:::" in out
    assert "::: {#ref-2" in out


def test_links_single_bracket_citation_in_body():
    md = "# Intro\n\nAs shown in [2]. Also [3].\n\n" + BIB
    out = link_citations(md)
    assert f"As shown in {_link(2, '[2]')}. Also {_link(3, '[3]')}." in out


def test_links_each_number_in_grouped_citation():
    md = "# Intro\n\nSee [1, 3] and [2;3].\n\n" + BIB
    out = link_citations(md)
    assert f"See [{_link(1)}, {_link(3)}] and [{_link(2)};{_link(3)}]." in out


def test_links_range_endpoints():
    md = "# Intro\n\nSee [1–3] and [1-2].\n\n" + BIB
    out = link_citations(md)
    assert f"See [{_link(1)}–{_link(3)}] and [{_link(1)}-{_link(2)}]." in out


def test_leaves_unmatched_and_nonnumeric_brackets_alone():
    md = "# Intro\n\nSee [9] and [Paper presentation] and [1, 9].\n\n" + BIB
    out = link_citations(md)
    assert "See [9] and [Paper presentation] and [1, 9]." in out


def test_links_superscript_citations():
    md = "# Intro\n\nAs shown<sup>2</sup> and here<sup>1,3</sup>.\n\n" + BIB
    out = link_citations(md)
    assert f"As shown<sup>{_link(2)}</sup> and here<sup>{_link(1)},{_link(3)}</sup>." in out


def test_skips_superscript_following_a_digit():
    md = "# Intro\n\nAbout 10<sup>2</sup> units.\n\n" + BIB
    out = link_citations(md)
    assert "About 10<sup>2</sup> units." in out


def test_does_not_link_markers_inside_references_section():
    out = link_citations(BIB)
    assert "#ref-1){" not in out
    assert "[1] Levin" in out


def test_only_accepts_sequential_entry_markers():
    md = "# References\n\n[1] Levin I. See also [5] elsewhere. [2] Kelly, K.\n"
    out = link_citations(md)
    assert "[1] Levin I. See also [5] elsewhere.\n:::" in out
    assert "::: {#ref-5" not in out
    assert "::: {#ref-2" in out


def test_recognizes_heading_variants():
    for heading in ("## **References**", "# 6. References", "# Bibliography", "### Works Cited"):
        md = f"# Intro\n\nSee [1].\n\n{heading}\n\n[1] Levin I. (2024).\n"
        out = link_citations(md)
        assert "::: {#ref-1" in out, heading
        assert _link(1, "[1]") in out, heading


def test_references_section_ends_at_next_heading():
    md = (
        "# Intro\n\nSee [1].\n\n"
        + BIB
        + "\n# Appendix\n\nMore on [2] here.\n"
    )
    out = link_citations(md)
    assert f"More on {_link(2, '[2]')} here." in out
    assert "::: {#ref-2" in out
    assert out.count(":::") == 6


def test_preserves_text_before_first_entry():
    md = "# References\n\nNote: all URLs accessed 2024.\n\n[1] Levin I. (2024).\n"
    out = link_citations(md)
    assert "Note: all URLs accessed 2024." in out
    assert "::: {#ref-1" in out


def test_returns_unchanged_when_section_has_no_numbered_entries():
    md = "# Intro\n\nSee [1].\n\n# References\n\nLevin, I. (2024). Cultural transformations.\n"
    assert link_citations(md) == md
