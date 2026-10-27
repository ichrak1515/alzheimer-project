"""RQ1 — Modalité GÉNÉTIQUE : génotype APOE.

Source : APOERES (GENOTYPE, ex. '3/4').
Le génotype ne change pas avec le temps : pas de risque de fuite temporelle.
Features :
- n_e4 : nombre d'allèles ε4 (0, 1, 2), facteur de risque
- n_e2 : nombre d'allèles ε2 (0, 1, 2), souvent protecteur
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "_shared"))

import pandas as pd
from cohort import load_cohort, load_table, save_features, report_coverage

cohort = load_cohort()
apoe = load_table("APOERES")
if apoe is None:
    raise SystemExit("Table APOERES absente.")

# Un génotype par patient (le premier non vide)
geno = (apoe.dropna(subset=["GENOTYPE"])
            .sort_values("RID")
            .drop_duplicates("RID", keep="first")[["RID", "GENOTYPE"]])
geno["GENOTYPE"] = geno["GENOTYPE"].astype(str).str.strip()
geno = geno[geno["GENOTYPE"].str.match(r"^[234]/[234]$")]

geno["n_e4"] = geno["GENOTYPE"].apply(lambda g: g.split("/").count("4"))
geno["n_e2"] = geno["GENOTYPE"].apply(lambda g: g.split("/").count("2"))

features = cohort[["RID"]].merge(geno[["RID", "n_e4", "n_e2"]], on="RID", how="left")
report_coverage(features, cohort, "genetique")
path = save_features(features, HERE)
print(f"\nFeatures écrites : {path}")
