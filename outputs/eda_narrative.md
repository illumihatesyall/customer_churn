# EDA Narrative — Telco Customer Churn

Dataset: **100%** of 100-pct base. Class split — no-churn 73.5%, churn 26.5%. The minority class is roughly 1-in-4 customers, so models must guard against majority-class collapse (we use class weighting / `scale_pos_weight`).

## What stands out

- **Tenure dominates.** Brand-new customers (0–12 months) churn at **47.4%**, vs. long-tenured 49+ month customers at **9.5%** — a clear retention curve.

- **Month-to-month contracts bleed customers.** M2M churn = 42.7% vs. one-year = 11.3% vs. two-year = 2.8%.

- **Fiber optic internet customers churn the most**: 41.9% — materially higher than DSL (19.0%) or No-internet (7.4%). Likely a price / service-quality story worth investigating with the network team.

- **Electronic check payers** churn at 45.3% — by far the riskiest billing channel. Auto-pay methods (bank transfer / credit card) all sit lower.

- **High-value customers (>$70/mo)** churn at 35.4% vs. 17.4% for the rest — high ARPU is being lost faster than the base.

## Most likely churn drivers (signed correlation with Churn)

**Positively correlated (push churn up):**

- `charges_per_service`: +0.393
- `OnlineSecurity_No`: +0.343
- `TechSupport_No`: +0.337
- `tb_0-12`: +0.318
- `IS_Fiber optic`: +0.308

**Negatively correlated (protective):**

- `Contract_ord`: -0.397
- `tenure`: -0.352
- `tb_49+`: -0.263
- `StreamingMovies_No internet service`: -0.228
- `DeviceProtection_No internet service`: -0.228

## Business framing

Churn here is a **contract-stickiness** and **early-tenure** problem stacked on top of a **high-ARPU / fiber-optic** dissatisfaction signal. The most addressable levers are: (1) push month-to-month customers onto annual contracts, especially in the first 12 months; (2) shift electronic-check payers onto auto-pay; (3) diagnose why fiber-optic customers without add-on services (tech support, security) leave at materially higher rates. Bundling value-add services appears to act as a retention moat.