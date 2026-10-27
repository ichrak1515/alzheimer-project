import pandas as pd
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent))
try:
    from config import PROJECT_ROOT, OUTPUT_DIR, DXSUM_FILE, find_file
except ImportError:
    from scripts.config import PROJECT_ROOT, OUTPUT_DIR, DXSUM_FILE, find_file

fichier_qualite = find_file("ADNI_MCI_AD_24M_quality_check.csv", [OUTPUT_DIR, PROJECT_ROOT])
fichier_visites = find_file("ADNI_MCI_AD_24M_T24_visits.csv", [OUTPUT_DIR, PROJECT_ROOT])

print(f"Qualité cohorte source : {fichier_qualite}")
print(f"Visites source         : {fichier_visites}")
print(f"DXSUM source           : {DXSUM_FILE}")

cohorte = pd.read_csv(fichier_qualite)
cohorte.columns = cohorte.columns.str.strip()

print("\n" + "=" * 60)
print("1. EFFECTIFS DES STATUTS ACTUELS")
print("=" * 60)

if "status" in cohorte.columns:
    print(cohorte["status"].value_counts(dropna=False))
else:
    print("Colonne 'status' absente. Colonnes disponibles :", cohorte.columns.tolist())

# Charger les visites :
# Privilégier la table complète DXSUM si disponible pour avoir M06, M12, M18, M24
suivi_complet = None
if DXSUM_FILE.exists():
    try:
        dx = pd.read_csv(DXSUM_FILE, low_memory=False)
        dx.columns = dx.columns.str.strip().str.strip('"')
        dx["EXAMDATE"] = pd.to_datetime(dx["EXAMDATE"], errors="coerce")
        dx["RID"] = pd.to_numeric(dx["RID"], errors="coerce")

        if "baseline_date" in cohorte.columns and "RID" in cohorte.columns:
            base_dates = cohorte[["RID", "baseline_date"]].dropna().drop_duplicates(subset="RID")
            base_dates["baseline_date"] = pd.to_datetime(base_dates["baseline_date"], errors="coerce")
            merged_dx = dx.merge(base_dates, on="RID", how="inner")
            merged_dx["days_from_baseline"] = (merged_dx["EXAMDATE"] - merged_dx["baseline_date"]).dt.days
            merged_dx["months_from_baseline"] = merged_dx["days_from_baseline"] / 30.4375

            # Détecter AD via DXAD ou DIAGNOSIS==3
            is_ad = (pd.to_numeric(merged_dx.get("DXAD"), errors="coerce") == 1)
            if "DIAGNOSIS" in merged_dx.columns:
                is_ad = is_ad | (pd.to_numeric(merged_dx["DIAGNOSIS"], errors="coerce") == 3)
            merged_dx["is_AD"] = is_ad

            suivi_complet = merged_dx
            print(f"\nTable complète DXSUM chargée : {len(suivi_complet)} visites pour {suivi_complet['RID'].nunique()} patients de la cohorte.")
    except Exception as e:
        print("Note : Impossible de charger le suivi complet DXSUM :", e)

print("\n" + "=" * 60)
print("2. DIAGNOSTICS À LA VISITE PROCHE DE 24 MOIS")
print("=" * 60)

if fichier_visites.exists():
    visites = pd.read_csv(fichier_visites)
    print("Nombre de visites T24 :", len(visites))
    print("Nombre de patients T24 :", visites["RID"].nunique())
    if "diagnosis" in visites.columns:
        print("\nRépartition des diagnostics T24 :")
        print(visites["diagnosis"].value_counts(dropna=False))

print("\n" + "=" * 60)
print("3. RECHERCHE D'UN DIAGNOSTIC AD AVANT OU À 24 MOIS")
print("=" * 60)

if suivi_complet is not None:
    # Analyse sur l'ensemble du suivi de 0 à 27 mois
    visites_0_27m = suivi_complet[
        (suivi_complet["months_from_baseline"] >= 0) &
        (suivi_complet["months_from_baseline"] <= 27)
    ].copy()

    patients_ad = set(visites_0_27m.loc[visites_0_27m["is_AD"], "RID"].dropna())
    print(f"Patients avec au moins une visite AD entre 0 et 27 mois : {len(patients_ad)}")
else:
    # Fallback sur visites T24
    visites["months_from_baseline"] = pd.to_numeric(visites["months_from_baseline"], errors="coerce")
    visites["DXAD"] = pd.to_numeric(visites["DXAD"], errors="coerce")
    suivi_sub = visites[(visites["months_from_baseline"] >= 0) & (visites["months_from_baseline"] <= 27)]
    patients_ad = set(suivi_sub.loc[suivi_sub["DXAD"] == 1, "RID"].dropna())
    print(f"Patients avec DXAD = 1 (visites disponibles) : {len(patients_ad)}")

if "RID" in cohorte.columns and "status" in cohorte.columns:
    cohorte["AD_avant_ou_a_24m"] = cohorte["RID"].isin(patients_ad)

    print("\nCroisement Statut Cohorte x Diagnostic AD antérieur ou à 24 mois :")
    print(pd.crosstab(
        cohorte["status"],
        cohorte["AD_avant_ou_a_24m"],
        margins=True
    ))

    # Patients actuellement STABLE_MCI ayant eu un diagnostic AD
    suspects = cohorte[
        (cohorte["status"] == "STABLE_MCI") &
        (cohorte["AD_avant_ou_a_24m"])
    ]

    print(f"\nPatients classés STABLE_MCI ayant pourtant un diagnostic AD : {len(suspects)}")
    if len(suspects) > 0:
        print(suspects[["RID", "status", "AD_avant_ou_a_24m"]])

    fichier_suspects_out = OUTPUT_DIR / "patients_stable_MCI_a_verifier.csv"
    suspects.to_csv(fichier_suspects_out, index=False)

    print(f"\nFichier créé : {fichier_suspects_out}")

print("\nVérification terminée avec succès.")
