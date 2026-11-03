# Preuves, brique par brique

Briques choisies : 1, 3, 6, 8, 9.
Modèle : `qwen3.5:4b-q4_K_M` (Ollama), `num_ctx` = 8192, `think=False`.

## Brique 1 : mon propre outil
- **Ce que je montre :** le modèle appelle `decrire`, `comparer`, `classement_marques` et `compter`, des fonctions
  écrites dans `nutri/tools.py`. Le modèle ne fait aucun calcul : il demande un outil, Python l'exécute
  (`executer_outil` dans `nutri/agent.py`), et le résultat lui est renvoyé.
- **Fichiers :** `nutri/tools.py`, `nutri/agent.py`, `tests/test_tools.py`
- **Traces :**
  - `traces/trace_20261101_125333.json` : « Les céréales bio contiennent-elles moins de sucre ? » →
    `comparer(sucres, groupe=bio)` → 13,2 g contre 18,6 g ;
  - `traces/trace_20261102_113831.json` : « Quelle est la teneur moyenne en sel des céréales bio ? » →
    `decrire(sel, bio=True)` → 0,13 g ± 0,02 g.
- **Reproduire :** `python -m nutri.agent "Les céréales bio contiennent-elles moins de sucre ?"`

## Brique 3 : une règle imposée par le code
- **Règle 1 :** le système n'affiche jamais un chiffre qui n'a pas été calculé par un outil. Chaque nombre de la
  réponse doit être un arrondi correct d'un nombre des résultats d'outils (ou de la question) ; sinon la
  réponse est remplacée par un message de refus.
- **Règle 2 :** un outil ne peut pas filtrer ni comparer selon le bio ou le Nutri-Score si la question n'en parle
  pas. Le calcul n'est pas fait, et l'erreur est renvoyée au modèle pour qu'il corrige son appel.
- **Où :** `nutri/garde_fou.py` (`filtrer_reponse`, `verifier_filtres`), appliqué dans `nutri/agent.py`
  (règle 1 dans `repondre`, règle 2 dans `executer_outil`).
- **Tests qui essaient d'enfreindre les règles :** `tests/test_garde_fou.py` (15 tests, dont 3 tirés de vraies traces).
- **Reproduire :** `python -m pytest tests/test_garde_fou.py -v`
- **Exemples réels bloqués :**
  - `traces/trace_20261102_113046.json` : « Combien de grammes de sucre dans un bol de 40 g de céréales bio ? ».
    Qwen a calculé lui-même 13,17 × 0,4 = « 5,3 g ». Le calcul est juste, mais il ne vient pas d'un outil :
    bloqué ;
  - `traces/trace_20261102_113111.json` : « Combien de calories apporte une portion de 30 g de céréales ? ».
    Qwen a filtré les seules céréales non bio, puis a écrit « 124,9 kcal exactement », un calcul faux :
    bloqué. Cette trace montre aussi que le mauvais filtre passait : d'où la règle 2 ;
  - `traces/trace_20261102_113921.json` : même question, après la règle 2. `decrire(energie_kcal, bio=False)`
    est refusé, Qwen se corrige et prend les 953 céréales, puis la règle 1 bloque son calcul de portion
    (« 122,84 »).
- **Limites :** le garde-fou ne vérifie pas le sens (une phrase qui contredit ses propres chiffres), ni le choix
  du nutriment, ni un nombre écrit en lettres ; un nombre inventé qui tombe par hasard sur un nombre autorisé
  passe.

## Brique 6 : données sales, décisions écrites
- **Données :** Open Food Facts, catégorie « breakfast-cereals », pays France. 1000 produits téléchargés
  (pages 1 à 10 de l'API ; la page 11 a répondu 503), **953** gardés (543 bio, 410 non bio).
- **Journal :** `data/journal_nettoyage.md` (chaque étape avec le nombre de produits touchés, et les 28 fusions
  de marques).
- **Règle absente du fichier :** règlement (UE) n° 1169/2011 « INCO », annexe XIV : sel = sodium × 2,5 et
  énergie = 4 × glucides + 4 × protéines + 9 × lipides + 2 × fibres (kcal).
- **Décisions principales :**
  - une valeur impossible (hors bornes physiques, sucres > glucides…) est mise à vide, mais la fiche est gardée :
    l'erreur ne touche qu'une case. Cas réel : « Pétales blé goût chocolat », 2114 kJ écrits dans la case kcal ;
    la valeur a été vidée puis recalculée par la formule INCO ;
  - une fiche dont l'énergie s'écarte de plus de 20 % du calcul INCO est **retirée** : on ne sait pas quelle
    valeur est fausse (4 produits) ;
  - les 25 produits sans Nutri-Score sont gardés (le calculer demanderait d'inventer le sel manquant) et comptés
    par l'outil `comparer` (`sans_nutriscore`) ;
  - les écritures d'une même marque sont regroupées par mots entiers (« carrefour bio » → carrefour,
    « kellogg s produits aliment sas » → kelloggs) : 177 → 149 marques. La colonne bio reste fondée sur le
    label officiel, pas sur le nom de la marque.
- **Tests :** `tests/test_clean.py`
- **Reproduire :** `python -m nutri.download && python -m nutri.clean`

## Brique 8 : des chiffres avec leur incertitude
- **Ce que je montre :** chaque moyenne est donnée avec sa marge d'erreur à 95 % (1,96 × écart type / √n) et
  sa fourchette. Pour la comparaison bio / non bio, l'écart a sa propre marge (√(et₁² + et₂²) × 1,96), et
  `difference_nette` dit si la fourchette de l'écart exclut 0.
- **Où :** `nutri/tools.py` (`_erreur_type`, `_intervalle`, `decrire`, `comparer`) ; le prompt de
  `nutri/agent.py` demande d'écrire la marge et de dire « on ne peut pas conclure » si l'écart n'est pas net.
- **Tests à réponse calculée à la main :** `tests/test_tools.py`
- **Exemples :**
  - sucres : bio 13,17 g, non bio 18,59 g ; écart −5,42 g ± 1,07 g → **net** ;
  - lipides : bio 10,69 g, non bio 10,48 g ; écart 0,21 g ± 0,84 g, fourchette [−0,63 ; 1,05] qui contient 0
    → **pas net** : l'écart peut venir du hasard ;
  - trace `traces/trace_20261102_113831.json` : sel des céréales bio, « 0,13 g ± 0,02 g ».
- **Ce que ces données ne permettent pas de conclure :**
  - l'échantillon n'est pas représentatif du marché : ce sont les premières pages d'Open Food Facts, avec 57 %
    de bio, alors que le bio est minoritaire en rayon. Les moyennes décrivent ces 953 fiches, pas toutes les
    céréales vendues en France ;
  - un écart net entre bio et non bio n'est pas une **cause** : les céréales bio ne sont pas moins sucrées
    *parce qu'*elles sont bio (ce sont peut-être d'autres types de produits, plus de mueslis et moins de
    céréales pour enfants) ;
  - les fiches sont remplies par des bénévoles : la marge mesure le hasard de l'échantillon, pas les erreurs
    de saisie ;
  - 25 produits sans Nutri-Score sont exclus des comparaisons par Nutri-Score.

