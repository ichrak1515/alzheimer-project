# Q2 — Fusion multimodale et étude d'ablation

## 1. Objectif

Cette partie du projet étudie l'apport de la fusion multimodale pour prédire la conversion de patients présentant un trouble cognitif léger (*Mild Cognitive Impairment — MCI*) vers la maladie d'Alzheimer dans un délai de 24 mois.

Les expériences combinent plusieurs modalités cliniques, cognitives, démographiques, génétiques et biologiques. Une étude d'ablation complète l'analyse afin d'évaluer la contribution de chaque modalité aux performances prédictives.

## 2. Cohorte et données

Les expériences de fusion et l'étude d'ablation portent sur une cohorte de 100 patients ADNI :

- 50 patients convertisseurs vers Alzheimer ;
- 50 patients stables.

La variable cible distingue les patients convertisseurs des patients stables à l'horizon de 24 mois après le baseline.

### Modalités et variables

| Modalité | Variables | Nombre |
|---|---|---:|
| Cognition | MMSE, CDR-SB, CDR global, ADAS13 | 4 |
| Démographie | Âge, sexe, niveau d'éducation | 3 |
| Génétique | Nombre d'allèles APOE ε4 et ε2 | 2 |
| Biomarqueurs du LCR | Aβ40, Aβ42, ratio Aβ42/Aβ40, tau et p-tau transformés logarithmiquement | 5 |
| **Total** | | **14** |

Les variables sont préparées dans les fichiers de caractéristiques de `q1/`. L'IRM n'est pas incluse dans les expériences présentées ici.

## 3. Méthodologie

Deux modèles de classification sont évalués :

- **Logistic Regression** : régression logistique avec imputation des valeurs manquantes et standardisation.
- **Random Forest** : ensemble d'arbres de décision avec imputation des valeurs manquantes.

Le prétraitement, les paramètres et la validation croisée sont définis dans les modules partagés du projet, notamment `q1/_shared/evaluation.py`.

### Métriques

- **AUROC** : capacité à distinguer les convertisseurs des patients stables.
- **AUPRC** : synthèse de la précision et du rappel.
- **Sensibilité** : proportion de convertisseurs correctement détectés.
- **Spécificité** : proportion de patients stables correctement identifiés.
- **F1-score** : compromis entre précision et rappel.

Les résultats sont présentés sous la forme **moyenne ± écart-type** sur les évaluations de validation croisée.

## 4. Expériences de fusion multimodale

Dix combinaisons de modalités sont évaluées.

| Expérience | Modalités | Variables |
|---|---|---:|
| Q2-01 | Cognition + démographie | 7 |
| Q2-02 | Cognition + génétique | 6 |
| Q2-03 | Cognition + LCR | 9 |
| Q2-04 | Démographie + génétique | 5 |
| Q2-05 | Démographie + LCR | 8 |
| Q2-06 | Cognition + démographie + génétique | 9 |
| Q2-07 | Cognition + démographie + LCR | 12 |
| Q2-08 | Cognition + génétique + LCR | 11 |
| Q2-09 | Démographie + génétique + LCR | 10 |
| Q2-10 | Cognition + démographie + génétique + LCR | 14 |

### 4.1 Comparaison des performances

#### AUROC

| Expérience | Logistic Regression | Random Forest |
|---|---:|---:|
| Q2-01 | 0,7960 ± 0,1038 | 0,7704 ± 0,1054 |
| Q2-02 | 0,8164 ± 0,0893 | 0,8264 ± 0,0842 |
| Q2-03 | 0,8212 ± 0,1075 | **0,8728 ± 0,0776** |
| Q2-04 | 0,7512 ± 0,0846 | 0,6848 ± 0,1171 |
| Q2-05 | 0,7656 ± 0,0877 | 0,7460 ± 0,0955 |
| Q2-06 | 0,8160 ± 0,0873 | 0,8216 ± 0,0893 |
| Q2-07 | 0,8056 ± 0,0996 | 0,8544 ± 0,0772 |
| Q2-08 | 0,8156 ± 0,1099 | 0,8708 ± 0,0735 |
| Q2-09 | 0,7580 ± 0,0986 | 0,7448 ± 0,1024 |
| Q2-10 | 0,8040 ± 0,0984 | 0,8524 ± 0,0741 |

#### AUPRC

| Expérience | Logistic Regression | Random Forest |
|---|---:|---:|
| Q2-01 | 0,7872 ± 0,1148 | 0,7451 ± 0,1156 |
| Q2-02 | 0,8017 ± 0,1102 | 0,8192 ± 0,0915 |
| Q2-03 | 0,7830 ± 0,1189 | **0,8655 ± 0,0913** |
| Q2-04 | 0,7956 ± 0,0703 | 0,7538 ± 0,0890 |
| Q2-05 | 0,7478 ± 0,0773 | 0,7118 ± 0,1039 |
| Q2-06 | 0,8097 ± 0,1039 | 0,8119 ± 0,1024 |
| Q2-07 | 0,7742 ± 0,1128 | 0,8365 ± 0,1051 |
| Q2-08 | 0,7822 ± 0,1193 | 0,8647 ± 0,0838 |
| Q2-09 | 0,7603 ± 0,0912 | 0,7168 ± 0,1094 |
| Q2-10 | 0,7852 ± 0,1125 | 0,8406 ± 0,0890 |

### 4.2 Interprétation

La combinaison **cognition + LCR (Q2-03)** obtient les meilleures performances moyennes observées parmi les dix expériences pour Random Forest : une AUROC de 0,8728 et une AUPRC de 0,8655.

Les résultats montrent également que :

