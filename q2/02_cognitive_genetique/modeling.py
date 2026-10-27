
"""RQ2 — Fusion des modalités COGNITIVE + GÉNÉTIQUE."""

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


COGNITIVE_PATH = Q1_DIR / "01_cognitive" / "data" / "features.csv"
GENETIC_PATH = Q1_DIR / "03_genetique" / "data" / "features.csv"

for path in [COGNITIVE_PATH, GENETIC_PATH]:
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path}")

cognitive = pd.read_csv(COGNITIVE_PATH)
genetic = pd.read_csv(GENETIC_PATH)

cohort = load_cohort()

print("=" * 60)
print("RQ2 — COGNITION + GÉNÉTIQUE")
print("=" * 60)



# 3. Vérification des identifiants
for name, data in [
    ("Cognition", cognitive),
    ("Génétique", genetic),
]:
    if "RID" not in data.columns:
        raise ValueError(f"La colonne RID est absente de {name}.")

    if data["RID"].duplicated().any():
        raise ValueError(
            f"Des RID sont dupliqués dans les données {name}."
        )

# Colonnes explicatives de chaque modalité
cognitive_cols = [c for c in cognitive.columns if c != "RID"]
genetic_cols = [c for c in genetic.columns if c != "RID"]

if not cognitive_cols:
    raise ValueError("Aucune variable cognitive trouvée.")

if not genetic_cols:
    raise ValueError("Aucune variable génétique trouvée.")

overlap = set(cognitive_cols) & set(genetic_cols)
if overlap:
    raise ValueError(
        f"Variables présentes dans les deux modalités : {overlap}"
    )



# 4. Fusion des modalités


df = cohort.merge(cognitive, on="RID", how="inner")
df = df.merge(genetic, on="RID", how="inner")


mask = (
    df[cognitive_cols].notna().any(axis=1)
    & df[genetic_cols].notna().any(axis=1)
)

df = df.loc[mask].copy().reset_index(drop=True)

feature_cols = cognitive_cols + genetic_cols

X = df[feature_cols]
y = df["target"].astype(int).to_numpy()

# Vérifications avant la validation croisée
if y.size == 0:
    raise ValueError("Aucun patient utilisable après la fusion.")

if pd.Series(y).nunique() < 2:
    raise ValueError("Il faut des patients convertisseurs et stables.")

print(f"\nPatients retenus : {len(df)}")
print(f"Convertisseurs : {(y == 1).sum()}")
print(f"Patients stables : {(y == 0).sum()}")
print(f"Variables cognitives : {cognitive_cols}")
print(f"Variables génétiques : {genetic_cols}")
print(f"Nombre total de variables : {len(feature_cols)}")


# 5. Entraînement et évaluation


results = cross_validate(X, y)

results.insert(0, "combination", "cognitive+genetic")
results.insert(1, "n", len(df))
results.insert(2, "n_pos", int((y == 1).sum()))
results.insert(3, "n_features", len(feature_cols))

print("\nRésultats :")
print(results.to_string(index=False))



# 6. Sauvegarde des résultats


RESULTS_DIR = HERE / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

output_path = RESULTS_DIR / "cognitive_genetique_results.csv"
results.to_csv(output_path, index=False)

print(f"\nFichier sauvegardé : {output_path}")
