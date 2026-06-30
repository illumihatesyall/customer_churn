"""Streamlit dashboard — Customer Churn Analysis."""
from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import shap
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
TENURE_ORDER = ["0-12", "13-24", "25-48", "49+"]

# ── page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Churn Intelligence",
    page_icon="📉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── load artefacts ────────────────────────────────────────────────────────────
@st.cache_resource
def load_all():
    df = pd.read_parquet(ROOT / "data" / "processed" / "features.parquet")

    with open(ROOT / "models" / "churn_model.pkl", "rb") as f:
        model = pickle.load(f)
    with open(ROOT / "models" / "feature_cols.pkl", "rb") as f:
        feature_cols = pickle.load(f)
    with open(ROOT / "models" / "threshold.pkl", "rb") as f:
        threshold = pickle.load(f)
    with open(ROOT / "models" / "metrics.pkl", "rb") as f:
        metrics = pickle.load(f)

    shap_values = np.load(ROOT / "data" / "shap_values.npy")
    shap_expected = float(np.load(ROOT / "data" / "shap_expected_value.npy").item())

    X = df[feature_cols].astype(float).values
    probs = model.predict_proba(X)[:, 1]
    df = df.copy()
    df["churn_prob"] = probs
    df["churn_pred"] = (probs >= threshold).astype(int)
    df["risk_tier"] = pd.cut(
        probs,
        bins=[0, 0.3, 0.5, 0.7, 1.0],
        labels=["Low", "Medium", "High", "Critical"],
    )
    df["customer_id"] = range(1, len(df) + 1)

    return df, model, feature_cols, threshold, metrics, shap_values, shap_expected


df, model, feature_cols, threshold, metrics, shap_values, shap_expected = load_all()


def cohort_table(source: pd.DataFrame) -> pd.DataFrame:
    if "tenure_bucket" in source.columns:
        cohort = (
            source.groupby("tenure_bucket", observed=True)["Churn"]
            .agg(["mean", "count"])
            .rename(columns={"mean": "Churn Rate", "count": "Customers"})
        )
    else:
        rows = []
        for bucket in TENURE_ORDER:
            col = f"tb_{bucket}"
            if col not in source.columns:
                continue
            sub = source[source[col] == 1]
            if len(sub):
                rows.append((bucket, sub["Churn"].mean(), len(sub)))
        cohort = pd.DataFrame(rows, columns=["tenure_bucket", "Churn Rate", "Customers"])
        if cohort.empty:
            return cohort
        cohort = cohort.set_index("tenure_bucket")

    cohort = cohort.reindex([b for b in TENURE_ORDER if b in cohort.index])
    cohort["Churn Rate (%)"] = (cohort["Churn Rate"] * 100).round(1)
    return cohort


def segment_columns(source: pd.DataFrame) -> list[str]:
    prefixes = ("Contract", "IS_", "PM_")
    cols = [c for c in source.columns if c.startswith(prefixes) or c == "is_high_value"]
    preferred = ["Contract_ord", "is_high_value"]
    return [c for c in preferred if c in cols] + sorted(c for c in cols if c not in preferred)

# ── sidebar nav ──────────────────────────────────────────────────────────────
st.sidebar.image("https://img.icons8.com/color/96/combo-chart.png", width=60)
st.sidebar.title("Churn Intelligence")
page = st.sidebar.radio(
    "Navigate",
    ["📊 KPI Overview", "🔍 Customer Risk List", "📈 EDA & Cohorts", "🧠 SHAP Insights", "🎛️ What-If Simulator"],
)

