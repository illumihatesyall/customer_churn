# Customer Churn Project Documentation

Generated for report writing and project handoff. This file documents the full `churn_project` folder: objective, data, code, pipeline, artifacts, metrics, outputs, business interpretation, dashboard, and known caveats.

## 1. Project Overview

This project is an end-to-end customer churn analysis and prediction workflow using the IBM Telco Customer Churn dataset. It starts from a raw CSV, cleans and engineers customer-level features, performs exploratory data analysis, trains churn prediction models, explains model behavior with SHAP, creates actionable customer segments, and produces business-facing deliverables.

Main business question:

> Which customers are likely to churn, why are they at risk, and what actions should the business take to reduce churn?

Primary outcome:

- A tuned XGBoost churn model.
- A logistic regression baseline.
- EDA charts and narrative.
- SHAP interpretation charts.
- Three actionable churn segments.
- Executive memo in Markdown and PDF.
- PowerPoint presentation.
- Streamlit dashboard with KPIs, risk list, SHAP views, and what-if simulation.

## 2. Folder Structure

```text
churn_project/
  Makefile
  package.json
  package-lock.json
  requirements.txt
  run_all.py
  project.md
  data/
    raw/
      telco_churn.csv
    processed/
      features.parquet
      churn.duckdb
    shap_values.npy
    shap_expected_value.npy
  models/
    baseline_model.pkl
    churn_model.pkl
    feature_cols.pkl
    threshold.pkl
    metrics.pkl
    interpret_stats.pkl
  outputs/
    class_imbalance.png
    cohort_churn.png
    correlation.png
    eda_narrative.md
    executive_memo.md
    executive_memo.pdf
    feature_importance_comparison.png
    lift_chart.png
    segments.md
    segment_churn.png
    shap_bar.png
    shap_beeswarm.png
    churn_presentation.pptx
  src/
    etl.py
    eda.py
    model.py
    interpret.py
    memo.py
    export_memo_pdf.py
    dashboard.py
    build_pptx.js
```

`node_modules/` is present but is vendor dependency output from `npm install`; it is not project source.

## 3. Environment And Dependencies

Python dependencies are listed in `requirements.txt`:

```text
pandas
pyarrow
duckdb
scikit-learn
xgboost
lightgbm
shap
optuna
matplotlib
seaborn
requests
```

Additional dependencies used by source files but not listed in `requirements.txt`:

- `streamlit`, used by `src/dashboard.py`.
- `reportlab`, used by `src/export_memo_pdf.py`.

Node dependency from `package.json`:

- `pptxgenjs` version range `^4.0.1`, used by `src/build_pptx.js`.

Useful setup commands:

```bash
pip install -r requirements.txt
pip install streamlit reportlab
npm install
```

## 4. How To Run The Project

Run the full Python pipeline with GNU Make:

```bash
make all
```

Equivalent portable command for systems without Make:

```bash
python run_all.py
```

The full pipeline order is:

1. `src/etl.py`
2. `src/eda.py`
3. `src/model.py`
4. `src/interpret.py`
5. `src/memo.py`

Other deliverables:

```bash
python src/export_memo_pdf.py
node src/build_pptx.js
streamlit run src/dashboard.py
```

`run_all.py` verifies that expected core artifacts exist after execution.

## 5. Dataset

Raw file:

```text
data/raw/telco_churn.csv
```

Source URL in `src/etl.py`:

```text
https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv
```

Raw shape and target:

- Rows: 7,043 customers.
- Raw columns: 21.
- Target column: `Churn`.
- Churned customers: 1,869.
- Non-churned customers: 5,174.
- Churn rate: 26.5%.
- Retained rate: 73.5%.

Raw columns:

```text
customerID
gender
SeniorCitizen
Partner
Dependents
tenure
PhoneService
MultipleLines
InternetService
OnlineSecurity
OnlineBackup
DeviceProtection
TechSupport
StreamingTV
StreamingMovies
Contract
PaperlessBilling
PaymentMethod
MonthlyCharges
TotalCharges
Churn
```

Important raw category distributions:

- `Contract`: Month-to-month 3,875; Two year 1,695; One year 1,473.
- `PaymentMethod`: Electronic check 2,365; Mailed check 1,612; Bank transfer automatic 1,544; Credit card automatic 1,522.
- `InternetService`: Fiber optic 3,096; DSL 2,421; No internet service 1,526.

