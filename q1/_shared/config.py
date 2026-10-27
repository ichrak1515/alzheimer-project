"""Paramètres communs à toutes les modalités de RQ1."""
import os
from pathlib import Path

Q1_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Dossier des tables ADNI brutes (même logique que scripts/config.py)
_env = os.getenv("ADNI_DATA_DIR")
if _env and Path(_env).exists():
    DATA_DIR = Path(_env)
elif (PROJECT_ROOT / "Tables_27Oct2026").exists():
    DATA_DIR = PROJECT_ROOT / "Tables_27Oct2026"
else:
    DATA_DIR = PROJECT_ROOT / "data" / "raw"

# Cohorte produite par scripts/build_adni_cohort.py
COHORT_FILE = PROJECT_ROOT / "outputs" / "ADNI_MCI_AD_24M_cohort.csv"

RESULTS_DIR = Q1_DIR / "results"

# Échantillon commun de 100 patients (même liste pour toutes les modalités)
USE_SAMPLE_100 = True
SAMPLE_RIDS_FILE = Q1_DIR / "_shared" / "rids_100.csv"
SAMPLE_PER_CLASS = 50

# Fenêtre autour de la date T0 (DXSUM bl) pour rattacher une mesure au baseline
BASELINE_WINDOW_DAYS = 60

# Valeurs sentinelles ADNI : -4 = non disponible, -1 = inconnu
ADNI_MISSING_CODES = [-1, -4]

# Validation
CV_SPLITS = 5
CV_REPEATS = 5
RANDOM_STATE = 42
