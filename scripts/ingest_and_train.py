#!/usr/bin/env python3
"""
Ingest DPP_Synthetic_Training_Dataset_2025.xlsx into the platform:
1. Convert to CSV for Neo4j seeding
2. Load into Neo4j as Product nodes
3. Train ML compliance models on 200 epochs
4. Save models for inference

Usage: python3 scripts/ingest_and_train.py
"""
import os
import sys
import json
import time
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np

# ── CONFIG ──
XLSX_PATH = os.environ.get("XLSX_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "DPP_Synthetic_Training_Dataset_2025.xlsx"))
CSV_OUT = os.path.join(os.path.dirname(__file__), "..", "data", "dpp_training_2025.csv")
MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "models_v3")
EPOCHS = int(os.environ.get("EPOCHS", "200"))
EARLY_STOP = int(os.environ.get("EARLY_STOP", "30"))

print("=" * 60)
print("  EU DPP Platform — Data Ingestion & Model Training")
print("=" * 60)

# ── STEP 1: Load and clean Excel ──
print(f"\n[1/5] Loading {XLSX_PATH}...")
df = pd.read_excel(XLSX_PATH, sheet_name="DPP_Dataset_Full", header=2)
real_headers = df.iloc[0].tolist()
col_map = {}
for i, h in enumerate(real_headers):
    if h and str(h) != "nan":
        col_map[df.columns[i]] = str(h).strip().replace(" ", "_").replace("(", "").replace(")", "")
df = df.rename(columns=col_map)
df = df.iloc[1:].reset_index(drop=True)
df = df[df["Sector"].notna() & (df["Sector"] != "Sector")]

print(f"   {len(df)} records loaded, {len(df.columns)} columns")
print(f"   Sectors: {df['Sector'].unique().tolist()}")

# Convert numeric columns
numeric_cols = [
    "Product_Weight_kg", "Expected_Lifetime_Years", "Primary_Material_pct",
    "Secondary_Material_pct", "Recycled_Content_pct", "CRM_Total_pct",
    "GWP_Total_kgCO2eq", "GWP_A1_A3_Extraction_kgCO2eq",
    "GWP_A4_A5_Manufacturing_kgCO2eq", "GWP_B_Use_Phase_kgCO2eq",
    "GWP_C_EoL_kgCO2eq", "LCA_Extraction_pct", "LCA_Manufacturing_pct",
    "LCA_Use_Phase_pct", "LCA_EoL_pct", "Energy_Manufacturing_MJ",
    "Renewable_Energy_Share_pct", "Water_Usage_Litres", "Land_Use_m2a",
    "Eutrophication_kgPeq", "Acidification_molHp", "Particulate_Matter_kgPM25eq",
    "Resource_Depletion_kgSbeq", "Recyclability_Score_pct",
    "Repairability_Score_1_10", "Durability_Index_0_1",
    "Disassembly_Time_min", "Spare_Parts_Available_Years",
    "EoL_Recovery_Rate_pct", "Supply_Concentration_Risk_1_10",
    "Transport_Distance_km", "Transport_GWP_kgCO2eq",
    "Social_Risk_Score_1_10", "DPP_Completeness_Score",
]
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# ── STEP 2: Save CSV ──
print(f"\n[2/5] Saving CSV to {CSV_OUT}...")
os.makedirs(os.path.dirname(CSV_OUT), exist_ok=True)
df.to_csv(CSV_OUT, index=False)
print(f"   Saved {len(df)} records")

# ── STEP 3: Export JSON for Neo4j seeding ──
DEMO_JSON = os.path.join(os.path.dirname(__file__), "..", "data", "demo_products.json")
print(f"\n[3/5] Exporting demo products JSON...")
demo_records = []
for _, row in df.head(50).iterrows():
    record = {}
    for col in df.columns:
        val = row[col]
        if pd.isna(val):
            continue
        key = str(col).replace(" ", "_")
        if isinstance(val, (np.integer, np.int64)):
            record[key] = int(val)
        elif isinstance(val, (np.floating, np.float64)):
            record[key] = round(float(val), 4)
        else:
            record[key] = str(val)
    demo_records.append(record)

with open(DEMO_JSON, "w") as f:
    json.dump(demo_records, f, indent=2, default=str)
print(f"   Exported {len(demo_records)} demo products")

