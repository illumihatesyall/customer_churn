"""Modeling: logistic baseline + XGBoost (Optuna-tuned), full metrics + lift chart."""
from __future__ import annotations

import pickle
import sys
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import optuna
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    f1_score,
    precision_recall_curve,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

warnings.filterwarnings("ignore", category=UserWarning)
optuna.logging.set_verbosity(optuna.logging.WARNING)

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_PARQUET = ROOT / "data" / "processed" / "features.parquet"
MODELS = ROOT / "models"
OUT = ROOT / "outputs"
LIFT_PNG = OUT / "lift_chart.png"
MODEL_PKL = MODELS / "churn_model.pkl"
BASELINE_PKL = MODELS / "baseline_model.pkl"
FEATCOLS_PKL = MODELS / "feature_cols.pkl"
THRESHOLD_PKL = MODELS / "threshold.pkl"
METRICS_PKL = MODELS / "metrics.pkl"

N_TRIALS = 50
RANDOM_STATE = 42


def step(msg: str) -> None:
    print(f"[model] {msg}", flush=True)


def load_features() -> pd.DataFrame:
    if not PROCESSED_PARQUET.exists():
        raise FileNotFoundError(f"missing parquet: {PROCESSED_PARQUET} — run etl first")
    return pd.read_parquet(PROCESSED_PARQUET)


def time_split(df: pd.DataFrame):
    step("time-aware split: sort by tenure, first 80%=train, last 20%=test")
    df = df.sort_values("tenure", kind="mergesort").reset_index(drop=True)
    cut = int(len(df) * 0.8)
    train, test = df.iloc[:cut].copy(), df.iloc[cut:].copy()
    step(f"train={len(train)} (churn {train['Churn'].mean():.3f})  "
         f"test={len(test)} (churn {test['Churn'].mean():.3f})")
    return train, test


def features_target(df: pd.DataFrame, feature_cols: list[str] | None = None):
    drop = {"Churn"}
    if feature_cols is None:
        feature_cols = [c for c in df.columns if c not in drop]
    X = df[feature_cols].astype(float).values
    y = df["Churn"].astype(int).values
    return X, y, feature_cols


def train_baseline(X_tr, y_tr) -> Pipeline:
    step("training baseline logistic regression")
    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("lr", LogisticRegression(class_weight="balanced", max_iter=1000)),
    ])
    pipe.fit(X_tr, y_tr)
    return pipe


def tune_xgb(X_tr, y_tr, scale_pos_weight: float) -> dict:
    step(f"Optuna tuning XGBoost ({N_TRIALS} trials, maximize PR-AUC)")
    skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_STATE)

    def objective(trial: optuna.Trial) -> float:
        params = dict(
            n_estimators=trial.suggest_int("n_estimators", 200, 800, step=50),
            max_depth=trial.suggest_int("max_depth", 3, 8),
            learning_rate=trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            subsample=trial.suggest_float("subsample", 0.6, 1.0),
            colsample_bytree=trial.suggest_float("colsample_bytree", 0.6, 1.0),
            min_child_weight=trial.suggest_int("min_child_weight", 1, 10),
            scale_pos_weight=scale_pos_weight,
            objective="binary:logistic",
            eval_metric="aucpr",
            tree_method="hist",
            random_state=RANDOM_STATE,
            n_jobs=-1,
            verbosity=0,
        )
        scores = []
        for tr_idx, va_idx in skf.split(X_tr, y_tr):
            model = XGBClassifier(**params)
            model.fit(X_tr[tr_idx], y_tr[tr_idx])
            p = model.predict_proba(X_tr[va_idx])[:, 1]
            scores.append(average_precision_score(y_tr[va_idx], p))
        return float(np.mean(scores))

    sampler = optuna.samplers.TPESampler(seed=RANDOM_STATE)
    study = optuna.create_study(direction="maximize", sampler=sampler)
    study.optimize(objective, n_trials=N_TRIALS, show_progress_bar=False)
    step(f"best PR-AUC (CV) = {study.best_value:.4f}")
    step(f"best params = {study.best_params}")
    return study.best_params


def fit_final(X_tr, y_tr, best_params: dict, scale_pos_weight: float) -> XGBClassifier:
    step("fitting final XGBoost on full train")
    model = XGBClassifier(
        **best_params,
        scale_pos_weight=scale_pos_weight,
        objective="binary:logistic",
        eval_metric="aucpr",
        tree_method="hist",
        random_state=RANDOM_STATE,
        n_jobs=-1,
        verbosity=0,
    )
    model.fit(X_tr, y_tr)
    return model


def recall_at_top_k(y_true: np.ndarray, y_score: np.ndarray, k_frac: float = 0.1) -> float:
    n = len(y_true)
    k = max(1, int(np.ceil(n * k_frac)))
    order = np.argsort(-y_score)
    top = y_true[order[:k]]
    pos_total = max(1, int(y_true.sum()))
    return float(top.sum() / pos_total)


