"""Compare toutes les modalités de RQ1 (lit results/*.csv)."""
import pandas as pd
from config import RESULTS_DIR

files = sorted(RESULTS_DIR.glob("*_results.csv"))
if not files:
    raise SystemExit("Aucun résultat. Lancer les modeling.py d'abord.")

df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
df["score"] = df.apply(lambda r: f"{r['mean']:.3f} ± {r['std']:.3f}", axis=1)

table = df.pivot_table(index=["modality", "n", "n_pos", "model"],
                       columns="metric", values="score", aggfunc="first")
table = table[["AUROC", "AUPRC", "Sensibilite", "Specificite", "F1"]]
table = table.sort_values("AUROC", ascending=False)

print("\nRQ1 — comparaison des modalités (validation croisée)\n")
print(table.to_string())
table.to_csv(RESULTS_DIR / "RQ1_comparaison.csv")
print(f"\nFichier : {RESULTS_DIR / 'RQ1_comparaison.csv'}")