## 6. ETL And Feature Engineering

Implemented in:

```text
src/etl.py
```

Outputs:

```text
data/processed/features.parquet
data/processed/churn.duckdb
```

ETL behavior:

- If the raw CSV is missing, downloads it from the IBM GitHub URL.
- Loads the raw CSV with pandas.
- Converts blank `TotalCharges` values to `0`.
- Casts `TotalCharges` to float.
- Drops `customerID`.
- Encodes `Churn` as 1 for yes and 0 for no.
- Validates basic assumptions:
  - No nulls in key columns: `tenure`, `MonthlyCharges`, `TotalCharges`, `Churn`.
  - More than 7,000 rows.
  - Churn rate between 10% and 40%.

Engineered features:

- `avg_monthly_charges = TotalCharges / (tenure + 1)`
- `active_services`: count of active yes-valued service columns.
- `charges_per_service = MonthlyCharges / (active_services + 1)`
- `is_high_value = 1` when `MonthlyCharges > 70`, else 0.
- `tenure_bucket`: one of `0-12`, `13-24`, `25-48`, `49+`.
- `Contract_ord`: ordinal encoding of contract type:
  - Month-to-month = 0
  - One year = 1
  - Two year = 2

Categorical encodings:

- One-hot encodes `InternetService`.
- One-hot encodes `PaymentMethod`.
- Binary encodes:
  - `gender`: male = 1, female = 0.
  - `Partner`, `Dependents`, `PhoneService`, `PaperlessBilling`: yes = 1, no = 0.
- One-hot encodes service columns:
  - `MultipleLines`
  - `OnlineSecurity`
  - `OnlineBackup`
  - `DeviceProtection`
  - `TechSupport`
  - `StreamingTV`
  - `StreamingMovies`
- One-hot encodes `tenure_bucket`.

The processed feature table is stored in Parquet and also registered as DuckDB table `features`.

## 7. Exploratory Data Analysis

Implemented in:

```text
src/eda.py
```

EDA outputs:

```text
outputs/cohort_churn.png
outputs/segment_churn.png
outputs/correlation.png
outputs/class_imbalance.png
outputs/eda_narrative.md
```

EDA views:

- Churn by tenure cohort.
- Churn by contract, payment method, internet service, and high-value flag.
- Correlation heatmap for top numeric features associated with churn.
- Class imbalance chart.
- Narrative summary in Markdown.

Key EDA findings from `outputs/eda_narrative.md`:

- New customers in the `0-12` month tenure bucket churn at 47.4%.
- Long-tenured `49+` month customers churn at 9.5%.
- Month-to-month contracts churn at 42.7%.
- One-year contracts churn at 11.3%.
- Two-year contracts churn at 2.8%.
- Fiber optic customers churn at 41.9%.
- DSL customers churn at 19.0%.
- Customers with no internet service churn at 7.4%.
- Electronic check payers churn at 45.3%.
- High-value customers over $70/month churn at 35.4%.
- Lower-value customers churn at 17.4%.

Top positive churn correlations:

- `charges_per_service`: +0.393
- `OnlineSecurity_No`: +0.343
- `TechSupport_No`: +0.337
- `tb_0-12`: +0.318
- `IS_Fiber optic`: +0.308

Top protective correlations:

- `Contract_ord`: -0.397
- `tenure`: -0.352
- `tb_49+`: -0.263
- no-internet-service indicators: about -0.228

Business interpretation:

Churn is mainly an early-tenure and contract-stickiness problem, amplified by fiber-optic/high-ARPU dissatisfaction and risky payment behavior.

## 8. Modeling

Implemented in:

```text
src/model.py
```

Model outputs:

```text
models/baseline_model.pkl
models/churn_model.pkl
models/feature_cols.pkl
models/threshold.pkl
models/metrics.pkl
outputs/lift_chart.png
```

Modeling approach:

- Uses processed `features.parquet`.
- Sorts rows by `tenure`.
- Uses first 80% as train and final 20% as test.
- This is called a time-aware split in the code, but it is based on tenure, not real calendar time.
- Target is `Churn`.
- All non-target processed columns are model features.

Baseline model:

- `LogisticRegression`
- `StandardScaler`
- `class_weight="balanced"`
- `max_iter=1000`

