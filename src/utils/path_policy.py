from __future__ import annotations

import os

from pathlib import Path


def project_root() -> Path:
    # src/utils/path_policy.py -> project root is parents[2]
    return Path(__file__).resolve().parents[2]


def to_project_relative(path_value: str | Path | None) -> str | None:
    if path_value is None:
        return None
    text = str(path_value).strip()
    if not text:
        return text

    root = project_root()
    raw = Path(text).expanduser()
    abs_path = raw if raw.is_absolute() else (root / raw)
    abs_norm = abs_path.resolve(strict=False)
    rel = os.path.relpath(str(abs_norm), str(root))
    return Path(rel).as_posix()