## Brique 9 : une comparaison mesurée
- **Ce que je compare :** le système complet (Qwen + outils + garde-fou) et le modèle seul (Qwen sans outils ni
  garde-fou, `--modele-seul`), sur **12 questions à réponse connue**, **3 lancements** chacune (72 réponses).
  Les bonnes réponses sont calculées directement avec pandas, sans passer par `tools.py`.
- **Jugement :** une réponse est *juste* si elle contient un nombre à 2 % près de la bonne réponse (au moins
  0,01 d'écart permis), le bon nom de marque, ou, pour les lipides, une phrase prudente (« hasard »,
  « pas conclure »). *Bloquée* si le garde-fou l'a refusée. *Fausse* sinon.
- **Fichiers :** `nutri/evaluation.py`, `tests/test_evaluation.py`, résultats dans `resultats/evaluation.md`
  (tableau) et `resultats/evaluation.json` (les 72 traces complètes).
- **Reproduire :** `python -m nutri.evaluation` (environ 25 minutes ; `--rapide` pour un essai de 1 minute).

### Résultats (3 novembre 2026)
| Système | Taux de réponses justes, moyenne ± écart type sur 3 lancements | Justes | Fausses | Bloquées | Durée moyenne | Tokens lus en moyenne |
|---|---|---|---|---|---|---|
| Complet | **100 % ± 0 %** | 36 | 0 | 0 | 32 s | 2 371 |
| Modèle seul | **3 % ± 5 %** | 1 | 35 | 0 | 9 s | 195 |

Parmi les 35 réponses fausses du modèle seul : 26 disent qu'il faut un outil ou des données, et **9 inventent
des chiffres** (repérées en passant ses réponses dans le garde-fou). Le système complet est 3 à 4 fois plus
lent et lit 12 fois plus de tokens : c'est le prix des outils.

### Un échec expliqué à partir de sa trace
- **Trace :** `resultats/evaluation.json`, lancement 1, question 4, modèle seul : « Quelle est la teneur moyenne
  en sucres des céréales bio, pour 100 g ? »
- **Réponse :** « La teneur moyenne en sucres totaux dans les céréales bio vendues en France s'élève à
  **6,8 g ± 1,4 g** pour chaque 100 g de produit. Cependant, la différence nette avec la valeur globale
  (9,5 g ± 3,8 g) n'est pas significative, car le test statistique indique que cet écart pourrait être dû au
  hasard… » La bonne réponse est 13,17 g.
- **Ce que montre la trace :** la liste `appels` est vide : aucun outil n'a été appelé, aucun calcul n'a été
  fait. Pourtant, la réponse imite la forme que le prompt demande (une marge « ± », « différence nette »,
  « hasard ») : le modèle a recopié la *forme* des réponses du système sans en avoir les *chiffres*. Les quatre
  nombres sont inventés, et la réponse est fausse de moitié. Dans le système complet, le garde-fou l'aurait
  bloquée : aucun de ces nombres ne vient d'un outil.
- **Un deuxième échec, celui de la mesure :** le seul « juste » du modèle seul (lancement 3, question 12) est un
  faux positif de mon jugement. La réponse dit « … si la différence est statistiquement significative ou due au
  hasard » : elle ne conclut rien, elle annonce qu'elle va chercher. Le mot « hasard » suffit à mon jugement par
  mots-clés. Le vrai taux du modèle seul est donc 0 %.

### Limites de cette mesure
- Les 12 questions demandent chacune **un seul outil** : le système complet les réussit toutes. Les questions où
  il échoue (une portion de 30 g, un filtre que la question ne demande pas) sont connues mais pas dans les 12 :
  voir les traces bloquées de la brique 3 (`traces/trace_20261102_113111.json`, `113921`).
- Le modèle seul garde le même prompt, qui lui parle d'outils qu'il n'a pas : c'est pour ça qu'il répond
  souvent « j'ai besoin d'un outil ».
- 3 lancements, c'est peu pour mesurer la dispersion. Ici, elle est nulle pour le système complet.
- Le jugement par mots-clés et par nombres ne lit pas le sens (voir le faux positif ci-dessus).
