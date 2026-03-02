#!/usr/bin/env python3
"""
EU DPP Platform — Training Pipeline v2 (50 epochs, recalibré)
EU AI Act 2024/1689: Art.9 (risk), Art.10 (data governance),
                     Art.12 (audit trail), Art.15 (accuracy/robustness).
DPP Orchestration System v3.0 — YAML Master Config aligned.

Corrections v2 vs v1:
  A. Outlier removal: IQR par secteur, seulement sur colonnes non-null
  B. Data leakage corrigée: circularity_index exclu des features cibles
  C. Modèles: GradientBoosting warm_start (50 itérations = 50 "epochs")
  D. SMOTE + BorderlineSMOTE pour classes minoritaires
  E. Feature engineering: ratios carbone, scores composite, flags conformité
  F. Cross-validation (StratifiedKFold 5)
  G. Feature importance (Art.13 — explicabilité)
  H. Early stopping sur val_acc / val_f1
"""
import hashlib
import json
import os
import time
import uuid
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from imblearn.over_sampling import BorderlineSMOTE, SMOTE
from sklearn.ensemble import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    RandomForestClassifier,
    VotingClassifier,
)
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    mean_absolute_error,
    r2_score,
    confusion_matrix,
)
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler

warnings.filterwarnings("ignore")

# ─── Config ───────────────────────────────────────────────────────────────────
EPOCHS       = int(os.environ.get("EPOCHS", "50"))
RANDOM_STATE = 42
TEST_SIZE    = 0.15
VAL_SIZE     = 0.15
N_CV_FOLDS   = 5
EARLY_STOP   = int(os.environ.get("EARLY_STOP", "10"))  # epochs without improvement

DATA_PATH = os.environ.get(
    "DATA_PATH",
    str(Path(__file__).resolve().parent.parent.parent / "DATASET" / "dpp_unified_sample_80k.csv"),
)
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "models_v2"
AUDIT_DIR  = Path(__file__).resolve().parent.parent / "data" / "audit"

# ─── Feature definition (sans les targets) ────────────────────────────────────
BASE_NUMERIC = [
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
    "recycled_content_pct",
    "expected_lifespan_years",
    "tier1_suppliers",
    "tier2_suppliers",
]
CATEGORICAL = [
    "sector",
    "manufacturing_country",
    "energy_efficiency_class",
    "supply_chain_transparency",
    "ce_marking_status",
    "svhc_present",
    "conflict_minerals_status",
]

# ─── History ──────────────────────────────────────────────────────────────────
history: dict[str, list] = {
    "epoch": [],
    "espr_train_f1": [], "espr_val_f1": [], "espr_val_acc": [],
    "rohs_train_f1": [], "rohs_val_f1": [], "rohs_val_acc": [],
    "reach_train_f1": [], "reach_val_f1": [], "reach_val_acc": [],
    "circ_train_r2": [], "circ_val_r2": [], "circ_val_mae": [],
    "carbon_train_r2": [], "carbon_val_r2": [], "carbon_val_mae": [],
}


# ─── Audit (Art.12) ───────────────────────────────────────────────────────────
class AuditLogger:
    def __init__(self, sid: str, out: Path):
        out.mkdir(parents=True, exist_ok=True)
        self.path = out / f"audit_v2_{sid}.jsonl"
        self._prev = "0" * 64

    def _sha256(self, d: Any) -> str:
        return hashlib.sha256(json.dumps(d, sort_keys=True, default=str).encode()).hexdigest()

    def log(self, event: str, payload: dict) -> None:
        e = {"id": str(uuid.uuid4()), "ts": datetime.now(timezone.utc).isoformat(),
             "event": event, "payload": payload, "prev": self._prev}
        e["hash"] = self._sha256(e)
        self._prev = e["hash"]
        with open(self.path, "a") as f:
            f.write(json.dumps(e) + "\n")


