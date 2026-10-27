# RQ1 — Contribution de chaque modalité à la prédiction MCI → AD (24 mois)

Question : quel type de données (cognition, démographie, génétique,
biomarqueurs LCR, IRM) prédit le mieux la conversion MCI → Alzheimer ?
Chaque modalité est évaluée seule, avec les données disponibles à T0 uniquement.

## Structure

```
q1/
├── _shared/                 # code commun à toutes les modalités
│   ├── config.py            # chemins, fenêtre T0, paramètres de validation
│   ├── cohort.py            # cohorte, sélection au baseline, sauvegarde
│   ├── evaluation.py        # modèles, validation croisée, métriques
│   └── summarize.py         # comparaison finale des modalités
├── 01_cognitive/            # MMSE, CDR, ADAS-Cog 13, MoCA
├── 02_demographics/         # âge, sexe, éducation (PTDEMOG)
├── 03_genetique/            # génotype APOE (nombre d'allèles ε4 / ε2)
├── 04_biomarqueurs_lcr/     # Aβ42, tau, p-tau (Roche Elecsys)
├── 05_imagerie_irm/         # FreeSurfer (UCSFFSX7), non fourni ici
└── results/                 # sorties des modèles
```

Chaque dossier de modalité contient :
- `preprocessing.py` : extrait les variables au baseline et écrit `data/features.csv` ;
- `modeling.py` : entraîne les modèles et écrit `results/<modalité>_results.csv`.

## Ordre d'exécution

Depuis `q1/` (la cohorte `outputs/ADNI_MCI_AD_24M_cohort.csv` doit exister) :

```bash
for m in 01_cognitive 02_demographics 03_genetique 04_biomarqueurs_lcr 05_imagerie_irm; do
  (cd $m && python preprocessing.py && python modeling.py)
done
python _shared/summarize.py
```

Dépendances : `pandas numpy scikit-learn`.

## Règles appliquées

- **Pas de fuite temporelle** : chaque mesure est rattachée à T0 (date DXSUM `bl`)
  à +/- 60 jours (`BASELINE_WINDOW_DAYS`). Aucune visite de suivi n'est utilisée.
- **Pas de diagnostic dans les features** : le diagnostic définit la cible.
- **Imputation et normalisation dans le pipeline** : elles sont apprises sur le
  fold d'entraînement uniquement.
- **Codes sentinelles ADNI** (-1, -4) convertis en valeurs manquantes.
- **Colonnes vides exclues** automatiquement, avec un avertissement.
- **Validation** : 5 folds × 5 répétitions, stratifiée sur la cible.
- **Modèles** : régression logistique (référence) et forêt aléatoire,
  avec pondération des classes (converters ≈ 38 %).

## Limites connues

- Les fichiers fournis ne contiennent **pas** UCSFFSX7 (IRM), ni PET, ni plasma.
  La modalité IRM est donc prête dans le code mais non évaluable pour l'instant.
- **MoCA** : aucune mesure dans la fenêtre T0 pour cette extraction (début à m48).
- **LCR** : Aβ40 vide dans cette extraction, donc le rapport Aβ42/Aβ40 est exclu.
- Les effectifs diffèrent selon la modalité (ex. 48 patients pour le LCR).
  Les scores ne sont donc pas strictement comparables entre modalités tant que
  l'échantillon commun n'est pas utilisé. C'est à traiter avant la conclusion de RQ1.
- Cohorte de 100 sujets : les écarts-types sont larges ; une différence de
  quelques points d'AUROC n'est pas significative.
- Les noms de colonnes FreeSurfer (ST29SV, ST88SV, ST24TA, ST83TA, ST10CV) sont
  repris du projet et à vérifier dans DATADIC avant usage.
