import pandas as pd
import numpy as np
from pathlib import Path
import sys

try:
    from config import DXSUM_FILE, OUTPUT_DIR
except ImportError:
    from scripts.config import DXSUM_FILE, OUTPUT_DIR

# ============================================================
# CONFIGURATION
# ============================================================

OUTPUT_COHORT = OUTPUT_DIR / "ADNI_MCI_AD_24M_cohort.csv"
OUTPUT_CHECK = OUTPUT_DIR / "ADNI_MCI_AD_24M_quality_check.csv"
OUTPUT_T24 = OUTPUT_DIR / "ADNI_MCI_AD_24M_T24_visits.csv"

# ~24 mois (fenêtre 21-27 mois)
T24_MIN = 21
T24_MAX = 27


# ============================================================
# 1. CHARGEMENT
# ============================================================

print("=" * 75)
print("ADNI - CONSTRUCTION DE LA COHORTE MCI -> AD")
print("=" * 75)
print(f"Fichier DXSUM utilisé : {DXSUM_FILE}")

df = pd.read_csv(DXSUM_FILE, low_memory=False)
df.columns = df.columns.str.strip().str.strip('"')

print(f"\nLignes DXSUM       : {len(df)}")
print(f"Sujets uniques     : {df['RID'].nunique()}")


# ============================================================
# 2. PRÉPARATION
# ============================================================

df["EXAMDATE"] = pd.to_datetime(df["EXAMDATE"], errors="coerce")
df["DXMCI_num"] = pd.to_numeric(df.get("DXMCI"), errors="coerce")
df["DXAD_num"] = pd.to_numeric(df.get("DXAD"), errors="coerce")
if "DIAGNOSIS" in df.columns:
    diag_num = pd.to_numeric(df["DIAGNOSIS"], errors="coerce")
    # Si DIAGNOSIS=2 (MCI) et DXMCI_num n'est pas 1
    df.loc[diag_num == 2, "DXMCI_num"] = 1
    # Si DIAGNOSIS=3 (AD) et DXAD_num n'est pas 1
    df.loc[diag_num == 3, "DXAD_num"] = 1

df["VISCODE2_clean"] = (
    df["VISCODE2"]
    .astype(str)
    .str.strip()
    .str.lower()
)


# ============================================================
# 3. IDENTIFIER LES MCI AU BASELINE
# ============================================================

baseline_mci = df[
    (df["VISCODE2_clean"] == "bl") &
    (df["DXMCI_num"] == 1)
].copy()

baseline_mci = (
    baseline_mci
    .sort_values(["RID", "EXAMDATE"])
    .drop_duplicates("RID", keep="first")
)

print("\n" + "=" * 75)
print("BASELINE")
print("=" * 75)

print(f"MCI au baseline : {baseline_mci['RID'].nunique()}")


# ============================================================
# 4. RÉCUPÉRER TOUT LE SUIVI DES MCI
# ============================================================

baseline_dates = baseline_mci[["RID", "EXAMDATE"]].rename(
    columns={"EXAMDATE": "BASELINE_DATE"}
)

followup = df.merge(baseline_dates, on="RID", how="inner")

followup["days_from_baseline"] = (
    followup["EXAMDATE"] - followup["BASELINE_DATE"]
).dt.days

followup["months_from_baseline"] = followup["days_from_baseline"] / 30.4375

# On garde les visites à partir du baseline
followup = followup[followup["months_from_baseline"] >= -1].copy()


# ============================================================
# 5. DISPONIBILITÉ DU SUIVI
# ============================================================

print("\n" + "=" * 75)
print("SUIVI")
print("=" * 75)

for name, low, high in [
    ("T6", 3, 9),
    ("T12", 9, 15),
    ("T18", 15, 21),
    ("T24", T24_MIN, T24_MAX),
]:
    tmp = followup[
        (followup["months_from_baseline"] >= low) &
        (followup["months_from_baseline"] < high)
    ]
    print(f"{name:5s}: {tmp['RID'].nunique():4d} sujets")


# ============================================================
# 6. SÉLECTION DE LA FENÊTRE T24
# ============================================================

t24 = followup[
    (followup["months_from_baseline"] >= T24_MIN) &
    (followup["months_from_baseline"] < T24_MAX)
].copy()

print("\n" + "=" * 75)
print("FENÊTRE T24")
print("=" * 75)

print(f"Lignes T24 : {len(t24)}")
print(f"Sujets T24 : {t24['RID'].nunique()}")


# ============================================================
# 7. DIAGNOSTIC DE CHAQUE VISITE T24
# ============================================================

def get_diagnosis(row):
    is_ad = row["DXAD_num"] == 1
    is_mci = row["DXMCI_num"] == 1

    if is_ad and is_mci:
        return "AD_AND_MCI"
    if is_ad:
        return "AD"
    if is_mci:
        return "MCI"
    return "OTHER"


t24["diagnosis"] = t24.apply(get_diagnosis, axis=1)

print("\nDiagnostics des visites T24 :")
print(t24["diagnosis"].value_counts(dropna=False))


# ============================================================
# 8. CONSTRUIRE LE RÉSUMÉ PAR PATIENT
# ============================================================

