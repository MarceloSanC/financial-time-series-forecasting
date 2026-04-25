# Sweep 0_2_3 - Plot Analysis Log

## Scope
- Asset: `AAPL`
- Plot scope: `parent_sweep_id` prefix `0_2_3_`
- Output directory:
  - `data/analytics/reports/prediction_analysis_plots/asset=AAPL_scope_0_2_3`

## Analysis Protocol
- Always interpret plots only inside the same scoped cohort (`0_2_3_`).
- For ranking conclusions, do not use a single plot alone.
- Cross-check with:
  - `gold_dm_pairwise_results.parquet`
  - `gold_mcs_results.parquet`
  - `gold_win_rate_pairwise_results.parquet`
  - `gold_model_decision_final.parquet`

## Plot 1 - `fig_boxplot_error_by_fold_seed` (h+1)
- Main reading:
  - RMSE values are very close across candidates (tight range around ~`0.01335` to `0.01341`).
  - No large separation between models by point estimate alone.
- Interpretation:
  - The cohort appears performance-homogeneous for `h+1` under RMSE.
  - This suggests model choice should be based on statistical dominance/stability, not only mean RMSE.
- Decision impact:
  - This plot alone is insufficient to declare a robust winner.
  - Must be combined with DM, MCS, win-rate and calibration quality.

## Plot 2 - `fig_calibration_curve` (h+1)
- Main reading:
  - Nominal coverage: `0.8`
  - Observed coverage (PICP): approximately `0.75`
  - Point is below the ideal diagonal.
- Interpretation:
  - Quantile intervals are under-calibrated for `h+1` (under-coverage by ~5 p.p.).
  - Prediction intervals are somewhat optimistic (too narrow for target nominal coverage).
- Decision impact:
  - Calibration is materially better than degenerate cases (e.g., `PICP=0`), but still not ideal.
  - Report the under-coverage explicitly in final academic discussion and compare with MPIW.

## Plot 3 - `fig_dm_pvalue_matrix` (h+1)
- Main reading:
  - Most cells are high p-values (near `1.0`), with only sparse low p-value regions.
  - Matrix pattern appears in blocks, indicating groups of similar model configurations.
- Interpretation:
  - For most model pairs, DM test does not reject equal predictive accuracy.
  - There are only limited pairwise comparisons with clear statistical separation.
- Decision impact:
  - This plot does not support a single dominant winner by DM alone.
  - Final model choice should combine MCS membership, pairwise win-rate consistency, and calibration/risk quality.


## Plot 4 - `fig_feature_importance_global_all_features` (h+1)
- Main reading:
  - All features are visible in a single ranking by `|mean_delta_rmse|`.
  - Values are concentrated in a narrow band (approximately ~`0.011` to `0.012`).
  - The ordering exists, but the top-to-bottom gap is small.
- Interpretation:
  - There is no single dominant feature and no clearly irrelevant feature in this cohort/horizon.
  - The model behavior is consistent with distributed signal usage (combination effect), not single-feature dependence.
  - Fine-grained rank interpretation (1st vs 2nd vs 3rd) should be treated as low-confidence.
- Decision impact:
  - Use this plot to support a "diffuse global importance" conclusion, not a strong causal claim per feature.
  - Prefer grouped interpretation by feature families (baseline/technical/sentiment/fundamental).
  - Final selection should still be driven by paired statistics + calibration/risk, with feature importance as explanatory support.

### Practical readability note (for this plot)
- This full-features version is less intuitive for direct decision-making because bar differences are very small.
- Recommended usage:
  - keep this figure as completeness artifact,
  - use the top-k plot for communication,
  - add a complementary table/plot aggregated by feature family for interpretation clarity.


## Plot 5 - `fig_interval_width_vs_coverage` (h+1)
- How to read:
  - Each point is one model/config.
  - X-axis (`MPIW`) = mean interval width (p10-p90).
  - Y-axis (`PICP`) = observed coverage (how often the true value falls inside p10-p90).
- Main reading:
  - Clear positive relation: wider intervals -> higher coverage.
  - This is the expected uncertainty trade-off.
  - The scatter suggests different behavior regimes (distinct point clouds) across model families.
- Interpretation:
  - Higher coverage is not automatically better if it comes from very wide intervals.
  - Narrow intervals are more informative, but can under-cover.
- Decision impact:
  - Best candidates are near target nominal coverage (for p10-p90, target around `0.8`) with the smallest possible `MPIW`.
  - Selection criterion should avoid both extremes:
    - under-coverage with narrow intervals,
    - over-conservative wide intervals.

### Simplified explanation for presentation
- Moving right means: "the model gives a wider uncertainty band".
- Moving up means: "the band contains the true value more often".
- Good decision = closest to desired coverage while keeping the band as narrow as possible.


## Plot 6 - `fig_oos_timeseries_examples` (h+1)
- How to read:
  - Blue line (`y_true`) = realized return.
  - Orange line (`y_pred/p50`) = median forecast.
  - Shaded area (`p10-p90`) = predictive interval.
- Main reading:
  - `y_true` shows high short-term volatility with positive/negative spikes.
  - `y_pred/p50` stays near zero with much lower amplitude.
  - `p10-p90` band is relatively wide and fairly stable over time.
