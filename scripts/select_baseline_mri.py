import pandas as pd
from pathlib import Path
import sys

try:
    from config import OUTPUT_DIR, MANIFEST_FILE, COHORT_WITH_PTID_FILE
except ImportError:
    from scripts.config import OUTPUT_DIR, MANIFEST_FILE, COHORT_WITH_PTID_FILE

print(f"Manifest source : {MANIFEST_FILE}")
print(f"Cohorte source  : {COHORT_WITH_PTID_FILE}")

manifest = pd.read_csv(MANIFEST_FILE, low_memory=False)
cohort = pd.read_csv(COHORT_WITH_PTID_FILE, low_memory=False)

manifest.columns = manifest.columns.str.strip().str.strip('"')
cohort.columns = cohort.columns.str.strip()

print("Colonnes du manifeste :", manifest.columns.tolist())
print("Nombre de lignes du manifeste :", len(manifest))
print("Nombre de participants :", manifest["subject_id"].nunique())

# Normaliser les identifiants et les dates
manifest["subject_id"] = manifest["subject_id"].astype(str).str.strip()
manifest["image_date"] = pd.to_datetime(manifest["image_date"], errors="coerce")
cohort["PTID"] = cohort["PTID"].astype(str).str.strip()
cohort["baseline_date"] = pd.to_datetime(cohort["baseline_date"], errors="coerce")

# Garder les acquisitions MP-RAGE (et équivalents), sans les répétitions explicites
desc = manifest["image_description"].fillna("").str.upper().str.strip()
is_t1 = desc.str.contains("MP-RAGE", regex=False) | desc.str.contains("MPR", regex=False) | desc.str.contains("IR-FSPGR", regex=False)
is_repeat = desc.str.contains("REPEAT", regex=False) | desc.str.contains("MPR-R", regex=False)

# Si MP-RAGE standard est présent, privilégier le format original MP-RAGE sans repeat
if desc.str.contains("MP-RAGE", regex=False).any():
    t1 = manifest[desc.str.contains("MP-RAGE", regex=False) & ~desc.str.contains("REPEAT")].copy()
else:
    t1 = manifest[is_t1 & ~is_repeat].copy()

# Associer les images aux dates de baseline
joined = t1.merge(
    cohort[["PTID", "baseline_date"]],
    left_on="subject_id",
    right_on="PTID",
    how="inner"
)
joined["days_from_baseline"] = (
    joined["image_date"] - joined["baseline_date"]
).dt.days
joined["abs_days_from_baseline"] = joined["days_from_baseline"].abs()

# Trier de façon déterministe
joined = joined.sort_values(
    ["subject_id", "abs_days_from_baseline", "image_date", "image_id"],
    ascending=[True, True, True, True]
)

# Sauvegarder dans outputs
output_candidates = OUTPUT_DIR / "ADNI_MRI_T1_candidates_near_baseline.csv"
joined.to_csv(output_candidates, index=False)

print(f"\nImages T1 candidates sans REPEAT : {len(t1)}")
print(f"Candidats liés à la cohorte : {len(joined)}")
print(f"Participants avec au moins une candidate : {joined['subject_id'].nunique()}")
print(f"Fichier créé : {output_candidates}")