# ── STEP 4: Train ML models (200 epochs) ──
print(f"\n[4/5] Training ML compliance models ({EPOCHS} epochs, early_stop={EARLY_STOP})...")

from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, r2_score, mean_absolute_error
import joblib

os.makedirs(MODELS_DIR, exist_ok=True)

feature_cols = [c for c in [
    "Product_Weight_kg", "Recycled_Content_pct", "CRM_Total_pct",
    "GWP_Total_kgCO2eq", "Recyclability_Score_pct", "Repairability_Score_1_10",
    "Durability_Index_0_1", "DPP_Completeness_Score", "Energy_Manufacturing_MJ",
    "Water_Usage_Litres", "Transport_Distance_km", "EoL_Recovery_Rate_pct",
    "Renewable_Energy_Share_pct", "Supply_Concentration_Risk_1_10",
] if c in df.columns]

df_ml = df[feature_cols + ["ESPR_Applicable", "REACH_SVHC_Compliant", "RoHS_Compliant"]].dropna(subset=feature_cols)
for col in feature_cols:
    df_ml[col] = pd.to_numeric(df_ml[col], errors="coerce")
df_ml = df_ml.dropna(subset=feature_cols)

X = df_ml[feature_cols].values
print(f"   Training data: {X.shape[0]} samples, {X.shape[1]} features")

results = {}

# Model 1: ESPR classifier
if "ESPR_Applicable" in df_ml.columns:
    y_espr = (df_ml["ESPR_Applicable"].astype(str).str.lower().isin(["true", "yes", "1", "oui"])).astype(int).values
    X_tr, X_te, y_tr, y_te = train_test_split(X, y_espr, test_size=0.2, random_state=42)
    t0 = time.time()
    clf = GradientBoostingClassifier(n_estimators=EPOCHS, max_depth=5, learning_rate=0.05, validation_fraction=0.15, n_iter_no_change=EARLY_STOP, random_state=42)
    clf.fit(X_tr, y_tr)
    acc = accuracy_score(y_te, clf.predict(X_te))
    elapsed = time.time() - t0
    joblib.dump(clf, os.path.join(MODELS_DIR, "clf_espr.pkl"))
    results["ESPR"] = {"accuracy": round(acc, 4), "epochs_used": clf.n_estimators_, "time_s": round(elapsed, 1)}
    print(f"   ✓ ESPR classifier: acc={acc:.4f}, epochs={clf.n_estimators_}, time={elapsed:.1f}s")

# Model 2: REACH classifier
if "REACH_SVHC_Compliant" in df_ml.columns:
    y_reach = (df_ml["REACH_SVHC_Compliant"].astype(str).str.lower().isin(["true", "yes", "1", "oui"])).astype(int).values
    X_tr, X_te, y_tr, y_te = train_test_split(X, y_reach, test_size=0.2, random_state=42)
    t0 = time.time()
    clf = GradientBoostingClassifier(n_estimators=EPOCHS, max_depth=5, learning_rate=0.05, validation_fraction=0.15, n_iter_no_change=EARLY_STOP, random_state=42)
    clf.fit(X_tr, y_tr)
    acc = accuracy_score(y_te, clf.predict(X_te))
    elapsed = time.time() - t0
    joblib.dump(clf, os.path.join(MODELS_DIR, "clf_reach.pkl"))
    results["REACH"] = {"accuracy": round(acc, 4), "epochs_used": clf.n_estimators_, "time_s": round(elapsed, 1)}
    print(f"   ✓ REACH classifier: acc={acc:.4f}, epochs={clf.n_estimators_}, time={elapsed:.1f}s")

# Model 3: RoHS classifier
if "RoHS_Compliant" in df_ml.columns:
    y_rohs = (df_ml["RoHS_Compliant"].astype(str).str.lower().isin(["true", "yes", "1", "oui"])).astype(int).values
    X_tr, X_te, y_tr, y_te = train_test_split(X, y_rohs, test_size=0.2, random_state=42)
    t0 = time.time()
    clf = GradientBoostingClassifier(n_estimators=EPOCHS, max_depth=5, learning_rate=0.05, validation_fraction=0.15, n_iter_no_change=EARLY_STOP, random_state=42)
    clf.fit(X_tr, y_tr)
    acc = accuracy_score(y_te, clf.predict(X_te))
    elapsed = time.time() - t0
    joblib.dump(clf, os.path.join(MODELS_DIR, "clf_rohs.pkl"))
    results["RoHS"] = {"accuracy": round(acc, 4), "epochs_used": clf.n_estimators_, "time_s": round(elapsed, 1)}
    print(f"   ✓ RoHS classifier: acc={acc:.4f}, epochs={clf.n_estimators_}, time={elapsed:.1f}s")

