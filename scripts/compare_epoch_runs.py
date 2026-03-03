#!/usr/bin/env python3
"""Compare metrics from history_v2_epochs200.json vs history_v2_epochs500.json."""
import json
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "models_v2"

def main():
    h200_path = OUTPUT_DIR / "history_v2_epochs200.json"
    h500_path = OUTPUT_DIR / "history_v2_epochs500.json"
    if not h200_path.exists():
        print(f"  Missing {h200_path} — run training with RUN_LABEL=epochs200 first.")
        return
    if not h500_path.exists():
        print(f"  Missing {h500_path} — run training with RUN_LABEL=epochs500 first.")
        return

    with open(h200_path) as f:
        h200 = json.load(f)
    with open(h500_path) as f:
        h500 = json.load(f)

    def best_epoch(history, key):
        vals = history.get(key, [])
        if not vals:
            return None, None
        best_val = max(vals)
        best_ep = vals.index(best_val) + 1
        return best_val, best_ep

    print("\n  ─── Best validation metrics (200 vs 500 epochs) ───\n")
    for name, key_f1, key_acc in [
        ("ESPR ", "espr_val_f1",  "espr_val_acc"),
        ("RoHS ", "rohs_val_f1",  "rohs_val_acc"),
        ("REACH", "reach_val_f1", "reach_val_acc"),
    ]:
        v200, ep200 = best_epoch(h200, key_f1)
        v500, ep500 = best_epoch(h500, key_f1)
        a200 = h200.get(key_acc, [])[ep200 - 1] if ep200 and h200.get(key_acc) else None
        a500 = h500.get(key_acc, [])[ep500 - 1] if ep500 and h500.get(key_acc) else None
        print(f"  {name}  F1:  200ep → {v200:.4f} @ epoch {ep200}   |  500ep → {v500:.4f} @ epoch {ep500}")
        if a200 is not None and a500 is not None:
            print(f"        Acc: 200ep → {a200:.4f}             |  500ep → {a500:.4f}")

    for name, key_r2, key_mae in [
        ("Circularity ", "circ_val_r2", "circ_val_mae"),
        ("Carbon      ", "carbon_val_r2", "carbon_val_mae"),
    ]:
        r200, ep200 = best_epoch(h200, key_r2)
        r500, ep500 = best_epoch(h500, key_r2)
        m200 = h200.get(key_mae, [])[ep200 - 1] if ep200 and h200.get(key_mae) else None
        m500 = h500.get(key_mae, [])[ep500 - 1] if ep500 and h500.get(key_mae) else None
        print(f"  {name} R²:  200ep → {r200:.4f} @ epoch {ep200}   |  500ep → {r500:.4f} @ epoch {ep500}")
        if m200 is not None and m500 is not None:
            print(f"        MAE: 200ep → {m200:.4f}             |  500ep → {m500:.4f}")

    n200 = len(h200.get("epoch", []))
    n500 = len(h500.get("epoch", []))
    print(f"\n  Epochs run: 200-config → {n200} (early stop or full)  |  500-config → {n500}")
    print()

if __name__ == "__main__":
    main()
