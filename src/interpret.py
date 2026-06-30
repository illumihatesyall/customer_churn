"""Interpretation: SHAP values, importance comparison, 3 actionable segments."""
from __future__ import annotations

import pickle
import sys
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from sklearn.inspection import permutation_importance

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_PARQUET = ROOT / "data" / "processed" / "features.parquet"
MODELS = ROOT / "models"
OUT = ROOT / "outputs"
DATA = ROOT / "data"

MODEL_PKL = MODELS / "churn_model.pkl"
FEATCOLS_PKL = MODELS / "feature_cols.pkl"
METRICS_PKL = MODELS / "metrics.pkl"

SHAP_VALUES_NPY = DATA / "shap_values.npy"
SHAP_EXPECTED_NPY = DATA / "shap_expected_value.npy"
BEESWARM_PNG = OUT / "shap_beeswarm.png"
BAR_PNG = OUT / "shap_bar.png"
IMP_COMPARE_PNG = OUT / "feature_importance_comparison.png"
SEGMENTS_MD = OUT / "segments.md"
INTERPRET_STATS_PKL = MODELS / "interpret_stats.pkl"


def step(msg: str) -> None:
    print(f"[interpret] {msg}", flush=True)


def load_all():
    for p in (MODEL_PKL, FEATCOLS_PKL, PROCESSED_PARQUET):
        if not p.exists():
            raise FileNotFoundError(f"missing artifact: {p} — earlier phases not run")
    with open(MODEL_PKL, "rb") as f:
        model = pickle.load(f)
    with open(FEATCOLS_PKL, "rb") as f:
        feature_cols = pickle.load(f)
    df = pd.read_parquet(PROCESSED_PARQUET)
    return model, feature_cols, df


def compute_shap(model, X: np.ndarray, feature_cols: list[str]):
    step(f"SHAP TreeExplainer on full dataset (n={len(X)}, p={X.shape[1]})")
    explainer = shap.TreeExplainer(model)
    sv = explainer.shap_values(X)
    if isinstance(sv, list):
        sv = sv[1]
    expected = explainer.expected_value
    if isinstance(expected, (list, np.ndarray)):
        try:
            expected = float(np.asarray(expected).ravel()[-1])
        except Exception:
            expected = float(np.asarray(expected).ravel()[0])
    step(f"shap shape={sv.shape}  expected_value={expected:.4f}")
    return sv, float(expected)


def save_shap_artifacts(sv: np.ndarray, expected: float) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    np.save(SHAP_VALUES_NPY, sv)
    np.save(SHAP_EXPECTED_NPY, np.asarray([expected]))
    step(f"wrote {SHAP_VALUES_NPY} and {SHAP_EXPECTED_NPY}")


def plot_shap(sv: np.ndarray, X: np.ndarray, feature_cols: list[str]) -> None:
    step(f"plotting beeswarm -> {BEESWARM_PNG}")
    shap.summary_plot(sv, X, feature_names=feature_cols, show=False, max_display=20)
    fig = plt.gcf()
    fig.set_size_inches(10, 8)
    fig.tight_layout()
    fig.savefig(BEESWARM_PNG, dpi=130)
    plt.close(fig)

    step(f"plotting bar -> {BAR_PNG}")
    shap.summary_plot(sv, X, feature_names=feature_cols, plot_type="bar",
                      show=False, max_display=20)
    fig = plt.gcf()
    fig.set_size_inches(10, 8)
    fig.tight_layout()
    fig.savefig(BAR_PNG, dpi=130)
    plt.close(fig)


