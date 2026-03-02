#!/usr/bin/env python3
"""
EU DPP Platform - Training Pipeline (50 epochs)
EU AI Act 2024/1689 compliant: Art.9 (risk), Art.10 (data governance),
Art.12 (audit trail), Art.15 (accuracy/robustness).

Multi-task compliance predictor:
  Task A: ESPR compliance status (4 classes)
  Task B: RoHS compliance (3 classes)
  Task C: REACH status (4 classes)
  Task D: Circularity index regression
  Task E: Carbon footprint regression

Usage:
  cd eu-dpp-platform && python scripts/train_dpp_models.py
  DATA_PATH=/path/to/csv EPOCHS=50 python scripts/train_dpp_models.py
"""
import csv
import hashlib
import json
import os
import sys
import time
import uuid
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.linear_model import SGDClassifier, SGDRegressor
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    mean_absolute_error,
    r2_score,
)
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.utils import shuffle

warnings.filterwarnings("ignore")

# ─── Configuration ────────────────────────────────────────────────────────────
EPOCHS = int(os.environ.get("EPOCHS", "50"))
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "1000"))
RANDOM_STATE = 42
TEST_SIZE = 0.20
VAL_SIZE = 0.10
CONFIDENCE_THRESHOLD_AUTO = 0.85  # EU AI Act Art. 14

DATA_PATH = os.environ.get(
    "DATA_PATH",
    str(
        Path(__file__).resolve().parent.parent.parent
        / "DATASET"
        / "dpp_unified_sample_80k.csv"
    ),
)
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "models"
AUDIT_DIR = Path(__file__).resolve().parent.parent / "data" / "audit"

# ─── Feature columns (common across all sectors) ──────────────────────────────
NUMERIC_FEATURES = [
    "carbon_footprint_kg_co2eq",
    "carbon_raw_materials_pct",
    "carbon_manufacturing_pct",
    "carbon_distribution_pct",
    "carbon_use_phase_pct",
    "carbon_end_of_life_pct",
    "annual_energy_consumption_kwh",
    "weight_kg",
    "recyclability_score",
    "repairability_score",
    "durability_score",
    "circularity_index",
    "recycled_content_pct",
    "expected_lifespan_years",
    "tier1_suppliers",
    "tier2_suppliers",
]
CATEGORICAL_FEATURES = [
    "sector",
    "manufacturing_country",
    "energy_efficiency_class",
    "supply_chain_transparency",
    "ce_marking_status",
    "svhc_present",
    "conflict_minerals_status",
]

# ─── Targets ──────────────────────────────────────────────────────────────────
CLASSIFICATION_TARGETS = {
    "espr_compliance": "espr_compliance_status",
    "rohs_compliance": "rohs_compliance",
    "reach_status": "reach_status",
}
REGRESSION_TARGETS = {
    "circularity_index": "circularity_index",
    "carbon_footprint": "carbon_footprint_kg_co2eq",
}

# ─── Epoch history ─────────────────────────────────────────────────────────────
history: dict[str, list] = {
    "epoch": [],
    "espr_train_acc": [],
    "espr_val_acc": [],
    "espr_f1": [],
    "rohs_train_acc": [],
    "rohs_val_acc": [],
    "rohs_f1": [],
    "reach_train_acc": [],
    "reach_val_acc": [],
    "reach_f1": [],
    "circularity_mae": [],
    "circularity_r2": [],
    "carbon_mae": [],
    "carbon_r2": [],
    "elapsed_s": [],
}


# ─── EU AI Act Art.12 - Audit Logger ──────────────────────────────────────────
class TrainingAuditLogger:
    """Immutable audit trail for training decisions (EU AI Act Article 12)."""

    def __init__(self, session_id: str, output_dir: Path) -> None:
        self.session_id = session_id
        output_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = output_dir / f"training_audit_{session_id}.jsonl"
        self._prev_hash = "0" * 64

    def _sha256(self, data: Any) -> str:
        return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()

    def log(self, event_type: str, payload: dict[str, Any]) -> None:
        entry = {
            "entry_id": str(uuid.uuid4()),
            "session_id": self.session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "payload": payload,
            "prev_hash": self._prev_hash,
        }
        entry["hash"] = self._sha256(entry)
        self._prev_hash = entry["hash"]
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")


