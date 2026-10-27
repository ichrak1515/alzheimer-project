"""RQ1 — Modalité BIOMARQUEURS LCR (Roche Elecsys) au baseline.

Source : UPENNBIOMK_ROCHE_ELECSYS (Aβ40, Aβ42, tau, p-tau).
Features :
- abeta40, abeta42 : concentrations brutes
- abeta42_40 : rapport Aβ42/Aβ40 (plus robuste que chaque valeur seule)
- tau_log, ptau_log : log(1 + x), car tau et p-tau sont très asymétriques
Le prélèvement est rattaché à la visite la plus proche de T0 (+/- 60 j).
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "_shared"))

import numpy as np
import pandas as pd
from cohort import load_cohort, load_table, select_baseline, save_features, report_coverage

cohort = load_cohort()
lcr = load_table("UPENNBIOMK_ROCHE_ELECSYS")
if lcr is None:
    raise SystemExit("Table UPENNBIOMK_ROCHE_ELECSYS absente.")

lcr = lcr[["RID", "EXAMDATE", "ABETA40", "ABETA42", "TAU", "PTAU"]].copy()
# Les exports complets peuvent contenir du texte (ex. '>1700') : conversion explicite
for col in ["ABETA40", "ABETA42", "TAU", "PTAU"]:
    lcr[col] = pd.to_numeric(lcr[col], errors="coerce")
base = select_baseline(lcr, "EXAMDATE", cohort)

features = base[["RID"]].copy()
features["abeta40"] = base["ABETA40"].values
features["abeta42"] = base["ABETA42"].values
features["abeta42_40"] = features["abeta42"] / features["abeta40"]
features["tau_log"] = np.log1p(base["TAU"].values)
features["ptau_log"] = np.log1p(base["PTAU"].values)

features = cohort[["RID"]].merge(features, on="RID", how="left")
report_coverage(features, cohort, "biomarqueurs_lcr")
path = save_features(features, HERE)
print(f"\nFeatures écrites : {path}")
