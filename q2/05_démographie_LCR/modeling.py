
"""RQ2 — Fusion des modalités DÉMOGRAPHIE + BIOMARQUEURS LCR."""

import sys
from pathlib import Path

import pandas as pd


# 1. Chemins du projet


HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent.parent
Q1_DIR = PROJECT_ROOT / "q1"

sys.path.insert(0, str(Q1_DIR / "_shared"))

from cohort import load_cohort
from evaluation import cross_validate



# 2. Chargement des données Q1


DEMOGRAPHIC_PATH = (
    Q1_DIR / "02_demographics" / "data" / "features.csv"
)
LCR_PATH = (
    Q1_DIR / "04_biomarqueurs_lcr" / "data" / "features.csv"
)

for path in [DEMOGRAPHIC_PATH, LCR_PATH]:
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path}")

demographics = pd.read_csv(DEMOGRAPHIC_PATH)
lcr = pd.read_csv(LCR_PATH)
cohort = load_cohort()

print("=" * 60)
print("RQ2 — DÉMOGRAPHIE + BIOMARQUEURS LCR")
print("=" * 60)


# 3. Vérification des données


for name, data in [
    ("Démographie", demographics),
    ("LCR", lcr),
]:
    if "RID" not in data.columns:
        raise ValueError(f"La colonne RID est absente de {name}.")

    if data["RID"].duplicated().any():
        raise ValueError(f"Des RID sont dupliqués dans {name}.")

demographic_cols = [
    c for c in demographics.columns if c != "RID"
]
lcr_cols = [
    c for c in lcr.columns if c != "RID"
]

if not demographic_cols or not lcr_cols:
    raise ValueError("Une des modalités ne contient aucune variable.")

overlap = set(demographic_cols) & set(lcr_cols)
if overlap:
    raise ValueError(f"Variables communes aux deux modalités : {overlap}")



# 4. Fusion des modalités


df = cohort.merge(demographics, on="RID", how="inner")
df = df.merge(lcr, on="RID", how="inner")

# Garder les patients ayant au moins une variable renseignée
# dans chaque modalité.
mask = (
    df[demographic_cols].notna().any(axis=1)
    & df[lcr_cols].notna().any(axis=1)
)

df = df.loc[mask].copy().reset_index(drop=True)

feature_cols = demographic_cols + lcr_cols

X = df[feature_cols]
y = df["target"].astype(int).to_numpy()

if len(df) == 0:
    raise ValueError("Aucun patient utilisable après la fusion.")

if pd.Series(y).nunique() < 2:
    raise ValueError("Il faut des patients convertisseurs et stables.")

print(f"\nPatients retenus : {len(df)}")
print(f"Convertisseurs : {(y == 1).sum()}")
print(f"Patients stables : {(y == 0).sum()}")
print(f"Variables démographiques : {demographic_cols}")
print(f"Variables LCR : {lcr_cols}")
print(f"Nombre total de variables : {len(feature_cols)}")



# 5. Évaluation des modèles


results = cross_validate(X, y)

results.insert(0, "combination", "demographics+lcr")
results.insert(1, "n", len(df))
results.insert(2, "n_pos", int((y == 1).sum()))
results.insert(3, "n_features", len(feature_cols))

print("\nRésultats :")
print(results.to_string(index=False))


# 6. Sauvegarde des résultats


RESULTS_DIR = HERE / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

output_path = RESULTS_DIR / "demographie_lcr_results.csv"
results.to_csv(output_path, index=False)

print(f"\nFichier sauvegardé : {output_path}")
