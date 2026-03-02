from __future__ import annotations

"""
Official entrypoint to regenerate sweep artifacts (reports + plots).

`main_generate_sweep_plots` is kept as a backward-compatible alias.
"""

from src.main_generate_sweep_plots import generate_for_sweep, main


if __name__ == "__main__":
    main()
