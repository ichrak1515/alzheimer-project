from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Dossier des tables cliniques ADNI :
# 1) Variable d'environnement ADNI_DATA_DIR si définie
# 2) Tables_27Oct2026 si existant
# 3) data/raw par défaut
env_data = os.getenv("ADNI_DATA_DIR")
if env_data and Path(env_data).exists():
    DATA_DIR = Path(env_data)
elif (PROJECT_ROOT / "Tables_27Oct2026").exists():
    DATA_DIR = PROJECT_ROOT / "Tables_27Oct2026"
elif (PROJECT_ROOT / "data" / "raw").exists():
    DATA_DIR = PROJECT_ROOT / "data" / "raw"
else:
    DATA_DIR = PROJECT_ROOT / "Tables_27Oct2026"

# SORTIE : fichiers créés par les scripts
OUTPUT_DIR = PROJECT_ROOT / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


def find_file(name_patterns, search_dirs=None):
    """Recherche un fichier selon des motifs dans plusieurs dossiers."""
    if search_dirs is None:
        search_dirs = [OUTPUT_DIR, DATA_DIR, PROJECT_ROOT, PROJECT_ROOT / "data" / "raw"]
    if isinstance(name_patterns, str):
        name_patterns = [name_patterns]

    for d in search_dirs:
        if not d.exists():
            continue
        for pattern in name_patterns:
            if "*" in pattern:
                matches = list(d.glob(pattern))
                if matches:
                    return sorted(matches)[-1]  # Le plus récent / dernier par ordre alphabétique
            else:
                candidate = d / pattern
                if candidate.exists():
                    return candidate
    return search_dirs[0] / name_patterns[0]


# Fichiers clés résolus dynamiquement avec fallbacks appropriés
DXSUM_FILE = find_file(["*DXSUM*.csv", "DXSUM_05Oct2026.csv"])
ROSTER_FILE = find_file(["*ROSTER*.csv", "ROSTER_05Oct2026.csv"])
MANIFEST_FILE = find_file(["*Manifest*.csv", "100-ID_Clinical_Cohort_Manifest_27Oct2026.csv"])
COHORT_WITH_PTID_FILE = find_file(["ADNI_MCI_AD_24M_cohort_with_PTID.csv"], [OUTPUT_DIR, PROJECT_ROOT])
MRI_CANDIDATES_FILE = find_file(["ADNI_MRI_T1_candidates_near_baseline.csv"], [OUTPUT_DIR, PROJECT_ROOT])