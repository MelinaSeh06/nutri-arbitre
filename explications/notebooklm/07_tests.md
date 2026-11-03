# Nutri-Arbitre — Fichier 7 : le dossier `tests/`, vérifier automatiquement

> **Pour qui est ce document :** une étudiante qui débute en Python et qui doit expliquer ces fichiers à l'oral,
> ligne par ligne. Tout est expliqué depuis le début, avec des exemples concrets tirés du vrai projet.

## Le projet en 30 secondes (contexte commun à tous les documents)

Nutri-Arbitre est le projet final du cours « Coding for AI » (PGE3S1, aivancity). C'est un petit **agent** :
on lui pose une question en français sur les **céréales du petit-déjeuner vendues en France** (par exemple
« Les céréales bio contiennent-elles moins de sucre ? »), et il répond avec de vrais chiffres.

- Le **modèle de langage** est Qwen3.5-4B (version compressée `qwen3.5:4b-q4_K_M`), qui tourne **en local** sur
  l'ordinateur grâce au logiciel Ollama. C'est un petit modèle : il se trompe et invente facilement des chiffres.
- Les **données** viennent d'Open Food Facts, une base de données ouverte et collaborative de produits
  alimentaires. On a gardé **953 céréales** (543 bio, 410 non bio), avec leurs valeurs pour 100 g : énergie,
  glucides, sucres, lipides, acides gras saturés, fibres, protéines, sel, et leur Nutri-Score.
- **L'idée centrale : le modèle n'a pas le droit d'inventer un chiffre.** Il ne calcule rien lui-même. Il
  choisit un **outil** (une fonction Python), Python fait le calcul, et un **garde-fou** écrit en code bloque
  toute réponse qui contient un chiffre qui ne vient pas d'un outil.

Le trajet des données, de bout en bout, en 7 fichiers :

1. `download.py` télécharge les produits bruts depuis Open Food Facts.
2. `clean.py` nettoie ces données sales et écrit chaque décision dans un journal.
3. `tools.py` contient les outils de calcul (moyenne, comparaison, classement, comptage).
4. `garde_fou.py` contient les deux règles imposées par le code.
5. `agent.py` est le chef d'orchestre : il parle à Qwen, exécute les outils, applique le garde-fou.
6. `evaluation.py` mesure le système : 16 questions à réponse connue, système complet contre modèle seul.
7. Le dossier `tests/` vérifie automatiquement chaque étape sur des exemples calculés à la main.

