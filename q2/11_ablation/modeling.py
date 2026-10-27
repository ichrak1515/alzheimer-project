
from pathlib import Path
import sys
import pandas as pd

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent.parent
Q1_DIR = PROJECT_ROOT / "q1"

sys.path.insert(0, str(Q1_DIR / "_shared"))

from cohort import load_cohort
from evaluation import cross_validate


# ============================================================
# 1. MODALITÉS ET VARIABLES
# ============================================================

MODALITIES = {
    "cognition": (
        "01_cognitive",
        ["mmse", "cdr_sb", "cdr_global", "adas13"],
    ),
    "demographie": (
        "02_demographics",
        ["age", "sexe_femme", "education"],
    ),
    "genetique": (
        "03_genetique",
        ["n_e4", "n_e2"],
    ),
    "lcr": (
        "04_biomarqueurs_lcr",
        ["abeta40", "abeta42", "abeta42_40",
         "tau_log", "ptau_log"],
    ),
}


def load_features(folder):
    path = Q1_DIR / folder / "data" / "features.csv"

    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path}")

    features = pd.read_csv(path)

    if "RID" not in features.columns:
        raise ValueError(f"Colonne RID absente : {path}")

    if features["RID"].duplicated().any():
        raise ValueError(f"RID en double : {path}")

    return features


# ============================================================
# 2. CONSTRUIRE UNE COHORTE COMMUNE
# ============================================================

def prepare_cohort():
    df = load_cohort().copy()

    if df["RID"].duplicated().any():
        raise ValueError("RID dupliqués dans la cohorte initiale.")

    feature_cols = {}

    for name, (folder, cols) in MODALITIES.items():
        features = load_features(folder)

        missing = [col for col in cols if col not in features.columns]
        if missing:
            raise ValueError(
                f"Variables absentes ({name}) : {missing}"
            )

        # Même logique que Q2-10 : fusion interne
        df = df.merge(features, on="RID", how="inner")

        # Même règle de disponibilité pour chaque modalité
        df = df[df[cols].notna().any(axis=1)].copy()

        feature_cols[name] = cols

    df = df.dropna(subset=["target"]).copy()

    if df["RID"].duplicated().any():
        raise ValueError("Des RID sont dupliqués après les fusions.")

    df = df.sort_values("RID").reset_index(drop=True)

    return df, feature_cols


# ============================================================
# 3. ABLATIONS
# ============================================================

def main():
    print("=" * 70)
    print("Q2 — ABLATION DES MODALITÉS")
    print("=" * 70)

    df, feature_cols = prepare_cohort()

    y = df["target"].astype(int).to_numpy()

    if len(set(y)) != 2:
        raise ValueError("Les deux classes sont nécessaires.")

    print(f"\nPatients communs : {len(df)}")
    print(f"Convertisseurs : {(y == 1).sum()}")
    print(f"Patients stables : {(y == 0).sum()}")

    # Sauvegarder les patients exacts utilisés
    output_dir = HERE / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    df[["RID", "target"]].to_csv(
        output_dir / "cohorte_ablation_rids.csv",
        index=False,
    )

    experiments = {
        "complet": [
            "cognition", "demographie", "genetique", "lcr"
        ],
        "sans_cognition": [
            "demographie", "genetique", "lcr"
        ],
        "sans_demographie": [
            "cognition", "genetique", "lcr"
        ],
        "sans_genetique": [
            "cognition", "demographie", "lcr"
        ],
        "sans_lcr": [
            "cognition", "demographie", "genetique"
        ],
    }

    all_results = []

    for experiment, modalities in experiments.items():
        cols = [
            col
            for modality in modalities
            for col in feature_cols[modality]
        ]

        X = df[cols]

        print("\n" + "-" * 70)
        print(f"Expérience : {experiment}")
        print(f"Modalités : {' + '.join(modalities)}")
        print(f"Nombre de variables : {len(cols)}")

        results = cross_validate(X, y)
        results.insert(0, "experience", experiment)
        results.insert(1, "modalites", " + ".join(modalities))
        results["n_patients"] = len(df)
        results["n_variables"] = len(cols)

        print(results.to_string(index=False))

        all_results.append(results)

    # Regrouper et sauvegarder tous les résultats
    final_results = pd.concat(all_results, ignore_index=True)

    details_path = output_dir / "ablation_details.csv"
    final_results.to_csv(details_path, index=False)

    print("\n" + "=" * 70)
    print("COMPARAISON DES AUROC")
    print("=" * 70)

    auroc = final_results[
        final_results["metric"] == "AUROC"
    ][["experience", "model", "mean", "std"]]

    print(auroc.to_string(index=False))

    summary_path = output_dir / "ablation_summary.csv"
    final_results.to_csv(summary_path, index=False)

    print(f"\nRID : {output_dir / 'cohorte_ablation_rids.csv'}")
    print(f"Résultats : {details_path}")
    print(f"Résumé : {summary_path}")


if __name__ == "__main__":
    main()
