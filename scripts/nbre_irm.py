import pandas as pd
from pathlib import Path
import sys

try:
    from config import PROJECT_ROOT, OUTPUT_DIR, find_file
except ImportError:
    from scripts.config import PROJECT_ROOT, OUTPUT_DIR, find_file

csv_path = find_file("ADNI_MRI_T1_candidates_near_baseline.csv", [OUTPUT_DIR, PROJECT_ROOT])

print("Fichier recherché :", csv_path)
print("Fichier existant  :", csv_path.exists())

if not csv_path.exists():
    raise FileNotFoundError(f"Fichier introuvable : {csv_path}")

df = pd.read_csv(csv_path)

# Nombre de candidates IRM par patient
counts = df.groupby("PTID").size()

print("\nPatients avec au moins une IRM :", len(counts))
print("\nRépartition du nombre d'IRM candidates par patient :")
print(counts.value_counts().sort_index())

print("\nPatients ayant plusieurs IRM candidates :")
print(counts[counts > 1].sort_values(ascending=False).head(20))