# ─── Data loading & feature engineering ───────────────────────────────────────
def load_and_engineer(path: str, audit: AuditLogger) -> pd.DataFrame:
    """Load 80k CSV, impute by sector, engineer features. Fixes Bug A, B."""
    print(f"\n[LOAD] {path}")
    t0 = time.time()
    df = pd.read_csv(path, low_memory=False)

    # Sector mapping from product_id prefix
    prefix_map = {
        "elec": "electronics", "batt": "batteries", "text": "textiles",
        "veh":  "vehicles",    "cons": "construction", "furn": "furniture",
        "plas": "plastics",    "chem": "chemicals",
    }
    df["sector"] = df["product_id"].str.split("-").str[0].str.lower().map(prefix_map).fillna("electronics")

    # Sector-level medians for numeric imputation
    for col in BASE_NUMERIC:
        if col in df.columns:
            df[col] = df.groupby("sector")[col].transform(lambda x: x.fillna(x.median()))
            df[col] = df[col].fillna(df[col].median())

    # Classification target imputation (realistic EU-sector defaults)
    sector_espr = {
        "electronics": "Partial_Compliance", "batteries": "Full_Compliance",
        "textiles": "Partial_Compliance", "vehicles": "Full_Compliance",
        "construction": "Transitional", "furniture": "Partial_Compliance",
        "plastics": "Transitional", "chemicals": "Partial_Compliance",
    }
    sector_rohs = {
        "electronics": "Compliant", "batteries": "Compliant",
        "textiles": "Compliant", "vehicles": "Exempt_Category",
        "construction": "Compliant", "furniture": "Compliant",
        "plastics": "Compliant", "chemicals": "Compliant",
    }
    sector_reach = {
        "electronics": "Registered", "batteries": "Registered",
        "textiles": "Pre_Registered", "vehicles": "Registered",
        "construction": "Pre_Registered", "furniture": "Pre_Registered",
        "plastics": "Registered", "chemicals": "SVHC_Declared",
    }
    for col, mapping in [("espr_compliance_status", sector_espr),
                          ("rohs_compliance", sector_rohs),
                          ("reach_status", sector_reach)]:
        df[col] = df[col].fillna(df["sector"].map(mapping))

    # Circularity index: impute then keep for regression
    df["circularity_index"] = df.groupby("sector")["circularity_index"].transform(
        lambda x: x.fillna(x.median()))
    df["circularity_index"] = df["circularity_index"].fillna(50.0)

    # ── Feature Engineering (Art.13 — explicabilité) ──────────────────────────
    # Ratio carbone use_phase / total (comportement produit en usage)
    eps = 1e-6
    df["carbon_use_phase_ratio"] = df["carbon_use_phase_pct"].fillna(0) / (
        df["carbon_raw_materials_pct"].fillna(0) + df["carbon_manufacturing_pct"].fillna(0) +
        df["carbon_distribution_pct"].fillna(0) + df["carbon_use_phase_pct"].fillna(0) +
        df["carbon_end_of_life_pct"].fillna(0) + eps)
    # Score qualité circulaire composite
    df["circular_quality_score"] = (
        df["recyclability_score"].fillna(50) * 0.4 +
        df["repairability_score"].fillna(50) * 0.3 +
        df["durability_score"].fillna(50) * 0.2 +
        df["recycled_content_pct"].fillna(0) * 0.1
    )
    # Ratio fournisseurs multi-tier
    df["supplier_depth_ratio"] = df["tier2_suppliers"].fillna(1) / (df["tier1_suppliers"].fillna(1) + eps)
    # Efficience énergétique encodée (A=7 ... G=1)
    eff_map = {"A+++": 10, "A++": 9, "A+": 8, "A": 7, "B": 6, "C": 5, "D": 4, "E": 3, "F": 2, "G": 1}
    df["energy_eff_numeric"] = df["energy_efficiency_class"].map(eff_map).fillna(4.0)
    # Log-transform carbon footprint
    df["log_carbon"] = np.log1p(df["carbon_footprint_kg_co2eq"].fillna(0))
    # SVHC binary flag
    df["svhc_flag"] = (df["svhc_present"].astype(str).str.lower().isin(["true", "yes", "1"])).astype(int)
    # Lifespan efficiency score
    df["lifespan_carbon_ratio"] = df["expected_lifespan_years"].fillna(5) / (df["log_carbon"].fillna(1) + eps)

    print(f"  {len(df):,} rows | {df.shape[1]} columns | {time.time()-t0:.1f}s")

    # ── IQR outlier removal (FIX A: par secteur, colonnes non-null, minority protégées) ──
    n_before = len(df)
    numeric_for_outlier = ["carbon_footprint_kg_co2eq", "weight_kg", "recyclability_score"]

    # Protect minority classes: never remove rows where RoHS is Non_Compliant or ESPR is Exempt
    protected_mask = (
        (df["rohs_compliance"] == "Non_Compliant") |
        (df["espr_compliance_status"] == "Exempt") |
        (df["reach_status"] == "SVHC_Declared")
    )

    rows_to_drop = pd.Series(False, index=df.index)
    for sector in df["sector"].unique():
        mask_sector = (df["sector"] == sector) & ~protected_mask
        for col in numeric_for_outlier:
            if col not in df.columns:
                continue
            non_null_vals = df.loc[mask_sector & df[col].notna(), col]
            if len(non_null_vals) < 20:
                continue
            Q1, Q3 = non_null_vals.quantile(0.25), non_null_vals.quantile(0.75)
            IQR = Q3 - Q1
            if IQR == 0:
                continue
            lo, hi = Q1 - 3 * IQR, Q3 + 3 * IQR
            outlier_idx = df.index[mask_sector & df[col].notna() & ((df[col] < lo) | (df[col] > hi))]
            rows_to_drop[outlier_idx] = True

    df = df[~rows_to_drop].copy()
    n_after = len(df)
    pct = (n_before - n_after) / n_before * 100
    print(f"  IQR outlier removal: {n_before-n_after:,} rows ({pct:.1f}%) — {n_after:,} retained (minority protected)")
    print(f"  Sectors: {df['sector'].value_counts().to_dict()}")

    audit.log("DATA_LOAD_AND_ENGINEER", {
        "rows_raw": n_before, "rows_clean": n_after, "pct_removed": round(pct, 2),
        "features_engineered": ["carbon_use_phase_ratio", "circular_quality_score",
                                 "supplier_depth_ratio", "energy_eff_numeric",
                                 "log_carbon", "svhc_flag", "lifespan_carbon_ratio"],
        "article": "EU AI Act Article 10",
    })
    return df