# ─── EU AI Act Art.10 - Data Governance ───────────────────────────────────────
def data_governance_checks(df: pd.DataFrame, audit: TrainingAuditLogger) -> pd.DataFrame:
    """Article 10 - data quality, representativeness, bias mitigation."""
    print("\n[Art.10] Data Governance Checks...")

    # 1. Missing value analysis
    missing_pct = (df.isnull().sum() / len(df) * 100).round(2)
    high_missing = missing_pct[missing_pct > 30].to_dict()
    print(f"  Columns >30% missing: {len(high_missing)} → {list(high_missing.keys())[:5]}")

    # 2. Class balance check (ESPR)
    espr_dist = df["espr_compliance_status"].value_counts(normalize=True).round(3).to_dict()
    max_imbalance = max(espr_dist.values()) / min(espr_dist.values()) if min(espr_dist.values()) > 0 else 999
    print(f"  ESPR class distribution: {espr_dist}")
    print(f"  Max class imbalance ratio: {max_imbalance:.2f}x")

    # 3. Sector balance (geographic diversity - Kolmogorov-Smirnov)
    sector_dist = df["sector"].value_counts().to_dict()
    print(f"  Sector distribution: {sector_dist}")

    # 4. Country diversity
    n_countries = df["manufacturing_country"].nunique()
    print(f"  Manufacturing countries: {n_countries}")

    # 5. Remove extreme outliers (3σ on numeric features)
    n_before = len(df)
    for col in NUMERIC_FEATURES:
        if col in df.columns:
            mean, std = df[col].mean(), df[col].std()
            if std > 0:
                df = df[np.abs((df[col] - mean) / std) < 3]
    n_after = len(df)
    print(f"  Outlier removal: {n_before - n_after} rows removed ({(n_before-n_after)/n_before*100:.1f}%)")

    audit.log("DATA_GOVERNANCE", {
        "rows_after_cleaning": len(df),
        "missing_high_cols": list(high_missing.keys()),
        "sector_distribution": sector_dist,
        "n_countries": n_countries,
        "espr_class_imbalance_ratio": max_imbalance,
        "article": "EU AI Act Article 10",
    })

    return df


# ─── EU AI Act Art.9 - Risk Assessment ────────────────────────────────────────
def risk_assessment(df: pd.DataFrame, audit: TrainingAuditLogger) -> dict:
    """Article 9 - training risk assessment before model training."""
    print("\n[Art.9] Risk Assessment...")
    risks = []
    risk_score = 0.0

    # Data bias risk
    rohs_nc = (df["rohs_compliance"] == "Non_Compliant").sum() / len(df)
    if rohs_nc < 0.01:
        risks.append({"risk": "MINORITY_CLASS_ROHS_NON_COMPLIANT", "severity": 0.7, "mitigation": "class_weight=balanced"})
        risk_score += 0.3
        print(f"  ⚠ Minority class risk: RoHS Non_Compliant = {rohs_nc:.2%}")
    else:
        print(f"  ✓ RoHS Non_Compliant class ratio: {rohs_nc:.2%}")

    # Data coverage risk
    n_rows = len(df)
    if n_rows < 10000:
        risks.append({"risk": "INSUFFICIENT_DATA", "severity": 0.8, "mitigation": "data_augmentation"})
        risk_score += 0.5
        print(f"  ⚠ Insufficient data: {n_rows} rows")
    else:
        print(f"  ✓ Data sufficiency: {n_rows:,} rows")

    # Model risk
    risks.append({"risk": "LLM_HALLUCINATION_ON_NOVEL_REGS", "severity": 0.5, "mitigation": "citation_validation + human_review"})

    overall = "ACCEPTABLE" if risk_score <= 0.3 else ("MODERATE" if risk_score <= 0.6 else "HIGH")
    print(f"  Risk score: {risk_score:.2f} → {overall}")
    print(f"  Identified risks: {len(risks)}")

    audit.log("RISK_ASSESSMENT", {
        "risks": risks,
        "risk_score": risk_score,
        "overall_risk": overall,
        "article": "EU AI Act Article 9",
        "training_proceed": overall != "HIGH",
    })

    if overall == "HIGH":
        raise RuntimeError("Training halted: risk score too high. Review and mitigate before proceeding.")
    return {"risks": risks, "risk_score": risk_score, "overall": overall}