Le projet valide 5 « briques » de la consigne : **brique 1** (le modèle appelle nos propres outils),
**brique 3** (une règle imposée par le code et non par le prompt), **brique 6** (données sales, décisions
écrites), **brique 8** (des chiffres avec leur marge d'erreur), **brique 9** (une comparaison mesurée).

À l'oral, l'examinateur peut choisir **n'importe quelle fonction au hasard** et demander de l'expliquer ligne
par ligne. Ce document sert à préparer exactement ça.


---

## 1. Le rôle de ces fichiers

Un **test** est une petite fonction qui lance une partie du code sur un exemple dont on connaît **déjà** la bonne
réponse, calculée à la main, et qui vérifie que le code trouve la même.

Le projet a **42 tests**, répartis en 4 fichiers de tests (plus un fichier de données de test). Ils tournent en
moins d'une seconde, **sans appeler Qwen**, et donnent toujours le même résultat.

| Fichier | Tests | Ce qu'il prouve | Brique |
|---|---|---|---|
| `conftest.py` | – | prépare les petits produits inventés | – |
| `test_clean.py` | 9 | le nettoyage retire les bonnes lignes, applique INCO, vide les valeurs impossibles, regroupe les marques | 6 |
| `test_tools.py` | 12 | les outils donnent les moyennes, marges et `difference_nette` calculées à la main | 1, 8 |
| `test_garde_fou.py` | 15 | on **essaie d'enfreindre** les deux règles, et le code bloque | 3 |
| `test_evaluation.py` | 6 | la façon de juger les réponses, la moyenne et l'écart type | 9 |

**Comment on les lance :**
```
python -m pytest                              # tous les tests
python -m pytest tests/test_garde_fou.py -v   # un seul fichier, avec le nom de chaque test
```

Ce que l'on voit quand tout va bien :
```
..........................................                               [100%]
42 passed in 0.35s
```
Chaque point est un test réussi. Un test raté afficherait un `F`, puis la ligne fautive et les valeurs obtenues.

---

## 2. Les notions à connaître avant de lire le code

### pytest
**pytest** est l'outil qui lance les tests. Il cherche dans le dossier `tests/` les fichiers dont le nom commence
par `test_`, et dans ces fichiers les fonctions dont le nom commence par `test_`. Il les lance toutes, une par une,
et compte les réussites et les échecs. (Le fichier `pyproject.toml` lui dit où chercher : `testpaths = ["tests"]`.)

### `assert`
`assert condition` veut dire « je vérifie que cette condition est vraie ». Si elle est vraie, rien ne se passe. Si
elle est fausse, le test **échoue**.

```python
assert 2 + 2 == 4     # rien ne se passe
assert 2 + 2 == 5     # le test échoue : AssertionError
```

### La bonne réponse est écrite dans le test
C'est le principe le plus important : on calcule la réponse **à la main**, et on l'écrit dans le test, avec le
calcul en commentaire. On peut la vérifier sans faire confiance au code. Exemple : « (10 + 20) / 2 = 15 ».

### Une fixture
Une **fixture** est une donnée préparée pour les tests, marquée par `@pytest.fixture`. Un test qui écrit son nom
entre ses parenthèses la reçoit automatiquement : pytest appelle la fixture et lui donne le résultat. Les fixtures
du fichier `conftest.py` servent à **tous** les fichiers de tests (pytest lit ce fichier tout seul).

### Simuler le modèle
Les tests du garde-fou ne lancent pas Qwen. On écrit **à la place de Qwen** une réponse qui contient un chiffre
inventé (souvent une vraie réponse de Qwen, recopiée), et on vérifie que le garde-fou la bloque.

---

## 3. Le code, fichier par fichier

### Fichier 1 : `conftest.py`, les petits produits inventés

Code de `tests/conftest.py`, lignes 1 à 35 (le numéro de ligne est à gauche de la barre) :

```python
  1 | """Petits produits inventés dont on connaît la réponse à la main."""
  2 | import pytest
  3 | 
  4 | from nutri.clean import nettoyer
  5 | 
  6 | 
  7 | def produit(code, nom="Céréales", marque="Marque", labels=(), ns="a", **nutr):
  8 |     return {"code": code, "product_name": nom, "brands": marque, "labels_tags": list(labels),
  9 |             "nutriscore_grade": ns, "nutriments": nutr}
 10 | 
 11 | 
 12 | @pytest.fixture
 13 | def produits_bruts():
 14 |     return [
 15 |         produit("1", marque="Bio Village", labels=["en:organic"], ns="a",
 16 |                 **{"sugars_100g": 10, "carbohydrates_100g": 60, "fat_100g": 5,
 17 |                    "proteins_100g": 10, "fiber_100g": 8, "salt_100g": 0.5}),
 18 |         produit("2", marque="BIO VILLAGE", labels=["fr:ab-agriculture-biologique"], ns="b",
 19 |                 **{"sugars_100g": 20, "carbohydrates_100g": 70, "fat_100g": 5,
 20 |                    "proteins_100g": 10, "sodium_100g": 0.2}),
 21 |         produit("3", marque="Kellogg's", ns="d",
 22 |                 **{"sugars_100g": 30, "carbohydrates_100g": 80, "fat_100g": 2,
 23 |                    "proteins_100g": 6, "salt_100g": 1.0}),
 24 |         produit("3", marque="Kellogg's", ns="d", **{"sugars_100g": 30}),          # doublon
 25 |         produit("4", nom="", **{"sugars_100g": 5}),                              # sans nom
 26 |         produit("5", marque="KELLOGG’S", ns="unknown",
 27 |                 **{"sugars_100g": 90, "carbohydrates_100g": 50, "fat_100g": 3,   # sucres > glucides
 28 |                    "proteins_100g": 7, "salt_100g": 150}),                       # sel impossible
 29 |         produit("6", marque="Vide"),                                             # aucune valeur
 30 |     ]
 31 | 
 32 | 
 33 | @pytest.fixture
 34 | def df(produits_bruts):
 35 |     return nettoyer(produits_bruts)[0]
```

- **Lignes 7 à 9 : `produit(...)`**, une petite fonction qui fabrique un produit **au même format** qu'Open Food
  Facts (avec `product_name`, `brands`, `nutriments`…). `**nutr` récupère tous les nutriments donnés en arguments
  nommés dans un dictionnaire. Cela évite de réécrire la structure complète à chaque produit.
- **Lignes 12 à 30 : la fixture `produits_bruts`**, 7 produits, chacun avec un défaut choisi exprès :

| Produit | Particularité | Ce que le nettoyage doit faire |
|---|---|---|
| 1 | bio (label `en:organic`), pas d'énergie | le garder ; énergie INCO = 4×60 + 4×10 + 9×5 + 2×8 = 341 kcal |
| 2 | bio (label AB), « BIO VILLAGE » en majuscules, sodium sans sel | marque « bio village » ; sel = 0,2 × 2,5 = 0,5 g |
| 3 | Kellogg's | le garder |
| 3 bis | même code-barres que le 3 | retirer le doublon |
| 4 | sans nom | le retirer |
| 5 | sucres (90) > glucides (50), 150 g de sel, Nutri-Score « unknown » | vider ces 3 valeurs, garder le produit |
| 6 | aucune valeur nutritionnelle | le retirer |

  Résultat attendu : 7 − 1 doublon − 1 sans nom − 1 vide = **4 produits**, dont 2 bio.
- **Lignes 33 à 35 : la fixture `df`.** Elle **reçoit** elle-même la fixture `produits_bruts`, la nettoie avec la
  vraie fonction `nettoyer`, et garde le tableau (`[0]`, car `nettoyer` renvoie le tableau et le journal).

**Pourquoi des produits inventés et pas les 953 vrais ?** Sur les vrais, on ne pourrait pas calculer les réponses
à la main, et un défaut précis (un doublon, un sel impossible) ne serait pas forcément présent. Ici, chaque défaut
est là exprès.

---

### Fichier 2 : `test_clean.py` (brique 6)

Code de `tests/test_clean.py`, lignes 1 à 71 (le numéro de ligne est à gauche de la barre) :

```python
  1 | """Brique 6 / R2 : le nettoyage donne le résultat calculé à la main."""
  2 | import pandas as pd
  3 | 
  4 | from nutri.clean import nettoyer, normaliser_marque, regrouper_marques
  5 | 
  6 | 
  7 | def test_lignes_retirees(produits_bruts):
  8 |     df, journal = nettoyer(produits_bruts)
  9 |     # 7 produits : -1 doublon, -1 sans nom, -1 sans aucune valeur = 4
 10 |     assert len(df) == 4
 11 |     assert "Doublons de code-barres retirés : 1." in journal
 12 |     assert "Produits sans nom retirés : 1." in journal
 13 | 
 14 | 
 15 | def test_regle_inco_sel_depuis_sodium(df):
 16 |     # produit 2 : sodium 0,2 g -> sel 0,5 g
 17 |     assert df.loc[df["code"] == "2", "sel"].item() == 0.5
 18 | 
 19 | 
 20 | def test_regle_inco_energie_calculee(df):
 21 |     # produit 1 : 4*60 + 4*10 + 9*5 + 2*8 = 341 kcal
 22 |     assert df.loc[df["code"] == "1", "energie_kcal"].item() == 341
 23 | 
 24 | 
 25 | def test_fiche_incoherente_retiree():
 26 |     # vrai cas des données : « Muesli croustillant chocolat » déclare 437 kcal,
 27 |     # mais 4*33 + 4*4,7 + 9*6,6 + 2*3,9 = 218 kcal : écart de 100 %, on ne sait pas qui est faux
 28 |     from tests.conftest import produit
 29 |     nutr = {"carbohydrates_100g": 33, "proteins_100g": 4.7, "fat_100g": 6.6, "fiber_100g": 3.9}
 30 |     incoherent = produit("10", **nutr, **{"energy-kcal_100g": 437})
 31 |     coherent = produit("11", **nutr, **{"energy-kcal_100g": 230})        # écart de 5 % : gardé
 32 |     df, journal = nettoyer([incoherent, coherent])
 33 |     assert list(df["code"]) == ["11"]
 34 |     assert any("fiche incohérente), produits retirés : 1." in l for l in journal)
 35 | 
 36 | 
 37 | def test_valeurs_impossibles_mises_a_vide(df):
 38 |     p5 = df[df["code"] == "5"].iloc[0]
 39 |     assert pd.isna(p5["sucres"])       # sucres (90) > glucides (50)
 40 |     assert pd.isna(p5["sel"])          # 150 g de sel pour 100 g : impossible
 41 |     assert pd.isna(p5["nutriscore"])   # 'unknown' -> vide
 42 | 
 43 | 
 44 | def test_bio_et_marques(df):
 45 |     assert df["bio"].sum() == 2
 46 |     assert set(df["marque"]) == {"bio village", "kelloggs"}
 47 | 
 48 | 
 49 | def test_regroupement_des_marques():
 50 |     marques = pd.Series(["kelloggs", "kelloggs", "kellogg s produits aliment sas", "carrefour",
 51 |                          "carrefour bio", "lu", "lucien georgelin", "aline olivier", "alineolivier",
 52 |                          "societe des produits nestle sa", None])
 53 |     regroupees, fusions = regrouper_marques(marques)
 54 |     assert list(regroupees[:5]) == ["kelloggs", "kelloggs", "kelloggs", "carrefour", "carrefour"]
 55 |     assert regroupees[6] == "lucien georgelin"         # mots entiers : pas rangé chez « lu »
 56 |     assert regroupees[8] == "aline olivier"            # même nom sans espaces
 57 |     assert regroupees[9] == "nestle"                   # table écrite à la main
 58 |     assert pd.isna(regroupees[10])                     # pas de marque : reste vide
 59 |     assert "carrefour bio -> carrefour" in fusions
 60 | 
 61 | 
 62 | def test_marque_cas_limites():
 63 |     assert normaliser_marque(None) is None
 64 |     assert normaliser_marque("   ") is None
 65 |     assert normaliser_marque("Nestlé, Nestle France") == "nestle"
 66 | 
 67 | 
 68 | def test_liste_vide():
 69 |     df, journal = nettoyer([])
 70 |     assert len(df) == 0
 71 |     assert journal[-1] == "Arrivée : 0 produits."
```

- **Lignes 7 à 12 :** les lignes retirées : 4 produits restent, et le journal dit bien 1 doublon et 1 produit sans
  nom. On vérifie aussi **le journal**, pas seulement le tableau.
- **Lignes 15 à 17 : la règle INCO du sel.** `df.loc[df["code"] == "2", "sel"]` prend la case « sel » de la ligne
  dont le code est « 2 » (un masque), et `.item()` sort la valeur de cette case. On attend 0,2 × 2,5 = 0,5.
- **Lignes 20 à 22 : la règle INCO de l'énergie**, 341 kcal pour le produit 1.
- **Lignes 25 à 34 : la fiche incohérente**, un **vrai cas** des données : le muesli qui déclare 437 kcal alors
  que le calcul donne 218. On fabrique deux produits avec les mêmes nutriments : l'un à 437 kcal (écart de 100 %),
  l'autre à 230 kcal (écart de 5 %). Seul le second doit rester. `any(...)` répond vrai si **au moins une** ligne
  du journal contient la phrase attendue.
- **Lignes 37 à 41 : les valeurs impossibles** du produit 5 sont vides (`pd.isna`), mais le produit est toujours là.
- **Lignes 44 à 46 :** 2 produits bio, et les marques normalisées : « BIO VILLAGE » et « Bio Village » donnent la
  même marque, « Kellogg's » et « KELLOGG’S » aussi. `set(...)` donne l'ensemble des marques différentes.
- **Lignes 49 à 59 : le regroupement des marques**, avec les cas de la séance 2 : « kellogg s produits aliment sas »
  → kelloggs, « carrefour bio » → carrefour, « lucien georgelin » **n'est pas** rangé chez « lu » (mots entiers),
  « alineolivier » → « aline olivier », la table des alias pour nestle, et une marque vide qui reste vide.
- **Lignes 62 à 65 :** les cas limites de `normaliser_marque` : rien, des espaces, et deux marques séparées par
  une virgule.
- **Lignes 68 à 71 :** une liste vide ne fait pas planter le nettoyage.

---

### Fichier 3 : `test_tools.py` (briques 1 et 8)

Code de `tests/test_tools.py`, lignes 1 à 87 (le numéro de ligne est à gauche de la barre) :

```python
  1 | """Brique 1 / R2 : les outils renvoient les chiffres calculés à la main."""
  2 | import pandas as pd
  3 | import pytest
  4 | 
  5 | from nutri import tools
  6 | 
  7 | 
  8 | def test_decrire_sucres_bio(df):
  9 |     r = tools.decrire(df, "sucres", bio=True)
 10 |     assert r["n"] == 2 and r["moyenne"] == 15.0      # (10 + 20) / 2
 11 |     assert r["min"] == 10.0 and r["max"] == 20.0
 12 | 
 13 | 
 14 | def test_decrire_selection_vide(df):
 15 |     r = tools.decrire(df, "sucres", nutriscore="e")    # aucun produit en E
 16 |     assert r["n"] == 0 and r["moyenne"] is None
 17 | 
 18 | 
 19 | def test_comparer_bio(df):
 20 |     r = tools.comparer(df, "sucres", "bio")
 21 |     # bio : 15 ; non bio : seul le produit 3 a une valeur de sucres (30)
 22 |     assert r["ecart_bio_moins_non_bio"] == -15.0
 23 | 
 24 | 
 25 | def test_classement_ignore_petites_marques(df):
 26 |     r = tools.classement_marques(df, "sucres", min_produits=2)
 27 |     assert [m["marque"] for m in r["marques"]] == ["bio village"]
 28 | 
 29 | 
 30 | def test_nutriment_inconnu_refuse(df):
 31 |     with pytest.raises(ValueError):
 32 |         tools.decrire(df, "vitamine_c")
 33 | 
 34 | 
 35 | def test_compter(df):
 36 |     assert tools.compter(df)["n"] == 4
 37 |     assert tools.compter(df, bio=False)["n"] == 2
 38 | 
 39 | 
 40 | def _tableau(bio, non_bio):
 41 |     """Petit tableau inventé : des valeurs de sucres pour des produits bio et non bio."""
 42 |     lignes = [{"bio": True, "sucres": s} for s in bio] + [{"bio": False, "sucres": s} for s in non_bio]
 43 |     return pd.DataFrame(lignes)
 44 | 
 45 | 
 46 | def test_marge_erreur_a_la_main(df):
 47 |     # bio : 10 et 20 -> écart-type 7,07 ; erreur type 7,07 / racine(2) = 5 ; marge 1,96 x 5 = 9,8
 48 |     r = tools.decrire(df, "sucres", bio=True)
 49 |     assert r["marge_95"] == 9.8
 50 |     assert r["intervalle_95"] == [5.2, 24.8]              # 15 - 9,8 et 15 + 9,8
 51 | 
 52 | 
 53 | def test_marge_impossible_avec_une_seule_valeur(df):
 54 |     # non bio : un seul produit a une valeur de sucres -> pas de dispersion, pas de marge
 55 |     r = tools.decrire(df, "sucres", bio=False)
 56 |     assert r["n"] == 1 and r["marge_95"] is None and r["intervalle_95"] is None
 57 |     assert tools.comparer(df, "sucres", "bio")["difference_nette"] is None
 58 | 
 59 | 
 60 | def test_difference_nette():
 61 |     # bio 10 et 12 (moy. 11), non bio 30 et 32 (moy. 31) : erreur type 1 dans chaque groupe
 62 |     # écart -20 ; erreur type de l'écart racine(1 + 1) = 1,41 ; marge 1,96 x 1,41 = 2,77
 63 |     r = tools.comparer(_tableau([10, 12], [30, 32]), "sucres", "bio")
 64 |     assert r["ecart_bio_moins_non_bio"] == -20.0 and r["marge_95_ecart"] == 2.77
 65 |     assert r["difference_nette"] is True                  # [-22,77 ; -17,23] ne contient pas 0
 66 | 
 67 | 
 68 | def test_difference_pas_nette():
 69 |     # bio 10 et 30 (moy. 20), non bio 14 et 30 (moy. 22) : écart -2, mais marge de 25 environ
 70 |     r = tools.comparer(_tableau([10, 30], [14, 30]), "sucres", "bio")
 71 |     assert r["ecart_bio_moins_non_bio"] == -2.0
 72 |     assert r["difference_nette"] is False                 # 0 est dans l'intervalle : hasard possible
 73 | 
 74 | 
 75 | def test_sans_nutriscore_compte(df):
 76 |     # produit 5 : Nutri-Score « unknown » -> vide, mais il a des lipides : il est écarté et compté
 77 |     r = tools.comparer(df, "lipides", "nutriscore")
 78 |     assert r["sans_nutriscore"] == 1
 79 |     assert sum(g["n"] for g in r["groupes"]) == 3         # 4 produits - 1 sans Nutri-Score
 80 | 
 81 | 
 82 | def test_bio_en_texte(df):
 83 |     # un petit modèle envoie parfois "false" au lieu de false : ne pas inverser le filtre
 84 |     assert tools.compter(df, bio="false")["n"] == 2
 85 |     assert tools.decrire(df, "sucres", bio="true")["moyenne"] == 15.0
 86 |     with pytest.raises(ValueError):
 87 |         tools.compter(df, bio="peut-être")
```

- **Lignes 8 à 11 :** `decrire` sur les sucres des bio : 2 produits (10 et 20 g), moyenne (10 + 20) / 2 = 15.
- **Lignes 14 à 16 :** une sélection vide (aucun produit en E) donne n = 0 et une moyenne `None`, sans planter.
- **Lignes 19 à 22 :** `comparer` : bio 15, non bio 30 (seul le produit 3 a une valeur de sucres, le 5 a été
  vidé) → écart 15 − 30 = **−15**.
- **Lignes 25 à 27 :** le classement ignore les marques de moins de 2 produits : seule « bio village » reste.
- **Lignes 30 à 32 : une erreur attendue.** `with pytest.raises(ValueError):` veut dire « la ligne en dessous
  **doit** provoquer une ValueError ». Le test réussit si le code **refuse** « vitamine_c ». S'il l'acceptait, le
  test échouerait.
- **Lignes 35 à 37 :** `compter` : 4 produits en tout, 2 non bio.
- **Lignes 40 à 43 : `_tableau`**, une petite fonction qui fabrique un tableau de sucres bio et non bio choisis
  à la main, pour tester la brique 8 avec des nombres simples.
- **Lignes 46 à 50 : la marge, refaite à la main.** Bio 10 et 20 : écart type 7,07, erreur type 7,07 / √2 = 5,
  marge 1,96 × 5 = **9,8**, fourchette [15 − 9,8 ; 15 + 9,8] = **[5,2 ; 24,8]**.
- **Lignes 53 à 57 :** avec une seule valeur (le non bio), pas de dispersion : pas de marge, et
  `difference_nette` vaut `None`.
- **Lignes 60 à 65 : une différence nette.** Bio 10 et 12 (moyenne 11), non bio 30 et 32 (moyenne 31). Dans chaque
  groupe, l'erreur type vaut 1. Écart −20 ; erreur type de l'écart √(1² + 1²) = 1,41 ; marge 1,96 × 1,41 = 2,77 ;
  fourchette [−22,77 ; −17,23] : 0 n'est pas dedans → `True`.
- **Lignes 68 à 72 : une différence pas nette.** Bio 10 et 30, non bio 14 et 30 : l'écart n'est que de −2, mais
  les valeurs sont très étalées, la marge est d'environ 25 : 0 est dans la fourchette → `False`.
- **Lignes 75 à 79 :** le produit 5 (Nutri-Score « unknown ») est compté dans `sans_nutriscore`, et les groupes
  contiennent 3 produits sur 4.
- **Lignes 82 à 87 :** le texte `"false"` envoyé par un petit modèle ne doit pas inverser le filtre (rappel :
  `bool("false")` vaut True en Python), et un texte inconnu (« peut-être ») est refusé.

---

### Fichier 4 : `test_garde_fou.py` (brique 3)

Code de `tests/test_garde_fou.py`, lignes 1 à 93 (le numéro de ligne est à gauche de la barre) :

```python
  1 | """Brique 3 : on ESSAIE d'enfreindre la règle « aucun chiffre non calculé » et on vérifie
  2 | que le code bloque. Aucun appel au modèle : on simule ses réponses."""
  3 | from nutri.agent import executer_outil
  4 | from nutri.garde_fou import filtrer_reponse, verifier, verifier_filtres
  5 | 
  6 | RESULTAT = [{"nutriment": "sucres", "n": 42, "moyenne": 18.37}]
  7 | 
  8 | 
  9 | def test_chiffre_invente_bloque():
 10 |     reponse = "Les céréales bio contiennent en moyenne 12,5 g de sucre."
 11 |     ok, fautifs = verifier(reponse, RESULTAT)
 12 |     assert not ok and fautifs == ["12,5"]
 13 |     assert filtrer_reponse(reponse, RESULTAT).startswith("Réponse bloquée")
 14 | 
 15 | 
 16 | def test_reponse_sans_outil_bloquee():
 17 |     # le modèle répond de mémoire, sans avoir appelé d'outil
 18 |     assert not verifier("Environ 25 g de sucre pour 100 g.", [])[0]
 19 | 
 20 | 
 21 | def test_chiffre_calcule_autorise_avec_arrondi():
 22 |     reponse = "Sur 42 produits, la moyenne est de 18,4 g pour 100 g."
 23 |     assert filtrer_reponse(reponse, RESULTAT) == reponse
 24 | 
 25 | 
 26 | def test_arrondi_trop_large_bloque():
 27 |     assert not verifier("La moyenne est de 17 g.", RESULTAT)[0]   # 18,37 n'est pas « 17 »
 28 | 
 29 | 
 30 | def test_mauvais_arrondi_bloque():
 31 |     assert verifier("La moyenne est de 18 g.", RESULTAT)[0]       # 18,37 s'arrondit à 18
 32 |     assert not verifier("La moyenne est de 19 g.", RESULTAT)[0]   # mais pas à 19
 33 |     assert not verifier("La moyenne est de 18,5 g.", RESULTAT)[0] # ni à 18,5
 34 | 
 35 | 
 36 | def test_vrai_calcul_de_qwen_bloque():
 37 |     # vraie trace du 02/11/2026 : Qwen a calculé lui-même 13,17 x 0,4 = 5,3 g pour un bol de 40 g.
 38 |     # Le calcul est juste, mais il n'a pas été fait par un outil : bloqué.
 39 |     resultat = [{"nutriment": "sucres", "n": 543, "moyenne": 13.17, "marge_95": 0.69}]
 40 |     question = "Combien de grammes de sucre y a-t-il dans un bol de 40 g de céréales bio ?"
 41 |     reponse = "100 g contiennent 13,2 ± 0,7 g de sucre. Pour un bol de 40 g, environ 5,3 g."
 42 |     assert verifier(reponse, resultat, question) == (False, ["5,3"])
 43 | 
 44 | 
 45 | def test_constantes_autorisees():
 46 |     assert verifier("Marge à 95 %, pour 100 g.", [])[0]
 47 | 
 48 | 
 49 | def test_reponse_sans_chiffre_autorisee():
 50 |     assert verifier("Je ne peux pas répondre à cette question.", [])[0]
 51 | 
 52 | 
 53 | def test_chiffre_de_la_question_autorise():
 54 |     assert verifier("En 2024, je n'ai pas de données datées.", [], "Et en 2024 ?")[0]
 55 | 
 56 | 
 57 | def test_outil_inconnu_ne_plante_pas():
 58 |     assert "erreur" in executer_outil(None, "rm_rf", {})
 59 | 
 60 | 
 61 | def test_mauvais_argument_renvoye_au_modele(df):
 62 |     assert "erreur" in executer_outil(df, "decrire", {"nutriment": "vitamine_c"})
 63 | 
 64 | 
 65 | def test_filtre_bio_refuse_si_la_question_n_en_parle_pas(df):
 66 |     # vrai cas du 02/11/2026 : question sur toutes les céréales, Qwen a filtré les non bio
 67 |     question = "Combien de calories apporte une portion de 30 g de céréales, en moyenne ?"
 68 |     r = executer_outil(df, "decrire", {"nutriment": "energie_kcal", "bio": False}, question)
 69 |     assert "erreur" in r and "moyenne" not in r          # le calcul filtré n'est jamais fait
 70 |     r = executer_outil(df, "decrire", {"nutriment": "energie_kcal"}, question)
 71 |     assert "moyenne" in r                                # sans filtre : accepté
 72 | 
 73 | 
 74 | def test_filtres_acceptes_si_la_question_en_parle():
 75 |     assert verifier_filtres("Les céréales bio sont-elles sucrées ?", {"bio": True}) is None
 76 |     assert verifier_filtres("Et les produits issus de l'agriculture biologique ?", {"bio": True}) is None
 77 |     assert verifier_filtres("Sucre des céréales au Nutri-Score A ?", {"nutriscore": "a"}) is None
 78 |     assert verifier_filtres("Sucre des céréales A ?", {"nutriscore": "a"}) is not None   # pas de Nutri-Score
 79 |     assert verifier_filtres("Qui fabrique la biologie ?", {"bio": True}) is not None     # « biologie » n'est pas « bio »
 80 | 
 81 | 
 82 | def test_decoupage_en_groupes_refuse_si_la_question_n_en_parle_pas():
 83 |     # 2e vrai cas du 02/11/2026 : même question, Qwen a cette fois comparé bio et non bio
 84 |     question = "Combien de calories apporte une portion de 30 g de céréales, en moyenne ?"
 85 |     assert verifier_filtres(question, {"nutriment": "energie_kcal", "groupe": "bio"}) is not None
 86 |     assert verifier_filtres(question, {"nutriment": "energie_kcal", "groupe": "nutriscore"}) is not None
 87 |     assert verifier_filtres("Les céréales bio sont-elles moins sucrées ?", {"groupe": "bio"}) is None
 88 | 
 89 | 
 90 | def test_ecart_negatif_ecrit_en_positif_autorise():
 91 |     resultat = [{"ecart_bio_moins_non_bio": -20.0}]
 92 |     assert verifier("Les bio ont 20 g de sucre en moins.", resultat)[0]
 93 |     assert not verifier("Les bio ont 20 g de moins sur 3 produits.", resultat)[0]  # le 3 est inventé
```

C'est le fichier qui **essaie d'enfreindre** les règles. Aucun appel au modèle : on écrit les réponses à sa place.
- **Ligne 6 : `RESULTAT`**, un faux résultat d'outil : n = 42, moyenne 18,37.
- **Lignes 9 à 13 :** un chiffre inventé (12,5) est bloqué, et le garde-fou désigne exactement le bon nombre. La
  réponse affichée commence par « Réponse bloquée ».
- **Lignes 16 à 18 :** une réponse de mémoire, sans aucun outil, est bloquée.
- **Lignes 21 à 23 :** une réponse correcte (42 produits, 18,4 g) passe telle quelle.
- **Lignes 26 à 33 : les arrondis.** Pour 18,37 : « 17 » refusé, « 18 » accepté, « 19 » refusé, « 18,5 » refusé.
- **Lignes 36 à 42 : la vraie réponse de Qwen du 2 novembre 2026**, recopiée : le bol de 40 g. Résultat attendu :
  `(False, ["5,3"])` : bloquée, et seul 5,3 est fautif. 13,2 et 0,7 viennent de l'outil, 40 de la question, 100 est
  une constante.
- **Lignes 45 et 46 :** les constantes 95 et 100 sont acceptées.
- **Lignes 49 et 50 :** une réponse sans chiffre passe.
- **Lignes 53 et 54 :** un nombre de la question (2024) peut être répété.
- **Lignes 57 et 58 :** un outil inconnu (« rm_rf », le nom d'une commande qui efface des fichiers) ne fait pas
  planter : on reçoit une erreur.
- **Lignes 61 et 62 :** un mauvais argument est renvoyé au modèle sous forme d'erreur.
- **Lignes 65 à 71 : la règle n° 2, vrai cas du 2 novembre.** Le filtre `bio=False` est refusé, et le test vérifie
  que **le calcul n'a pas été fait** (`"moyenne" not in r`). Le même appel sans filtre est accepté.
- **Lignes 74 à 79 :** les filtres acceptés quand la question en parle, et deux pièges : « Sucre des céréales A ? »
  (pas de mot « Nutri-Score ») et « Qui fabrique la biologie ? » (« biologie » n'est pas « bio »).
- **Lignes 82 à 87 :** le découpage en groupes (`groupe="bio"`) est aussi refusé si la question n'en parle pas
  (2e vrai cas du 2 novembre).
- **Lignes 90 à 93 :** un écart négatif peut s'écrire sans signe (« 20 g en moins »), mais un chiffre inventé à côté
  (3 produits) est quand même bloqué.

---

### Fichier 5 : `test_evaluation.py` (brique 9)

Code de `tests/test_evaluation.py`, lignes 1 à 50 (le numéro de ligne est à gauche de la barre) :

```python
  1 | """Brique 9 : on vérifie la façon de juger les réponses, sans appeler le modèle (fausses traces)."""
  2 | from nutri.evaluation import juger, nombre_juste, resumer
  3 | 
  4 | 
  5 | def _trace(reponse, bloquee=False):
  6 |     return {"reponse": reponse, "bloquee": bloquee}
  7 | 
  8 | 
  9 | def test_nombre_juste_a_2_pourcent_pres():
 10 |     assert nombre_juste("En moyenne 13,2 g de sucres.", 13.165)      # arrondi : juste
 11 |     assert nombre_juste("Environ 13 g.", 13.165)                      # 1,3 % d'écart : juste
 12 |     assert not nombre_juste("Environ 25 g.", 13.165)                  # réponse de mémoire : fausse
 13 |     assert nombre_juste("0,13 g de sel.", 0.1265)                     # écart permis d'au moins 0,01
 14 |     assert not nombre_juste("0,1 g de sel.", 0.1265)
 15 | 
 16 | 
 17 | def test_ecart_negatif_ecrit_sans_signe():
 18 |     assert nombre_juste("Les bio ont 5,42 g de sucres en moins.", -5.42)
 19 | 
 20 | 
 21 | def test_reponse_bloquee_ni_juste_ni_fausse():
 22 |     tache = {"type": "nombre", "attendu": 953}
 23 |     # le message de refus contient des nombres : il ne faut pas le juger « juste » par accident
 24 |     assert juger(tache, _trace("Réponse bloquée (953)", bloquee=True)) == "bloquee"
 25 | 
 26 | 
 27 | def test_texte_et_prudence():
 28 |     marque = {"type": "texte", "attendu": "jardin bio etic"}
 29 |     assert juger(marque, _trace("C'est Jardin Bio Etic, avec 6,5 g.")) == "juste"
 30 |     assert juger(marque, _trace("C'est Celnat.")) == "fausse"
 31 |     prudence = {"type": "prudence", "attendu": ["hasard", "pas conclure"]}
 32 |     assert juger(prudence, _trace("L'écart peut venir du hasard.")) == "juste"
 33 |     assert juger(prudence, _trace("Oui, les bio ont plus de lipides.")) == "fausse"
 34 | 
 35 | 
 36 | def test_resume_moyenne_et_dispersion():
 37 |     r = resumer([["juste", "juste"], ["juste", "fausse"], ["bloquee", "fausse"]])
 38 |     assert r["taux_juste_par_lancement"] == [1.0, 0.5, 0.0]
 39 |     assert r["taux_juste_moyen"] == 0.5
 40 |     assert r["ecart_type"] == 0.5
 41 |     assert (r["justes"], r["fausses"], r["bloquees"], r["total"]) == (3, 2, 1, 6)
 42 | 
 43 | 
 44 | def test_refus_juste_seulement_sans_chiffre_invente():
 45 |     tache = {"type": "refus", "attendu": None}
 46 |     question = "Quelle est la teneur moyenne en vitamine C des céréales, pour 100 g ?"
 47 |     assert juger(tache, {"reponse": "Les données ne contiennent pas la vitamine C.", "bloquee": False,
 48 |                          "question": question}) == "juste"
 49 |     assert juger(tache, {"reponse": "Environ 2 mg pour 100 g.", "bloquee": False,
 50 |                          "question": question}) == "fausse"      # 2 est inventé (100 vient de la question)
```

- **Lignes 5 et 6 : `_trace`**, fabrique une fausse trace avec juste ce dont `juger` a besoin.
- **Lignes 9 à 14 :** le jugement « à 2 % près », avec le minimum de 0,01 pour le sel.
- **Lignes 17 et 18 :** un écart négatif écrit sans signe est juste.
- **Lignes 21 à 24 :** une réponse bloquée n'est **jamais** comptée juste, même si le message de refus contient
  le bon nombre (953).
- **Lignes 27 à 33 :** le jugement des types `texte` (majuscules ou non) et `prudence`.
- **Lignes 36 à 41 :** la moyenne et l'écart type, calculés à la main : taux 1,0, 0,5 et 0,0 → moyenne 0,5, écart
  type 0,5.
- **Lignes 44 à 50 :** le type `refus` : « Les données ne contiennent pas la vitamine C » est juste ; « Environ 2 mg
  pour 100 g » est faux (le 2 est inventé, le 100 vient de la question).

---

## 4. Pourquoi aucun test n'appelle Qwen

- **Qwen ne répond pas deux fois pareil :** un test qui l'appellerait passerait une fois et échouerait la suivante.
  Un test doit toujours donner le même résultat.
- **Qwen est lent :** environ 20 à 30 secondes par question. Les 42 tests tournent en moins d'une seconde.
- **Le comportement réel de Qwen est mesuré ailleurs :** dans la brique 9 (`evaluation.py`, 3 lancements par
  question) et dans les traces.

---

## 5. Les limites (à dire soi-même)

- **Un test ne prouve que les cas qu'on a pensé à écrire.** Le filtre bio non demandé n'était testé nulle part,
  jusqu'à ce qu'on le voie dans une vraie trace. On a alors ajouté la règle n° 2 et ses tests.
- **Les données de test sont inventées :** elles ne garantissent pas que les 953 vraies fiches n'ont pas un défaut
  auquel on n'a pas pensé.
- **`download.py` n'a pas de test :** il dépend d'Internet et de l'API d'Open Food Facts.
- **Tous les tests passent ≠ le système est sans erreur :** l'évaluation montre 27 % de réponses non justes.

---

## 6. Questions d'examinateur, avec leurs réponses

**Q1. Qu'est-ce qu'un test, et que fait `assert` ?** Une fonction qui lance une partie du code sur un exemple à
réponse connue. `assert` vérifie une condition : si elle est fausse, le test échoue.

**Q2. Comment connaissez-vous la bonne réponse d'un test ?** Je la calcule à la main, et le calcul est écrit en
commentaire. Exemple : la marge 1,96 × 7,07 / √2 = 9,8.

**Q3. Pourquoi ne pas tester sur les 953 vraies céréales ?** On ne pourrait pas calculer les réponses à la main, et
un défaut précis ne serait pas forcément présent. Les produits inventés ont chacun un défaut choisi exprès.

**Q4. Qu'est-ce qu'une fixture ?** Une donnée préparée pour les tests (`@pytest.fixture`, dans `conftest.py`). Un
test qui écrit `df` en paramètre la reçoit : pytest appelle la fixture, qui nettoie les 7 produits.

**Q5. Pourquoi 7 produits au départ et 4 à l'arrivée ?** On retire le doublon, le produit sans nom et le produit
sans aucune valeur. Le produit 5 est gardé : seules ses valeurs impossibles sont vidées.

**Q6. Que vérifie `with pytest.raises(ValueError):` ?** Que la ligne en dessous **provoque** une ValueError : le test
réussit si le code refuse, par exemple, un nutriment « vitamine_c ».

**Q7. Comment testez-vous le garde-fou sans lancer Qwen ?** On simule sa réponse : on écrit dans le test une
réponse avec un chiffre non calculé (la vraie réponse « 5,3 g » du 2 novembre) et on vérifie qu'elle est bloquée.

**Q8. Pourquoi aucun test n'appelle-t-il le modèle ?** Qwen ne répond pas deux fois pareil et il est lent. Le vrai
comportement du modèle est mesuré par la brique 9.

**Q9. Vos tests passent tous. Le système est-il donc sans erreur ?** Non. Les tests vérifient les cas qu'on a pensé
à écrire. Les traces et l'évaluation ont montré des erreurs qu'aucun test ne couvrait.

---

## 7. Résumé en 5 phrases

1. Un test lance une partie du code sur un exemple dont la bonne réponse est calculée à la main et écrite dans le test.
2. `conftest.py` fabrique 7 petits produits inventés, chacun avec un défaut choisi exprès, qui deviennent 4 produits propres.
3. Les tests vérifient le nettoyage (brique 6), les outils et leurs marges (briques 1 et 8), le jugement de l'évaluation (brique 9).
4. Les tests du garde-fou essaient d'enfreindre les deux règles en simulant les réponses de Qwen, dont de vraies réponses recopiées (brique 3).
5. Aucun test n'appelle Qwen : ils sont rapides et donnent toujours le même résultat ; le vrai comportement du modèle est mesuré par l'évaluation.
