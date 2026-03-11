from __future__ import annotations

import math

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ExplicitSweepAnalysisArtifacts:
    ranking_oos: pd.DataFrame
    robustness: pd.DataFrame
    generalization_gap: pd.DataFrame
    consistency: pd.DataFrame
    heatmap_test_rmse: pd.DataFrame
    confidence_intervals: pd.DataFrame
    dm_pairwise: pd.DataFrame
    mcs_result: pd.DataFrame
    mcs_trace: pd.DataFrame


class ExplicitConfigSweepAnalysisService:
    @staticmethod
    def _norm_cdf(x: float) -> float:
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

    @staticmethod
    def _parse_config_label(run_label: str) -> str:
        value = str(run_label)
        if "|seed=" in value:
            return value.split("|seed=", 1)[0]
        return value

    @staticmethod
    def _parse_seed(run_label: str) -> int | None:
        value = str(run_label)
        marker = "|seed="
        if marker not in value:
            return None
        token = value.split(marker, 1)[1].split("|", 1)[0].strip()
        try:
            return int(token)
        except Exception:
            return None

    @classmethod
    def build_run_level_tables(cls, run_df: pd.DataFrame) -> ExplicitSweepAnalysisArtifacts:
        ok = run_df[run_df["status"] == "ok"].copy()
        if ok.empty:
            empty = pd.DataFrame()
            return ExplicitSweepAnalysisArtifacts(
                ranking_oos=empty,
                robustness=empty,
                generalization_gap=empty,
                consistency=empty,
                heatmap_test_rmse=empty,
                confidence_intervals=empty,
                dm_pairwise=empty,
                mcs_result=empty,
                mcs_trace=empty,
            )

        ok["config_label"] = ok["run_label"].astype(str).map(cls._parse_config_label)
        ok["seed"] = ok["run_label"].astype(str).map(cls._parse_seed)
        for c in ["val_rmse", "val_mae", "val_da", "test_rmse", "test_mae", "test_da"]:
            ok[c] = pd.to_numeric(ok[c], errors="coerce")

        ranking = (
            ok.groupby(["config_signature", "config_label"], dropna=False)
            .agg(
                n_runs=("run_label", "count"),
                mean_val_rmse=("val_rmse", "mean"),
                mean_val_mae=("val_mae", "mean"),
                mean_val_da=("val_da", "mean"),
                mean_test_rmse=("test_rmse", "mean"),
                mean_test_mae=("test_mae", "mean"),
                mean_test_da=("test_da", "mean"),
            )
            .reset_index()
            .sort_values(["mean_test_rmse", "mean_test_mae", "mean_test_da"], ascending=[True, True, False])
            .reset_index(drop=True)
        )

        robustness = (
            ok.groupby(["config_signature", "config_label"], dropna=False)
            .agg(
                std_test_rmse=("test_rmse", "std"),
                std_test_mae=("test_mae", "std"),
                std_test_da=("test_da", "std"),
                iqr_test_rmse=("test_rmse", lambda s: float(np.nanpercentile(s, 75) - np.nanpercentile(s, 25))),
                iqr_test_mae=("test_mae", lambda s: float(np.nanpercentile(s, 75) - np.nanpercentile(s, 25))),
                iqr_test_da=("test_da", lambda s: float(np.nanpercentile(s, 75) - np.nanpercentile(s, 25))),
            )
            .reset_index()
        )

        ok["gap_rmse_test_minus_val"] = ok["test_rmse"] - ok["val_rmse"]
        ok["gap_mae_test_minus_val"] = ok["test_mae"] - ok["val_mae"]
        ok["gap_da_test_minus_val"] = ok["test_da"] - ok["val_da"]
        gap = (
            ok.groupby(["config_signature", "config_label"], dropna=False)[
                ["gap_rmse_test_minus_val", "gap_mae_test_minus_val", "gap_da_test_minus_val"]
            ]
            .mean()
            .reset_index()
        )

        unit = ok.dropna(subset=["fold_name", "seed"]).copy()
        unit["rank_rmse"] = unit.groupby(["fold_name", "seed"])["test_rmse"].rank(method="min", ascending=True)
        consistency = (
            unit.groupby(["config_signature", "config_label"], dropna=False)["rank_rmse"]
            .agg(
                top1_rate=lambda s: float(np.mean(s <= 1)),
                top3_rate=lambda s: float(np.mean(s <= 3)),
                top5_rate=lambda s: float(np.mean(s <= 5)),
            )
            .reset_index()
        )

        heatmap = (
            ok.groupby(["config_label", "fold_name"], dropna=False)["test_rmse"]
            .mean()
            .reset_index()
            .pivot(index="config_label", columns="fold_name", values="test_rmse")
            .sort_index()
        )

        ci_rows: list[dict[str, Any]] = []
        for (cfg_sig, cfg_lbl), grp in ok.groupby(["config_signature", "config_label"], dropna=False):
            for metric in ["test_rmse", "test_mae", "test_da"]:
                values = pd.to_numeric(grp[metric], errors="coerce").dropna().to_numpy(dtype=float)
                if len(values) == 0:
                    continue
                mean = float(np.mean(values))
                std = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
                se = std / math.sqrt(len(values)) if len(values) > 0 else float("nan")
                half = 1.96 * se if math.isfinite(se) else float("nan")
                ci_rows.append(
                    {
                        "config_signature": cfg_sig,
                        "config_label": cfg_lbl,
                        "metric": metric,
                        "n": int(len(values)),
                        "mean": mean,
                        "std": std,
                        "ci95_low": float(mean - half),
                        "ci95_high": float(mean + half),
                    }
                )
        ci_df = pd.DataFrame(ci_rows)

        empty = pd.DataFrame()
        return ExplicitSweepAnalysisArtifacts(
            ranking_oos=ranking,
            robustness=robustness,
            generalization_gap=gap,
            consistency=consistency,
            heatmap_test_rmse=heatmap,
            confidence_intervals=ci_df,
            dm_pairwise=empty,
            mcs_result=empty,
            mcs_trace=empty,
        )

    @classmethod
    def compute_dm_and_mcs(
        cls,
        predictions_df: pd.DataFrame,
        *,
        alpha: float = 0.05,
        bootstrap_samples: int = 300,
        block_len: int = 5,
        random_seed: int = 42,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        if predictions_df.empty:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        pred = predictions_df.copy()
        pred["config_label"] = pred["run_label"].astype(str).map(cls._parse_config_label)
        pred["squared_error"] = pd.to_numeric(pred["squared_error"], errors="coerce")
        agg = (
            pred.groupby(["fold_name", "timestamp", "config_label"], dropna=False)["squared_error"]
            .mean()
            .reset_index()
        )
        loss_matrix = agg.pivot(index=["fold_name", "timestamp"], columns="config_label", values="squared_error")
        loss_matrix = loss_matrix.dropna(axis=0, how="any")
        if loss_matrix.empty or loss_matrix.shape[1] < 2:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        dm_rows: list[dict[str, Any]] = []
        configs = loss_matrix.columns.tolist()
        for i, left in enumerate(configs):
            for right in configs[i + 1 :]:
                d = (loss_matrix[left] - loss_matrix[right]).to_numpy(dtype=float)
                d = d[np.isfinite(d)]
                n = len(d)
                if n < 5:
                    continue
                mean_d = float(np.mean(d))
                d_centered = d - mean_d
                lag = int(min(max(1, n ** (1 / 3)), 10))
                gamma0 = float(np.dot(d_centered, d_centered) / n)
                hac = gamma0
                for k in range(1, lag + 1):
                    cov = float(np.dot(d_centered[k:], d_centered[:-k]) / n)
                    weight = 1.0 - (k / (lag + 1))
                    hac += 2.0 * weight * cov
                var_mean = hac / n
                if var_mean <= 0 or not math.isfinite(var_mean):
                    continue
                stat = mean_d / math.sqrt(var_mean)
                pvalue = 2.0 * (1.0 - cls._norm_cdf(abs(stat)))
                dm_rows.append(
                    {
                        "left_config": left,
                        "right_config": right,
                        "n": n,
                        "mean_loss_diff_left_minus_right": mean_d,
                        "dm_stat": stat,
                        "pvalue_two_sided": pvalue,
                    }
                )
        dm_df = pd.DataFrame(dm_rows).sort_values("pvalue_two_sided") if dm_rows else pd.DataFrame()

        mean_loss = loss_matrix.mean(axis=0).sort_values()
        configs_order = mean_loss.index.tolist()
        mat = loss_matrix[configs_order].to_numpy(dtype=float)
        rng = np.random.default_rng(random_seed)

        active = list(range(mat.shape[1]))
        trace_rows: list[dict[str, Any]] = []

        def _block_bootstrap_indices(n_obs: int) -> np.ndarray:
            idx: list[int] = []
            while len(idx) < n_obs:
                start = int(rng.integers(0, n_obs))
                block = [(start + o) % n_obs for o in range(block_len)]
                idx.extend(block)
            return np.asarray(idx[:n_obs], dtype=int)

        while len(active) > 1:
            sub = mat[:, active]
            n_obs, n_models = sub.shape
            dbar = np.zeros((n_models, n_models), dtype=float)
            for i in range(n_models):
                for j in range(n_models):
                    dbar[i, j] = float(np.mean(sub[:, i] - sub[:, j]))

            boot = np.zeros((bootstrap_samples, n_models, n_models), dtype=float)
            for b in range(bootstrap_samples):
                idx = _block_bootstrap_indices(n_obs)
                sample = sub[idx, :]
                for i in range(n_models):
                    for j in range(n_models):
                        boot[b, i, j] = float(np.mean(sample[:, i] - sample[:, j]))
            var = np.var(boot, axis=0, ddof=1)
            var[var <= 1e-12] = np.nan

            tmat = np.abs(dbar / np.sqrt(var))
            if np.isnan(tmat).all():
                break
            tr_stat = float(np.nanmax(tmat))
            boot_centered = boot - dbar[None, :, :]
            tboot = np.abs(boot_centered / np.sqrt(var)[None, :, :])
            tr_boot = np.array(
                [
                    (float(np.nanmax(tb)) if not np.isnan(tb).all() else float("nan"))
                    for tb in tboot
                ],
                dtype=float,
            )
            tr_boot = tr_boot[np.isfinite(tr_boot)]
            if len(tr_boot) == 0:
                break
            pvalue = float(np.mean(tr_boot >= tr_stat))

            if pvalue >= alpha or not np.isfinite(pvalue):
                break

            losses_mean = np.mean(sub, axis=0)
            worst_local = int(np.argmax(losses_mean))
            worst_global = active[worst_local]
            trace_rows.append(
                {
                    "step": len(trace_rows) + 1,
                    "removed_config": configs_order[worst_global],
                    "tr_stat": tr_stat,
                    "pvalue": pvalue,
                }
            )
            active.pop(worst_local)

        selected = [configs_order[i] for i in active]
        mcs_result = pd.DataFrame(
            {
                "config_label": configs_order,
                "selected_in_mcs_alpha_0_05": [c in selected for c in configs_order],
                "mean_loss": [float(mean_loss[c]) for c in configs_order],
            }
        )
        mcs_trace = pd.DataFrame(trace_rows)
        return dm_df, mcs_result, mcs_trace