Main model:

- `XGBClassifier`
- Binary logistic objective.
- `eval_metric="aucpr"`
- `tree_method="hist"`
- `random_state=42`
- `n_jobs=-1`
- Class imbalance handled with `scale_pos_weight = negative_count / positive_count`.

Hyperparameter tuning:

- Library: Optuna.
- Trials: 50.
- Sampler: TPE sampler with seed 42.
- Cross-validation: 3-fold stratified CV.
- Optimization metric: average precision / PR-AUC.
- Tuned parameters:
  - `n_estimators`
  - `max_depth`
  - `learning_rate`
  - `subsample`
  - `colsample_bytree`
  - `min_child_weight`

Decision threshold:

- The threshold is selected from the precision-recall curve to maximize F1 on the held-out test set.
- Saved to `models/threshold.pkl`.

## 9. Model Performance

Held-out test size:

- 1,409 customers.

Performance from `outputs/executive_memo.md`:

| Metric | Baseline Logistic Regression | Tuned XGBoost |
|---|---:|---:|
| PR-AUC | 0.2316 | 0.2503 |
| ROC-AUC | 0.8148 | 0.8043 |
| Recall at top 10% | 0.3763 | 0.4194 |
| Lift at top 10% | 3.76x | 4.19x |
| Best F1 | 0.3254 | 0.3470 |
| Best-F1 threshold | 0.331 | 0.386 |

Interpretation:

- XGBoost improves PR-AUC, top-10% recall, lift, and F1 compared with the logistic baseline.
- Logistic regression has slightly higher ROC-AUC, but the project emphasizes PR-AUC and top-decile lift because churn intervention is a targeted outreach problem.
- The XGBoost model captures 41.9% of churners by targeting only the highest-risk 10% of customers.
- The top-decile lift of 4.19x means the model is about 4.19 times better than random targeting at finding churners in the top 10%.

## 10. Model Interpretation

Implemented in:

```text
src/interpret.py
```

Interpretation outputs:

```text
data/shap_values.npy
data/shap_expected_value.npy
outputs/shap_beeswarm.png
outputs/shap_bar.png
outputs/feature_importance_comparison.png
outputs/segments.md
models/interpret_stats.pkl
```

Interpretation methods:

- SHAP `TreeExplainer` on the trained XGBoost model.
- SHAP values computed for the full processed dataset.
- Global SHAP beeswarm plot.
- Global SHAP mean absolute value bar chart.
- XGBoost gain importance compared with permutation importance.
- Three actionable segments selected from top mean absolute SHAP features.

Important interpretation note:

SHAP explains the model's learned relationships. It supports prioritization and diagnosis, but it does not prove causation. Business actions should be validated with experiments or holdout tests.

## 11. Actionable Segments

Generated by:

```text
src/interpret.py
```

Saved in:

```text
outputs/segments.md
models/interpret_stats.pkl
```

Segments from `outputs/segments.md`:

1. `Contract_ord` below 0.69
   - Represents month-to-month customers.
   - Churn rate: 42.7%.
   - Comparison group churn rate: 6.8%.
   - Risk ratio: 6.32x.
   - Affected customers: about 3,875.
   - Mean absolute SHAP: 0.6735.

2. `tenure` below 29 months
   - Represents newer and mid-tenure customers.
   - Churn rate: 39.5%.
   - Comparison group churn rate: 13.2%.
   - Risk ratio: 2.98x.
   - Affected customers: about 3,569.
   - Mean absolute SHAP: 0.4275.

3. `charges_per_service` above 13.97
   - Represents customers paying more for each active service.
   - Churn rate: 43.4%.
   - Comparison group churn rate: 9.7%.
   - Risk ratio: 4.45x.
   - Affected customers: about 3,520.
   - Mean absolute SHAP: 0.3210.

Business actions mapped to segments:

- Convert month-to-month customers to annual contracts.
- Improve onboarding and early-tenure check-ins.
- Bundle services or add value for customers with high charges per service.
- Investigate fiber-optic service quality and pricing perception.
- Move electronic-check customers toward auto-pay.

## 12. Executive Memo

Generated by:

```text
src/memo.py
```

Output:

```text
outputs/executive_memo.md
```

The memo combines:

