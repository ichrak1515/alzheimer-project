from pathlib import Path
import pandas as pd
import sys

# Ajouter scripts au path si nécessaire
try:
    from config import DATA_DIR, OUTPUT_DIR
except ImportError:
    from scripts.config import DATA_DIR, OUTPUT_DIR

print("Dossier source :", DATA_DIR)
print("Existe :", DATA_DIR.exists())

files = sorted(list(DATA_DIR.glob("*.csv")))
print("Nombre de CSV :", len(files))

summary = []

for file in files:
    if "summary" in file.name.lower():
        continue

    try:
        df = pd.read_csv(file, low_memory=False)

        for col in df.columns:
            summary.append({
                "file": file.name,
                "column": col,
                "dtype": str(df[col].dtype),
                "non_null": int(df[col].notna().sum()),
                "unique": int(df[col].nunique())
            })

        print(f"[OK] {file.name}")

    except Exception as e:
        print(f"[ERROR] {file.name} : {e}")

result = pd.DataFrame(summary)

# Sauvegarder dans outputs
output_file = OUTPUT_DIR / "ADNI_columns_summary.csv"
result.to_csv(output_file, index=False, encoding="utf-8-sig")

print("\n==============================")
print("Terminé")
print("Colonnes résumées :", len(result))
print("Fichier :", output_file)
print("==============================")