import pandas as pd
from pathlib import Path
import sys

try:
    from config import PROJECT_ROOT, OUTPUT_DIR, find_file
except ImportError:
    from scripts.config import PROJECT_ROOT, OUTPUT_DIR, find_file

p = find_file("ADNI_T1_baseline_selected.csv", [OUTPUT_DIR, PROJECT_ROOT])

print("Fichier recherché :", p)
print("Fichier existant  :", p.exists())

if p.exists():
    df = pd.read_csv(p)

    print("Dimensions :", df.shape)
    print("Colonnes   :", df.columns.tolist())
    print(df.head())

    if "PTID" in df.columns:
        print("\nPatients uniques :", df["PTID"].nunique())
        print("Lignes en double par patient :", df["PTID"].duplicated().sum())

    if "days_from_baseline" in df.columns:
        valides = df[df["days_from_baseline"].between(-30, 0)].copy()
        print("\nPatients avec une IRM entre J-30 et J0 :", valides["PTID"].nunique())
        print("Patients avec une IRM après la baseline :", (df["days_from_baseline"] > 0).sum())
        print("Patients avec une IRM à plus de 30 jours avant la baseline :", (df["days_from_baseline"] < -30).sum())
else:
    print("Le fichier n'existe pas à cet emplacement.")