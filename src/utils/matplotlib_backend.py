from __future__ import annotations

import os


def ensure_non_interactive_matplotlib_backend() -> None:
    """
    Force a non-interactive backend for headless/CLI execution.

    This avoids Tk-related crashes (SIGABRT) when plot objects are finalized
    outside the main UI thread during batch training/sweeps.
    """
    os.environ.setdefault("MPLBACKEND", "Agg")
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
    except Exception:
        # Plot callers already handle ImportError/optional matplotlib usage.
        return
