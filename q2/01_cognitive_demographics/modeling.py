
"""RQ2 :cognition + démographie."""

import sys
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent.parent
Q1_DIR = PROJECT_ROOT / "q1"

sys.path.insert(0, str(Q1_DIR / "_shared"))

from cohort import load_cohort
from evaluation import cross_validate

# Fichiers produits par les preprocessing.py de Q1
COGNITIVE_FILE = (
    Q1_DIR / "01_cognitive" / "data" / "features.csv"
)
DEMOGRAPHICS_FILE = (
    Q1_DIR / "02_demographics" / "data" / "features.csv"
)

RESULTS_DIR = HERE / "results"


def main():
    # Charger la cohorte et les étiquettes de Q1
    cohort = load_cohort()[["RID", "target"]]

    # Charger les deux modalités
    for path in [COGNITIVE_FILE, DEMOGRAPHICS_FILE]:
        if not path.exists():
            raise FileNotFoundError(
                f"Fichier absent : {path}\n"
                "Exécute d'abord le preprocessing.py de Q1."
            )

    cognitive = pd.read_csv(COGNITIVE_FILE)
    demographics = pd.read_csv(DEMOGRAPHICS_FILE)

    # Vérifier qu'il existe une seule ligne par patient
    for name, features in [
        ("cognitive", cognitive),
        ("demographics", demographics),
    ]:
        if features["RID"].duplicated().any():
            raise ValueError(
                f"RID dupliqués dans les features {name}."
            )

    # Fusionner les deux modalités sur RID
    df = cohort.merge(cognitive, on="RID", how="inner")
    df = df.merge(
        demographics, on="RID", how="inner",
        suffixes=("_cognitive", "_demographics")
    )

    cognitive_cols = [
        c for c in cognitive.columns if c != "RID"
    ]
    demographic_cols = [
        c for c in demographics.columns if c != "RID"
    ]

    # Vérifier les colonnes dupliquées entre modalités
    duplicates = set(cognitive_cols) & set(demographic_cols)
    if duplicates:
        raise ValueError(
            f"Colonnes communes aux modalités : {sorted(duplicates)}"
        )

    feature_cols = cognitive_cols + demographic_cols

    # Conserver les patients ayant au moins une donnée
    # dans chacune des deux modalités
    mask = (
        df[cognitive_cols].notna().any(axis=1)
        & df[demographic_cols].notna().any(axis=1)
    )
    df = df.loc[mask].reset_index(drop=True)

    X = df[feature_cols]
    y = df["target"].astype(int).to_numpy()

    print("=" * 60)
    print("RQ2 — COGNITION + DÉMOGRAPHIE")
    print("=" * 60)
    print(f"Patients : {len(df)}")
    print(f"Convertisseurs : {int(y.sum())}")
    print(f"Patients stables : {int((y == 0).sum())}")
    print(f"Variables cognitives : {cognitive_cols}")
    print(f"Variables démographiques : {demographic_cols}")

    res = cross_validate(X, y)
    res.insert(0, "combination", "cognitive+demographics")
    res.insert(1, "n", len(df))
    res.insert(2, "n_pos", int(y.sum()))
    res.insert(3, "n_features", len(feature_cols))

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output = RESULTS_DIR / "cognitive_demographics_results.csv"
    res.to_csv(output, index=False)

    print("\nRésultats :")
    print(res.to_string(index=False))
    print(f"\nFichier sauvegardé : {output}")


if __name__ == "__main__":
    main()
