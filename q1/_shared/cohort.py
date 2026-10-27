"""Chargement de la cohorte et sélection des mesures au baseline (T0).

Règle : pour chaque patient, on ne garde qu'une mesure par table, la plus
proche de la date T0, à +/- BASELINE_WINDOW_DAYS. Aucune mesure postérieure
à la fenêtre n'est utilisée (évite la fuite de données).
"""
import re

import numpy as np
import pandas as pd

from config import (COHORT_FILE, DATA_DIR, BASELINE_WINDOW_DAYS, ADNI_MISSING_CODES,
                    USE_SAMPLE_100, SAMPLE_RIDS_FILE)


def load_cohort():
    """Cohorte MCI -> AD à 24 mois : RID, baseline_date, target."""
    c = pd.read_csv(COHORT_FILE, parse_dates=["baseline_date"])
    c = c[["RID", "baseline_date", "target"]].copy()
    if USE_SAMPLE_100:
        rids = pd.read_csv(SAMPLE_RIDS_FILE)["RID"]
        c = c[c["RID"].isin(rids)].copy()
    return c


def find_table(name):
    """Trouve le CSV d'une table ADNI (ex. 'MMSE', 'PTDEMOG').

    Reconnaît les deux conventions de nommage :
      - 100-Img100-Subj_Cohort_MMSE_27Oct2026.csv (échantillon)
      - MMSE_05Oct2026.csv (export complet dans data/raw)
    Le nom doit être un jeton complet, entouré de début/underscore.
    """
    pattern = re.compile(rf"(^|_){re.escape(name)}(_|\d)")
    matches = sorted(f for f in DATA_DIR.glob("*.csv") if pattern.search(f.name))
    return matches[-1] if matches else None


def load_table(name):
    """Charge une table ADNI et nettoie les codes sentinelles. None si absente."""
    path = find_table(name)
    if path is None:
        return None
    df = pd.read_csv(path, low_memory=False)
    df.columns = df.columns.str.strip().str.strip('"')
    num_cols = df.select_dtypes(include="number").columns
    df[num_cols] = df[num_cols].replace(ADNI_MISSING_CODES, np.nan)
    return df


def select_baseline(df, date_col, cohort, window=BASELINE_WINDOW_DAYS):
    """Une ligne par RID : la mesure la plus proche de T0, dans la fenêtre.

    Retourne aussi `days_from_baseline` (audit) et `baseline_date`.
    """
    x = df.copy()
    x["_date"] = pd.to_datetime(x[date_col], errors="coerce")
    x = x.merge(cohort[["RID", "baseline_date"]], on="RID", how="inner")
    x["days_from_baseline"] = (x["_date"] - x["baseline_date"]).dt.days
    x = x[x["days_from_baseline"].abs() <= window].copy()
    x["_abs"] = x["days_from_baseline"].abs()
    x = x.sort_values(["RID", "_abs"]).drop_duplicates("RID", keep="first")
    return x.drop(columns=["_abs", "_date"])


def extract_baseline(table_name, date_col, mapping, cohort):
    """Extrait les colonnes `mapping` {colonne_source: nom_feature} au baseline."""
    df = load_table(table_name)
    if df is None:
        raise FileNotFoundError(f"Table {table_name} absente de {DATA_DIR}")
    cols = ["RID", date_col] + list(mapping)
    base = select_baseline(df[cols], date_col, cohort)
    out = base[["RID"] + list(mapping)].rename(columns=mapping)
    for col in mapping.values():
        out[col] = pd.to_numeric(out[col], errors="coerce")
    return out, base


def save_features(features, folder):
    """Écrit folder/data/features.csv (une ligne par RID).

    Les colonnes totalement vides (aucune mesure au baseline) sont exclues
    avec un avertissement, sinon l'imputeur les supprimerait silencieusement.
    """
    empty = [c for c in features.columns if c != "RID" and features[c].isna().all()]
    if empty:
        print(f"ATTENTION : colonnes vides exclues (aucune donnée au baseline) : {empty}")
        features = features.drop(columns=empty)
    out_dir = folder / "data"
    out_dir.mkdir(exist_ok=True)
    path = out_dir / "features.csv"
    features.to_csv(path, index=False)
    return path


def report_coverage(features, cohort, name):
    """Affiche la couverture de chaque feature dans la cohorte."""
    n = len(cohort)
    feat_cols = [c for c in features.columns if c != "RID"]
    any_feat = features.dropna(subset=feat_cols, how="all")["RID"].nunique()
    print(f"\n[{name}] patients avec au moins une valeur : {any_feat}/{n}")
    for c in feat_cols:
        n_ok = features[c].notna().sum()
        print(f"   {c:<22s} {n_ok:4d}/{n}")