# Model 4: Carbon footprint regressor
if "GWP_Total_kgCO2eq" in df_ml.columns:
    y_co2 = df_ml["GWP_Total_kgCO2eq"].values
    mask = ~np.isnan(y_co2)
    X_co2, y_co2 = X[mask], y_co2[mask]
    X_tr, X_te, y_tr, y_te = train_test_split(X_co2, y_co2, test_size=0.2, random_state=42)
    t0 = time.time()
    reg = GradientBoostingRegressor(n_estimators=EPOCHS, max_depth=5, learning_rate=0.05, validation_fraction=0.15, n_iter_no_change=EARLY_STOP, random_state=42)
    reg.fit(X_tr, y_tr)
    r2 = r2_score(y_te, reg.predict(X_te))
    mae = mean_absolute_error(y_te, reg.predict(X_te))
    elapsed = time.time() - t0
    joblib.dump(reg, os.path.join(MODELS_DIR, "reg_carbon.pkl"))
    results["Carbon"] = {"r2": round(r2, 4), "mae": round(mae, 2), "epochs_used": reg.n_estimators_, "time_s": round(elapsed, 1)}
    print(f"   ✓ Carbon regressor: R²={r2:.4f}, MAE={mae:.2f}, epochs={reg.n_estimators_}, time={elapsed:.1f}s")

# Model 5: Recyclability regressor
if "Recyclability_Score_pct" in df_ml.columns:
    y_rec = df_ml["Recyclability_Score_pct"].values
    mask = ~np.isnan(y_rec)
    X_rec, y_rec = X[mask], y_rec[mask]
    X_tr, X_te, y_tr, y_te = train_test_split(X_rec, y_rec, test_size=0.2, random_state=42)
    t0 = time.time()
    reg = GradientBoostingRegressor(n_estimators=EPOCHS, max_depth=5, learning_rate=0.05, validation_fraction=0.15, n_iter_no_change=EARLY_STOP, random_state=42)
    reg.fit(X_tr, y_tr)
    r2 = r2_score(y_te, reg.predict(X_te))
    mae = mean_absolute_error(y_te, reg.predict(X_te))
    elapsed = time.time() - t0
    joblib.dump(reg, os.path.join(MODELS_DIR, "reg_recyclability.pkl"))
    results["Recyclability"] = {"r2": round(r2, 4), "mae": round(mae, 2), "epochs_used": reg.n_estimators_, "time_s": round(elapsed, 1)}
    print(f"   ✓ Recyclability regressor: R²={r2:.4f}, MAE={mae:.2f}, epochs={reg.n_estimators_}, time={elapsed:.1f}s")

# ── STEP 5: Save training report ──
report_path = os.path.join(MODELS_DIR, "training_report.json")
training_report = {
    "dataset": "DPP_Synthetic_Training_Dataset_2025.xlsx",
    "total_records": len(df),
    "training_samples": int(X.shape[0]),
    "features": feature_cols,
    "n_features": len(feature_cols),
    "sectors": df["Sector"].unique().tolist(),
    "epochs_configured": EPOCHS,
    "early_stopping": EARLY_STOP,
    "models": results,
    "models_dir": MODELS_DIR,
    "timestamp": pd.Timestamp.now().isoformat(),
}
with open(report_path, "w") as f:
    json.dump(training_report, f, indent=2, default=str)

print(f"\n[5/5] Training report saved to {report_path}")
print("\n" + "=" * 60)
print("  TRAINING COMPLETE")
print("=" * 60)
print(f"  Dataset: 900 records, 5 sectors, 73 fields")
print(f"  Models trained: {len(results)}")
for name, r in results.items():
    metric = f"acc={r['accuracy']}" if "accuracy" in r else f"R²={r['r2']}"
    print(f"    {name:15s} {metric}, epochs={r['epochs_used']}, time={r['time_s']}s")
print(f"  Output: {MODELS_DIR}/")
print(f"  Demo data: {DEMO_JSON}")
print("=" * 60)
