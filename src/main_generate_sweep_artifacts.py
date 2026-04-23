"""
Official entrypoint to regenerate sweep artifacts (reports + plots).

`main_generate_sweep_plots` is kept as a backward-compatible alias.
"""

from __future__ import annotations

from src.main_generate_sweep_plots import generate_for_sweep, main

__all__ = ["main", "generate_for_sweep"]

if __name__ == "__main__":
    main()