- Interpretation:
  - The model median forecast is conservative and mean-reverting (low sensitivity to extremes).
  - It under-represents spike magnitude in the central forecast.
  - Uncertainty band captures risk context better than point forecast captures timing/amplitude.
- Decision impact:
  - Useful as probabilistic baseline and risk-aware signal.
  - Limited for precise short-term extreme-event timing.
  - Should be interpreted jointly with calibration metrics (PICP) and interval width (MPIW).

### Defense-ready summary
- The model provides conservative central forecasts near zero and wider uncertainty bands; it favors probabilistic stability over sharp short-horizon extreme-move tracking.

## Next Plots To Analyze
- `fig_heatmap_metrics_by_horizon`
- `fig_feature_contrib_local_cases`

## Analysis Template (for each next plot)
- Plot:
- What it shows:
- Key quantitative signal:
- Statistical caveat:
- Decision impact:



## Consolidated interpretation note - feature set comparison meaning
- What can be stated safely from current plots/results:
  - In this scoped cohort (`0_2_3`) and current focus (`h+1`), differences across candidates are generally small in point metrics.
  - Statistical evidence is often insufficient to claim a single robust dominant feature-set combination.
- What cannot be concluded:
  - It is not correct to conclude that "all feature sets are equivalent" or that feature choice never matters.
- Correct interpretation:
  - Current evidence is inconclusive for strong dominance claims under this specific experimental slice.
  - True differences may exist but be small, context-dependent, or underpowered in this setup.
- Recommended next checks to test feature-set effect with higher power:
  1. Compare by feature-family blocks with effect size + CI95.
  2. Extend comparison to additional horizons (`h+7`, `h+30`) with same temporal intersection discipline.
  3. Evaluate stability by market regime (higher vs lower volatility windows).
  4. Keep pairwise tests strictly aligned by `target_timestamp` and scoped cohort.


## Academic benchmark against prior literature (aligned scope)

### Objective
Position the `0_2_3` findings against established evidence in financial forecasting with technical/sentiment signals, out-of-sample validation, and model comparison under uncertainty.

### Benchmark references and alignment
1. Fischer & Krauss (2018), *European Journal of Operational Research* (LSTM market prediction)
- Source: https://www.sciencedirect.com/science/article/abs/pii/S0377221717310652
- Literature signal: nonlinear models can improve directional prediction, with dominant signals often linked to short-term reversal/volatility patterns.
- Alignment with `0_2_3`: partially aligned. We also observe modest directional differentiation, but no overwhelming winner in point metrics.

2. Lo, Mamaysky, Wang (2000), *Journal of Finance* (foundations of technical analysis)
- Source: https://www.nber.org/papers/w7613
- Literature signal: technical patterns can add incremental information, but practical value is often moderate and context-dependent.
- Alignment with `0_2_3`: strongly aligned. Our results indicate small but nonzero differences, consistent with incremental (not explosive) gains.

3. Bollen, Mao, Zeng (2011), *Journal of Computational Science* (Twitter mood)
- Source: https://research.manchester.ac.uk/en/publications/twitter-mood-predicts-the-stock-market
- Literature signal: sentiment dimensions can improve forecasting in some settings; predictive relevance is selective and not uniform.
- Alignment with `0_2_3`: aligned. Sentiment-linked features appear relevant, but feature effects are diffuse and not sufficient to produce universal dominance.

4. Welch & Goyal (2008), *Review of Financial Studies* (equity premium predictability)
- Source: https://academic.oup.com/rfs/article/21/4/1455/1565737
- Literature signal: many proposed predictors fail to deliver stable, strong OOS superiority; instability and small gains are common.
- Alignment with `0_2_3`: strongly aligned. We find close model performance and limited pairwise statistical separation.

5. Campbell & Thompson (2008), *Review of Financial Studies* (restricted OOS prediction)
- Source: https://academic.oup.com/rfs/article/21/4/1509/1567518
- Literature signal: OOS gains can exist, but are usually small and require disciplined constraints/selection.
- Alignment with `0_2_3`: aligned. Our evidence suggests improvement is plausible but must be claimed conservatively with strict validation.

### Methodological benchmark references (statistical rigor)
6. Diebold & Mariano (1995), *JBES* (forecast comparison test)
- Source: https://www.tandfonline.com/doi/abs/10.1080/07350015.1995.10524599
- Relevance: validates pairwise predictive-accuracy comparison logic used in DM tables.

7. Hansen, Lunde, Nason (2011), *Econometrica* (Model Confidence Set)
- Source: https://tesnewdev.econometricsociety.org/publications/econometrica/2011/03/01/model-confidence-set
- Relevance: supports confidence-set interpretation when no single model clearly dominates.

### Consolidated benchmark conclusion
- The observed `0_2_3` pattern (small metric spread, limited pairwise dominance, calibration trade-off, conservative median forecasts, diffuse global feature importance) is consistent with mainstream empirical findings in financial return forecasting.
- Therefore, current project status is methodologically coherent with academic standards: we are on the right track, provided final claims remain conservative and evidence-weighted.
- Recommended claim style for final report: "evidence supports incremental predictive contribution and probabilistic utility under strict OOS/statistical controls, not universal model or feature-set dominance."