- Dataset size and churn rate.
- Model performance.
- Top-decile targeting performance.
- Revenue impact estimate.
- EDA findings.
- Actionable segments.
- Recommended actions.
- Caveats.

Headline memo numbers:

- 7,043 customers.
- 1,869 churners.
- 26.5% churn.
- XGBoost PR-AUC: 0.250.
- XGBoost ROC-AUC: 0.804.
- Top-10% recall: 41.9%.
- Lift: 4.19x.
- Estimated annual retained revenue: $42,818.

Revenue estimate assumptions:

- Target top 10% of accounts by model churn probability.
- Capture 41.9% of churners in that top decile.
- Assume 30% save rate from outreach.
- Average monthly charge of churners: $74.44.
- Annual value per retained churner: monthly charge times 12.

## 13. PDF Export

Implemented in:

```text
src/export_memo_pdf.py
```

Input:

```text
outputs/executive_memo.md
```

Output:

```text
outputs/executive_memo.pdf
```

The PDF exporter uses ReportLab. It includes:

- Custom title, subtitle, headings, body, bullet, code, and table styles.
- Markdown inline conversion for bold, italic, code ticks, and links.
- Markdown table parsing into ReportLab tables.
- Executive memo branding colors.

## 14. PowerPoint Presentation

Implemented in:

```text
src/build_pptx.js
```

Output:

```text
outputs/churn_presentation.pptx
```

Technology:

- Node.js
- `pptxgenjs`

The presentation is a 16:9 business deck with 13 slides:

1. Title
2. Agenda
3. Business problem
4. Dataset and pipeline
5. EDA: cohort and class imbalance
6. EDA: segments
7. Model comparison
8. Cumulative lift
9. SHAP insights
10. Three actionable segments
11. Recommendations
12. Revenue impact
13. Thank you / Q&A

The deck embeds generated images from `outputs/`.

Important caveat:

Some numbers in `build_pptx.js` are hard-coded in slide text. If the model is retrained and metrics change, the slide script should be manually reviewed or refactored to read from `metrics.pkl`.

## 15. Streamlit Dashboard

Implemented in:

```text
src/dashboard.py
```

Run with:

```bash
streamlit run src/dashboard.py
```

Dashboard pages:

1. KPI Overview
   - Total customers.
   - Historical churn rate.
   - Monthly recurring revenue.
   - Predicted MRR at risk.
   - High/critical risk count.
   - Risk tier distribution.
   - Model performance table.
   - Churn probability distribution.

2. Customer Risk List
   - Ranked customers by predicted churn probability.
   - Filters for minimum probability, risk tier, and top N.
   - Shows monthly charge, tenure, actual churn, and top SHAP drivers.

3. EDA & Cohorts
   - Cohort retention view.
   - Segment churn view.
   - Saved EDA charts.

4. SHAP Insights
   - Global SHAP bar chart.
   - SHAP beeswarm.
   - Feature importance comparison.
   - Individual customer SHAP breakdown.

5. What-If Simulator
   - Select a customer.
   - Adjust top features with sliders.
   - Recompute churn probability with the trained model.
   - Show risk change and modified features.

Dashboard data dependencies:

- `data/processed/features.parquet`
- `models/churn_model.pkl`
- `models/feature_cols.pkl`
- `models/threshold.pkl`
- `models/metrics.pkl`
- `data/shap_values.npy`
- `data/shap_expected_value.npy`

Potential dashboard issue:

- `dashboard.py` checks for a `tenure_bucket` column, but ETL one-hot encodes `tenure_bucket` and drops the original column. The cohort tab may not display the intended grouped cohort table unless it is updated to reconstruct cohorts from `tb_` one-hot columns or preserve `tenure_bucket`.

## 16. Artifact Catalog

Data artifacts:

- `data/raw/telco_churn.csv`: raw IBM Telco churn CSV.
- `data/processed/features.parquet`: cleaned and engineered model table.
- `data/processed/churn.duckdb`: DuckDB database with table `features`.
- `data/shap_values.npy`: full-dataset SHAP matrix.
- `data/shap_expected_value.npy`: SHAP expected value.

Model artifacts:

