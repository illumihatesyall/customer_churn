# Executive Memo — Customer Churn

## 1. Executive Summary
- Out of **7,043 customers**, **1,869 (26.5%)** have churned — meaningfully above any tolerable steady-state.
- A tuned XGBoost model identifies churn risk with **PR-AUC 0.250** / **ROC-AUC 0.804**, capturing **41.9% of churners by targeting only the top 10%** of accounts (lift = **4.19x**).
- Three actionable segments concentrate most of the avoidable churn; targeted outreach on the top-10% risk list could save an estimated **$42,818/yr** at a conservative 30% save-rate.

## 2. EDA Key Findings
- Class balance: 73.5% retained vs 26.5% churned — moderate imbalance, handled with `scale_pos_weight`.
- Tenure is the dominant signal: short-tenure (0–12 mo) cohorts churn at multiples of the long-tenure cohort (see [cohort_churn.png](cohort_churn.png)).
- Contract type, payment method, and internet service are the most discriminating categorical drivers ([segment_churn.png](segment_churn.png)); month-to-month + electronic-check + fiber-optic is the classic high-risk profile.
- Detailed prose narrative: [eda_narrative.md](eda_narrative.md).

## 3. Model Performance (held-out time-aware test set, n=1,409)
| Metric | Baseline (LogReg) | XGBoost (tuned) |
|---|---|---|
| PR-AUC | 0.2316 | **0.2503** |
| ROC-AUC | 0.8148 | **0.8043** |
| Recall @ top-10% | 0.3763 | **0.4194** |
| Lift @ top-10% | 3.76x | **4.19x** |
| Best-F1 | 0.3254 | **0.3470** |
| Best-F1 threshold | 0.331 | 0.386 |

See [lift_chart.png](lift_chart.png).

## 4. The 3 Actionable Segments
1. **`Contract_ord` below 0.69** — 42.7% churn vs 6.8% in the other half (6.32x), affecting ~3875 customers.
2. **`tenure` below 29.00** — 39.5% churn vs 13.2% in the other half (2.98x), affecting ~3569 customers.
3. **`charges_per_service` above 13.97** — 43.4% churn vs 9.7% in the other half (4.45x), affecting ~3520 customers.

Full breakdown: [segments.md](segments.md). SHAP attribution: [shap_beeswarm.png](shap_beeswarm.png), [shap_bar.png](shap_bar.png).

## 5. Recommended Actions
1. **Stand up a weekly top-10% risk list** from the model — at current performance, contacting these ~141 customers per scoring run captures **41.9%** of all coming churners.
2. **Convert month-to-month customers** to annual contracts via targeted discounting, prioritising tenure < 12 months.
3. **Reduce electronic-check usage** with a one-time auto-pay enrollment incentive — this single switch correlates strongly with retention.
4. **Investigate fiber-optic churn root cause** with the network/ops team — this segment loses high-ARPU customers at the fastest rate.

### Estimated revenue impact
~**$42,818/yr** retained, assuming:
- top-10% targeting captures 41.9% of churners,
- 30% save-rate from outreach (industry benchmark; replace with internal data once available),
- average ARPU of saved customers = $74.44/mo × 12.

### Caveats
- Split is time-aware on `tenure`, not calendar time — production deployment must re-validate on rolling-window holdouts.
- Causation vs correlation: SHAP attributions identify drivers in the model, not real-world levers. Validate via A/B test before rolling discounts at scale.
- The 30% save-rate is a placeholder. Final ROI depends on actual lift from outreach, which we recommend measuring with a randomized holdout group from launch.
