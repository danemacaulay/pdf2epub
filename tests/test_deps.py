from pathlib import Path
from unittest.mock import patch

import pytest

from pdf2epub.deps import (
    MissingDependencyError,
    check_conversion_deps,
    require_llama_server,
    require_marker_single,
    require_pandoc,
)


def test_require_pandoc_missing():
    with patch("pdf2epub.deps.which", return_value=None):
        with pytest.raises(MissingDependencyError) as ei:
            require_pandoc()
        assert "brew install pandoc" in str(ei.value)


def test_require_llama_missing():
    with patch("pdf2epub.deps.which", return_value=None):
        with pytest.raises(MissingDependencyError) as ei:
            require_llama_server()
        assert "brew install llama.cpp" in str(ei.value)


def test_check_skips_llama_when_fast():
    with patch("pdf2epub.deps.require_pandoc", return_value=Path("/bin/pandoc")):
        with patch("pdf2epub.deps.require_marker_single", return_value=Path("/bin/marker_single")):
            with patch("pdf2epub.deps.require_llama_server") as llama:
                check_conversion_deps(fast=True)
                llama.assert_not_called()


def test_check_requires_llama_when_balanced():
    with patch("pdf2epub.deps.require_pandoc", return_value=Path("/bin/pandoc")):
        with patch("pdf2epub.deps.require_marker_single", return_value=Path("/bin/marker_single")):
            with patch("pdf2epub.deps.require_llama_server", return_value=Path("/bin/llama-server")) as llama:
                check_conversion_deps(fast=False)
                llama.assert_called_once()
