from __future__ import annotations

import argparse
import json
import math
from pathlib import Path, PureWindowsPath

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


def _load_summary(summary_path: Path) -> dict:
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("optuna_summary.json root must be an object")
    return payload


def _resolve_artifact_path(summary_path: Path, path_str: str) -> Path:
    candidate = Path(path_str)
    if candidate.is_absolute() and candidate.exists():
        return candidate
    joined = (summary_path.parent / candidate).resolve()
    if joined.exists():
        return joined
    # Legacy compatibility: artifacts may contain absolute Windows paths.
    # Fallback to the same filename in the current sweep directory.
    windows_name = PureWindowsPath(path_str).name
    fallback_name = windows_name if windows_name else candidate.name
    fallback = (summary_path.parent / fallback_name).resolve()
    return fallback


def _load_top_entries(summary_path: Path) -> list[dict]:
    summary = _load_summary(summary_path)
    top_k_json = summary.get("artifacts", {}).get("top_k_json")
    if not top_k_json:
        raise ValueError("optuna_summary.json does not contain artifacts.top_k_json")
    top_k_path = _resolve_artifact_path(summary_path, str(top_k_json))
    return json.loads(top_k_path.read_text(encoding="utf-8"))


def _load_all_entries(summary_path: Path) -> list[dict]:
    summary = _load_summary(summary_path)
    trials_json = summary.get("artifacts", {}).get("trials_json")
    if not trials_json:
        return []
    trials_path = _resolve_artifact_path(summary_path, str(trials_json))
    if not trials_path.exists():
        return []
    trials = json.loads(trials_path.read_text(encoding="utf-8"))
    if not isinstance(trials, list):
        return []
    ranked = [
        t for t in trials
        if isinstance(t, dict) and t.get("objective_value") is not None
    ]
    ranked.sort(key=lambda item: float(item.get("objective_value", math.inf)))
    all_entries: list[dict] = []
    for idx, item in enumerate(ranked, start=1):
        all_entries.append(
            {
                "rank": idx,
                "trial_number": int(item.get("trial_number", idx - 1)),
                "top_run": item.get("top_run", {}) or {},
            }
        )
    return all_entries


def _save_plot(
    run_output_dir: Path,
    entries: list[dict],
    *,
    filename: str,
    plot_title_suffix: str,
    x_axis_label: str,
) -> Path | None:
    if not entries:
        return None

    x = list(range(len(entries)))
    labels = [
        f"R{int(entry.get('rank', i + 1))} | T{int(entry.get('trial_number', i))}"
        for i, entry in enumerate(entries)
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

        for entry in entries:
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

        ax.set_title(f"{title} - {plot_title_suffix}")
        ax.grid(True, linestyle="--", alpha=0.35)
        ax.legend(loc="best")

    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels(labels, rotation=40, ha="right")
    axes[-1].set_xlabel(x_axis_label)
    fig.tight_layout()

    output_path = run_output_dir / filename
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path


def main() -> None:
    args = _parse_args()
    summary_path = (Path(args.sweep_dir) / "optuna_summary.json").resolve()
    if not summary_path.exists():
        raise FileNotFoundError(f"Summary not found: {summary_path}")
    summary = _load_summary(summary_path)

    top_entries = _load_top_entries(summary_path)
    if not top_entries:
        raise ValueError("No top-k entries found to plot.")

    top_output = _save_plot(
        summary_path.parent,
        top_entries,
        filename="optuna_top_k_val_test_metrics.png",
        plot_title_suffix="Top-k Optuna Trials",
        x_axis_label="Top-k ranking by objective value",
    )
    if top_output is not None:
        print(f"Generated: {top_output}")
        artifacts = summary.get("artifacts")
        if not isinstance(artifacts, dict):
            artifacts = {}
            summary["artifacts"] = artifacts
        artifacts["top_k_val_test_metrics_plot_png"] = str(top_output.resolve())

    all_entries = _load_all_entries(summary_path)
    all_output = _save_plot(
        summary_path.parent,
        all_entries,
        filename="optuna_all_trials_val_test_metrics.png",
        plot_title_suffix="All Optuna Trials",
        x_axis_label="Trial ranking by objective value",
    )
    if all_output is not None:
        print(f"Generated: {all_output}")
        artifacts = summary.get("artifacts")
        if not isinstance(artifacts, dict):
            artifacts = {}
            summary["artifacts"] = artifacts
        artifacts["all_trials_val_test_metrics_plot_png"] = str(all_output.resolve())

    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
