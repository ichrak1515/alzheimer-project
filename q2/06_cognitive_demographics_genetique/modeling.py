
from pathlib import Path
import sys

import pandas as pd


# Q2 — Cognition + Démographie + Génétique


HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent.parent
Q1_DIR = PROJECT_ROOT / "q1"

sys.path.insert(0, str(Q1_DIR / "_shared"))

from cohort import load_cohort
from evaluation import cross_validate


def load_features(modality, filename="features.csv"):
    path = Q1_DIR / modality / "data" / filename

    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path}")

    df = pd.read_csv(path)

    if "RID" not in df.columns:
        raise ValueError(f"Colonne RID absente dans {path}")

    if df["RID"].duplicated().any():
        raise ValueError(f"RID en double dans {path}")

    return df


def main():
    print("=" * 70)
    print("Q2 — COGNITION + DÉMOGRAPHIE + GÉNÉTIQUE")
    print("=" * 70)

    cohort = load_cohort()

    cognitive = load_features("01_cognitive")
    demographics = load_features("02_demographics")
    genetics = load_features("03_genetique")

    df = cohort.merge(cognitive, on="RID", how="inner")
    df = df.merge(demographics, on="RID", how="inner")
    df = df.merge(genetics, on="RID", how="inner")

    modality_features = {
        "cognition": ["mmse", "cdr_sb", "cdr_global", "adas13"],
        "demographie": ["age", "sexe_femme", "education"],
        "genetique": ["n_e4", "n_e2"],
    }

    for modality, cols in modality_features.items():
        missing = [col for col in cols if col not in df.columns]
        if missing:
            raise ValueError(
                f"Variables absentes pour {modality} : {missing}"
            )

    feature_cols = (
        modality_features["cognition"]
        + modality_features["demographie"]
        + modality_features["genetique"]
    )

    # Cohorte avec au moins une valeur observée dans chaque modalité.
    for modality, cols in modality_features.items():
        df = df[df[cols].notna().any(axis=1)]

    df = df.dropna(subset=["target"])

    X = df[feature_cols]
    y = df["target"].astype(int).to_numpy()

    print(f"\nPatients retenus : {len(df)}")
    print(f"Convertisseurs : {(y == 1).sum()}")
    print(f"Patients stables : {(y == 0).sum()}")
    print(f"Nombre de variables : {len(feature_cols)}")
    print(f"Variables : {feature_cols}")

    if len(set(y)) != 2:
        raise ValueError("Il faut les deux classes pour évaluer les modèles.")

    results = cross_validate(X, y)

    print("\nRÉSULTATS")
    print("-" * 70)

    for model_name, metrics in results.items():
        print(f"\n{model_name}")
        for metric, value in metrics.items():
            if isinstance(value, (int, float)):
                print(f"  {metric}: {value:.6f}")
            else:
                print(f"  {metric}: {value}")

    output_dir = HERE / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for model_name, metrics in results.items():
        row = {"model": model_name}
        row.update(metrics)
        rows.append(row)

    output_path = output_dir / "cognitive_demographics_genetique_results.csv"
    pd.DataFrame(rows).to_csv(output_path, index=False)

    print(f"\nRésultats enregistrés : {output_path}")


if __name__ == "__main__":
    main()
