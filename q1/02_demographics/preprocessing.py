"""RQ1 — Modalité DÉMOGRAPHIQUE / CLINIQUE : âge, sexe, éducation au baseline.

Source : PTDEMOG.
- age = date T0 - année de naissance (PTDOBYY), en années
- sexe_femme = 1 si femme, 0 si homme (PTGENDER : 1 homme, 2 femme)
- education = PTEDUCAT (années d'études)
Les valeurs -4 (non disponible) sont mises à NaN (voir config).
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "_shared"))

import pandas as pd
from cohort import load_cohort, load_table, select_baseline, save_features, report_coverage

cohort = load_cohort()
pt = load_table("PTDEMOG")
if pt is None:
    raise SystemExit("Table PTDEMOG absente.")

pt = pt[["RID", "VISDATE", "PTGENDER", "PTEDUCAT", "PTDOBYY"]].copy()
base = select_baseline(pt, "VISDATE", cohort)

dob = pd.to_datetime(base["PTDOBYY"], errors="coerce")
features = pd.DataFrame({
    "RID": base["RID"],
    "age": (base["baseline_date"] - dob).dt.days / 365.25,
    "sexe_femme": base["PTGENDER"].map({1: 0, 2: 1}),
    "education": pd.to_numeric(base["PTEDUCAT"], errors="coerce"),
})

features = cohort[["RID"]].merge(features, on="RID", how="left")
report_coverage(features, cohort, "demographics")
path = save_features(features, HERE)
print(f"\nFeatures écrites : {path}")