def lift_at_top_k(y_true: np.ndarray, y_score: np.ndarray, k_frac: float = 0.1) -> float:
    n = len(y_true)
    k = max(1, int(np.ceil(n * k_frac)))
    order = np.argsort(-y_score)
    top_rate = y_true[order[:k]].mean()
    base = y_true.mean()
    if base == 0:
        return float("inf")
    return float(top_rate / base)


def best_f1_threshold(y_true: np.ndarray, y_score: np.ndarray) -> float:
    precision, recall, thresholds = precision_recall_curve(y_true, y_score)
    f1s = 2 * precision * recall / np.clip(precision + recall, 1e-9, None)
    f1s = f1s[:-1]
    if len(thresholds) == 0:
        return 0.5
    best = int(np.argmax(f1s))
    return float(thresholds[best])


def lift_curve_plot(y_true: np.ndarray, y_score: np.ndarray) -> None:
    step(f"writing lift chart -> {LIFT_PNG}")
    order = np.argsort(-y_score)
    y_sorted = y_true[order]
    cum_pos = np.cumsum(y_sorted)
    total_pos = max(1, y_sorted.sum())
    pct_targeted = np.arange(1, len(y_sorted) + 1) / len(y_sorted)
    pct_captured = cum_pos / total_pos
    random_line = pct_targeted

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(pct_targeted * 100, pct_captured * 100, label="Model", color="#3b7dd8", lw=2)
    ax.plot(pct_targeted * 100, random_line * 100, label="Random", color="gray", ls="--")
    ax.axvline(10, color="#d83b5b", ls=":", label="Top 10%")
    ax.set_xlabel("% customers targeted (ranked by predicted churn prob)")
    ax.set_ylabel("% of actual churners captured")
    ax.set_title("Lift / cumulative gains")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(LIFT_PNG, dpi=130)
    plt.close(fig)


def evaluate(name: str, model, X_te, y_te, threshold: float | None = None) -> dict:
    p = model.predict_proba(X_te)[:, 1]
    pr_auc = average_precision_score(y_te, p)
    roc_auc = roc_auc_score(y_te, p)
    r10 = recall_at_top_k(y_te, p, 0.10)
    l10 = lift_at_top_k(y_te, p, 0.10)
    thr = threshold if threshold is not None else best_f1_threshold(y_te, p)
    preds = (p >= thr).astype(int)
    f1 = f1_score(y_te, preds)
    report = classification_report(y_te, preds, digits=3)
    step(f"--- {name} ---")
    step(f"PR-AUC={pr_auc:.4f}  ROC-AUC={roc_auc:.4f}")
    step(f"Recall@top-10% = {r10:.4f}  Lift@top-10% = {l10:.2f}x")
    step(f"Best-F1 threshold = {thr:.4f}  F1 = {f1:.4f}")
    print(report, flush=True)
    return dict(
        name=name, pr_auc=float(pr_auc), roc_auc=float(roc_auc),
        recall_top10=float(r10), lift_top10=float(l10),
        threshold=float(thr), f1=float(f1), report=report, probs=p,
    )


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    MODELS.mkdir(parents=True, exist_ok=True)

    df = load_features()
    train, test = time_split(df)
    X_tr, y_tr, feature_cols = features_target(train)
    X_te, y_te, _ = features_target(test, feature_cols)
    step(f"n_features={len(feature_cols)}")

    pos = int(y_tr.sum())
    neg = int(len(y_tr) - pos)
    spw = neg / max(1, pos)
    step(f"scale_pos_weight = {spw:.3f}  (neg={neg} / pos={pos})")

    baseline = train_baseline(X_tr, y_tr)
    base_metrics = evaluate("baseline (logreg)", baseline, X_te, y_te)

    best_params = tune_xgb(X_tr, y_tr, spw)
    xgb = fit_final(X_tr, y_tr, best_params, spw)
    xgb_metrics = evaluate("xgboost (tuned)", xgb, X_te, y_te)

    lift_curve_plot(y_te, xgb_metrics["probs"])

    step("persisting artifacts")
    with open(MODEL_PKL, "wb") as f:
        pickle.dump(xgb, f)
    with open(BASELINE_PKL, "wb") as f:
        pickle.dump(baseline, f)
    with open(FEATCOLS_PKL, "wb") as f:
        pickle.dump(feature_cols, f)
    with open(THRESHOLD_PKL, "wb") as f:
        pickle.dump(xgb_metrics["threshold"], f)

    serializable = {
        "baseline": {k: v for k, v in base_metrics.items() if k != "probs"},
        "xgboost": {k: v for k, v in xgb_metrics.items() if k != "probs"},
        "best_params": best_params,
        "scale_pos_weight": spw,
        "train_size": len(y_tr),
        "test_size": len(y_te),
    }
    with open(METRICS_PKL, "wb") as f:
        pickle.dump(serializable, f)
    step(f"DONE. wrote {MODEL_PKL.name}, {BASELINE_PKL.name}, {FEATCOLS_PKL.name}, "
         f"{THRESHOLD_PKL.name}, {METRICS_PKL.name}, {LIFT_PNG.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
