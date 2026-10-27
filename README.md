# ALZ_ADNI — Alzheimer's Disease Neuroimaging Initiative (ADNI) Project

## Objectif

Ce projet vise à identifier, parmi les patients **MCI (Mild Cognitive Impairment)** du dataset ADNI, ceux qui ont **converti vers Alzheimer's Disease (AD)** dans un délai de 24 mois à partir du baseline. L'objectif final est la construction d'une cohorte équilibrée pour l'entraînement d'un modèle de classification basé sur l'IRM cérébrale T1.

**Labels cibles :**
- `1` → MCI → AD (convertisseur à 24 mois)
- `0` → MCI → MCI stable (non-convertisseur)

---

## Structure du Projet

```
ALZ_ADNI/
├── scripts/               # Scripts Python de traitement
│   ├── config.py          # Chemins et paramètres centralisés
│   ├── build_adni_cohort.py       # Construction de la cohorte MCI→AD vs stable
│   ├── select_baseline_mri.py     # Sélection des IRM T1 baseline
│   ├── selection_irm_finale.py    # Sélection finale des IRM
│   ├── analyze_mci_followup.py    # Analyse du suivi à 24 mois
│   ├── verification.py            # Vérification des conversions MCI→AD
│   ├── verifier.py                # Vérification approfondie des patients
│   ├── prepare_adni_ids.py        # Préparation des listes d'IDs ADNI
│   ├── inspect_adni_files.py      # Inspection des fichiers ADNI
│   ├── column_adni.py             # Résumé des colonnes ADNI
│   └── nbre_irm.py                # Comptage des IRM par patient
├── outputs/               # Résultats générés (ignorés par Git sauf résumés)
├── Tables_27Oct2026/      # Données ADNI brutes (ignorées par Git)
├── .gitignore
└── README.md
```

---

## Pipeline

1. **`build_adni_cohort.py`** — Construit la cohorte en identifiant les MCI qui convertissent en AD à 24 mois (±3 mois, soit 21–27 mois) depuis le DXSUM.
2. **`select_baseline_mri.py`** — Sélectionne l'IRM T1 baseline pour chaque sujet (dans les 90 jours suivant le baseline).
3. **`selection_irm_finale.py`** — Sélection finale et vérification de qualité.
4. **`analyze_mci_followup.py`** — Analyse le statut des MCI à 24 mois.
5. **`verification.py`** — Vérifie les conversions MCI→AD dans les données.

---

## Données

Les données ADNI sont soumises à un accord d'accès. Elles **ne sont pas incluses** dans ce dépôt.

Pour accéder aux données : [adni.loni.usc.edu](https://adni.loni.usc.edu)

---

## Environnement

```bash
pip install pandas numpy
```

---

## Cohort Summary (100 sujets)

| Groupe | N |
|--------|---|
| MCI → AD (convertisseurs) | ~50 |
| MCI stable | ~50 |

Voir `outputs/ADNI_MCI_AD_24M_cohort.csv` pour les détails.
