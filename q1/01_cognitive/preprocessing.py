"""RQ1 — Modalité COGNITIVE : scores de tests au baseline (T0).

Variables : MMSE, CDR (CDRSB, CDGLOBAL), ADAS-Cog 13, MoCA (optionnelle).
Une mesure par test, la plus proche de T0 (fenêtre +/- 60 jours).
Une table absente est ignorée avec un avertissement, pas une erreur.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "_shared"))

from cohort import load_cohort, extract_baseline, save_features, report_coverage

cohort = load_cohort()

TESTS = [
    ("MMSE", "VISDATE", {"MMSCORE": "mmse"}),
    ("CDR", "VISDATE", {"CDRSB": "cdr_sb", "CDGLOBAL": "cdr_global"}),
    ("ADAS", "VISDATE", {"TOTAL13": "adas13"}),
    ("MOCA", "VISDATE", {"MOCA": "moca"}),
]

features = cohort[["RID"]].copy()
for table, date_col, mapping in TESTS:
    try:
        part, _ = extract_baseline(table, date_col, mapping, cohort)
    except FileNotFoundError:
        print(f"ATTENTION : table {table} absente, variables ignorées : {list(mapping.values())}")
        continue
    features = features.merge(part, on="RID", how="left")

report_coverage(features, cohort, "cognitive")
path = save_features(features, HERE)
print(f"\nFeatures écrites : {path}")
