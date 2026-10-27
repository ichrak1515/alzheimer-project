"""Tire un échantillon de 100 patients commun à toutes les modalités.

Étapes :
1. ne garder que les patients qui ont AU MOINS une valeur dans CHAQUE modalité ;
2. tirer 50 convertisseurs et 50 stables (graine fixe) ;
3. écrire la liste des RID dans _shared/rids_100.csv.

À lancer UNE fois, après les preprocessing.py sur la cohorte complète
(USE_SAMPLE_100 = False dans config.py). Le fichier rids_100.csv est ensuite
utilisé par toutes les modalités, donc tout le monde obtient les mêmes 100 patients.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import pandas as pd
from config import Q1_DIR, SAMPLE_RIDS_FILE, SAMPLE_PER_CLASS, RANDOM_STATE
from cohort import load_cohort

MODALITY_DIRS = ["01_cognitive", "02_demographics", "03_genetique",
                 "04_biomarqueurs_lcr", "05_imagerie_irm"]

cohort = load_cohort()  # cohorte complète : USE_SAMPLE_100 doit être False

common = set(cohort["RID"])
for m in MODALITY_DIRS:
    f = pd.read_csv(Q1_DIR / m / "data" / "features.csv")
    feat_cols = [c for c in f.columns if c != "RID"]
    have = set(f.dropna(subset=feat_cols, how="all")["RID"])
    common &= have
    print(f"{m:22s} patients avec données : {len(have)}")

pool = cohort[cohort["RID"].isin(common)]
print(f"\nPatients avec TOUTES les modalités : {len(pool)} "
      f"(convertisseurs {int((pool.target == 1).sum())}, stables {int((pool.target == 0).sum())})")

if (pool.target == 1).sum() < SAMPLE_PER_CLASS or (pool.target == 0).sum() < SAMPLE_PER_CLASS:
    raise SystemExit("Pas assez de patients dans une classe pour l'échantillon demandé.")

sample = pd.concat([
    pool[pool.target == 1].sample(SAMPLE_PER_CLASS, random_state=RANDOM_STATE),
    pool[pool.target == 0].sample(SAMPLE_PER_CLASS, random_state=RANDOM_STATE),
]).sort_values("RID")

sample[["RID"]].to_csv(SAMPLE_RIDS_FILE, index=False)
print(f"\nÉchantillon : {len(sample)} patients "
      f"({int((sample.target == 1).sum())} convertisseurs, {int((sample.target == 0).sum())} stables)")
print(f"Liste écrite : {SAMPLE_RIDS_FILE}")
