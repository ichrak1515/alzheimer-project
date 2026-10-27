"""RQ1 — Modèles sur la modalité GÉNÉTIQUE uniquement."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "_shared"))

from evaluation import run_modality

run_modality("03_genetique", HERE / "data" / "features.csv")
