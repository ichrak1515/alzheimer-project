"""Validation croisée et métriques communes à toutes les modalités."""
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, f1_score, recall_score,
                             roc_auc_score, confusion_matrix)
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from config import CV_SPLITS, CV_REPEATS, RANDOM_STATE, RESULTS_DIR
from cohort import load_cohort


def make_models():
    """Deux modèles de base : linéaire (référence) et forêt aléatoire.

    L'imputation et la normalisation sont DANS le pipeline : elles sont
    apprises sur le fold d'entraînement uniquement (pas de fuite).
    """
    return {
        "logreg": Pipeline([
            ("imp", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]),
        "random_forest": Pipeline([
            ("imp", SimpleImputer(strategy="median")),
            ("clf", RandomForestClassifier(
                n_estimators=300, min_samples_leaf=3,
                class_weight="balanced", random_state=RANDOM_STATE)),
        ]),
    }


def _fold_metrics(y_true, proba, threshold=0.5):
    pred = (proba >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()
    return {
        "AUROC": roc_auc_score(y_true, proba),
        "AUPRC": average_precision_score(y_true, proba),
        "Sensibilite": recall_score(y_true, pred, zero_division=0),
        "Specificite": tn / (tn + fp) if (tn + fp) else np.nan,
        "F1": f1_score(y_true, pred, zero_division=0),
    }


def cross_validate(X, y):
    """Retourne un DataFrame : modèle x métrique, moyenne et écart-type sur les folds."""
    cv = RepeatedStratifiedKFold(n_splits=CV_SPLITS, n_repeats=CV_REPEATS,
                                 random_state=RANDOM_STATE)
    rows = []
    for name, base_model in make_models().items():
        fold_results = []
        for tr, te in cv.split(X, y):
            model = clone(base_model)
            model.fit(X.iloc[tr], y[tr])
            proba = model.predict_proba(X.iloc[te])[:, 1]
            fold_results.append(_fold_metrics(y[te], proba))
        res = pd.DataFrame(fold_results)
        for metric in res.columns:
            rows.append({
                "model": name,
                "metric": metric,
                "mean": res[metric].mean(),
                "std": res[metric].std(),
            })
    return pd.DataFrame(rows)


def run_modality(name, features_path):
    """Pipeline commun : fusion cohorte + features, CV, sauvegarde des résultats."""
    print("=" * 70)
    print(f"RQ1 — modalité : {name}")
    print("=" * 70)

    if not features_path.exists():
        print(f"Features absentes ({features_path}). Lancer preprocessing.py d'abord.")
        return None

    cohort = load_cohort()
    feats = pd.read_csv(features_path)
    df = cohort.merge(feats, on="RID", how="left")

    feat_cols = [c for c in feats.columns if c != "RID"]
    # On ne garde que les patients ayant au moins une valeur de cette modalité
    df = df.dropna(subset=feat_cols, how="all").reset_index(drop=True)
    if df.empty:
        print("Aucun patient avec données pour cette modalité.")
        return None

    X = df[feat_cols]
    y = df["target"].astype(int).to_numpy()
    print(f"Patients : {len(df)}   (convertisseurs : {y.sum()}, stables : {(y == 0).sum()})")
    print(f"Features : {feat_cols}")

    res = cross_validate(X, y)
    res.insert(0, "modality", name)
    res.insert(1, "n", len(df))
    res.insert(2, "n_pos", int(y.sum()))

    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / f"{name}_results.csv"
    res.to_csv(out, index=False)

    auc = res[res.metric == "AUROC"].set_index("model")
    for m in auc.index:
        print(f"  {m:14s} AUROC = {auc.loc[m, 'mean']:.3f} ± {auc.loc[m, 'std']:.3f}")
    print(f"Résultats : {out}")
    return res