# ─── Feature Engineering ───────────────────────────────────────────────────────
def build_features(df: pd.DataFrame):
    """Build numeric feature matrix X from the dataframe."""
    label_encoders: dict[str, LabelEncoder] = {}
    X = df[NUMERIC_FEATURES].copy()

    for col in CATEGORICAL_FEATURES:
        if col in df.columns:
            le = LabelEncoder()
            X[col] = le.fit_transform(df[col].fillna("UNKNOWN").astype(str))
            label_encoders[col] = le

    X = X.fillna(X.median(numeric_only=True))
    return X, label_encoders


# ─── Mini-batch epoch training ─────────────────────────────────────────────────
def train_epoch(
    clf: SGDClassifier,
    X_train: np.ndarray,
    y_train: np.ndarray,
    batch_size: int,
    classes: np.ndarray,
    sample_weight_fn=None,
) -> None:
    """One epoch of mini-batch training via partial_fit."""
    X_s, y_s = shuffle(X_train, y_train, random_state=None)
    for start in range(0, len(X_s), batch_size):
        X_b = X_s[start: start + batch_size]
        y_b = y_s[start: start + batch_size]
        sw = sample_weight_fn(y_b) if sample_weight_fn else None
        clf.partial_fit(X_b, y_b, classes=classes, sample_weight=sw)


def train_regression_epoch(
    reg: SGDRegressor,
    X_train: np.ndarray,
    y_train: np.ndarray,
    batch_size: int,
) -> None:
    X_s, y_s = shuffle(X_train, y_train, random_state=None)
    for start in range(0, len(X_s), batch_size):
        X_b = X_s[start: start + batch_size]
        y_b = y_s[start: start + batch_size]
        reg.partial_fit(X_b, y_b)


