import pandas as pd
from pathlib import Path
import sys

try:
    from config import PROJECT_ROOT, OUTPUT_DIR, DATA_DIR, DXSUM_FILE, ROSTER_FILE, find_file
except ImportError:
    from scripts.config import PROJECT_ROOT, OUTPUT_DIR, DATA_DIR, DXSUM_FILE, ROSTER_FILE, find_file

# Dossier contenant les fichiers de la cohorte
cohort_path = find_file("ADNI_MCI_AD_24M_cohort.csv", [OUTPUT_DIR, PROJECT_ROOT])
cohort = pd.read_csv(cohort_path)
cohort.columns = cohort.columns.str.strip()
cohort["RID"] = pd.to_numeric(cohort["RID"], errors="coerce")

# Trouver la correspondance RID -> PTID
mapping = None

# 1) Essayer ROSTER si présent
if ROSTER_FILE.exists():
    try:
        roster = pd.read_csv(ROSTER_FILE)
        roster.columns = roster.columns.str.strip().str.strip('"')
        if "RID" in roster.columns and "PTID" in roster.columns:
            roster["RID"] = pd.to_numeric(roster["RID"], errors="coerce")
            mapping = roster[["RID", "PTID"]].dropna().drop_duplicates(subset="RID")
            print("Mapping RID->PTID chargé depuis ROSTER :", ROSTER_FILE.name)
    except Exception as e:
        print("Avertissement lecture ROSTER :", e)

# 2) Vérifier la cohorte existante avec PTID si disponible (pour conserver les 272 IDs d'origine)
candidate_tables = [
    PROJECT_ROOT / "ADNI_MCI_AD_24M_cohort_with_PTID.csv",
    OUTPUT_DIR / "ADNI_MCI_AD_24M_cohort_with_PTID.csv",
    DXSUM_FILE,
    DATA_DIR / "100-Img100-Subj_Cohort_PTDEMOG_27Oct2026.csv",
]

for table_path in candidate_tables:
    if table_path.exists():
        try:
            t = pd.read_csv(table_path, low_memory=False)
            t.columns = t.columns.str.strip().str.strip('"')
            if "RID" in t.columns and "PTID" in t.columns:
                t["RID"] = pd.to_numeric(t["RID"], errors="coerce")
                t["PTID"] = t["PTID"].astype(str).str.strip().str.strip('"')
                sub = t[["RID", "PTID"]].dropna().drop_duplicates(subset="RID")
                if mapping is None or len(sub) > len(mapping):
                    mapping = sub
                    print(f"Mapping RID->PTID extrait depuis {table_path.name} ({len(mapping)} correspondances)")
                    if len(mapping) >= len(cohort):
                        break
        except Exception as e:
            continue

if mapping is None:
    raise RuntimeError("Impossible de trouver une table contenant les colonnes RID et PTID.")

# Associer chaque participant de la cohorte à son PTID
result = cohort.merge(mapping, on="RID", how="left")

missing = result[result["PTID"].isna()]
print(f"Participants dans la cohorte : {len(cohort)}")
print(f"PTID retrouvés : {result['PTID'].notna().sum()}")
print(f"PTID manquants : {len(missing)}")

# Sauvegarder dans outputs
output_cohort = OUTPUT_DIR / "ADNI_MCI_AD_24M_cohort_with_PTID.csv"
output_txt = OUTPUT_DIR / "ADNI_PTID_list.txt"

result.to_csv(output_cohort, index=False)

ids = result["PTID"].dropna().drop_duplicates()
txt_content = ",".join(ids)
output_txt.write_text(txt_content, encoding="utf-8")

print("\nFichiers créés :")
print(f"- {output_cohort}")
print(f"- {output_txt}")