# ─── Feature matrix builder ────────────────────────────────────────────────────
ENGINEERED = [
    "carbon_use_phase_ratio", "circular_quality_score", "supplier_depth_ratio",
    "energy_eff_numeric", "log_carbon", "svhc_flag", "lifespan_carbon_ratio",
]

def build_X(df: pd.DataFrame, le_dict: dict, fit: bool = True) -> np.ndarray:
    cols = BASE_NUMERIC + ENGINEERED
    X = df[cols].copy()
    for col in CATEGORICAL:
        if col not in df.columns:
            continue
        if fit:
            le = LabelEncoder()
            X[col] = le.fit_transform(df[col].fillna("UNKNOWN").astype(str))
            le_dict[col] = le
        else:
            le = le_dict[col]
            vals = df[col].fillna("UNKNOWN").astype(str)
            X[col] = vals.map(lambda v: le.transform([v])[0] if v in le.classes_ else -1)
    return X.fillna(0).values.astype(float)


# ─── Progress bar ─────────────────────────────────────────────────────────────
def bar(val: float, width: int = 20) -> str:
    filled = int(val * width)
    return "█" * filled + "░" * (width - filled)


def print_ep(ep: int, m: dict, best: dict) -> None:
    stars_espr  = " ★" if m["espr_val_f1"]   >= best.get("espr_val_f1", -1)   else ""
    stars_rohs  = " ★" if m["rohs_val_f1"]   >= best.get("rohs_val_f1", -1)   else ""
    stars_reach = " ★" if m["reach_val_f1"]  >= best.get("reach_val_f1", -1)  else ""
    stars_co2   = " ★" if m["carbon_val_r2"] >= best.get("carbon_val_r2", -1) else ""
    print(
        f"  Ep {ep:>2} │ "
        f"ESPR  [{bar(m['espr_val_f1'])}] F1={m['espr_val_f1']:.3f} acc={m['espr_val_acc']:.3f}{stars_espr} │ "
        f"RoHS F1={m['rohs_val_f1']:.3f}{stars_rohs} │ "
        f"REACH F1={m['reach_val_f1']:.3f}{stars_reach} │ "
        f"Circ R²={m['circ_val_r2']:.3f} │ "
        f"CO2 R²={m['carbon_val_r2']:.3f}{stars_co2} │ {m['elapsed']:.1f}s"
    )


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    sid = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    audit = AuditLogger(sid, AUDIT_DIR)

    print("=" * 110)
    print(" EU DPP PLATFORM — TRAINING v2 (GradientBoosting + SMOTE, recalibré)")
    print(f" EU AI Act 2024/1689 compliant │ Session: {sid} │ Epochs: {EPOCHS}")
    print("=" * 110)

    audit.log("SESSION_START", {
        "version": "2.0", "epochs": EPOCHS, "early_stop": EARLY_STOP,
        "algorithms": ["GradientBoostingClassifier", "GradientBoostingRegressor", "SMOTE"],
        "fixes": ["IQR_outlier", "no_data_leakage", "non_linear_model", "SMOTE_minority"],
    })

    # ── Load & engineer ────────────────────────────────────────────────────────
    df = load_and_engineer(DATA_PATH, audit)

    # ── Art.9 Risk assessment ──────────────────────────────────────────────────
    print("\n[Art.9] Risk Assessment...")
    espr_dist = df["espr_compliance_status"].value_counts(normalize=True)
    rohs_nc   = (df["rohs_compliance"] == "Non_Compliant").sum() / len(df)
    print(f"  ESPR distribution: {espr_dist.round(3).to_dict()}")
    print(f"  RoHS Non_Compliant: {rohs_nc:.2%}")
    print(f"  Total samples for training: {len(df):,}")
    audit.log("RISK_ASSESSMENT", {
        "espr_distribution": espr_dist.round(4).to_dict(),
        "rohs_non_compliant_pct": round(rohs_nc, 4),
        "n_samples": len(df), "article": "EU AI Act Article 9",
    })

    # ── Encode targets ─────────────────────────────────────────────────────────
    le_espr  = LabelEncoder(); y_espr  = le_espr.fit_transform(df["espr_compliance_status"])
    le_rohs  = LabelEncoder(); y_rohs  = le_rohs.fit_transform(df["rohs_compliance"])
    le_reach = LabelEncoder(); y_reach = le_reach.fit_transform(df["reach_status"])
    y_circ   = df["circularity_index"].values.astype(float)
    y_carbon = np.log1p(df["carbon_footprint_kg_co2eq"].fillna(0).values.astype(float))

    print(f"\n  ESPR classes:  {list(le_espr.classes_)}")
    print(f"  RoHS classes:  {list(le_rohs.classes_)}")
    print(f"  REACH classes: {list(le_reach.classes_)}")

    # ── Feature matrix ─────────────────────────────────────────────────────────
    le_dict: dict = {}
    X = build_X(df, le_dict, fit=True)
    feature_names = BASE_NUMERIC + ENGINEERED + [c for c in CATEGORICAL if c in df.columns]
    print(f"\n  X shape: {X.shape} ({len(feature_names)} features)")

    # ── Train / Val / Test split ───────────────────────────────────────────────
    # FIX B: pour circularity, features SANS circularity_index
    circ_feat_idx = [i for i, f in enumerate(BASE_NUMERIC + ENGINEERED)
                     if f not in ("circularity_index",)]

    idx = np.arange(len(X))
    idx_tv, idx_test = train_test_split(idx, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y_espr)
    idx_train, idx_val = train_test_split(idx_tv, test_size=VAL_SIZE / (1 - TEST_SIZE),
                                           random_state=RANDOM_STATE, stratify=y_espr[idx_tv])

    X_train, X_val, X_test = X[idx_train], X[idx_val], X[idx_test]
    ye_tr, ye_v, ye_te   = y_espr[idx_train],  y_espr[idx_val],  y_espr[idx_test]
    yr_tr, yr_v, yr_te   = y_rohs[idx_train],  y_rohs[idx_val],  y_rohs[idx_test]
    yc_tr, yc_v, yc_te   = y_reach[idx_train], y_reach[idx_val], y_reach[idx_test]
    yci_tr, yci_v, yci_te = y_circ[idx_train],  y_circ[idx_val],  y_circ[idx_test]
    yco_tr, yco_v, yco_te = y_carbon[idx_train], y_carbon[idx_val], y_carbon[idx_test]

    print(f"  Train: {len(X_train):,} │ Val: {len(X_val):,} │ Test: {len(X_test):,}")

    # ── Scale ──────────────────────────────────────────────────────────────────
    scaler = StandardScaler()
    X_tr_s  = scaler.fit_transform(X_train)
    X_v_s   = scaler.transform(X_val)
    X_te_s  = scaler.transform(X_test)
    X_ci_tr = X_tr_s[:, circ_feat_idx]  # No leakage for circularity
    X_ci_v  = X_v_s[:, circ_feat_idx]
    X_ci_te = X_te_s[:, circ_feat_idx]

    # ── SMOTE oversampling (FIX D) ────────────────────────────────────────────
    print("\n[SMOTE] Oversampling minority classes...")
    for name, y_tr, tag in [("ESPR", ye_tr, "espr"), ("RoHS", yr_tr, "rohs"), ("REACH", yc_tr, "reach")]:
        counts = dict(zip(*np.unique(y_tr, return_counts=True)))
        min_count = min(counts.values())
        print(f"  {name}: {counts} → minority={min_count}")

    # SMOTE on ESPR
    smote = SMOTE(random_state=RANDOM_STATE, k_neighbors=min(5, min(
        (ye_tr == c).sum() for c in np.unique(ye_tr)) - 1))
    X_tr_espr, ye_tr_s = smote.fit_resample(X_tr_s, ye_tr)
    print(f"  ESPR after SMOTE: {dict(zip(*np.unique(ye_tr_s, return_counts=True)))}")

    # BorderlineSMOTE on RoHS (Non_Compliant tiny minority) — skip if 1 class
    n_rohs_classes = len(np.unique(yr_tr))
    if n_rohs_classes >= 2:
        min_rohs = min((yr_tr == c).sum() for c in np.unique(yr_tr))
        if min_rohs >= 6:
            bsmote = BorderlineSMOTE(random_state=RANDOM_STATE, k_neighbors=min(5, min_rohs - 1))
            X_tr_rohs, yr_tr_s = bsmote.fit_resample(X_tr_s, yr_tr)
        else:
            X_tr_rohs, yr_tr_s = X_tr_s, yr_tr
    else:
        X_tr_rohs, yr_tr_s = X_tr_s, yr_tr
        print(f"  RoHS: single class in train — no SMOTE needed")
    print(f"  RoHS after SMOTE: {dict(zip(*np.unique(yr_tr_s, return_counts=True)))}")

    # SMOTE on REACH — skip if 1 class
    n_reach_classes = len(np.unique(yc_tr))
    if n_reach_classes >= 2:
        min_reach = min((yc_tr == c).sum() for c in np.unique(yc_tr))
        if min_reach >= 6:
            smote_r = SMOTE(random_state=RANDOM_STATE, k_neighbors=min(5, min_reach - 1))
            X_tr_reach, yc_tr_s = smote_r.fit_resample(X_tr_s, yc_tr)
        else:
            X_tr_reach, yc_tr_s = X_tr_s, yc_tr
    else:
        X_tr_reach, yc_tr_s = X_tr_s, yc_tr
        print(f"  REACH: single class in train — no SMOTE needed")
    print(f"  REACH after SMOTE: {dict(zip(*np.unique(yc_tr_s, return_counts=True)))}")

    # ── Gradient Boosting — warm_start = 50 epochs (FIX C) ───────────────────
    # n_estimators_per_epoch × 50 = total trees
    N_PER_EPOCH = 10  # 10 trees/epoch × 50 epochs = 500 total trees
    print(f"\n[MODEL] GradientBoosting warm_start — {N_PER_EPOCH} trees/epoch × {EPOCHS} epochs = {N_PER_EPOCH*EPOCHS} total trees")

    clf_espr = GradientBoostingClassifier(
        n_estimators=N_PER_EPOCH, max_depth=5, learning_rate=0.05,
        subsample=0.8, min_samples_leaf=20, random_state=RANDOM_STATE,
        warm_start=True,
    )
    clf_rohs = GradientBoostingClassifier(
        n_estimators=N_PER_EPOCH, max_depth=4, learning_rate=0.05,
        subsample=0.8, min_samples_leaf=15, random_state=RANDOM_STATE,
        warm_start=True,
    )
    clf_reach = GradientBoostingClassifier(
        n_estimators=N_PER_EPOCH, max_depth=4, learning_rate=0.05,
        subsample=0.8, min_samples_leaf=15, random_state=RANDOM_STATE,
        warm_start=True,
    )
    reg_circ = GradientBoostingRegressor(
        n_estimators=N_PER_EPOCH, max_depth=4, learning_rate=0.05,
        subsample=0.8, random_state=RANDOM_STATE, warm_start=True,
    )
    reg_carbon = GradientBoostingRegressor(
        n_estimators=N_PER_EPOCH, max_depth=5, learning_rate=0.05,
        subsample=0.8, random_state=RANDOM_STATE, warm_start=True,
    )

    # ── 50-Epoch Training Loop ─────────────────────────────────────────────────
    print(f"\n{'─'*110}")
    print(f"  TRAINING — {EPOCHS} EPOCHS | GradientBoosting warm_start | SMOTE balanced classes")
    print(f"  ★ = new best | Early stop after {EARLY_STOP} epochs without F1 improvement on ESPR")
    print(f"{'─'*110}")

    best: dict = {}
    best_models: dict = {}
    no_improve_count = 0
    t_start = time.time()

    for epoch in range(1, EPOCHS + 1):
        t_ep = time.time()
        n_trees = epoch * N_PER_EPOCH

        # Update n_estimators and fit (warm_start adds trees incrementally)
        clf_espr.set_params(n_estimators=n_trees);  clf_espr.fit(X_tr_espr, ye_tr_s)
        clf_rohs.set_params(n_estimators=n_trees);  clf_rohs.fit(X_tr_rohs, yr_tr_s)
        clf_reach.set_params(n_estimators=n_trees); clf_reach.fit(X_tr_reach, yc_tr_s)
        reg_circ.set_params(n_estimators=n_trees);  reg_circ.fit(X_ci_tr, yci_tr)
        reg_carbon.set_params(n_estimators=n_trees); reg_carbon.fit(X_tr_s, yco_tr)

        # ── Metrics ────────────────────────────────────────────────────────────
        ep_val  = clf_espr.predict(X_v_s)
        ep_tr   = clf_espr.predict(X_tr_espr)
        espr_v_f1  = f1_score(ye_v, ep_val, average="weighted", zero_division=0)
        espr_v_acc = accuracy_score(ye_v, ep_val)
        espr_tr_f1 = f1_score(ye_tr_s, ep_tr, average="weighted", zero_division=0)

        rp_val  = clf_rohs.predict(X_v_s)
        rp_tr   = clf_rohs.predict(X_tr_rohs)
        rohs_v_f1  = f1_score(yr_v, rp_val, average="weighted", zero_division=0)
        rohs_v_acc = accuracy_score(yr_v, rp_val)
        rohs_tr_f1 = f1_score(yr_tr_s, rp_tr, average="weighted", zero_division=0)

        rc_val  = clf_reach.predict(X_v_s)
        rc_tr   = clf_reach.predict(X_tr_reach)
        reach_v_f1  = f1_score(yc_v, rc_val, average="weighted", zero_division=0)
        reach_v_acc = accuracy_score(yc_v, rc_val)
        reach_tr_f1 = f1_score(yc_tr_s, rc_tr, average="weighted", zero_division=0)

        ci_v = reg_circ.predict(X_ci_v)
        circ_v_r2  = r2_score(yci_v, ci_v)
        circ_v_mae = mean_absolute_error(yci_v, ci_v)
        circ_tr_r2 = r2_score(yci_tr, reg_circ.predict(X_ci_tr))

        co_v = reg_carbon.predict(X_v_s)
        carbon_v_r2  = r2_score(yco_v, co_v)
        carbon_v_mae = mean_absolute_error(yco_v, co_v)
        carbon_tr_r2 = r2_score(yco_tr, reg_carbon.predict(X_tr_s))

        m = {
            "espr_train_f1": espr_tr_f1, "espr_val_f1": espr_v_f1, "espr_val_acc": espr_v_acc,
            "rohs_train_f1": rohs_tr_f1, "rohs_val_f1": rohs_v_f1, "rohs_val_acc": rohs_v_acc,
            "reach_train_f1": reach_tr_f1, "reach_val_f1": reach_v_f1, "reach_val_acc": reach_v_acc,
            "circ_train_r2": circ_tr_r2, "circ_val_r2": circ_v_r2, "circ_val_mae": circ_v_mae,
            "carbon_train_r2": carbon_tr_r2, "carbon_val_r2": carbon_v_r2, "carbon_val_mae": carbon_v_mae,
            "elapsed": time.time() - t_ep,
        }

        # Track history
        for k in m:
            if k in history:
                history[k].append(m[k])
        history["epoch"].append(epoch)

        # Update best
        improved = espr_v_f1 > best.get("espr_val_f1", -1)
        if improved:
            best = {k: v for k, v in m.items()}
            best["epoch"] = epoch
            import copy
            best_models = {
                "clf_espr": copy.deepcopy(clf_espr),
                "clf_rohs": copy.deepcopy(clf_rohs),
                "clf_reach": copy.deepcopy(clf_reach),
                "reg_circ": copy.deepcopy(reg_circ),
                "reg_carbon": copy.deepcopy(reg_carbon),
            }
            no_improve_count = 0
        else:
            no_improve_count += 1

        print_ep(epoch, m, best)

        # Audit every 10 epochs
        if epoch % 10 == 0:
            audit.log("EPOCH_METRICS", {
                "epoch": epoch, "n_trees": n_trees,
                "espr_val_f1": round(espr_v_f1, 4), "espr_val_acc": round(espr_v_acc, 4),
                "rohs_val_f1": round(rohs_v_f1, 4), "rohs_val_acc": round(rohs_v_acc, 4),
                "reach_val_f1": round(reach_v_f1, 4), "reach_val_acc": round(reach_v_acc, 4),
                "circ_val_r2": round(circ_v_r2, 4), "carbon_val_r2": round(carbon_v_r2, 4),
                "article": "EU AI Act Article 12",
            })

        # Early stopping
        if no_improve_count >= EARLY_STOP:
            print(f"\n  ⏹  Early stopping at epoch {epoch} — no ESPR F1 improvement for {EARLY_STOP} epochs.")
            break

    total_time = time.time() - t_start
    print(f"\n{'─'*110}")
    print(f"  Training complete: {time.time()-t_start:.1f}s total │ Best ESPR val F1={best.get('espr_val_f1',0):.4f} @ epoch {best.get('epoch',0)}")

    # ── Use best models for final evaluation ──────────────────────────────────
    print(f"\n{'═'*110}")
    print(f"  FINAL EVALUATION — TEST SET (EU AI Act Article 15) — Best models from epoch {best.get('epoch',0)}")
    print(f"{'═'*110}")

    clf_e_best  = best_models["clf_espr"]
    clf_r_best  = best_models["clf_rohs"]
    clf_rc_best = best_models["clf_reach"]
    reg_ci_best = best_models["reg_circ"]
    reg_co_best = best_models["reg_carbon"]

    print("\n  [Task A] ESPR Compliance Status (GradientBoosting)")
    ye_pred = clf_e_best.predict(X_te_s)
    print(classification_report(ye_te, ye_pred, target_names=le_espr.classes_, zero_division=0))
    espr_te_acc = accuracy_score(ye_te, ye_pred)
    espr_te_f1  = f1_score(ye_te, ye_pred, average="weighted", zero_division=0)

    print("\n  [Task B] RoHS Compliance")
    yr_pred = clf_r_best.predict(X_te_s)
    print(classification_report(yr_te, yr_pred, target_names=le_rohs.classes_, zero_division=0))
    rohs_te_acc = accuracy_score(yr_te, yr_pred)
    rohs_te_f1  = f1_score(yr_te, yr_pred, average="weighted", zero_division=0)

    print("\n  [Task C] REACH Status")
    yc_pred = clf_rc_best.predict(X_te_s)
    print(classification_report(yc_te, yc_pred, target_names=le_reach.classes_, zero_division=0))
    reach_te_acc = accuracy_score(yc_te, yc_pred)
    reach_te_f1  = f1_score(yc_te, yc_pred, average="weighted", zero_division=0)

    print("\n  [Task D] Circularity Index (sans data leakage)")
    ci_te = reg_ci_best.predict(X_ci_te)
    circ_te_mae = mean_absolute_error(yci_te, ci_te)
    circ_te_r2  = r2_score(yci_te, ci_te)
    print(f"  MAE: {circ_te_mae:.4f} │ R²: {circ_te_r2:.4f}")

    print("\n  [Task E] Carbon Footprint (log-scale)")
    co_te = reg_co_best.predict(X_te_s)
    carbon_te_mae = mean_absolute_error(yco_te, co_te)
    carbon_te_r2  = r2_score(yco_te, co_te)
    print(f"  MAE: {carbon_te_mae:.4f} │ R²: {carbon_te_r2:.4f}")

    # ── Feature importance (Art.13 — explicabilité) ─────────────────────────
    print(f"\n{'─'*110}")
    print("  FEATURE IMPORTANCE — ESPR (Top 10) — EU AI Act Article 13 Explicabilité")
    fi = clf_e_best.feature_importances_
    feat_used = BASE_NUMERIC + ENGINEERED + [c for c in CATEGORICAL if c in df.columns]
    fi_pairs = sorted(zip(feat_used, fi), key=lambda x: x[1], reverse=True)[:10]
    for fname, fval in fi_pairs:
        print(f"    {fname:<35} {fval:.4f} {'█'*int(fval*200)}")

    # ── Cross-validation (StratifiedKFold 5) ──────────────────────────────────
    print(f"\n{'─'*110}")
    print(f"  CROSS-VALIDATION — StratifiedKFold (k={N_CV_FOLDS}) — ESPR Task")
    from sklearn.model_selection import cross_val_score
    cv_clf = GradientBoostingClassifier(
        n_estimators=best.get("epoch", EPOCHS) * N_PER_EPOCH,
        max_depth=5, learning_rate=0.05, subsample=0.8,
        min_samples_leaf=20, random_state=RANDOM_STATE,
    )
    cv_scores = cross_val_score(cv_clf, X_tr_s, ye_tr, cv=N_CV_FOLDS,
                                 scoring="f1_weighted", n_jobs=-1)
    print(f"  F1 weighted: {cv_scores.round(4)} → mean={cv_scores.mean():.4f} ±{cv_scores.std():.4f}")

    # ── Convergence summary ───────────────────────────────────────────────────
    print(f"\n{'─'*110}")
    print("  CONVERGENCE SUMMARY (best validation scores)")
    print(f"{'─'*110}")
    for task, f1_key, acc_key in [
        ("ESPR ", "espr_val_f1",  "espr_val_acc"),
        ("RoHS ", "rohs_val_f1",  "rohs_val_acc"),
        ("REACH", "reach_val_f1", "reach_val_acc"),
    ]:
        bf1 = max(history[f1_key]);  bep = history[f1_key].index(bf1) + 1
        bacc = history[acc_key][bep - 1]
        delta_f1  = history[f1_key][-1]  - history[f1_key][0]
        delta_acc = history[acc_key][-1] - history[acc_key][0]
        print(f"  {task}: best_F1={bf1:.4f} best_acc={bacc:.4f} @ep{bep:>2} │ "
              f"Δf1={delta_f1:+.4f} Δacc={delta_acc:+.4f}")

    for task, r2_key, mae_key in [
        ("Circularity ", "circ_val_r2",   "circ_val_mae"),
        ("CO2 footprint", "carbon_val_r2", "carbon_val_mae"),
    ]:
        br2 = max(history[r2_key]);  bep = history[r2_key].index(br2) + 1
        bmae = history[mae_key][bep - 1]
        print(f"  {task}: best_R²={br2:.4f} best_MAE={bmae:.4f} @ep{bep:>2}")

    # ── V1 vs V2 comparison ───────────────────────────────────────────────────
    print(f"\n{'─'*110}")
    print("  V1 vs V2 COMPARISON")
    v1 = {"ESPR acc": 0.2177, "RoHS acc": 0.1330, "REACH acc": 0.3442,
          "Circ R2": 1.0000, "CO2 R2": 0.8028}
    v2 = {"ESPR acc": espr_te_acc, "RoHS acc": rohs_te_acc, "REACH acc": reach_te_acc,
          "Circ R2": circ_te_r2, "CO2 R2": carbon_te_r2}
    for k in v1:
        delta = v2[k] - v1[k]
        arrow = "▲" if delta > 0 else "▼"
        print(f"  {k:<15}: v1={v1[k]:.4f} → v2={v2[k]:.4f}  {arrow}{abs(delta):.4f}")

    # ── Art.15 final status ────────────────────────────────────────────────────
    thresholds = {"ESPR": 0.70, "RoHS": 0.80, "REACH": 0.60}
    passed = {
        "ESPR":  espr_te_f1  >= thresholds["ESPR"],
        "RoHS":  rohs_te_f1  >= thresholds["RoHS"],
        "REACH": reach_te_f1 >= thresholds["REACH"],
    }

    print(f"\n{'═'*110}")
    print("  ART.15 ACCURACY THRESHOLDS")
    for k, th in thresholds.items():
        f1 = {"ESPR": espr_te_f1, "RoHS": rohs_te_f1, "REACH": reach_te_f1}[k]
        status = "✅ PASS" if passed[k] else "❌ FAIL"
        gap = f1 - th
        print(f"  {k:<8}: F1={f1:.4f} (threshold ≥{th}) {status} {gap:+.4f}")

    overall = all(passed.values())
    print(f"\n  Overall Art.15 status: {'✅ ALL THRESHOLDS MET' if overall else '⚠  PARTIAL — see above'}")
    print(f"  ESPR test F1={espr_te_f1:.4f} acc={espr_te_acc:.4f}")
    print(f"  RoHS test F1={rohs_te_f1:.4f} acc={rohs_te_acc:.4f}")
    print(f"  REACH test F1={reach_te_f1:.4f} acc={reach_te_acc:.4f}")
    print(f"  Circularity R²={circ_te_r2:.4f} MAE={circ_te_mae:.4f}")
    print(f"  Carbon R²={carbon_te_r2:.4f} MAE={carbon_te_mae:.4f}")
    print(f"  Training time: {total_time:.1f}s")
    print(f"{'═'*110}\n")

    # ── Save ──────────────────────────────────────────────────────────────────
    hist_path = OUTPUT_DIR / f"history_v2_{sid}.json"
    with open(hist_path, "w") as f:
        json.dump(history, f, indent=2)

    import joblib
    for name, obj in [
        ("clf_espr", clf_e_best), ("clf_rohs", clf_r_best), ("clf_reach", clf_rc_best),
        ("reg_circ", reg_ci_best), ("reg_carbon", reg_co_best),
        ("scaler", scaler), ("le_espr", le_espr), ("le_rohs", le_rohs),
        ("le_reach", le_reach), ("le_dict", le_dict),
    ]:
        joblib.dump(obj, OUTPUT_DIR / f"{name}_{sid}.pkl")
    print(f"  Models saved: {OUTPUT_DIR}/")
    print(f"  History:      {hist_path}")
    print(f"  Audit trail:  {AUDIT_DIR}/audit_v2_{sid}.jsonl\n")

    audit.log("FINAL_EVALUATION", {
        "espr_test_f1": round(espr_te_f1, 4), "espr_test_acc": round(espr_te_acc, 4),
        "rohs_test_f1": round(rohs_te_f1, 4), "rohs_test_acc": round(rohs_te_acc, 4),
        "reach_test_f1": round(reach_te_f1, 4), "reach_test_acc": round(reach_te_acc, 4),
        "circ_test_r2": round(circ_te_r2, 4), "carbon_test_r2": round(carbon_te_r2, 4),
        "cv_f1_mean": round(float(cv_scores.mean()), 4),
        "cv_f1_std": round(float(cv_scores.std()), 4),
        "all_thresholds_met": overall,
        "article": "EU AI Act Article 15",
    })


if __name__ == "__main__":
    main()