# ════════════════════════════════════════════════════════════════════════════
# PAGE 1 — KPI OVERVIEW
# ════════════════════════════════════════════════════════════════════════════
if page == "📊 KPI Overview":
    st.title("📊 KPI Overview")

    total = len(df)
    churned = df["Churn"].sum()
    churn_rate = churned / total
    avg_monthly = df["MonthlyCharges"].mean()
    mrr = df["MonthlyCharges"].sum()
    mrr_at_risk = df.loc[df["churn_pred"] == 1, "MonthlyCharges"].sum()
    high_risk = (df["risk_tier"].isin(["High", "Critical"])).sum()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Customers", f"{total:,}")
    c2.metric("Churn Rate (historical)", f"{churn_rate:.1%}")
    c3.metric("Monthly Revenue (MRR)", f"${mrr:,.0f}")
    c4.metric("MRR at Risk (predicted)", f"${mrr_at_risk:,.0f}", delta=f"-${mrr_at_risk:,.0f}", delta_color="inverse")
    c5.metric("High / Critical Risk", f"{high_risk:,}")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Risk Tier Distribution")
        tier_counts = df["risk_tier"].value_counts().reindex(["Low", "Medium", "High", "Critical"]).fillna(0)
        st.bar_chart(tier_counts, color=["#2ecc71", "#f39c12", "#e74c3c", "#8e44ad"][0])

    with col2:
        st.subheader("Model Performance")
        xgb = metrics["xgboost"]
        base = metrics["baseline"]
        perf = pd.DataFrame({
            "Metric": ["PR-AUC", "ROC-AUC", "Recall @ Top-10%", "Lift @ Top-10%", "Best F1"],
            "Baseline (LogReg)": [
                f"{base['pr_auc']:.4f}", f"{base['roc_auc']:.4f}",
                f"{base['recall_top10']:.4f}", f"{base['lift_top10']:.2f}x", f"{base['f1']:.4f}",
            ],
            "XGBoost (tuned)": [
                f"{xgb['pr_auc']:.4f}", f"{xgb['roc_auc']:.4f}",
                f"{xgb['recall_top10']:.4f}", f"{xgb['lift_top10']:.2f}x", f"{xgb['f1']:.4f}",
            ],
        })
        st.dataframe(perf, use_container_width=True, hide_index=True)

    st.subheader("Churn Probability Distribution")
    hist_data = pd.cut(df["churn_prob"], bins=20).value_counts().sort_index()
    hist_df = pd.DataFrame({
        "prob_bin": [str(i.mid.round(2)) for i in hist_data.index],
        "count": hist_data.values,
    })
    st.bar_chart(hist_df.set_index("prob_bin"))


