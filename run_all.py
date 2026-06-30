"""Portable equivalent of `make all` for systems without GNU make."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = ["etl.py", "eda.py", "model.py", "interpret.py", "memo.py"]

EXPECTED = [
    "data/raw/telco_churn.csv",
    "data/processed/features.parquet",
    "data/processed/churn.duckdb",
    "outputs/cohort_churn.png",
    "outputs/segment_churn.png",
    "outputs/correlation.png",
    "outputs/class_imbalance.png",
    "outputs/eda_narrative.md",
    "models/churn_model.pkl",
    "models/baseline_model.pkl",
    "models/feature_cols.pkl",
    "models/threshold.pkl",
    "outputs/lift_chart.png",
    "data/shap_values.npy",
    "data/shap_expected_value.npy",
    "outputs/shap_beeswarm.png",
    "outputs/shap_bar.png",
    "outputs/feature_importance_comparison.png",
    "outputs/segments.md",
    "outputs/executive_memo.md",
]


def main() -> int:
    for s in SCRIPTS:
        path = ROOT / "src" / s
        print(f"\n========== running {s} ==========", flush=True)
        proc = subprocess.run([sys.executable, str(path)], cwd=str(ROOT))
        if proc.returncode != 0:
            print(f"FAILED in {s} (exit {proc.returncode})", flush=True)
            return proc.returncode

    print("\n========== verifying outputs ==========", flush=True)
    missing = [p for p in EXPECTED if not (ROOT / p).exists()]
    if missing:
        print("MISSING:", flush=True)
        for p in missing:
            print(f"  - {p}", flush=True)
        return 1
    for p in EXPECTED:
        print(f"OK  {p}", flush=True)
    print(f"\nAll {len(EXPECTED)} expected artifacts present.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