- `models/baseline_model.pkl`: fitted logistic regression pipeline.
- `models/churn_model.pkl`: fitted tuned XGBoost model.
- `models/feature_cols.pkl`: ordered model feature list.
- `models/threshold.pkl`: best-F1 decision threshold for XGBoost.
- `models/metrics.pkl`: serialized model metrics, parameters, split sizes.
- `models/interpret_stats.pkl`: interpretation metadata including actionable segments.

Report and chart artifacts:

- `outputs/cohort_churn.png`: churn rate by tenure bucket.
- `outputs/segment_churn.png`: churn by contract, payment, internet, high-value flag.
- `outputs/correlation.png`: top feature correlation heatmap.
- `outputs/class_imbalance.png`: churn vs no-churn counts.
- `outputs/lift_chart.png`: cumulative gains/lift chart.
- `outputs/shap_beeswarm.png`: SHAP distribution plot.
- `outputs/shap_bar.png`: mean absolute SHAP importance.
- `outputs/feature_importance_comparison.png`: gain vs permutation importance.
- `outputs/eda_narrative.md`: EDA narrative.
- `outputs/segments.md`: actionable segment write-up.
- `outputs/executive_memo.md`: business memo.
- `outputs/executive_memo.pdf`: PDF version of memo.
- `outputs/churn_presentation.pptx`: presentation deck.

## 17. Source File Responsibilities

`src/etl.py`

- Downloads raw data if absent.
- Cleans raw data.
- Engineers features.
- Validates processed data.
- Saves Parquet and DuckDB outputs.

`src/eda.py`

- Loads raw and processed data.
- Creates EDA plots.
- Computes segment and cohort churn rates.
- Writes EDA narrative.

`src/model.py`

- Loads processed features.
- Creates tenure-sorted train/test split.
- Trains logistic regression baseline.
- Tunes XGBoost with Optuna.
- Evaluates both models.
- Saves model artifacts and metrics.
- Writes lift chart.

`src/interpret.py`

- Loads trained model and feature columns.
- Computes SHAP values.
- Writes SHAP plots.
- Compares XGBoost gain with permutation importance.
- Builds three actionable segments.
- Saves interpretation artifacts.

`src/memo.py`

- Loads metrics, interpretation stats, and processed data.
- Computes business summary values.
- Estimates revenue impact.
- Writes `outputs/executive_memo.md`.

`src/export_memo_pdf.py`

- Converts the executive memo Markdown to a styled PDF.

`src/dashboard.py`

- Streamlit dashboard for business exploration and model inspection.

`src/build_pptx.js`

- Creates a PowerPoint presentation from generated charts and scripted slide content.

`run_all.py`

- Portable full-pipeline runner.
- Executes ETL, EDA, modeling, interpretation, and memo generation.
- Verifies expected artifacts.

`Makefile`

- Provides simple targets: `data`, `eda`, `model`, `interpret`, `memo`, `all`.

## 18. Quality Checks And Validation

Built-in checks:

- ETL asserts key columns have no nulls.
- ETL asserts row count is over 7,000.
- ETL asserts churn rate is between 10% and 40%.
- `run_all.py` checks that expected artifacts exist after the pipeline.
- Modeling uses stratified CV during hyperparameter tuning.
- Modeling compares against a logistic regression baseline.
- Interpretation includes both SHAP and permutation importance.

Missing or limited checks:

- No formal unit tests are present.
- `package.json` has only the default failing `npm test` script.
- There is no automated dashboard test.
- There is no data drift check.
- There is no model calibration check.
- There is no fairness or bias analysis.
- There is no production scoring script separate from dashboard inference.

## 19. Known Caveats

Important analytical caveats:

- The split is sorted by `tenure`, not by real calendar date. It is more realistic than a pure random split for tenure progression, but it is not a true temporal validation.
- The model is trained on a public historical dataset, not a live company database.
- SHAP and correlation do not prove causation.
- Revenue impact uses a 30% save-rate assumption, not an observed experiment result.
- The dashboard generates synthetic `customer_id` values from row order because the ETL drops original `customerID`.
- The project uses historical churn labels, so a production version would need fresh snapshots and future churn windows.

Technical caveats:

- Some comments and strings in source/output files show mojibake characters, likely from encoding display issues.
- PowerPoint slide text has hard-coded metrics and should be refreshed after retraining.
- No `.gitignore` is shown in this folder; large/generated files such as `node_modules`, model pickles, and outputs may need ignore rules depending on submission requirements.

