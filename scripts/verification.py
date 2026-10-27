from pathlib import Path
import pandas as pd
import sys

try:
    from config import PROJECT_ROOT, OUTPUT_DIR, find_file
except ImportError:
    from scripts.config import PROJECT_ROOT, OUTPUT_DIR, find_file

chemin = find_file("ADNI_MRI_T1_candidates_near_baseline.csv", [OUTPUT_DIR, PROJECT_ROOT])
fichier_cohorte = find_file("ADNI_MCI_AD_24M_cohort_with_PTID.csv", [OUTPUT_DIR, PROJECT_ROOT])

if not chemin.exists():
    print(f"Fichier candidates introuvable : {chemin}")
    raise SystemExit

print("Fichier trouvé :", chemin)
df = pd.read_csv(chemin)
print("Colonnes :", df.columns.tolist())

ID = "PTID"

print("\nNombre de lignes (= nombre d'IRM) :", len(df))
print("Nombre de patients différents    :", df[ID].nunique())

print("\nNombre d'IRM par patient :")
print(df.groupby(ID).size().value_counts().sort_index())

# 1) l'IRM la plus proche de T0 pour chaque patient
proche = df.loc[df.groupby("PTID")["abs_days_from_baseline"].idxmin()]
print("\nIRM retenues (1 par patient) :", len(proche))
print("Distance à T0 (en jours) :")
print(proche["abs_days_from_baseline"].describe())

# 2) y a-t-il plusieurs IRM à la même date pour un même patient ?
doublons = df.duplicated(["PTID", "image_date"]).sum()
print("\nIRM ayant la même date qu'une autre du même patient :", doublons)

coh = pd.read_csv(fichier_cohorte)
print("\nColonnes cohorte :", coh.columns.tolist())
print("Patients cohorte :", coh["PTID"].nunique())

CIBLE = "target"

avec_irm = coh["PTID"].isin(proche["PTID"])
print("\nAvec IRM candidate :", avec_irm.sum())
print("Sans IRM candidate :", (~avec_irm).sum())
print("IRM hors cohorte   :", (~proche["PTID"].isin(coh["PTID"])).sum())

print("\nRépartition de la cible :")
print("Cohorte entière :\n", coh[CIBLE].value_counts())
print("Avec IRM        :\n", coh.loc[avec_irm, CIBLE].value_counts())
proche = proche.merge(coh[["PTID", "target"]], on="PTID")

print("\nIRM retenues avant T0 :", (proche["days_from_baseline"] < 0).sum())
print("IRM retenues après T0 :", (proche["days_from_baseline"] > 0).sum())

print("\nFenêtre avant T0 | Patients | Converters | Stables")

for jours in [30, 60, 90]:
    s = proche[
        (proche["days_from_baseline"] <= 0) &
        (proche["days_from_baseline"] >= -jours)
    ]

    converters = int((s["target"] == 1).sum())
    stables = int((s["target"] == 0).sum())

    print(
        f"{jours:>3} jours       | "
        f"{len(s):>8} | "
        f"{converters:>10} | "
        f"{stables:>7}"
    )