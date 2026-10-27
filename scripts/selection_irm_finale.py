from pathlib import Path
import pandas as pd
import sys

sys.path.append(str(Path(__file__).resolve().parent))
try:
    from config import PROJECT_ROOT, OUTPUT_DIR, DATA_DIR, find_file
except ImportError:
    from scripts.config import PROJECT_ROOT, OUTPUT_DIR, DATA_DIR, find_file

fichier_irm = find_file("ADNI_MRI_T1_candidates_near_baseline.csv", [OUTPUT_DIR, PROJECT_ROOT])
fichier_cohorte = find_file("ADNI_MCI_AD_24M_cohort_with_PTID.csv", [OUTPUT_DIR, PROJECT_ROOT])

fichier_sortie_90j = OUTPUT_DIR / "ADNI_T1_baseline_90j.csv"
fichier_sortie_sel = OUTPUT_DIR / "ADNI_T1_baseline_selected.csv"
fichier_txt = OUTPUT_DIR / "ADNI_T1_baseline_image_ids.txt"

# Charger les données
irm = pd.read_csv(fichier_irm)
cohorte = pd.read_csv(fichier_cohorte)

# Préparer les dates
irm["image_date"] = pd.to_datetime(irm["image_date"], errors="coerce")
irm["baseline_date"] = pd.to_datetime(irm["baseline_date"], errors="coerce")
irm["days_from_baseline"] = (
    irm["image_date"] - irm["baseline_date"]
).dt.days

# Garder les IRM entre 90 jours avant T0 et T0 inclus
irm = irm[
    irm["days_from_baseline"].between(-90, 0)
].copy()

# Si la table officielle Key_MRI d'ADNI est disponible, privilégier son choix d'image
key_mri_file = find_file("*Key_MRI*.csv", [DATA_DIR, PROJECT_ROOT])
if key_mri_file.exists():
    try:
        key_df = pd.read_csv(key_mri_file, low_memory=False)
        key_df.columns = [c.strip().strip('"') for c in key_df.columns]
        key_img_ids = set(key_df["image_id"].dropna().astype(str))
        irm["is_key_mri"] = irm["image_id"].astype(str).isin(key_img_ids)
        print(f"Alignement avec la table officielle ADNI Key_MRI ({key_mri_file.name})")
    except Exception:
        irm["is_key_mri"] = False
else:
    irm["is_key_mri"] = False

# Une seule IRM par patient :
# 1) Image officielle Key_MRI en priorité
# 2) La plus proche de T0
# 3) L'image la plus récente
# 4) Tri déterministe sur image_id
irm["abs_days_from_baseline"] = irm["days_from_baseline"].abs()
irm = irm.sort_values(
    ["PTID", "is_key_mri", "abs_days_from_baseline", "image_date", "image_id"],
    ascending=[True, False, True, False, True]
)

selection = irm.drop_duplicates(subset="PTID", keep="first").copy()
selection = selection.drop(columns=["is_key_mri"], errors="ignore")

# Ajouter le label clinique
cohort_subset = cohorte[["PTID", "target"]].dropna().drop_duplicates(subset="PTID")
selection = selection.merge(
    cohort_subset,
    on="PTID",
    how="inner"
)

# Sauvegarder les fichiers CSV dans outputs
selection.to_csv(fichier_sortie_90j, index=False)
selection.to_csv(fichier_sortie_sel, index=False)

# Générer la liste d'image_ids
image_ids = selection["image_id"].astype(str).tolist()
txt_content = "\n".join(image_ids) + "\n"
fichier_txt.write_text(txt_content, encoding="utf-8")

# Vérifications
print("Fichiers créés :")
print(f"- {fichier_sortie_90j}")
print(f"- {fichier_sortie_sel}")
print(f"- {fichier_txt}")
print("\nNombre de patients :", selection["PTID"].nunique())
print("Doublons PTID :", selection["PTID"].duplicated().sum())
print("Nombre d'image_ids exportés :", len(image_ids))
print("\nRépartition des classes :")
print(selection["target"].value_counts().sort_index())
print("\nDistance à T0 (jours) :")
print(selection["days_from_baseline"].describe())
