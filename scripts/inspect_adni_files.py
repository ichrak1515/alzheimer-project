from pathlib import Path
import pandas as pd
import sys

try:
    from config import DATA_DIR, OUTPUT_DIR
except ImportError:
    from scripts.config import DATA_DIR, OUTPUT_DIR

print("Dossier source :", DATA_DIR)

# Tous les CSV
files = sorted([f for f in DATA_DIR.glob("*.csv") if "summary" not in f.name.lower()])

summary = []

for file in files:
    try:
        df = pd.read_csv(file, low_memory=False)

        important_cols = [
            "RID", "PTID", "VISCODE", "VISCODE2",
            "VISDATE", "EXAMDATE", "PHASE",
            "DX", "DXCURREN", "DXCHANGE"
        ]

        present = [c for c in important_cols if c in df.columns]

        # Vérification des doublons RID + VISCODE
        duplicate_count = None

        if "RID" in df.columns:
            visit_col = None

            if "VISCODE" in df.columns:
                visit_col = "VISCODE"
            elif "VISCODE2" in df.columns:
                visit_col = "VISCODE2"

            if visit_col:
                duplicate_count = df.duplicated(
                    subset=["RID", visit_col]
                ).sum()

        summary.append({
            "file": file.name,
            "rows": len(df),
            "columns": len(df.columns),
            "important_columns": ", ".join(present),
            "duplicate_RID_VISCODE": duplicate_count
        })

        print(f"[OK] {file.name}")

    except Exception as e:
        summary.append({
            "file": file.name,
            "rows": None,
            "columns": None,
            "important_columns": f"ERROR: {e}",
            "duplicate_RID_VISCODE": None
        })

        print(f"[ERROR] {file.name} : {e}")


summary_df = pd.DataFrame(summary)

output = OUTPUT_DIR / "ADNI_files_summary.csv"
summary_df.to_csv(output, index=False, encoding="utf-8-sig")

print("\nRésumé terminé.")
print(f"Fichier créé : {output}")