- Les combinaisons contenant la cognition obtiennent généralement de meilleures performances que les combinaisons sans cognition.
- La combinaison cognition + génétique + LCR (Q2-08) présente des performances proches de Q2-03.
- La fusion des quatre modalités (Q2-10) n'améliore pas systématiquement les performances par rapport aux combinaisons utilisant moins de modalités.
- Les combinaisons démographie + génétique et démographie + LCR présentent des performances plus faibles pour Random Forest dans cette cohorte.

Ces observations sont descriptives et ne démontrent pas, à elles seules, la supériorité statistique d'une combinaison.

## 5. Étude d'ablation — Q2-11

### 5.1 Objectif

L'étude d'ablation part de la configuration complète Q2-10 et supprime une modalité à la fois. Les cinq configurations sont évaluées sur les mêmes 100 patients.

| Configuration | Modalités conservées | Variables |
|---|---|---:|
| Complet | Cognition + démographie + génétique + LCR | 14 |
| Sans cognition | Démographie + génétique + LCR | 10 |
| Sans démographie | Cognition + génétique + LCR | 11 |
| Sans génétique | Cognition + démographie + LCR | 12 |
| Sans LCR | Cognition + démographie + génétique | 9 |

### 5.2 Résultats de l'ablation

#### AUROC

| Configuration | Logistic Regression | Random Forest |
|---|---:|---:|
| Complet | 0,8040 ± 0,0984 | 0,8524 ± 0,0741 |
| Sans cognition | 0,7580 ± 0,0986 | 0,7448 ± 0,1024 |
| Sans démographie | 0,8156 ± 0,1099 | **0,8708 ± 0,0735** |
| Sans génétique | 0,8056 ± 0,0996 | 0,8544 ± 0,0772 |
| Sans LCR | 0,8160 ± 0,0873 | 0,8216 ± 0,0893 |

#### AUPRC

| Configuration | Logistic Regression | Random Forest |
|---|---:|---:|
| Complet | 0,7852 ± 0,1125 | 0,8406 ± 0,0890 |
| Sans cognition | 0,7603 ± 0,0912 | 0,7168 ± 0,1094 |
| Sans démographie | 0,7822 ± 0,1193 | **0,8647 ± 0,0838** |
| Sans génétique | 0,7742 ± 0,1128 | 0,8365 ± 0,1051 |
| Sans LCR | 0,8097 ± 0,1039 | 0,8119 ± 0,1024 |

### 5.3 Interprétation de l'ablation

- **Cognition :** sa suppression entraîne une diminution importante de l'AUROC, particulièrement pour Random Forest, qui passe de 0,8524 à 0,7448.
- **LCR :** sa suppression réduit l'AUROC de Random Forest de 0,8524 à 0,8216, ce qui suggère un apport prédictif complémentaire.
- **Génétique :** sa suppression entraîne une variation faible de l'AUROC de Random Forest, qui passe de 0,8524 à 0,8544.
- **Démographie :** sa suppression augmente l'AUROC de Random Forest à 0,8708. Dans cette cohorte, les variables démographiques n'apportent donc pas d'amélioration apparente à la configuration complète.

La meilleure AUROC observée pour Random Forest est de 0,8728 avec cognition + LCR dans Q2-03, et de 0,8708 sans démographie dans l'ablation Q2-11.

Les différences restent exploratoires compte tenu de la taille de la cohorte et de la variabilité des évaluations.

## 6. Résultats complémentaires de Q2-10

Pour la configuration complète, les autres métriques sont :

| Modèle | Sensibilité | Spécificité | F1-score |
|---|---:|---:|---:|
| Logistic Regression | 0,7720 ± 0,1308 | 0,7520 ± 0,1327 | 0,7622 ± 0,0981 |
| Random Forest | 0,8240 ± 0,1200 | 0,7560 ± 0,1261 | 0,7954 ± 0,0832 |

Random Forest présente ici une sensibilité et un F1-score moyens supérieurs à ceux de la régression logistique.

## 7. Structure du dossier

```text
q2/
├── README.md
├── 01_cognitive_demographics/
├── 02_cognitive_genetique/
├── 03_cognitive_lcr/
├── 04_demographics_genetique/
├── 05_démographie_LCR/
├── 06_cognitive_demographics_genetique/
├── 07_cognitive_demographics_lcr/
├── 08_cognitive_genetique_lcr/
├── 09_demographics_genetique_lcr/
├── 10_cognitive_demographics_genetique_lcr/
└── 11_ablation/
```

Chaque dossier d'expérience contient son script `modeling.py` et un dossier `results/` avec les résultats correspondants.

Le dossier `11_ablation/` contient notamment :

- `modeling.py` : exécution des cinq configurations ;
- `results/cohorte_ablation_rids.csv` : identifiants des patients retenus ;
- `results/ablation_details.csv` : résultats détaillés des expériences ;
- `results/ablation_summary.csv` : résumé des performances.

## 8. Conclusion générale

Les expériences montrent que la combinaison des variables cognitives et des biomarqueurs du LCR est particulièrement performante dans cette cohorte. Random Forest atteint une AUROC moyenne de 0,8728 et une AUPRC moyenne de 0,8655 avec ces deux modalités.

L'étude d'ablation confirme l'importance de la cognition dans les performances observées et suggère un apport complémentaire des biomarqueurs du LCR. L'ajout de toutes les modalités ne garantit cependant pas une amélioration des résultats.

La cohorte étant limitée à 100 patients, ces résultats doivent être considérés comme préliminaires. Une validation indépendante, une analyse plus approfondie des valeurs manquantes et une évaluation de la robustesse des modèles sont nécessaires avant d'envisager une utilisation clinique.
