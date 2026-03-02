from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import matplotlib.pyplot as plt


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate/re-generate Optuna top-k val/test metrics plot "
            "(RMSE, MAE, DA) from an Optuna sweep directory."
        )
    )
    parser.add_argument(
        "--sweep-dir",
        required=True,
        help=(
            "Directory containing optuna_summary.json. Example: "
            "data/models/AAPL/optuna/optuna_0_1_baseline_hpo/BASELINE_FEATURES"
        ),
    )
    return parser.parse_args()


def _load_top_entries(summary_path: Path) -> list[dict]:
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    top_k_json = summary.get("artifacts", {}).get("top_k_json")
    if not top_k_json:
        raise ValueError("optuna_summary.json does not contain artifacts.top_k_json")
    top_k_path = Path(top_k_json)
    if not top_k_path.is_absolute():
        top_k_path = (summary_path.parent / top_k_path).resolve()
    return json.loads(top_k_path.read_text(encoding="utf-8"))


def _save_plot(run_output_dir: Path, top_entries: list[dict]) -> Path:
    x = list(range(len(top_entries)))
    labels = [
        f"R{int(entry.get('rank', i + 1))} | T{int(entry.get('trial_number', i))}"
        for i, entry in enumerate(top_entries)
    ]

    metric_specs = [
        ("RMSE", "mean_val_rmse", "std_val_rmse", "mean_test_rmse", "std_test_rmse"),
        ("MAE", "mean_val_mae", "std_val_mae", "mean_test_mae", "std_test_mae"),
        ("DA", "mean_val_da", "std_val_da", "mean_test_da", "std_test_da"),
    ]

    fig, axes = plt.subplots(3, 1, figsize=(14, 14), sharex=True)
    axes = list(axes)

    for ax, (title, val_mean_key, val_std_key, test_mean_key, test_std_key) in zip(axes, metric_specs):
        val_mean: list[float] = []
        val_std: list[float] = []
        test_mean: list[float] = []
        test_std: list[float] = []

        for entry in top_entries:
            top_run = entry.get("top_run", {}) or {}
            val_m = top_run.get(val_mean_key)
            val_s = top_run.get(val_std_key)
            test_m = top_run.get(test_mean_key)
            test_s = top_run.get(test_std_key)

            val_mean.append(float(val_m) if val_m is not None else math.nan)
            val_std.append(float(val_s) if val_s is not None else 0.0)
            test_mean.append(float(test_m) if test_m is not None else math.nan)
            test_std.append(float(test_s) if test_s is not None else 0.0)

        val_low = [m - s if not math.isnan(m) else math.nan for m, s in zip(val_mean, val_std)]
        val_h = [2.0 * s if not math.isnan(m) else math.nan for m, s in zip(val_mean, val_std)]
        test_low = [m - s if not math.isnan(m) else math.nan for m, s in zip(test_mean, test_std)]
        test_h = [2.0 * s if not math.isnan(m) else math.nan for m, s in zip(test_mean, test_std)]
        val_x = [xi - 0.12 for xi in x]
        test_x = [xi + 0.12 for xi in x]

        ax.plot(x, val_mean, marker="o", linewidth=1.8, color="#1f77b4", label="val mean")
        ax.bar(
            val_x,
            val_h,
            bottom=val_low,
            width=0.22,
            color="#1f77b4",
            edgecolor="#1f77b4",
            linewidth=0.8,
            alpha=0.16,
            label="val +- std (box)",
        )
        ax.plot(x, test_mean, marker="s", linewidth=1.8, color="#ff7f0e", label="test mean")
        ax.bar(
            test_x,
            test_h,
            bottom=test_low,
            width=0.22,
            color="#ff7f0e",
            edgecolor="#ff7f0e",
            linewidth=0.8,
            alpha=0.16,
            label="test +- std (box)",
        )

        ax.set_title(f"{title} - Top-k Optuna Trials")
        ax.grid(True, linestyle="--", alpha=0.35)
        ax.legend(loc="best")

    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels(labels, rotation=40, ha="right")
    axes[-1].set_xlabel("Top-k ranking by objective value")
    fig.tight_layout()

    output_path = run_output_dir / "optuna_top_k_val_test_metrics.png"
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path


def main() -> None:
    args = _parse_args()
    summary_path = (Path(args.sweep_dir) / "optuna_summary.json").resolve()
    if not summary_path.exists():
        raise FileNotFoundError(f"Summary not found: {summary_path}")

    top_entries = _load_top_entries(summary_path)
    if not top_entries:
        raise ValueError("No top-k entries found to plot.")

    output_path = _save_plot(summary_path.parent, top_entries)
    print(f"Generated: {output_path}")


if __name__ == "__main__":
    main()
