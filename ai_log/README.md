# Journal d'usage de l'IA

Les exports des conversations sont dans ce dossier (`conversation_*.md` ou `.pdf`).

## Séance 1 : vendredi 30 octobre 2026
- **Outils et exports :**
  - Claude, pour la création du projet : `conversation_1a_creation.pdf` (à ajouter) ;
  - Claude Code (extension VS Code), le soir : `conversation_1b_claude_code_2026-10-30.md`.
- **Demandé :**
  - à Claude : le choix du sujet, la structure du projet, le code du téléchargement, du nettoyage, des
    outils, du garde-fou, de l'agent et des tests ;
  - à Claude Code : relire tout le projet et faire le point ; installer l'environnement et lancer les
    tests ; télécharger et nettoyer les données ; tester l'agent avec Qwen ; simplifier le code pour que
    je puisse l'expliquer à l'oral ; une fiche PDF d'explication de `download.py` ; un plan de
    présentation ; le premier commit.
- **Mes décisions :**
  - faire simplifier les passages trop compacts (`for … else`, `lambda`, fonction récursive du garde-fou)
    pour pouvoir expliquer n'importe quelle fonction, même si le code est un peu plus long ;
  - pas d'interface web : la démo se fera dans le terminal, où l'on voit les appels d'outils ;
  - garder les 957 céréales téléchargées (pages 1 à 10) plutôt que de retélécharger, pour que les réponses
    de la brique 9 restent fixes ; le biais (57 % de bio) sera écrit dans EVIDENCE.md ;
  - ne pas mettre le PDF de la consigne dans le dépôt.
- **Gardé tel quel :** les corrections proposées par Claude Code après sa relecture, vérifiées par les
  tests (24 passent) :
  - garde-fou : l'arrondi accepté passe d'une unité à une demi-unité (avant, « 19 » passait pour 18,37) ;
  - outils : `bio` envoyé en texte (`"false"`) par le modèle n'inverse plus le filtre ;
  - téléchargement : 5 essais en cas d'erreur 503 et enregistrement après chaque page ;
  - compatibilité Python 3.9 (`from __future__ import annotations`) ;
  - `think=False` dans l'appel à Qwen (71 s → 29 s par question).
- **Corrigé à la main (quoi ?) :** rien.
- **Prompt ou pseudo-code réécrit (quelle ligne, pourquoi) :** aucun. Le test avec Qwen a montré deux
  problèmes à traiter plus tard : il a répondu « Non » alors que ses propres chiffres disaient « Oui »
  (le garde-fou vérifie les chiffres, pas le sens), et il a parlé de différence « significative » entre
  1 produit et 1 produit (ce que la brique 8 doit corriger).

## Séance 2 : dimanche 1er novembre 2026
- **Outil et export :** Claude Code (extension VS Code) : `conversation_2_claude_code_2026-11-01.md`.
- **Demandé :** vérifier qu'on a bien accès aux données ; expliquer `clean.py` et `tools.py`, avec une
  fiche PDF pour chacun (`explications/02_clean.pdf`, `03_tools.pdf`) ; coder la brique 8 (marge d'erreur) ;
  répondre à mes questions de compréhension : le masque pandas, la marge d'erreur, la fourchette, les écarts
  négatifs, la combinaison des deux marges.
- **Mes décisions :**
  - **retirer les fiches dont l'énergie contredit la formule INCO** (plus de 20 % d'écart), au lieu de
    seulement les marquer : 437 kcal pour un muesli, ce n'est pas choquant, donc ce sont les autres valeurs
    qui ont été mal remplies ou remplies en partie. Comme on ne sait pas lesquelles, toute la fiche est
    douteuse. 4 produits sur 957 retirés, il en reste 953 ;
  - **garder les 25 produits sans Nutri-Score** : ils ont leurs autres valeurs et servent pour toutes les
    questions sauf celles sur le Nutri-Score. J'ai proposé de calculer leur Nutri-Score moi-même, mais on y
    a renoncé après vérification : 20 n'ont pas de teneur en sel (19) ou en acides gras saturés (1), et
    il faudrait l'inventer ; les 5 autres sont « non concernés » (aliments pour bébé). À la place, l'outil
    `comparer` indique combien de produits n'ont pas de Nutri-Score (`sans_nutriscore`) ;
  - **regrouper les écritures d'une même marque** (« kellogg s produits aliment sas » → kelloggs,
    « carrefour bio » → carrefour) : une marque qui commence par les mots entiers d'une autre est la même.
    Mots entiers et pas lettres, pour ne pas ranger « lucien georgelin » chez « lu ». La colonne bio reste
    fondée sur le label officiel, pas sur le nom de la marque. 28 fusions, 177 → 149 marques ;
  - planning : expliquer 2 codes par jour jusqu'à la fin.
- **Gardé tel quel :**
  - le code de la brique 8 dans `tools.py` (`_erreur_type`, `_intervalle`, `difference_nette`, `sans_nutriscore`),
    vérifié par 5 tests à réponse connue calculée à la main ;
  - `regrouper_marques` et la table `ALIAS_MARQUES` dans `clean.py`, après avoir relu la liste des 28 fusions
    écrite dans le journal de nettoyage ;
  - les fiches PDF d'explication. En tout, 31 tests passent.
- **Corrigé à la main (quoi ?) :** rien dans le code. Les trois changements du nettoyage viennent de mes
  questions et ont été codés par l'IA après mon accord.
- **Prompt ou pseudo-code réécrit (quelle ligne, pourquoi) :** deux lignes ajoutées au `PROMPT_SYSTEME`
  (`agent.py`) : « écris la marge d'erreur (marge_95) » et « si difference_nette vaut false, dis qu'on ne
  peut pas conclure », pour la brique 8. Premier essai réel : Qwen a bien répondu sur le sucre, mais sans
  écrire la marge. Le prompt ne suffit donc pas toujours, et ce sera à mesurer dans la brique 9.
- **Ce que j'ai appris :** je pensais qu'avec 4 fois plus de produits la marge serait plus grande. C'est
  l'inverse : l'erreur type diminue, et 1,96 × une erreur type plus petite donne une marge plus petite.
