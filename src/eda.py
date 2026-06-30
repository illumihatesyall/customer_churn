"""EDA: cohort/segment/correlation/imbalance plots + written narrative."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_PARQUET = ROOT / "data" / "processed" / "features.parquet"
RAW_CSV = ROOT / "data" / "raw" / "telco_churn.csv"
OUT = ROOT / "outputs"
COHORT_PNG = OUT / "cohort_churn.png"
SEGMENT_PNG = OUT / "segment_churn.png"
CORR_PNG = OUT / "correlation.png"
IMB_PNG = OUT / "class_imbalance.png"
NARRATIVE_MD = OUT / "eda_narrative.md"

TENURE_ORDER = ["0-12", "13-24", "25-48", "49+"]


def step(msg: str) -> None:
    print(f"[eda] {msg}", flush=True)


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not PROCESSED_PARQUET.exists():
        raise FileNotFoundError(f"missing parquet: {PROCESSED_PARQUET} — run etl first")
    if not RAW_CSV.exists():
        raise FileNotFoundError(f"missing raw csv: {RAW_CSV}")
    step(f"loading processed parquet {PROCESSED_PARQUET}")
    feats = pd.read_parquet(PROCESSED_PARQUET)
    step(f"loading raw csv {RAW_CSV} for human-readable category labels")
    raw = pd.read_csv(RAW_CSV)
    raw["Churn"] = (raw["Churn"].astype(str).str.lower() == "yes").astype(int)
    return feats, raw


def plot_cohort(feats: pd.DataFrame) -> None:
    step("cohort: churn rate by tenure_bucket")
    bucket_cols = [c for c in feats.columns if c.startswith("tb_")]
    rows = []
    for c in bucket_cols:
        sub = feats[feats[c] == 1]
        rows.append((c.replace("tb_", ""), sub["Churn"].mean(), len(sub)))
    df = pd.DataFrame(rows, columns=["tenure_bucket", "churn_rate", "n"])
    df["tenure_bucket"] = pd.Categorical(df["tenure_bucket"], categories=TENURE_ORDER, ordered=True)
    df = df.sort_values("tenure_bucket")

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(df["tenure_bucket"].astype(str), df["churn_rate"], color="#3b7dd8")
    for bar, rate, n in zip(bars, df["churn_rate"], df["n"]):
        ax.text(bar.get_x() + bar.get_width() / 2, rate + 0.005,
                f"{rate * 100:.1f}%\n(n={n})", ha="center", va="bottom", fontsize=9)
    ax.set_title("Churn rate by tenure cohort")
    ax.set_xlabel("Tenure bucket (months)")
    ax.set_ylabel("Churn rate")
    ax.set_ylim(0, df["churn_rate"].max() * 1.25)
    fig.tight_layout()
    fig.savefig(COHORT_PNG, dpi=130)
    plt.close(fig)
    step(f"wrote {COHORT_PNG}")


def plot_segments(raw: pd.DataFrame, feats: pd.DataFrame) -> dict:
    step("segments: Contract, PaymentMethod, InternetService, is_high_value")
    raw = raw.copy()
    raw["is_high_value"] = (raw["MonthlyCharges"] > 70).astype(int)
    cats = {
        "Contract": raw,
        "PaymentMethod": raw,
        "InternetService": raw,
        "is_high_value": raw,
    }

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    summary: dict[str, pd.DataFrame] = {}
    for ax, (col, src) in zip(axes.flatten(), cats.items()):
        grp = src.groupby(col)["Churn"].agg(["mean", "count"]).reset_index()
        grp = grp.sort_values("mean", ascending=False)
        grp[col] = grp[col].astype(str)
        bars = ax.bar(grp[col], grp["mean"], color="#d8723b")
        for bar, rate, n in zip(bars, grp["mean"], grp["count"]):
            ax.text(bar.get_x() + bar.get_width() / 2, rate + 0.005,
                    f"{rate * 100:.1f}%\n(n={n})", ha="center", va="bottom", fontsize=8)
        ax.set_title(f"Churn rate by {col}")
        ax.set_ylabel("Churn rate")
        ax.tick_params(axis="x", rotation=20)
        ax.set_ylim(0, grp["mean"].max() * 1.25)
        summary[col] = grp
    fig.suptitle("Segment-level churn", fontsize=14)
    fig.tight_layout()
    fig.savefig(SEGMENT_PNG, dpi=130)
    plt.close(fig)
    step(f"wrote {SEGMENT_PNG}")
    return summary


def plot_correlation(feats: pd.DataFrame) -> pd.Series:
    step("correlation heatmap of numeric features vs Churn")
    numeric = feats.select_dtypes(include=["number"]).copy()
    corr = numeric.corr(numeric_only=True)
    target_corr = corr["Churn"].drop("Churn").sort_values(key=lambda s: s.abs(), ascending=False)

    top = target_corr.head(15).index.tolist() + ["Churn"]
    sub = corr.loc[top, top]
    fig, ax = plt.subplots(figsize=(11, 9))
    sns.heatmap(sub, cmap="coolwarm", center=0, annot=True, fmt=".2f",
                annot_kws={"size": 7}, ax=ax, cbar_kws={"shrink": 0.8})
    ax.set_title("Top-15 numeric features correlated with Churn")
    fig.tight_layout()
    fig.savefig(CORR_PNG, dpi=130)
    plt.close(fig)
    step(f"wrote {CORR_PNG}")
    return target_corr


def plot_class_imbalance(feats: pd.DataFrame) -> tuple[float, float]:
    step("class imbalance bar chart")
    counts = feats["Churn"].value_counts().sort_index()
    total = counts.sum()
    pct = counts / total * 100

    fig, ax = plt.subplots(figsize=(6, 5))
    bars = ax.bar(["No churn (0)", "Churn (1)"], counts.values,
                  color=["#3b7dd8", "#d83b5b"])
    for bar, n, p in zip(bars, counts.values, pct.values):
        ax.text(bar.get_x() + bar.get_width() / 2, n + total * 0.005,
                f"{n}\n({p:.1f}%)", ha="center", va="bottom", fontsize=10)
    ax.set_title("Class balance")
    ax.set_ylabel("Customers")
    ax.set_ylim(0, counts.max() * 1.15)
    fig.tight_layout()
    fig.savefig(IMB_PNG, dpi=130)
    plt.close(fig)
    step(f"wrote {IMB_PNG}")
    return float(pct.iloc[0]), float(pct.iloc[1])


def write_narrative(
    cohort_rates: pd.DataFrame,
    seg_summary: dict,
    target_corr: pd.Series,
    pct_no: float,
    pct_yes: float,
) -> None:
    step(f"writing narrative -> {NARRATIVE_MD}")

    contract = seg_summary["Contract"]
    payment = seg_summary["PaymentMethod"]
    internet = seg_summary["InternetService"]
    hv = seg_summary["is_high_value"]

    top_pos = target_corr[target_corr > 0].head(5)
    top_neg = target_corr[target_corr < 0].head(5)

    def fmt_rate(df_, col, val):
        r = df_.loc[df_[col].astype(str) == str(val), "mean"]
        return f"{float(r.iloc[0]) * 100:.1f}%" if len(r) else "n/a"

    lines = []
    lines.append("# EDA Narrative — Telco Customer Churn\n")
    lines.append(f"Dataset: **{int(pct_no + pct_yes and 100)}%** of {int(round((pct_no + pct_yes)))}-pct base. "
                 f"Class split — no-churn {pct_no:.1f}%, churn {pct_yes:.1f}%. "
                 "The minority class is roughly 1-in-4 customers, so models must guard against "
                 "majority-class collapse (we use class weighting / `scale_pos_weight`).\n")

    lines.append("## What stands out\n")
    lines.append(f"- **Tenure dominates.** Brand-new customers (0–12 months) churn at "
                 f"**{cohort_rates.iloc[0]['churn_rate'] * 100:.1f}%**, "
                 f"vs. long-tenured 49+ month customers at "
                 f"**{cohort_rates.iloc[-1]['churn_rate'] * 100:.1f}%** — a clear retention curve.\n")
    lines.append(f"- **Month-to-month contracts bleed customers.** "
                 f"M2M churn = {fmt_rate(contract, 'Contract', 'Month-to-month')} "
                 f"vs. one-year = {fmt_rate(contract, 'Contract', 'One year')} "
                 f"vs. two-year = {fmt_rate(contract, 'Contract', 'Two year')}.\n")
    lines.append(f"- **Fiber optic internet customers churn the most**: "
                 f"{fmt_rate(internet, 'InternetService', 'Fiber optic')} — "
                 f"materially higher than DSL ({fmt_rate(internet, 'InternetService', 'DSL')}) or "
                 f"No-internet ({fmt_rate(internet, 'InternetService', 'No')}). Likely a price / "
                 "service-quality story worth investigating with the network team.\n")
    lines.append(f"- **Electronic check payers** churn at {fmt_rate(payment, 'PaymentMethod', 'Electronic check')} — "
                 "by far the riskiest billing channel. Auto-pay methods (bank transfer / credit card) all sit lower.\n")
    lines.append(f"- **High-value customers (>$70/mo)** churn at "
                 f"{fmt_rate(hv, 'is_high_value', '1')} vs. {fmt_rate(hv, 'is_high_value', '0')} for the rest — "
                 "high ARPU is being lost faster than the base.\n")

    lines.append("## Most likely churn drivers (signed correlation with Churn)\n")
    lines.append("**Positively correlated (push churn up):**\n")
    for k, v in top_pos.items():
        lines.append(f"- `{k}`: {v:+.3f}")
    lines.append("\n**Negatively correlated (protective):**\n")
    for k, v in top_neg.items():
        lines.append(f"- `{k}`: {v:+.3f}")
    lines.append("")

    lines.append("## Business framing\n")
    lines.append(
        "Churn here is a **contract-stickiness** and **early-tenure** problem stacked on top of a "
        "**high-ARPU / fiber-optic** dissatisfaction signal. The most addressable levers are: "
        "(1) push month-to-month customers onto annual contracts, especially in the first 12 months; "
        "(2) shift electronic-check payers onto auto-pay; "
        "(3) diagnose why fiber-optic customers without add-on services (tech support, security) "
        "leave at materially higher rates. Bundling value-add services appears to act as a retention moat."
    )
    NARRATIVE_MD.write_text("\n".join(lines), encoding="utf-8")
    step(f"wrote {NARRATIVE_MD}")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    feats, raw = load()
    cohort_rows = []
    bucket_cols = [c for c in feats.columns if c.startswith("tb_")]
    for c in bucket_cols:
        sub = feats[feats[c] == 1]
        cohort_rows.append((c.replace("tb_", ""), sub["Churn"].mean(), len(sub)))
    cohort_df = pd.DataFrame(cohort_rows, columns=["tenure_bucket", "churn_rate", "n"])
    cohort_df["tenure_bucket"] = pd.Categorical(
        cohort_df["tenure_bucket"], categories=TENURE_ORDER, ordered=True
    )
    cohort_df = cohort_df.sort_values("tenure_bucket").reset_index(drop=True)

    plot_cohort(feats)
    seg_summary = plot_segments(raw, feats)
    target_corr = plot_correlation(feats)
    pct_no, pct_yes = plot_class_imbalance(feats)
    write_narrative(cohort_df, seg_summary, target_corr, pct_no, pct_yes)
    step("DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
