# Preuves, brique par brique

Briques choisies : 1, 3, 6, 8, 9.

## Brique 1 : mon propre outil
- **Ce que je montre :** le modèle appelle `comparer`, `decrire`, `classement_marques`, `compter`, fonctions écrites dans `nutri/tools.py`.
- **Fichiers :** `nutri/tools.py`, `nutri/agent.py`, `traces/<À COMPLÉTER>.json`
- **Reproduire :** `python -m nutri.agent "Les céréales bio contiennent-elles moins de sucre ?"`

## Brique 3 : une règle imposée par le code
- **Règle :** le système n'affiche jamais un chiffre qui n'a pas été calculé par un outil.
- **Où :** `nutri/garde_fou.py`, appliqué dans `nutri/agent.py` (fonction `repondre`).
- **Test qui essaie d'enfreindre la règle :** `tests/test_garde_fou.py`
- **Reproduire :** `python -m pytest tests/test_garde_fou.py -v`
- **Exemple réel bloqué :** `traces/<À COMPLÉTER>.json`

## Brique 6 : données sales, décisions écrites
- **Données :** Open Food Facts, catégorie « breakfast-cereals », pays France.
- **Journal :** `data/journal_nettoyage.md`
- **Règle absente du fichier :** règlement (UE) n° 1169/2011 « INCO », annexe XIV : sel = sodium × 2,5 et énergie = 4 × glucides + 4 × protéines + 9 × lipides + 2 × fibres.
- **Reproduire :** `python -m nutri.download && python -m nutri.clean`

## Brique 8 : des chiffres avec leur incertitude
*(jour 2)*

## Brique 9 : une comparaison mesurée
*(jour 2)*