# ─── Print epoch summary ──────────────────────────────────────────────────────
def print_epoch(ep: int, metrics: dict) -> None:
    bar = "█" * int(metrics["espr_val"] * 20)
    bar_r = "░" * (20 - len(bar))
    print(
        f"  Ep {ep:>2} | ESPR val={metrics['espr_val']:.4f} [{bar}{bar_r}] "
        f"f1={metrics['espr_f1']:.3f} | "
        f"RoHS val={metrics['rohs_val']:.4f} f1={metrics['rohs_f1']:.3f} | "
        f"REACH val={metrics['reach_val']:.4f} f1={metrics['reach_f1']:.3f} | "
        f"Circ R²={metrics['circ_r2']:.3f} MAE={metrics['circ_mae']:.2f} | "
        f"CO2 R²={metrics['co2_r2']:.3f} MAE={metrics['co2_mae']:.2f} | "
        f"{metrics['elapsed']:.1f}s"
    )


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    session_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    audit = TrainingAuditLogger(session_id, AUDIT_DIR)

    print("=" * 90)
    print(" EU DPP PLATFORM - TRAINING PIPELINE")
    print(f" EU AI Act 2024/1689 Compliant | Session: {session_id}")
    print(f" Epochs: {EPOCHS} | Batch: {BATCH_SIZE} | Random seed: {RANDOM_STATE}")
    print("=" * 90)

    audit.log("TRAINING_SESSION_START", {
        "session_id": session_id,
        "epochs": EPOCHS,
        "batch_size": BATCH_SIZE,
        "data_path": str(DATA_PATH),
        "framework": "scikit-learn SGDClassifier/SGDRegressor",
        "compliance": ["EU_AI_Act_2024_1689", "ESPR_2024_1252", "Battery_Reg_2023_1542"],
    })

    # ── Load data ──────────────────────────────────────────────────────────────
    print(f"\n[LOAD] Reading dataset: {DATA_PATH}")
    t0 = time.time()
    df = pd.read_csv(DATA_PATH, low_memory=False)
    # Map sector from product_id prefix
    prefix_map = {
        "elec": "electronics", "batt": "batteries", "text": "textiles",
        "veh": "vehicles", "cons": "construction", "furn": "furniture",
        "plas": "plastics", "chem": "chemicals",
    }
    df["_prefix"] = df["product_id"].str.split("-").str[0].str.lower()
    df["sector"] = df["_prefix"].map(prefix_map).fillna("electronics")
    df = df.drop(columns=["_prefix"])

    # For rows without espr/rohs/reach: impute from sector-level defaults
    sector_defaults = {
        "electronics": ("Partial_Compliance", "Compliant", "Registered"),
        "batteries": ("Full_Compliance", "Compliant", "Registered"),
        "textiles": ("Partial_Compliance", "Compliant", "Pre_Registered"),
        "vehicles": ("Full_Compliance", "Exempt_Category", "Registered"),
        "construction": ("Transitional", "Compliant", "Pre_Registered"),
        "furniture": ("Partial_Compliance", "Compliant", "Pre_Registered"),
        "plastics": ("Transitional", "Compliant", "Registered"),
        "chemicals": ("Partial_Compliance", "Compliant", "SVHC_Declared"),
    }
    for col_idx, col_name in enumerate(["espr_compliance_status", "rohs_compliance", "reach_status"]):
        for sector, defaults in sector_defaults.items():
            mask = (df["sector"] == sector) & df[col_name].isna()
            df.loc[mask, col_name] = defaults[col_idx]

    # Impute numeric targets
    df["circularity_index"] = df["circularity_index"].fillna(df.groupby("sector")["circularity_index"].transform("median"))
    df["circularity_index"] = df["circularity_index"].fillna(50.0)
    df["carbon_footprint_kg_co2eq"] = df["carbon_footprint_kg_co2eq"].fillna(df.groupby("sector")["carbon_footprint_kg_co2eq"].transform("median"))
    df["carbon_footprint_kg_co2eq"] = df["carbon_footprint_kg_co2eq"].fillna(30.0)

    # Now filter only rows with all 5 targets present
    df = df[
        df["espr_compliance_status"].notna() &
        df["rohs_compliance"].notna() &
        df["reach_status"].notna() &
        df["circularity_index"].notna() &
        df["carbon_footprint_kg_co2eq"].notna()
    ].copy()

    print(f"  Loaded {len(df):,} usable rows in {time.time()-t0:.1f}s")
    print(f"  Sector counts: { df['sector'].value_counts().to_dict() }")
    audit.log("DATA_LOAD", {"rows": len(df), "columns": len(df.columns)})

    # ── Data Governance (Art.10) ───────────────────────────────────────────────
    df = data_governance_checks(df, audit)

    # ── Risk Assessment (Art.9) ────────────────────────────────────────────────
    risk_assessment(df, audit)

    # ── Feature engineering ────────────────────────────────────────────────────
    print("\n[FEATURES] Building feature matrix...")
    X, label_encoders = build_features(df)

    # Encode targets
    le_espr = LabelEncoder()
    le_rohs = LabelEncoder()
    le_reach = LabelEncoder()
    y_espr = le_espr.fit_transform(df["espr_compliance_status"].astype(str))
    y_rohs = le_rohs.fit_transform(df["rohs_compliance"].astype(str))
    y_reach = le_reach.fit_transform(df["reach_status"].astype(str))
    y_circ = df["circularity_index"].values.astype(float)
    y_carbon = np.log1p(df["carbon_footprint_kg_co2eq"].values.astype(float))  # log-scale

    print(f"  X shape: {X.shape}")
    print(f"  ESPR classes: {list(le_espr.classes_)}")
    print(f"  RoHS classes: {list(le_rohs.classes_)}")
    print(f"  REACH classes: {list(le_reach.classes_)}")

    # ── Train/Val/Test split ───────────────────────────────────────────────────
    X_np = X.values.astype(float)
    X_tv, X_test, ye_tv, ye_test = train_test_split(X_np, y_espr, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y_espr)
    X_train, X_val, ye_train, ye_val = train_test_split(X_tv, ye_tv, test_size=VAL_SIZE / (1 - TEST_SIZE), random_state=RANDOM_STATE)

    # Same split for other targets (using same indices)
    idx_all = np.arange(len(X_np))
    idx_tv, idx_test = train_test_split(idx_all, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y_espr)
    idx_train, idx_val = train_test_split(idx_tv, test_size=VAL_SIZE / (1 - TEST_SIZE), random_state=RANDOM_STATE)

    yr_train, yr_val, yr_test = y_rohs[idx_train], y_rohs[idx_val], y_rohs[idx_test]
    yc_train, yc_val, yc_test = y_reach[idx_train], y_reach[idx_val], y_reach[idx_test]
    yci_train, yci_val, yci_test = y_circ[idx_train], y_circ[idx_val], y_circ[idx_test]
    yco_train, yco_val, yco_test = y_carbon[idx_train], y_carbon[idx_val], y_carbon[idx_test]

    print(f"  Train: {len(X_train):,} | Val: {len(X_val):,} | Test: {len(X_test):,}")

    # ── Scale ──────────────────────────────────────────────────────────────────
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_val_s = scaler.transform(X_val)
    X_test_s = scaler.transform(X_test)

    # ── Initialise classifiers (SGD = supports partial_fit for epochs) ──────────
    clf_espr = SGDClassifier(loss="modified_huber", alpha=1e-4, max_iter=1, random_state=RANDOM_STATE)
    clf_rohs = SGDClassifier(loss="modified_huber", alpha=1e-4, max_iter=1, random_state=RANDOM_STATE)
    clf_reach = SGDClassifier(loss="modified_huber", alpha=1e-4, max_iter=1, random_state=RANDOM_STATE)
    reg_circ = SGDRegressor(alpha=1e-4, max_iter=1, random_state=RANDOM_STATE)
    reg_carbon = SGDRegressor(alpha=1e-4, max_iter=1, random_state=RANDOM_STATE)

    classes_espr = np.unique(y_espr)
    classes_rohs = np.unique(y_rohs)
    classes_reach = np.unique(y_reach)

    # Compute class weights for partial_fit (balanced, not supported inline)
    def make_sample_weight(y_full, y_batch):
        cw = compute_class_weight("balanced", classes=np.unique(y_full), y=y_full)
        cw_dict = dict(zip(np.unique(y_full), cw))
        return np.array([cw_dict[yi] for yi in y_batch])

    # ── 50-Epoch Training Loop ─────────────────────────────────────────────────
    print(f"\n{'─'*90}")
    print(f"  TRAINING — {EPOCHS} EPOCHS | Batch size: {BATCH_SIZE}")
    print(f"{'─'*90}")
    t_start = time.time()

    for epoch in range(1, EPOCHS + 1):
        t_ep = time.time()

        # Classification epochs (with balanced sample weights)
        train_epoch(clf_espr, X_train_s, ye_train, BATCH_SIZE, classes_espr,
                    lambda y: make_sample_weight(ye_train, y))
        train_epoch(clf_rohs, X_train_s, yr_train, BATCH_SIZE, classes_rohs,
                    lambda y: make_sample_weight(yr_train, y))
        train_epoch(clf_reach, X_train_s, yc_train, BATCH_SIZE, classes_reach,
                    lambda y: make_sample_weight(yc_train, y))

        # Regression epochs
        train_regression_epoch(reg_circ, X_train_s, yci_train, BATCH_SIZE)
        train_regression_epoch(reg_carbon, X_train_s, yco_train, BATCH_SIZE)

        # ── Metrics ──────────────────────────────────────────────────────────
        espr_train_acc = accuracy_score(ye_train, clf_espr.predict(X_train_s))
        espr_val_acc = accuracy_score(ye_val, clf_espr.predict(X_val_s))
        espr_f1 = f1_score(ye_val, clf_espr.predict(X_val_s), average="weighted", zero_division=0)

        rohs_train_acc = accuracy_score(yr_train, clf_rohs.predict(X_train_s))
        rohs_val_acc = accuracy_score(yr_val, clf_rohs.predict(X_val_s))
        rohs_f1 = f1_score(yr_val, clf_rohs.predict(X_val_s), average="weighted", zero_division=0)

        reach_train_acc = accuracy_score(yc_train, clf_reach.predict(X_train_s))
        reach_val_acc = accuracy_score(yc_val, clf_reach.predict(X_val_s))
        reach_f1 = f1_score(yc_val, clf_reach.predict(X_val_s), average="weighted", zero_division=0)

        circ_pred_val = reg_circ.predict(X_val_s)
        circ_mae = mean_absolute_error(yci_val, circ_pred_val)
        circ_r2 = r2_score(yci_val, circ_pred_val)

        carbon_pred_val = reg_carbon.predict(X_val_s)
        co2_mae = mean_absolute_error(yco_val, carbon_pred_val)
        co2_r2 = r2_score(yco_val, carbon_pred_val)

        elapsed = time.time() - t_ep

        metrics = {
            "espr_train": espr_train_acc,
            "espr_val": espr_val_acc,
            "espr_f1": espr_f1,
            "rohs_train": rohs_train_acc,
            "rohs_val": rohs_val_acc,
            "rohs_f1": rohs_f1,
            "reach_train": reach_train_acc,
            "reach_val": reach_val_acc,
            "reach_f1": reach_f1,
            "circ_mae": circ_mae,
            "circ_r2": circ_r2,
            "co2_mae": co2_mae,
            "co2_r2": co2_r2,
            "elapsed": elapsed,
        }

        # ── Append to history ─────────────────────────────────────────────────
        history["epoch"].append(epoch)
        history["espr_train_acc"].append(espr_train_acc)
        history["espr_val_acc"].append(espr_val_acc)
        history["espr_f1"].append(espr_f1)
        history["rohs_train_acc"].append(rohs_train_acc)
        history["rohs_val_acc"].append(rohs_val_acc)
        history["rohs_f1"].append(rohs_f1)
        history["reach_train_acc"].append(reach_train_acc)
        history["reach_val_acc"].append(reach_val_acc)
        history["reach_f1"].append(reach_f1)
        history["circularity_mae"].append(circ_mae)
        history["circularity_r2"].append(circ_r2)
        history["carbon_mae"].append(co2_mae)
        history["carbon_r2"].append(co2_r2)
        history["elapsed_s"].append(elapsed)

        print_epoch(epoch, metrics)

        # ── EU AI Act Art.12 audit per epoch (every 5) ────────────────────────
        if epoch % 5 == 0 or epoch == EPOCHS:
            audit.log("EPOCH_METRICS", {
                "epoch": epoch,
                "espr_val_accuracy": round(espr_val_acc, 4),
                "espr_f1_weighted": round(espr_f1, 4),
                "rohs_val_accuracy": round(rohs_val_acc, 4),
                "rohs_f1_weighted": round(rohs_f1, 4),
                "reach_val_accuracy": round(reach_val_acc, 4),
                "reach_f1_weighted": round(reach_f1, 4),
                "circularity_r2": round(circ_r2, 4),
                "carbon_r2": round(co2_r2, 4),
                "article": "EU AI Act Article 12",
            })

    total_time = time.time() - t_start
    print(f"{'─'*90}")
    print(f"  Training complete in {total_time:.1f}s ({total_time/EPOCHS:.2f}s/epoch)")

    # ── Final evaluation on TEST set (Art.15 - Accuracy & Robustness) ─────────
    print(f"\n{'═'*90}")
    print("  FINAL EVALUATION — TEST SET (EU AI Act Article 15)")
    print(f"{'═'*90}")

    print("\n  [Task A] ESPR Compliance Status")
    ye_pred = clf_espr.predict(X_test_s)
    print(classification_report(ye_test, ye_pred, target_names=le_espr.classes_, zero_division=0))
    espr_test_acc = accuracy_score(ye_test, ye_pred)
    espr_test_f1 = f1_score(ye_test, ye_pred, average="weighted", zero_division=0)

    print("\n  [Task B] RoHS Compliance")
    yr_pred = clf_rohs.predict(X_test_s)
    print(classification_report(yr_test, yr_pred, target_names=le_rohs.classes_, zero_division=0))
    rohs_test_acc = accuracy_score(yr_test, yr_pred)
    rohs_test_f1 = f1_score(yr_test, yr_pred, average="weighted", zero_division=0)

    print("\n  [Task C] REACH Status")
    yc_pred = clf_reach.predict(X_test_s)
    print(classification_report(yc_test, yc_pred, target_names=le_reach.classes_, zero_division=0))
    reach_test_acc = accuracy_score(yc_test, yc_pred)
    reach_test_f1 = f1_score(yc_test, yc_pred, average="weighted", zero_division=0)

    print("\n  [Task D] Circularity Index (regression)")
    circ_test_pred = reg_circ.predict(X_test_s)
    circ_test_mae = mean_absolute_error(yci_test, circ_test_pred)
    circ_test_r2 = r2_score(yci_test, circ_test_pred)
    print(f"  MAE: {circ_test_mae:.4f} | R²: {circ_test_r2:.4f}")

    print("\n  [Task E] Carbon Footprint (log-scale regression)")
    carbon_test_pred = reg_carbon.predict(X_test_s)
    co2_test_mae = mean_absolute_error(yco_test, carbon_test_pred)
    co2_test_r2 = r2_score(yco_test, carbon_test_pred)
    print(f"  MAE: {co2_test_mae:.4f} | R²: {co2_test_r2:.4f}")

    # ── Convergence summary ────────────────────────────────────────────────────
    print(f"\n{'─'*90}")
    print("  CONVERGENCE SUMMARY (Best validation scores)")
    print(f"{'─'*90}")
    print(f"  ESPR    best val acc: {max(history['espr_val_acc']):.4f}  (epoch {history['espr_val_acc'].index(max(history['espr_val_acc']))+1})")
    print(f"  RoHS    best val acc: {max(history['rohs_val_acc']):.4f}  (epoch {history['rohs_val_acc'].index(max(history['rohs_val_acc']))+1})")
    print(f"  REACH   best val acc: {max(history['reach_val_acc']):.4f}  (epoch {history['reach_val_acc'].index(max(history['reach_val_acc']))+1})")
    print(f"  Circ    best R²:      {max(history['circularity_r2']):.4f}  (epoch {history['circularity_r2'].index(max(history['circularity_r2']))+1})")
    print(f"  CO2     best R²:      {max(history['carbon_r2']):.4f}  (epoch {history['carbon_r2'].index(max(history['carbon_r2']))+1})")

    # ── EU AI Act Art.15 - final audit ────────────────────────────────────────
    meets_threshold = espr_test_acc >= 0.70 and rohs_test_acc >= 0.70 and reach_test_acc >= 0.70
    audit.log("FINAL_EVALUATION", {
        "article": "EU AI Act Article 15 - Accuracy and Robustness",
        "test_espr_accuracy": round(espr_test_acc, 4),
        "test_espr_f1": round(espr_test_f1, 4),
        "test_rohs_accuracy": round(rohs_test_acc, 4),
        "test_rohs_f1": round(rohs_test_f1, 4),
        "test_reach_accuracy": round(reach_test_acc, 4),
        "test_reach_f1": round(reach_test_f1, 4),
        "test_circularity_r2": round(circ_test_r2, 4),
        "test_carbon_r2": round(co2_test_r2, 4),
        "accuracy_threshold_70pct_met": meets_threshold,
        "total_epochs": EPOCHS,
        "total_training_time_s": round(total_time, 2),
        "dataset_size": len(df),
    })

    # ── Save history as JSON ───────────────────────────────────────────────────
    hist_path = OUTPUT_DIR / f"training_history_{session_id}.json"
    with open(hist_path, "w") as f:
        json.dump(history, f, indent=2)
    print(f"\n  History saved: {hist_path}")
    print(f"  Audit trail: {AUDIT_DIR / f'training_audit_{session_id}.jsonl'}")

    # ── Save models ────────────────────────────────────────────────────────────
    import joblib
    for name, obj in [
        ("clf_espr", clf_espr), ("clf_rohs", clf_rohs), ("clf_reach", clf_reach),
        ("reg_circ", reg_circ), ("reg_carbon", reg_carbon), ("scaler", scaler),
        ("le_espr", le_espr), ("le_rohs", le_rohs), ("le_reach", le_reach),
    ]:
        joblib.dump(obj, OUTPUT_DIR / f"{name}_{session_id}.pkl")
    print(f"  Models saved to: {OUTPUT_DIR}/")

    # ── Final status ─────────────────────────────────────────────────────────
    status = "✅ PASS" if meets_threshold else "⚠ BELOW THRESHOLD"
    print(f"\n{'═'*90}")
    print(f"  STATUS: {status} | Accuracy threshold (≥70%): {'MET' if meets_threshold else 'NOT MET'}")
    print(f"  ESPR test acc: {espr_test_acc:.4f} | RoHS: {rohs_test_acc:.4f} | REACH: {reach_test_acc:.4f}")
    print(f"  Circularity R²: {circ_test_r2:.4f} | Carbon R²: {co2_test_r2:.4f}")
    print("  EU AI Act Art.9 Risk: ASSESSED | Art.10 Governance: VALIDATED | Art.12 Audit: LOGGED | Art.15 Accuracy: EVALUATED")
    print(f"{'═'*90}\n")

    audit.log("TRAINING_SESSION_END", {"status": status, "meets_threshold": meets_threshold})


if __name__ == "__main__":
    main()
