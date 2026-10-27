"""RQ1 — Modalité IMAGERIE IRM : mesures FreeSurfer au baseline.

Source : UCSFFSX7 (FreeSurfer 7). Cette table N'EST PAS dans les fichiers
fournis (Tables_27Oct2026.zip) : le script s'arrête proprement dans ce cas.

Noms de colonnes repris du projet (ST29SV, ST88SV, ST24TA, ST83TA, ST10CV) :
à vérifier dans DATADIC avant usage.
Features :
- hippo_icv : volume hippocampique total (gauche + droit) / volume intracrânien
- entorhinal : épaisseur entorhinale moyenne (gauche + droit) / 2
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "_shared"))

import pandas as pd
from cohort import load_cohort, load_table, select_baseline, save_features, report_coverage

cohort = load_cohort()
fs = load_table("UCSFFSX7")
if fs is None:
    print("Table UCSFFSX7 absente des fichiers fournis : modalité IRM non traitable.")
    print("Ajouter UCSFFSX7 dans Tables_27Oct2026/ puis relancer ce script.")
    raise SystemExit(0)

date_col = next((c for c in ["EXAMDATE", "SCANDATE", "VISDATE"] if c in fs.columns), None)
if date_col is None:
    raise SystemExit("Aucune colonne de date reconnue dans UCSFFSX7.")

cols = ["ST29SV", "ST88SV", "ST24TA", "ST83TA", "ST10CV"]
fs = fs[["RID", date_col] + cols].copy()
base = select_baseline(fs, date_col, cohort)

features = base[["RID"]].copy()
features["hippo_icv"] = (base["ST29SV"] + base["ST88SV"]) / base["ST10CV"]
features["entorhinal"] = (base["ST24TA"] + base["ST83TA"]) / 2

features = cohort[["RID"]].merge(features, on="RID", how="left")
report_coverage(features, cohort, "imagerie_irm")
path = save_features(features, HERE)
print(f"\nFeatures écrites : {path}")