## 20. Recommended Improvements

High-priority:

1. Refactor `build_pptx.js` to read metrics from a JSON export instead of hard-coding key numbers.
2. Add a production scoring script that loads `churn_model.pkl`, `feature_cols.pkl`, and `threshold.pkl`.
3. Add basic tests for ETL row count, feature columns, target encoding, and model artifact loading.

Medium-priority:

1. Add model calibration analysis.
2. Add precision/recall tables at multiple outreach budgets: top 5%, 10%, 20%.
3. Add cost-benefit sensitivity table for save rates of 10%, 20%, 30%, 40%, and 50%.
4. Add fairness checks by gender and senior-citizen status.
5. Add data dictionary for every engineered feature.
6. Store metrics in Markdown/JSON as well as pickle for easier reporting.

Production-priority:

1. Replace tenure split with rolling calendar validation once timestamped data exists.
2. Define a churn prediction window, such as churn in next 30/60/90 days.
3. Create a repeatable weekly scoring job.
4. Integrate outreach outcomes back into the data.
5. Run randomized holdout experiments to estimate true retention lift.

## 21. Report-Ready Narrative

This project demonstrates a complete churn analytics workflow. The dataset contains 7,043 telco customers, of whom 1,869 churned, producing a churn rate of 26.5%. After cleaning and feature engineering, the project trains a logistic regression baseline and an Optuna-tuned XGBoost model. The final model is evaluated on a tenure-sorted holdout set of 1,409 customers.

The strongest churn drivers are contract type, tenure, charges per service, missing support/security services, fiber-optic internet, and electronic-check payment. Month-to-month customers churn much more than customers on annual contracts, new customers churn much more than long-tenured customers, and high-value customers are at elevated churn risk.

The tuned XGBoost model achieves PR-AUC 0.2503, ROC-AUC 0.8043, best F1 0.3470, and top-decile lift of 4.19x. This means that if the business targets only the highest-risk 10% of customers, it can capture 41.9% of churners. This is the key operational value of the model: it converts a broad churn problem into a focused retention list.

SHAP interpretation identifies three actionable segments: month-to-month customers, customers with tenure below 29 months, and customers with high charges per active service. These segments map directly to business interventions: annual-contract incentives, early-tenure onboarding, service bundling, payment-method migration, and investigation of fiber-optic dissatisfaction.

The executive memo estimates that targeted outreach could retain about $42,818 per year under conservative assumptions. This estimate depends on a 30% save rate and should be validated with an A/B test or randomized holdout group.

## 22. Possible Report Sections

A report generated from this project can use the following structure:

1. Executive summary
2. Business problem and objective
3. Dataset description
4. Data cleaning and feature engineering
5. Exploratory data analysis
6. Modeling methodology
7. Model evaluation
8. Model interpretation with SHAP
9. Actionable customer segments
10. Business recommendations
11. Revenue impact estimate
12. Dashboard and deliverables
13. Limitations
14. Future improvements
15. Conclusion

## 23. Key Numbers For Quick Reference

- Total customers: 7,043.
- Churners: 1,869.
- Churn rate: 26.5%.
- Retained customers: 5,174.
- Retained rate: 73.5%.
- Test set size: 1,409.
- XGBoost PR-AUC: 0.2503.
- XGBoost ROC-AUC: 0.8043.
- XGBoost best F1: 0.3470.
- XGBoost threshold: 0.386.
- XGBoost recall at top 10%: 41.9%.
- XGBoost lift at top 10%: 4.19x.
- Baseline PR-AUC: 0.2316.
- Baseline ROC-AUC: 0.8148.
- Estimated annual revenue retained: $42,818.
- Average monthly charge of churners used in ROI estimate: $74.44.

## 24. Conclusion

The project is a complete churn intelligence system, not just a model notebook. It covers the practical lifecycle from raw data to business recommendations: ETL, EDA, model training, evaluation, interpretation, segmentation, memo generation, PDF export, PowerPoint generation, and interactive dashboarding.

The main project message is clear: churn is concentrated among month-to-month, early-tenure, high-price-per-service customers, especially where fiber-optic service and electronic-check payment appear. The model gives the business a ranked outreach list, and SHAP gives a defensible explanation for why customers are risky. The next step should be an operational pilot with a randomized holdout to measure actual save rate and revenue impact.
