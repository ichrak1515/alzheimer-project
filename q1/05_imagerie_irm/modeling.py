"""RQ1 — Modèles sur la modalité IMAGERIE IRM uniquement (tableau FreeSurfer)."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "_shared"))

from evaluation import run_modality

run_modality("05_imagerie_irm", HERE / "data" / "features.csv")
