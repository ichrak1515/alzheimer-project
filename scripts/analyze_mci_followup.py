from pathlib import Path
import pandas as pd
import numpy as np
import sys

sys.path.append(str(Path(__file__).resolve().parent))
try:
    from config import OUTPUT_DIR, DXSUM_FILE
except ImportError:
    from scripts.config import OUTPUT_DIR, DXSUM_FILE

FILE = DXSUM_FILE

WINDOWS = {
    "T6":  (3, 9),
    "T12": (9, 15),
    "T18": (15, 21),
    "T24": (21, 27),
}

# ============================================================
# CHARGEMENT
# ============================================================

df = pd.read_csv(FILE, low_memory=False)

df["EXAMDATE"] = pd.to_datetime(
    df["EXAMDATE"],
    errors="coerce"
)

df["DXMCI_num"] = pd.to_numeric(
    df["DXMCI"],
    errors="coerce"
)

df["DXAD_num"] = pd.to_numeric(
    df["DXAD"],
    errors="coerce"
)

print("=" * 70)
print("DXSUM")
print("=" * 70)

print(f"Lignes : {len(df)}")
print(f"Sujets uniques : {df['RID'].nunique()}")

# ============================================================
# 1. MCI AU BASELINE
# ============================================================

baseline = df[
    (df["VISCODE2"].astype(str).str.lower() == "bl") &
    (df["DXMCI_num"] == 1)
].copy()

print("\n" + "=" * 70)
print("1. MCI AU BASELINE")
print("=" * 70)

print(f"Lignes baseline MCI : {len(baseline)}")
print(f"Sujets baseline MCI : {baseline['RID'].nunique()}")

# Une seule ligne par patient
baseline = (
    baseline
    .sort_values(["RID", "EXAMDATE"])
    .drop_duplicates("RID", keep="first")
)

# ============================================================
# 2. RÉCUPÉRER TOUT LE SUIVI DES PATIENTS MCI
# ============================================================

merged = df.merge(
    baseline[["RID", "EXAMDATE"]].rename(
        columns={"EXAMDATE": "BASELINE_DATE"}
    ),
    on="RID",
    how="inner"
)

# Calcul du nombre de mois depuis T0
merged["days_from_baseline"] = (
    merged["EXAMDATE"] - merged["BASELINE_DATE"]
).dt.days

merged["months_from_baseline"] = (
    merged["days_from_baseline"] / 30.4375
)

# Garder uniquement les visites à partir du baseline
followup = merged[
    merged["months_from_baseline"] >= -1
].copy()

# ============================================================
# 3. DISPONIBILITÉ DU SUIVI
# ============================================================

print("\n" + "=" * 70)
print("2. DISPONIBILITÉ DU SUIVI")
print("=" * 70)

for visit, (low, high) in WINDOWS.items():

    subset = followup[
        (followup["months_from_baseline"] >= low) &
        (followup["months_from_baseline"] < high)
    ].copy()

    print(
        f"{visit:>4} : "
        f"{subset['RID'].nunique():4d} sujets "
        f"({low}-{high} mois)"
    )

# ============================================================
# 4. VISITES T24
# ============================================================

t24 = followup[
    (followup["months_from_baseline"] >= 21) &
    (followup["months_from_baseline"] < 27)
].copy()

print("\n" + "=" * 70)
print("3. DIAGNOSTIC DANS LA FENÊTRE T24")
print("=" * 70)

print(f"Lignes T24 : {len(t24)}")
print(f"Sujets T24 : {t24['RID'].nunique()}")

# ============================================================
# 5. CLASSIFICATION
# ============================================================

def classify(row):

    if row["DXAD_num"] == 1:
        return "AD"

    if row["DXMCI_num"] == 1:
        return "MCI"

    return "OTHER"


t24["diagnosis"] = t24.apply(
    classify,
    axis=1
)

print("\nDiagnostic des visites T24 :")
print(
    t24["diagnosis"]
    .value_counts(dropna=False)
)

print("\nSujets uniques par diagnostic :")
print(
    t24.groupby("diagnosis")["RID"]
    .nunique()
    .sort_values(ascending=False)
)

# ============================================================
# 6. CONVERTERS
# ============================================================

ad_t24 = t24[
    t24["DXAD_num"] == 1
]

print("\n" + "=" * 70)
print("4. CONVERTERS")
print("=" * 70)

print(
    "MCI baseline -> AD a T24 :",
    ad_t24["RID"].nunique()
)

# ============================================================
# 7. STABLE MCI
# ============================================================

mci_t24 = t24[
    (t24["DXMCI_num"] == 1) &
    (t24["DXAD_num"] != 1)
]

print("\n" + "=" * 70)
print("5. STABLE MCI")
print("=" * 70)

print(
    "MCI baseline -> MCI a T24 :",
    mci_t24["RID"].nunique()
)

# ============================================================
# 8. RÉSUMÉ PAR PATIENT
# ============================================================

summary = (
    t24.groupby("RID")
    .agg(
        baseline_date=("BASELINE_DATE", "first"),
        min_months=("months_from_baseline", "min"),
        max_months=("months_from_baseline", "max"),
        has_AD=("DXAD_num", lambda x: (x == 1).any()),
        has_MCI=("DXMCI_num", lambda x: (x == 1).any()),
    )
    .reset_index()
)

summary["target"] = np.nan

summary.loc[
    summary["has_AD"],
    "target"
] = 1

summary.loc[
    (~summary["has_AD"]) & summary["has_MCI"],
    "target"
] = 0

# ============================================================
# 9. RÉSULTAT
# ============================================================

print("\n" + "=" * 70)
print("6. RÉSUMÉ FINAL PROVISOIRE")
print("=" * 70)

print(
    summary["target"]
    .value_counts(dropna=False)
    .sort_index()
)

print("\nRésumé :")
print(f"Total sujets T24 : {len(summary)}")
print(f"Converters       : {(summary['target'] == 1).sum()}")
print(f"Stables          : {(summary['target'] == 0).sum()}")
print(f"Ambigus          : {summary['target'].isna().sum()}")

# ============================================================
# 10. SAUVEGARDE
# ============================================================

output = OUTPUT_DIR / "MCI_T24_followup_analysis.csv"
summary.to_csv(output, index=False)

print("\nFichier sauvegardé :")
print(output)