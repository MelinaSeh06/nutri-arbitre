# Journal d'usage de l'IA

Les exports des conversations sont dans ce dossier (`conversation_*.md` ou `.pdf`).

## Séance 1 : vendredi 30 octobre 2026 (journée)
- **Outil :** Claude.
- **Demandé :** choix du sujet, structure du projet, code du téléchargement, du nettoyage, des outils, du garde-fou, de l'agent et des tests.
- **Gardé tel quel :** …
- **Corrigé à la main (quoi ?) :** …
- **Prompt ou pseudo-code réécrit (quelle ligne, pourquoi) :** …

## Séance 2 : vendredi 30 octobre 2026 (soir)
- **Outil :** Claude Code (extension VS Code). Export : `conversation_2_2026-10-30.md`.
- **Demandé :** relire tout le projet et faire le point ; installer l'environnement et lancer les tests ;
  télécharger et nettoyer les données ; tester l'agent avec Qwen ; simplifier le code pour que je puisse
  l'expliquer à l'oral ; une fiche PDF d'explication de `download.py` ; un plan de présentation ; le premier commit.
- **Mes décisions :**
  - faire simplifier les passages trop compacts (`for … else`, `lambda`, fonction récursive du garde-fou)
    pour pouvoir expliquer n'importe quelle fonction, même si le code est un peu plus long ;
  - pas d'interface web : la démo se fera dans le terminal, où l'on voit les appels d'outils ;
  - garder les 957 céréales téléchargées (pages 1 à 10) plutôt que de retélécharger, pour que les réponses
    de la brique 9 restent fixes ; le biais (57 % de bio) sera écrit dans EVIDENCE.md ;
  - ne pas mettre le PDF de la consigne dans le dépôt.
- **Gardé tel quel :** les corrections proposées par l'IA après sa relecture, vérifiées par les tests (24 passent) :
  - garde-fou : l'arrondi accepté passe d'une unité à une demi-unité (avant, « 19 » passait pour 18,37) ;
  - outils : `bio` envoyé en texte (`"false"`) par le modèle n'inverse plus le filtre ;
  - téléchargement : 5 essais en cas d'erreur 503 et enregistrement après chaque page ;
  - compatibilité Python 3.9 (`from __future__ import annotations`) ;
  - `think=False` dans l'appel à Qwen (71 s → 29 s par question).
- **Corrigé à la main (quoi ?) :** rien cette séance.
- **Prompt ou pseudo-code réécrit (quelle ligne, pourquoi) :** aucun. Le test avec Qwen a montré deux
  problèmes à traiter plus tard : il a répondu « Non » alors que ses propres chiffres disaient « Oui »
  (le garde-fou vérifie les chiffres, pas le sens), et il a parlé de différence « significative » entre
  1 produit et 1 produit (ce que la brique 8 doit corriger).
