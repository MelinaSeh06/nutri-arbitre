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
  garde-fou, `--modele-seul`), sur **16 questions à réponse connue**, dont 4 pièges, **3 lancements** chacune
  (96 réponses). Les bonnes réponses sont calculées directement avec pandas, sans passer par `tools.py`.
- **Les 4 pièges** visent les failles connues : une portion de 30 g et un écart entre deux groupes (le modèle doit
  calculer lui-même, aucun outil ne le fait), la vitamine C (absente des données : il ne faut donner aucun
  chiffre), et « les céréales sont-elles riches en sucres ? » (tentation de filtrer sur le bio).
- **Jugement :** une réponse est *juste* si elle contient un nombre à 2 % près de la bonne réponse (au moins 0,01
  d'écart permis), le bon nom de marque, une phrase prudente pour les lipides (« hasard », « pas conclure »), ou,
  pour la vitamine C, aucun chiffre inventé. *Bloquée* si le garde-fou l'a refusée. *Fausse* sinon, ce qui
  comprend aussi les non-réponses (« je n'ai pas réussi à répondre »).
- **Fichiers :** `nutri/evaluation.py`, `tests/test_evaluation.py`, résultats dans `resultats/evaluation.md`
  (tableau) et `resultats/evaluation.json` (les 96 traces complètes).
- **Reproduire :** `python -m nutri.evaluation` (environ 35 minutes ; `--rapide` pour un essai de 1 minute).
  Qwen ne répond pas deux fois pareil : un nouveau lancement donnera des chiffres proches, pas identiques.

### Résultats (3 novembre 2026, 13 h 36)
| Système | Taux de réponses justes, moyenne ± écart type sur 3 lancements | Justes | Fausses | Bloquées | Durée moyenne | Tokens lus en moyenne |
|---|---|---|---|---|---|---|
| Complet | **73 % ± 4 %** (69 %, 75 %, 75 %) | 35 | 5 | 8 | 19 s | 2 668 |
| Modèle seul | **12 % ± 6 %** (6 %, 19 %, 12 %) | 6 | 42 | 0 | 13 s | 196 |

- **Sur les 12 questions simples**, le système complet a 32 réponses justes sur 36 : une réponse bloquée
  (question 4) et la question 11 fausse 3 fois. Sur les 4 pièges, il n'a que les 3 réponses sur la vitamine C.
- **Le garde-fou a bloqué 8 réponses**, toutes à juste titre : 5 calculs faits par le modèle (portion, écart A / E),
  un « 4,42 g de moins » au lieu de 5,42 (question 4), et 2 réponses de mémoire après des appels refusés
  (« 13 g ± 2,6 g », « entre 12 et 25 g », question 16).
- **Le modèle seul invente des chiffres dans 17 réponses sur 48** (repérées en passant ses réponses dans le
  garde-fou), souvent avec une fausse marge (« 13,2 g ± 0,9 g ») et en prétendant avoir consulté un outil.
- **Une première évaluation**, sur les 12 questions simples seulement, avait donné 100 % ± 0 % pour le système
  complet et 3 % ± 5 % pour le modèle seul. J'ai décidé d'ajouter les 4 pièges, parce qu'un score de 100 % sur des
  questions faciles ne montrait pas les limites du système. Elle est dans l'historique git (commit `b66aa42`).

### Un échec expliqué à partir de sa trace
- **Trace :** `resultats/evaluation.json`, lancement 1, question 11, système complet : « Quelle marque (au moins
  5 produits) a la teneur moyenne en sucres la plus basse ? » Bonne réponse : jardin bio etic (6,5 g).
- **Ce que montre la trace :**
  1. Qwen appelle `classement_marques(nutriment="sucres", n=10, ordre="decroissant", min_produits=5)`. Il a choisi
     l'ordre **décroissant** : l'outil renvoie donc les marques les **plus** sucrées en premier ;
  2. il lit la première de la liste comme la moins sucrée : « la marque Crownfield a la teneur moyenne en sucres la
     plus basse avec 18,61 g » ;
  3. le garde-fou laisse passer la réponse : 18,61 vient bien d'un outil. **Il vérifie l'origine des chiffres, pas
     le sens de la phrase.**
- **Même erreur aux lancements 2 et 3** (au lancement 3, Belle France, 22,32 g, après un premier appel avec un
  argument mal écrit, `nutriments`). Lors de la première évaluation, 30 minutes plus tôt, la même question avait été
  juste 3 fois sur 3, avec `ordre="croissant"`. Le comportement de Qwen change d'un passage à l'autre, et
  3 lancements ne suffisent pas à le voir.
- **Ce qui l'éviterait :** un outil sans choix d'ordre (« marques_les_moins_sucrees »), ou une vérification qu'une
  réponse « la plus basse » cite bien le minimum. On ne l'a pas fait : c'est une limite connue.

### D'autres échecs tirés des traces
- **La règle n° 2 peut empêcher de répondre** (question 13, lancement 3) : Qwen fait 7 appels filtrés sur le bio
  ou le Nutri-Score, reçoit 7 fois l'erreur, et la boucle s'arrête à `MAX_TOURS` sans réponse. Question 16, lancement 3 : après
  4 refus, il conclut à tort qu'« aucun outil ne permet de calculer la moyenne générale ».
- **Un nom d'outil inventé** (question 16, lancement 2) : 3 appels à « descrire », refusés (« outil inconnu »), puis
  une réponse de mémoire, bloquée par le garde-fou.

### Les faux positifs de mon jugement (gardés volontairement)
- **Question 12 (lipides), modèle seul, compté juste 3 fois sur 3 :** les trois réponses inventent des moyennes
  (« 3,2 g ± 0,4 g » au lieu de 10,69 g) et ajoutent « pas significatif ». Mon jugement « prudence » ne cherche que
  des mots (« hasard », « pas conclure ») : il ne vérifie pas les chiffres.
- **Question 4, modèle seul, lancement 2, compté juste :** il invente 4 valeurs de « 5 produits » et en donne la
  moyenne, 14,04 g ; l'une des valeurs inventées, 13,2 g, tombe à 2 % de la bonne réponse (13,17 g). Juste par
  chance.
- **Ma décision :** j'aurais pu corriger le jugement et rejuger les traces (le modèle seul serait descendu vers 6 %).
  J'ai choisi de **garder ces faux positifs** et de les montrer. Malgré les outils, le garde-fou et le prompt,
  le système se trompe, et la mesure elle-même a des erreurs : c'est ce que je veux faire voir, plutôt qu'un
  chiffre corrigé après avoir vu les résultats.

### Limites de cette mesure
- 16 questions et 3 lancements, c'est peu ; la question 11 montre que le score change d'un passage à l'autre.
- Le jugement par nombres et par mots-clés ne lit pas le sens (faux positifs ci-dessus).
- Le modèle seul garde le même prompt, qui lui parle d'outils qu'il n'a pas : il répond souvent « j'ai besoin d'un
  outil ».
- Les questions sont écrites par moi : un utilisateur réel poserait des questions plus variées.
