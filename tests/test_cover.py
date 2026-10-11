from pathlib import Path

from PIL import Image

from pdf2epub.cover import generate_cover_image


def test_generate_cover_image_writes_jpeg(tmp_path: Path):
    out = tmp_path / "cover.jpg"
    path = generate_cover_image(out, title="Cognification", author="Kevin Kelly")
    assert path == out
    assert out.is_file()
    assert out.stat().st_size > 1000
    with Image.open(out) as im:
        assert im.format == "JPEG"
        assert im.size[0] < im.size[1]  # portrait book cover
        assert im.size[0] >= 400


def test_generate_cover_image_works_without_author(tmp_path: Path):
    out = tmp_path / "cover.jpg"
    generate_cover_image(out, title="Untitled Paper", author=None)
    assert out.is_file()
    with Image.open(out) as im:
        assert im.format == "JPEG"


def test_generate_cover_image_wraps_long_title(tmp_path: Path):
    out = tmp_path / "cover.jpg"
    title = (
        "A Very Long Academic Paper Title That Should Wrap Across Multiple Lines "
        "Without Overflowing The Cover Edges"
    )
    generate_cover_image(out, title=title, author="Ada Lovelace")
    assert out.is_file()