def plot_importance_comparison(model, X: np.ndarray, y: np.ndarray,
                               feature_cols: list[str]) -> None:
    step("computing gain vs permutation importance comparison")
    booster = model.get_booster()
    gain_scores = booster.get_score(importance_type="gain")
    gain_arr = np.zeros(len(feature_cols))
    for k, v in gain_scores.items():
        if k.startswith("f") and k[1:].isdigit():
            idx = int(k[1:])
            if 0 <= idx < len(feature_cols):
                gain_arr[idx] = v
    gain_norm = gain_arr / gain_arr.max() if gain_arr.max() > 0 else gain_arr

    # subsample for permutation speed
    n_perm = min(1000, len(X))
    rng = np.random.default_rng(0)
    idx = rng.choice(len(X), size=n_perm, replace=False)
    step(f"permutation importance on {n_perm} sample rows")
    perm = permutation_importance(
        model, X[idx], y[idx], n_repeats=3, random_state=0, n_jobs=1,
        scoring="average_precision",
    )
    perm_arr = perm.importances_mean
    perm_norm = perm_arr / perm_arr.max() if perm_arr.max() > 0 else perm_arr

    df = pd.DataFrame({
        "feature": feature_cols,
        "gain_norm": gain_norm,
        "perm_norm": perm_norm,
    })
    df = df.sort_values("gain_norm", ascending=False).head(15)

    fig, axes = plt.subplots(1, 2, figsize=(14, 7), sharey=True)
    order = df["feature"].tolist()[::-1]
    axes[0].barh(order, df["gain_norm"].iloc[::-1], color="#3b7dd8")
    axes[0].set_title("XGBoost gain (normalized)")
    axes[0].set_xlabel("gain / max(gain)")
    axes[1].barh(order, df["perm_norm"].iloc[::-1], color="#d8723b")
    axes[1].set_title("Permutation importance (normalized, PR-AUC drop)")
    axes[1].set_xlabel("Δ score / max")
    fig.suptitle("Feature importance — gain vs permutation (top 15 by gain)")
    fig.tight_layout()
    fig.savefig(IMP_COMPARE_PNG, dpi=130)
    plt.close(fig)
    step(f"wrote {IMP_COMPARE_PNG}")


def actionable_segments(sv: np.ndarray, df: pd.DataFrame,
                        feature_cols: list[str]) -> list[dict]:
    step("identifying 3 actionable segments")
    mean_abs = np.mean(np.abs(sv), axis=0)
    order = np.argsort(-mean_abs)
    baseline_rate = float(df["Churn"].mean())
    segs: list[dict] = []
    for i in order:
        feat = feature_cols[i]
        values = df[feat].astype(float).values
        # need spread to define a meaningful split
        if np.unique(values).size < 2:
            continue
        median = float(np.median(values))
        if median == values.max() or median == values.min():
            # try mean if median is degenerate
            median = float(np.mean(values))
        high_mask = values > median
        low_mask = ~high_mask
        if high_mask.sum() < 50 or low_mask.sum() < 50:
            continue
        high_rate = float(df.loc[high_mask, "Churn"].mean())
        low_rate = float(df.loc[low_mask, "Churn"].mean())
        if low_rate <= 0:
            continue
        ratio = high_rate / low_rate
        if abs(high_rate - low_rate) < 0.05:
            continue
        segs.append(dict(
            feature=feat,
            threshold=median,
            high_rate=high_rate,
            low_rate=low_rate,
            baseline_rate=baseline_rate,
            ratio=ratio,
            mean_abs_shap=float(mean_abs[i]),
            n_high=int(high_mask.sum()),
            n_low=int(low_mask.sum()),
        ))
        if len(segs) == 3:
            break
    return segs


def write_segments_md(segs: list[dict]) -> None:
    step(f"writing segments -> {SEGMENTS_MD}")
    lines = ["# Actionable Churn Segments\n",
             "Derived from top features by mean |SHAP|. Each segment splits the "
             "customer base at the feature's median value and compares churn rates.\n"]
    for i, s in enumerate(segs, 1):
        direction = "above" if s["high_rate"] > s["low_rate"] else "below"
        ratio = s["ratio"] if direction == "above" else (s["low_rate"] / s["high_rate"])
        risky_rate = max(s["high_rate"], s["low_rate"])
        safe_rate = min(s["high_rate"], s["low_rate"])
        lines.append(
            f"## Segment {i}: `{s['feature']}`\n"
            f"Customers with `{s['feature']}` {direction} {s['threshold']:.2f} "
            f"churn at **{risky_rate * 100:.1f}%** vs {safe_rate * 100:.1f}% baseline "
            f"— **{ratio:.2f}x more likely** to churn.\n"
            f"- mean |SHAP|: {s['mean_abs_shap']:.4f}\n"
            f"- group sizes: above-median n={s['n_high']}, below-median n={s['n_low']}\n"
            f"- dataset baseline churn rate: {s['baseline_rate'] * 100:.2f}%\n"
        )
    SEGMENTS_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    MODELS.mkdir(parents=True, exist_ok=True)
    model, feature_cols, df = load_all()
    X = df[feature_cols].astype(float).values
    y = df["Churn"].astype(int).values

    sv, expected = compute_shap(model, X, feature_cols)
    save_shap_artifacts(sv, expected)
    plot_shap(sv, X, feature_cols)
    plot_importance_comparison(model, X, y, feature_cols)
    segs = actionable_segments(sv, df, feature_cols)
    write_segments_md(segs)
    with open(INTERPRET_STATS_PKL, "wb") as f:
        pickle.dump({"segments": segs, "expected_value": expected}, f)
    step("DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
