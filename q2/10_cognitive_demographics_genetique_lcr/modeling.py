
from pathlib import Path
import sys
import pandas as pd

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent.parent
Q1_DIR = PROJECT_ROOT / "q1"

sys.path.insert(0, str(Q1_DIR / "_shared"))

from cohort import load_cohort
from evaluation import cross_validate


def load_features(modality):
    path = Q1_DIR / modality / "data" / "features.csv"

    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path}")

    df = pd.read_csv(path)

    if "RID" not in df.columns:
        raise ValueError(f"Colonne RID absente : {path}")

    if df["RID"].duplicated().any():
        raise ValueError(f"RID en double : {path}")

    return df


def main():
    print("=" * 70)
    print("Q2 — FUSION DES QUATRE MODALITÉS")
    print("Cognition + Démographie + Génétique + LCR")
    print("=" * 70)

    df = load_cohort()

    modalities = {
        "cognition": (
            "01_cognitive",
            ["mmse", "cdr_sb", "cdr_global", "adas13"]
        ),
        "demographie": (
            "02_demographics",
            ["age", "sexe_femme", "education"]
        ),
        "genetique": (
            "03_genetique",
            ["n_e4", "n_e2"]
        ),
        "lcr": (
            "04_biomarqueurs_lcr",
            ["abeta40", "abeta42", "abeta42_40",
             "tau_log", "ptau_log"]
        ),
    }

    feature_cols = []

    for name, (folder, cols) in modalities.items():
        features = load_features(folder)
        df = df.merge(features, on="RID", how="inner")

        missing = [col for col in cols if col not in df.columns]
        if missing:
            raise ValueError(
                f"Variables absentes ({name}) : {missing}"
            )

        # Garder les patients ayant au moins une valeur
        # disponible dans cette modalité.
        df = df[df[cols].notna().any(axis=1)]

        feature_cols.extend(cols)

    df = df.dropna(subset=["target"])

    if df["RID"].duplicated().any():
        raise ValueError("Des RID sont dupliqués après les fusions.")

    X = df[feature_cols]
    y = df["target"].astype(int).to_numpy()

    print(f"\nPatients retenus : {len(df)}")
    print(f"Convertisseurs : {(y == 1).sum()}")
    print(f"Patients stables : {(y == 0).sum()}")
    print(f"Nombre de variables : {len(feature_cols)}")
    print(f"Variables : {feature_cols}")

    if len(set(y)) != 2:
        raise ValueError("Les deux classes sont nécessaires.")

    results = cross_validate(X, y)

    print("\nRÉSULTATS")
    print("-" * 70)
    print(results.to_string(index=False))

    output_dir = HERE / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "all_modalities_results.csv"
    results.to_csv(output_path, index=False)

    print(f"\nRésultats enregistrés : {output_path}")


if __name__ == "__main__":
    main()