# ════════════════════════════════════════════════════════════════════════════
# PAGE 2 — CUSTOMER RISK LIST
# ════════════════════════════════════════════════════════════════════════════
elif page == "🔍 Customer Risk List":
    st.title("🔍 Customer Risk List")
    st.caption("Customers ranked by predicted churn probability with their top SHAP drivers.")

    col1, col2, col3 = st.columns(3)
    min_prob = col1.slider("Min churn probability", 0.0, 1.0, 0.5, 0.05)
    tier_filter = col2.multiselect("Risk tier", ["Low", "Medium", "High", "Critical"], default=["High", "Critical"])
    top_n = col3.number_input("Show top N customers", 10, 500, 100, 10)

    # Compute top-3 SHAP drivers per customer
    feat_array = np.array(feature_cols)
    shap_abs = np.abs(shap_values)
    top3_idx = np.argsort(-shap_abs, axis=1)[:, :3]
    top3_feats = [
        ", ".join([f"{feat_array[j]}({shap_values[i, j]:+.2f})" for j in top3_idx[i]])
        for i in range(len(df))
    ]
    df_display = df.copy()
    df_display["top_shap_drivers"] = top3_feats

    mask = (df_display["churn_prob"] >= min_prob)
    if tier_filter:
        mask &= df_display["risk_tier"].isin(tier_filter)

    result = (
        df_display[mask]
        .sort_values("churn_prob", ascending=False)
        .head(top_n)[["customer_id", "churn_prob", "risk_tier", "MonthlyCharges", "tenure", "top_shap_drivers", "Churn"]]
        .rename(columns={
            "customer_id": "Customer #",
            "churn_prob": "Churn Prob",
            "risk_tier": "Risk Tier",
            "MonthlyCharges": "Monthly ($)",
            "tenure": "Tenure (mo)",
            "top_shap_drivers": "Top SHAP Drivers",
            "Churn": "Actual Churn",
        })
    )
    result["Churn Prob"] = result["Churn Prob"].map("{:.1%}".format)

    st.metric("Customers matching filter", len(result))
    st.dataframe(result, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════════════════
# PAGE 3 — EDA & COHORTS
# ════════════════════════════════════════════════════════════════════════════
elif page == "📈 EDA & Cohorts":
    st.title("📈 EDA & Cohort Analysis")

    tab1, tab2, tab3 = st.tabs(["Cohort Retention", "Segment Churn", "Saved Charts"])

    with tab1:
        st.subheader("Churn Rate by Tenure Cohort")
        cohort = cohort_table(df)
        if not cohort.empty:
            st.bar_chart(cohort["Churn Rate (%)"])
            st.dataframe(cohort[["Customers", "Churn Rate (%)"]].astype(str), use_container_width=True)
        else:
            st.info("Tenure cohort columns were not found in the processed feature table.")

    with tab2:
        st.subheader("Churn Rate by Segment")
        seg_options = segment_columns(df)
        if seg_options:
            seg_col = st.selectbox(
                "Choose segment",
                seg_options,
            )
            seg_data = (
                df.groupby(seg_col)["Churn"]
                .agg(["mean", "count"])
                .rename(columns={"mean": "Churn Rate", "count": "N"})
            )
            seg_data["Churn Rate (%)"] = (seg_data["Churn Rate"] * 100).round(1)
            st.bar_chart(seg_data["Churn Rate (%)"])
            st.dataframe(seg_data[["N", "Churn Rate (%)"]].astype(str), use_container_width=True)
        else:
            st.info("No segment columns were found in the processed feature table.")

    with tab3:
        st.subheader("Saved EDA Charts")
        charts = {
            "Cohort Churn": ROOT / "outputs" / "cohort_churn.png",
            "Segment Churn": ROOT / "outputs" / "segment_churn.png",
            "Correlation Heatmap": ROOT / "outputs" / "correlation.png",
            "Class Imbalance": ROOT / "outputs" / "class_imbalance.png",
            "Lift Chart": ROOT / "outputs" / "lift_chart.png",
        }
        for label, path in charts.items():
            if path.exists():
                with st.expander(label):
                    st.image(str(path), use_column_width=True)


# ════════════════════════════════════════════════════════════════════════════
# PAGE 4 — SHAP INSIGHTS
# ════════════════════════════════════════════════════════════════════════════
elif page == "🧠 SHAP Insights":
    st.title("🧠 SHAP Feature Insights")

    tab1, tab2 = st.tabs(["Global Importance", "Individual Customer"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("SHAP Bar Chart (mean |SHAP|)")
            if (ROOT / "outputs" / "shap_bar.png").exists():
                st.image(str(ROOT / "outputs" / "shap_bar.png"), use_column_width=True)
        with col2:
            st.subheader("SHAP Beeswarm")
            if (ROOT / "outputs" / "shap_beeswarm.png").exists():
                st.image(str(ROOT / "outputs" / "shap_beeswarm.png"), use_column_width=True)

        st.subheader("Feature Importance Comparison (Gain vs Permutation)")
        if (ROOT / "outputs" / "feature_importance_comparison.png").exists():
            st.image(str(ROOT / "outputs" / "feature_importance_comparison.png"), use_column_width=True)

    with tab2:
        st.subheader("SHAP breakdown for a single customer")
        cust_idx = st.number_input("Customer row index (0-based)", 0, len(df) - 1, 0, 1)
        row_shap = shap_values[cust_idx]
        row_df = pd.DataFrame({
            "Feature": feature_cols,
            "Value": df[feature_cols].iloc[cust_idx].values,
            "SHAP": row_shap,
        }).sort_values("SHAP", key=abs, ascending=False).head(15)

        prob = df["churn_prob"].iloc[cust_idx]
        st.metric("Predicted churn probability", f"{prob:.1%}")

        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 5))
        colors_bar = ["#e74c3c" if v > 0 else "#2ecc71" for v in row_df["SHAP"]]
        ax.barh(row_df["Feature"], row_df["SHAP"], color=colors_bar)
        ax.axvline(0, color="black", linewidth=0.8)
        ax.set_xlabel("SHAP value (impact on log-odds of churn)")
        ax.set_title(f"Customer #{cust_idx} — SHAP breakdown (top 15)")
        ax.invert_yaxis()
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        st.dataframe(
            row_df.assign(
                **{"SHAP": row_df["SHAP"].map("{:+.4f}".format)}
            ),
            use_container_width=True,
            hide_index=True,
        )


# ════════════════════════════════════════════════════════════════════════════
# PAGE 5 — WHAT-IF SIMULATOR
# ════════════════════════════════════════════════════════════════════════════
elif page == "🎛️ What-If Simulator":
    st.title("🎛️ What-If Simulator")
    st.caption("Pick a customer, tweak their features, and see how churn probability changes in real time.")

    cust_idx = st.number_input("Select customer (row index)", 0, len(df) - 1, 0, 1)
    base_row = df[feature_cols].iloc[cust_idx].to_dict()
    base_prob = float(df["churn_prob"].iloc[cust_idx])

    st.markdown(f"**Baseline churn probability: `{base_prob:.1%}`**")
    st.divider()

    st.subheader("Adjust features")
    modified = {}
    cols = st.columns(3)

    # Show the most impactful features first (by mean |SHAP|)
    mean_abs_shap = np.abs(shap_values).mean(axis=0)
    sorted_feats = [feature_cols[i] for i in np.argsort(-mean_abs_shap)]

    for k, feat in enumerate(sorted_feats[:12]):
        col = cols[k % 3]
        val = float(base_row[feat])
        feat_min = float(df[feat].min())
        feat_max = float(df[feat].max())
        step = max(0.01, round((feat_max - feat_min) / 100, 4))
        new_val = col.slider(feat, feat_min, feat_max, val, step, key=f"slider_{feat}")
        modified[feat] = new_val

    # Build modified feature vector
    new_row = {**base_row, **modified}
    X_new = np.array([[new_row[f] for f in feature_cols]])
    new_prob = float(model.predict_proba(X_new)[0, 1])
    delta = new_prob - base_prob

    st.divider()
    col1, col2, col3 = st.columns(3)
    col1.metric("Baseline probability", f"{base_prob:.1%}")
    col2.metric("New probability", f"{new_prob:.1%}", delta=f"{delta:+.1%}", delta_color="inverse")
    col3.metric("Change", f"{delta:+.1%}", delta_color="off")

    if abs(delta) < 0.01:
        st.info("Probabilities are essentially unchanged.")
    elif delta < 0:
        st.success(f"Churn risk **reduced** by {abs(delta):.1%}. These changes could retain this customer.")
    else:
        st.warning(f"Churn risk **increased** by {delta:.1%}.")

    # Show changed features
    changed = {k: (base_row[k], v) for k, v in modified.items() if abs(v - base_row[k]) > 1e-6}
    if changed:
        st.subheader("Changes made")
        chg_df = pd.DataFrame([
            {"Feature": k, "Original": f"{base_row[k]:.3f}", "New": f"{v:.3f}",
             "Delta": f"{v - base_row[k]:+.3f}"}
            for k, (_, v) in changed.items()
        ])
        st.dataframe(chg_df, use_container_width=True, hide_index=True)
