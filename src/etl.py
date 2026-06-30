"""ETL: load raw Telco churn CSV, clean, engineer features, persist to parquet + DuckDB."""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = ROOT / "data" / "raw" / "telco_churn.csv"
PROCESSED_PARQUET = ROOT / "data" / "processed" / "features.parquet"
DUCKDB_PATH = ROOT / "data" / "processed" / "churn.duckdb"
DATASET_URL = (
    "https://raw.githubusercontent.com/IBM/"
    "telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv"
)

SERVICE_COLS = [
    "PhoneService", "MultipleLines", "OnlineSecurity", "OnlineBackup",
    "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies",
]


def step(msg: str) -> None:
    print(f"[etl] {msg}", flush=True)


def ensure_raw() -> None:
    if RAW_CSV.exists():
        step(f"raw file present: {RAW_CSV}")
        return
    RAW_CSV.parent.mkdir(parents=True, exist_ok=True)
    step(f"downloading dataset from {DATASET_URL}")
    resp = requests.get(DATASET_URL, timeout=60)
    resp.raise_for_status()
    RAW_CSV.write_bytes(resp.content)
    step(f"wrote {len(resp.content)} bytes to {RAW_CSV}")


def load_raw() -> pd.DataFrame:
    if not RAW_CSV.exists():
        raise FileNotFoundError(f"raw file missing: {RAW_CSV}")
    step(f"loading {RAW_CSV}")
    df = pd.read_csv(RAW_CSV)
    step(f"loaded shape={df.shape}")
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    step("cleaning: TotalCharges blanks -> 0.0, drop customerID, encode target")
    df = df.copy()
    df["TotalCharges"] = df["TotalCharges"].replace(r"^\s*$", "0", regex=True)
    df["TotalCharges"] = df["TotalCharges"].astype(float)
    df = df.drop(columns=["customerID"])
    df["Churn"] = (df["Churn"].astype(str).str.strip().str.lower() == "yes").astype(int)
    return df


def _count_active_services(row: pd.Series) -> int:
    count = 0
    for col in SERVICE_COLS:
        val = str(row[col]).strip().lower()
        if val in {"yes"}:
            count += 1
    return count


def feature_engineer(df: pd.DataFrame) -> pd.DataFrame:
    step("feature engineering")
    df = df.copy()
    df["avg_monthly_charges"] = df["TotalCharges"] / (df["tenure"] + 1)
    df["active_services"] = df.apply(_count_active_services, axis=1)
    df["charges_per_service"] = df["MonthlyCharges"] / (df["active_services"] + 1)
    df["is_high_value"] = (df["MonthlyCharges"] > 70).astype(int)
    df["tenure_bucket"] = pd.cut(
        df["tenure"],
        bins=[-0.1, 12, 24, 48, df["tenure"].max() + 1],
        labels=["0-12", "13-24", "25-48", "49+"],
    ).astype(str)

    contract_map = {"Month-to-month": 0, "One year": 1, "Two year": 2}
    if not set(df["Contract"].unique()).issubset(contract_map.keys()):
        raise ValueError(f"unexpected Contract values: {df['Contract'].unique()}")
    df["Contract_ord"] = df["Contract"].map(contract_map).astype(int)
    df = df.drop(columns=["Contract"])

    df = pd.get_dummies(
        df, columns=["InternetService", "PaymentMethod"], prefix=["IS", "PM"], dtype=int
    )

    binary_cols = [
        "gender", "Partner", "Dependents", "PhoneService", "PaperlessBilling",
    ]
    for col in binary_cols:
        df[col] = df[col].astype(str).str.strip()
    df["gender"] = (df["gender"].str.lower() == "male").astype(int)
    for col in ["Partner", "Dependents", "PhoneService", "PaperlessBilling"]:
        df[col] = (df[col].str.lower() == "yes").astype(int)

    triple_cols = [
        "MultipleLines", "OnlineSecurity", "OnlineBackup", "DeviceProtection",
        "TechSupport", "StreamingTV", "StreamingMovies",
    ]
    df = pd.get_dummies(df, columns=triple_cols, prefix=triple_cols, dtype=int)

    df = pd.get_dummies(df, columns=["tenure_bucket"], prefix="tb", dtype=int)
    return df


def validate(df: pd.DataFrame) -> None:
    step("validating")
    key_cols = ["tenure", "MonthlyCharges", "TotalCharges", "Churn"]
    nulls = df[key_cols].isnull().sum().sum()
    assert nulls == 0, f"unexpected nulls in key cols: {df[key_cols].isnull().sum()}"
    assert len(df) > 7000, f"row count too low: {len(df)}"
    rate = df["Churn"].mean()
    assert 0.1 < rate < 0.4, f"churn rate {rate:.3f} outside [0.1, 0.4]"
    step(f"validation OK: rows={len(df)} churn_rate={rate:.4f}")


def persist(df: pd.DataFrame) -> None:
    PROCESSED_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    step(f"writing parquet -> {PROCESSED_PARQUET}")
    df.to_parquet(PROCESSED_PARQUET, index=False)
    step(f"registering DuckDB table 'features' -> {DUCKDB_PATH}")
    con = duckdb.connect(str(DUCKDB_PATH))
    con.execute("DROP TABLE IF EXISTS features")
    con.execute(
        f"CREATE TABLE features AS SELECT * FROM read_parquet('{PROCESSED_PARQUET.as_posix()}')"
    )
    rows = con.execute("SELECT COUNT(*) FROM features").fetchone()[0]
    con.close()
    step(f"DuckDB rows={rows}")


def main() -> int:
    ensure_raw()
    raw = load_raw()
    cleaned = clean(raw)
    feats = feature_engineer(cleaned)
    validate(feats)
    persist(feats)
    step(f"DONE. columns={len(feats.columns)} rows={len(feats)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
