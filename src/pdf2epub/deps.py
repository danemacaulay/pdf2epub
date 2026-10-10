from __future__ import annotations

import shutil
from pathlib import Path


class MissingDependencyError(RuntimeError):
    def __init__(self, name: str, hint: str):
        self.name = name
        self.hint = hint
        super().__init__(f"Missing dependency: {name}\n{hint}")


def which(name: str) -> Path | None:
    found = shutil.which(name)
    return Path(found) if found else None


def require_pandoc() -> Path:
    path = which("pandoc")
    if path is None:
        raise MissingDependencyError("pandoc", "Install with: brew install pandoc")
    return path


def require_marker_single() -> Path:
    path = which("marker_single")
    if path is None:
        raise MissingDependencyError(
            "marker_single",
            "Install this package in an environment with marker-pdf:\n  pip install pdf2epub",
        )
    return path


def require_llama_server() -> Path:
    path = which("llama-server")
    if path is None:
        raise MissingDependencyError(
            "llama-server",
            "Required for balanced mode. Install with: brew install llama.cpp\n"
            "Or pass --fast to skip (lower quality).",
        )
    return path


def check_conversion_deps(*, fast: bool) -> None:
    require_pandoc()
    require_marker_single()
    if not fast:
        require_llama_server()