patient_summary = []

for rid, group in t24.groupby("RID"):
    group = group.sort_values("EXAMDATE")

    has_ad = (group["diagnosis"] == "AD").any()
    has_mci = (group["diagnosis"] == "MCI").any()
    has_ad_and_mci = (group["diagnosis"] == "AD_AND_MCI").any()

    # Règle :
    # AD présent -> converter
    # uniquement MCI -> stable
    # autre / ambigu -> exclu

    if has_ad_and_mci:
        target = np.nan
        status = "AMBIGUOUS_AD_MCI"
    elif has_ad:
        target = 1
        status = "CONVERTER"
    elif has_mci:
        target = 0
        status = "STABLE_MCI"
    else:
        target = np.nan
        status = "OTHER"

    # Chercher la première date de conversion AD sur TOUT le suivi
    full_patient_followup = followup[followup["RID"] == rid]
    full_ad_dates = full_patient_followup.loc[
        (full_patient_followup["DXAD_num"] == 1) & (full_patient_followup["months_from_baseline"] >= 0),
        "EXAMDATE"
    ]
    if len(full_ad_dates) > 0:
        conversion_date = full_ad_dates.min()
    else:
        ad_dates_t24 = group.loc[group["diagnosis"].isin(["AD", "AD_AND_MCI"]), "EXAMDATE"]
        conversion_date = ad_dates_t24.min() if len(ad_dates_t24) > 0 else pd.NaT

    patient_summary.append({
        "RID": rid,
        "baseline_date": group["BASELINE_DATE"].iloc[0],
        "t24_first_date": group["EXAMDATE"].min(),
        "t24_last_date": group["EXAMDATE"].max(),
        "followup_months_first": group["months_from_baseline"].min(),
        "followup_months_last": group["months_from_baseline"].max(),
        "has_AD": int(has_ad),
        "has_MCI": int(has_mci),
        "has_AD_AND_MCI": int(has_ad_and_mci),
        "conversion_date": conversion_date,
        "status": status,
        "target": target,
    })


cohort = pd.DataFrame(patient_summary)


# ============================================================
# 9. RÉSULTATS
# ============================================================

print("\n" + "=" * 75)
print("COHORTE PROVISOIRE")
print("=" * 75)

print(cohort["status"].value_counts(dropna=False))

print("\nTarget :")
print(cohort["target"].value_counts(dropna=False).sort_index())


# ============================================================
# 10. GARDER UNIQUEMENT LES CAS VALIDES
# ============================================================

final_cohort = cohort[cohort["target"].isin([0, 1])].copy()
final_cohort["target"] = final_cohort["target"].astype(int)


# ============================================================
# 11. CONTRÔLE DE LA COHORTE
# ============================================================

print("\n" + "=" * 75)
print("COHORTE FINALE")
print("=" * 75)

n_total = len(final_cohort)
n_converter = (final_cohort["target"] == 1).sum()
n_stable = (final_cohort["target"] == 0).sum()

print(f"Total       : {n_total}")
print(f"Converters  : {n_converter}")
print(f"Stable MCI  : {n_stable}")

if n_total > 0:
    print(f"Taux conversion : {100 * n_converter / n_total:.2f}%")


# ============================================================
# 12. CONTRÔLE DES DUPLICATIONS
# ============================================================

print("\n" + "=" * 75)
print("CONTRÔLES")
print("=" * 75)

print("RID uniques :", final_cohort["RID"].nunique())
print("Doublons RID :", final_cohort["RID"].duplicated().sum())
print("Dates baseline manquantes :", final_cohort["baseline_date"].isna().sum())
print("Targets manquantes :", final_cohort["target"].isna().sum())


# ============================================================
# 13. SAUVEGARDER LA COHORTE FINALE
# ============================================================

final_cohort = final_cohort[
    [
        "RID",
        "baseline_date",
        "t24_first_date",
        "t24_last_date",
        "followup_months_first",
        "followup_months_last",
        "conversion_date",
        "target",
    ]
].sort_values("RID")

final_cohort.to_csv(OUTPUT_COHORT, index=False)


# ============================================================
# 14. SAUVEGARDER LE CONTRÔLE QUALITÉ
# ============================================================

cohort.to_csv(OUTPUT_CHECK, index=False)


# ============================================================
# 15. SAUVEGARDER LES VISITES T24
# ============================================================

t24[
    [
        "RID",
        "BASELINE_DATE",
        "EXAMDATE",
        "months_from_baseline",
        "VISCODE",
        "VISCODE2",
        "DXMCI",
        "DXAD",
        "diagnosis",
    ]
].sort_values(["RID", "EXAMDATE"]).to_csv(OUTPUT_T24, index=False)


# ============================================================
# FIN
# ============================================================

print("\n" + "=" * 75)
print("FICHIERS CRÉÉS")
print("=" * 75)

print(f"\nCohorte finale  : {OUTPUT_COHORT}")
print(f"Contrôle qualité: {OUTPUT_CHECK}")
print(f"Visites T24     : {OUTPUT_T24}")

print("\nTerminé.")