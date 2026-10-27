"""RQ1 — Modèles sur la modalité DÉMOGRAPHIQUE uniquement."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "_shared"))

from evaluation import run_modality

run_modality("02_demographics", HERE / "data" / "features.csv")
