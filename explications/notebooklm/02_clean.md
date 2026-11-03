# Nutri-Arbitre — Fichier 2 : `clean.py`, nettoyer des données sales

> **Pour qui est ce document :** une étudiante qui débute en Python et qui doit expliquer ce fichier à l'oral,
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

## 1. Le rôle de ce fichier

`clean.py` est la **deuxième étape**. Les données d'Open Food Facts sont remplies par des bénévoles : elles
sont **sales**. On y trouve des doublons, des produits sans nom, des valeurs impossibles (150 g de sel pour
100 g), des marques écrites de dix façons différentes, des kilojoules écrits dans la case des kilocalories…

Ce fichier transforme la liste brute en un **tableau propre**, et il écrit **chaque décision** dans un journal.
C'est la **brique 6** : « données sales, décisions écrites ».

- **Ce qui entre :** `data/raw_cereales.json` (1000 produits bruts, écrit par `download.py`).
- **Ce qui sort :** `data/cereales_propres.csv` (953 céréales propres) et `data/journal_nettoyage.md` (le journal).
- **Comment on le lance :** `python -m nutri.clean`.

**La règle venue d'un document extérieur (exigée par la brique 6) :** le règlement européen n° 1169/2011, dit
« INCO », annexe XIV. Il donne deux formules officielles, qui ne sont pas dans le fichier de données :
- **sel = sodium × 2,5** ;
- **énergie (kcal) = 4 × glucides + 4 × protéines + 9 × lipides + 2 × fibres.**

**Le vrai journal du projet (résumé) :**

```
- Départ : 1000 produits.
- Doublons de code-barres retirés : 0.
- Produits sans nom retirés : 28.
- energie_kcal : 1 valeurs hors de [0, 900] kcal mises à vide.
- Sucres > glucides : 0 valeurs de sucres mises à vide.
- Énergie calculée depuis les macronutriments (règlement INCO) : 1 produits.
- Énergie déclarée à plus de 20 % du calcul INCO (fiche incohérente), produits retirés : 4.
- Nutri-Score non valide (unknown, not-applicable…) mis à vide : 30.
- Marques normalisées : 294 libellés bruts -> 177 marques.
- Marques regroupées (même début de nom, ou table écrite à la main) : 28 fusions -> 149 marques.
- Arrivée : 953 produits.
```

---

## 2. Les notions à connaître avant de lire le code

### Un DataFrame pandas
`pandas` est la bibliothèque Python des tableaux de données. Un **DataFrame** (souvent appelé `df`) est un
tableau, comme une feuille Excel : des **lignes** (ici, un produit par ligne) et des **colonnes** (code, nom,
marque, sucres…). Voici les 3 premières lignes de notre vrai tableau propre :

| code | nom | marque | bio | nutriscore | energie_kcal | sucres | sel |
|---|---|---|---|---|---|---|---|
| 3168930010265 | cruesly mélange de noix | pepsico france | False | b | 462 | 12.0 | 0.00 |
| 3229820019307 | Flocons d'avoine | bjorg | True | a | 363 | 1.7 | 0.02 |
| 3229820129488 | muesli raisin,datte,figue | bjorg | True | a | 352 | 14.0 | 0.03 |

`df["sucres"]` prend **une colonne**. Une colonne s'appelle une **Series**.

### Une valeur vide : `NaN` / `None`
Quand une case est vide, pandas écrit `NaN` (« Not a Number »). `isna()` répond « vrai » pour une case vide,
`notna()` pour une case remplie. `dropna()` enlève les cases (ou les lignes) vides. `fillna(0)` remplace les
cases vides par 0.

### Le masque (la technique la plus importante du fichier)
Un **masque** est une colonne de vrai / faux, une réponse par ligne. On l'obtient en posant une question à
une colonne :

```python
df["sel"] > 100
# ligne 0 : False
# ligne 1 : False
# ligne 2 : True    <- ce produit a plus de 100 g de sel pour 100 g : impossible
```

Ensuite, le masque sert à **choisir des lignes** :
- `df[masque]` garde les lignes où le masque vaut vrai ;
- `df[~masque]` garde les lignes où il vaut **faux** (`~` veut dire « non ») ;
- `df.loc[masque, "sel"] = None` met à vide la case « sel » **seulement** sur les lignes où le masque vaut vrai.
- `masque.sum()` compte les vrais (vrai compte 1, faux compte 0) : c'est le nombre de lignes concernées.

On combine deux masques avec `&` (« et ») et `|` (« ou ») :
`df["sel"].isna() & df["sodium"].notna()` = « le sel est vide **et** le sodium est rempli ».

**Pourquoi des masques et pas une boucle sur chaque ligne ?** Parce qu'en une seule ligne, pandas fait le
travail sur les 1000 produits d'un coup. C'est plus court, plus rapide et plus lisible.

### Le journal
`journal` est une simple **liste de phrases**. À chaque étape, on ajoute une phrase avec
`journal.append(...)` qui dit ce qu'on a fait et **combien** de produits sont touchés. À la fin, ces phrases
sont écrites dans `data/journal_nettoyage.md`. N'importe qui peut relire et contester nos décisions.

---

## 3. Le code, morceau par morceau

### Morceau 1 : l'en-tête et les réglages (lignes 1 à 35)

Code de `nutri/clean.py`, lignes 1 à 35 (le numéro de ligne est à gauche de la barre) :

```python
  1 | """Nettoie les données brutes d'Open Food Facts et écrit un journal de chaque décision.
  2 | 
  3 | Usage : python -m nutri.clean
  4 | 
  5 | Règles venues d'un document, absentes du fichier (brique 6) :
  6 |   Règlement (UE) n° 1169/2011 « INCO », annexe XIV :
  7 |   - sel = sodium x 2,5
  8 |   - énergie (kcal) = 4 x glucides + 4 x protéines + 9 x lipides + 2 x fibres
  9 | """
 10 | from __future__ import annotations   # « str | None » accepté aussi en Python 3.9
 11 | 
 12 | import json
 13 | import unicodedata
 14 | from pathlib import Path
 15 | 
 16 | import pandas as pd
 17 | 
 18 | ENTREE = Path("data/raw_cereales.json")
 19 | SORTIE = Path("data/cereales_propres.csv")
 20 | JOURNAL = Path("data/journal_nettoyage.md")
 21 | 
 22 | # nom dans Open Food Facts -> nom de notre colonne
 23 | NUTRIMENTS = {
 24 |     "energy-kcal_100g": "energie_kcal",
 25 |     "carbohydrates_100g": "glucides",
 26 |     "sugars_100g": "sucres",
 27 |     "fat_100g": "lipides",
 28 |     "saturated-fat_100g": "ags",
 29 |     "fiber_100g": "fibres",
 30 |     "proteins_100g": "proteines",
 31 |     "salt_100g": "sel",
 32 |     "sodium_100g": "sodium",
 33 | }
 34 | EN_GRAMMES = ["glucides", "sucres", "lipides", "ags", "fibres", "proteines", "sel", "sodium"]
 35 | LABELS_BIO = {"en:organic", "en:eu-organic", "fr:ab-agriculture-biologique"}
```

- **Lignes 1 à 9 : la docstring**, qui rappelle les deux formules du règlement INCO.
- **Ligne 10 : `from __future__ import annotations`.** Notre Python est la version 3.9. Cette ligne permet
  d'écrire `str | None` (« du texte ou rien ») dans les annotations, une écriture arrivée en 3.10. Sans elle,
  le programme plante en 3.9.
- **Ligne 13 : `unicodedata`**, un module pour enlever les accents (utilisé pour les marques).
- **Lignes 18 à 20 :** les trois fichiers : l'entrée, le tableau propre, le journal.
- **Lignes 23 à 33 : `NUTRIMENTS`**, un dictionnaire qui traduit les noms d'Open Food Facts (en anglais, avec
  `_100g`) en noms courts en français pour nos colonnes : `"sugars_100g"` devient `"sucres"`.
- **Ligne 34 : `EN_GRAMMES`**, les colonnes mesurées en grammes pour 100 g. Elles doivent être entre 0 et 100.
  L'énergie n'y est pas : elle est en kcal.
- **Ligne 35 : `LABELS_BIO`**, les trois étiquettes qui veulent dire « bio » : le label bio européen (deux
  écritures) et le label AB français. Les accolades `{...}` font un **ensemble** (`set`) : une collection sans
  doublons où la recherche « est-ce dedans ? » est très rapide.

---

### Morceau 2 : `normaliser_marque` (lignes 38 à 53)

Code de `nutri/clean.py`, lignes 38 à 53 (le numéro de ligne est à gauche de la barre) :

```python
 38 | def normaliser_marque(brut) -> str | None:
 39 |     """'KELLOGG'S, Kellogg' -> 'kelloggs' : 1re marque, minuscules, sans accents ni ponctuation."""
 40 |     if not isinstance(brut, str) or not brut.strip():
 41 |         return None
 42 |     premiere = brut.split(",")[0]                       # "KELLOGG'S, Kellogg" -> "KELLOGG'S"
 43 |     # enlever les accents : "é" est décomposé en "e" + accent, puis l'accent est jeté
 44 |     sans_accents = unicodedata.normalize("NFKD", premiere).encode("ascii", "ignore").decode()
 45 |     # garder seulement les lettres, les chiffres et les espaces : "kellogg's" -> "kelloggs"
 46 |     propre = ""
 47 |     for c in sans_accents.lower():
 48 |         if c.isalnum() or c == " ":
 49 |             propre += c
 50 |     propre = " ".join(propre.split())                   # espaces multiples -> un seul
 51 |     if propre == "":
 52 |         return None
 53 |     return propre
```

**But :** la même marque est écrite de mille façons : `"KELLOGG'S, Kellogg"`, `"Kellogg's"`, `"KELLOGG’S"`. On
veut une seule écriture : `"kelloggs"`.

- **Lignes 40 et 41 :** si la marque n'est pas du texte (case vide) ou si c'est seulement des espaces
  (`brut.strip()` enlève les espaces au début et à la fin, et il reste une chaîne vide), on renvoie `None`.
- **Ligne 42 :** `brut.split(",")` coupe le texte à chaque virgule, et `[0]` prend le premier morceau. Un
  produit peut avoir plusieurs marques (`"Nestlé, Nestle France"`) : on garde la première.
- **Ligne 44 : enlever les accents.** `normalize("NFKD", ...)` décompose chaque lettre accentuée en deux : la
  lettre et l'accent (« é » devient « e » + « ´ »). `.encode("ascii", "ignore")` ne garde que les caractères
  simples (ASCII) et jette les accents. `.decode()` remet le résultat en texte.
- **Lignes 46 à 49 :** on parcourt chaque caractère (`c`) du texte en minuscules (`.lower()`). On garde
  seulement les lettres et chiffres (`c.isalnum()`) et les espaces. L'apostrophe de « kellogg's » disparaît.
- **Ligne 50 :** `propre.split()` coupe aux espaces (plusieurs espaces comptent comme un seul), puis
  `" ".join(...)` recolle les mots avec un seul espace. `"bjorg   et  cie"` devient `"bjorg et cie"`.
- **Lignes 51 à 53 :** s'il ne reste rien (une marque faite seulement de ponctuation), `None` ; sinon on
  renvoie la marque propre.

**Vrais exemples, lancés sur le code :**

| Marque brute | Résultat |
|---|---|
| `"KELLOGG'S, Kellogg"` | `"kelloggs"` |
| `"Nestlé, Nestle France"` | `"nestle"` |
| `"Céréco SARL"` | `"cereco sarl"` |
| `"Bjorg et Cie"` | `"bjorg et cie"` |
| `"   "` | `None` |

Résultat sur nos données : **294 écritures brutes → 177 marques**.

---

### Morceau 3 : la table des alias et `regrouper_marques` (lignes 56 à 107)

Code de `nutri/clean.py`, lignes 56 à 107 (le numéro de ligne est à gauche de la barre) :

```python
 56 | # Marques que la règle de regroupement ne peut pas trouver seule (vérifiées à la main, 01/11/2026) :
 57 | # la marque est au milieu du nom, ou écrite avec une abréviation / une faute.
 58 | ALIAS_MARQUES = {
 59 |     "societe des produits nestle sa": "nestle",
 60 |     "the jordans ryvita company limited a division of abf grain products limited": "jordans",
 61 |     "crownfields": "crownfield",
 62 |     "tc": "terres et cereales",                     # TC = abréviation de Terres & Céréales
 63 |     "tc bio": "terres et cereales",
 64 |     "tc terre et cereales": "terres et cereales",
 65 |     "tc terres cereales bio": "terres et cereales",
 66 |     "tc terres et cereales bio": "terres et cereales",
 67 |     "terre et cereales": "terres et cereales",
 68 |     "terres cereales": "terres et cereales",
 69 |     "terres cereales bio": "terres et cereales",
 70 | }
 71 | 
 72 | 
 73 | def regrouper_marques(marques: pd.Series) -> tuple[pd.Series, list[str]]:
 74 |     """Regroupe les écritures d'une même marque. Renvoie (marques regroupées, liste des fusions).
 75 |     Règle : si une marque COMMENCE par les mots entiers d'une autre marque présente, c'est la même
 76 |     (« carrefour bio » -> « carrefour »). On compare sans les espaces (« kellogg s » = « kelloggs »).
 77 |     Mots entiers seulement : « lucien georgelin » n'est pas rangé chez « lu »."""
 78 |     originales = marques
 79 |     marques = marques.replace(ALIAS_MARQUES)
 80 | 
 81 |     # forme sans espaces -> écriture la plus fréquente (« aline olivier » plutôt que « alineolivier »)
 82 |     ecriture = {}
 83 |     for nom in marques.value_counts().index:          # du plus fréquent au moins fréquent
 84 |         cle = nom.replace(" ", "")
 85 |         if cle not in ecriture:
 86 |             ecriture[cle] = nom
 87 | 
 88 |     correspondance = {}
 89 |     for nom in marques.dropna().unique():
 90 |         mots = nom.split()
 91 |         cible = ecriture[nom.replace(" ", "")]
 92 |         # on essaie les débuts du nom : 1 mot, puis 2 mots collés, etc.
 93 |         for k in range(1, len(mots)):
 94 |             debut = "".join(mots[:k])
 95 |             if debut in ecriture:
 96 |                 cible = ecriture[debut]
 97 |                 break
 98 |         correspondance[nom] = cible
 99 | 
100 |     regroupees = marques.map(correspondance)
101 | 
102 |     # liste de toutes les fusions (table à la main + règle), pour le journal
103 |     fusions = []
104 |     for nom, cible in sorted(set(zip(originales.dropna(), regroupees.dropna()))):
105 |         if nom != cible:
106 |             fusions.append(f"{nom} -> {cible}")
107 |     return regroupees, fusions
```

**Le problème restant :** après la normalisation, il reste `"carrefour"`, `"carrefour bio"`,
`"carrefour kids"`, `"kellogg s produits aliment sas"`… C'est la même entreprise.

**La règle (décidée en séance 2) :** si une marque **commence par les mots entiers** d'une autre marque
présente, c'est la même. `"carrefour bio"` commence par le mot `"carrefour"`, donc c'est carrefour.
**Mots entiers, et pas lettres** : sinon `"lucien georgelin"` serait rangé chez `"lu"` (il commence par les
lettres « lu »). Avec les mots entiers, le premier mot est « lucien », qui n'est pas « lu ».

**Lignes 58 à 70 : `ALIAS_MARQUES`**, une table écrite à la main pour les cas que la règle ne trouve pas : la
marque est au milieu du nom (« societe des produits **nestle** sa »), ou abrégée (« tc » = Terres & Céréales).

**Ligne par ligne :**
- **Ligne 78 :** on garde les marques d'origine, pour écrire la liste des fusions à la fin.
- **Ligne 79 :** `replace(ALIAS_MARQUES)` remplace d'abord les alias : `"tc bio"` devient `"terres et cereales"`.
- **Lignes 82 à 86 : la forme sans espaces.** Certaines marques sont écrites collées ou non :
  `"aline olivier"` et `"alineolivier"`. On fabrique un dictionnaire `ecriture` : forme sans espaces →
  écriture la plus fréquente. `value_counts()` compte chaque marque, de la plus fréquente à la moins fréquente.
  Comme on parcourt dans cet ordre, la première écriture rencontrée pour une forme est la plus fréquente, et
  `if cle not in ecriture` empêche de l'écraser ensuite.
  Exemple : `ecriture["alineolivier"] = "aline olivier"`.
- **Lignes 88 à 98 : la règle des débuts de nom.** Pour chaque marque (`unique()` = chaque marque une seule fois) :
  - `mots = nom.split()` : `"carrefour bio"` → `["carrefour", "bio"]` ;
  - `cible` vaut d'abord la meilleure écriture de la marque elle-même ;
  - ligne 93 : `for k in range(1, len(mots))` essaie les débuts du nom : 1 mot, puis 2 mots… sans jamais
    prendre le nom entier (le `len(mots)` est exclu) ;
  - ligne 94 : `"".join(mots[:k])` colle les `k` premiers mots sans espace. `mots[:1]` = `["carrefour"]` →
    `"carrefour"` ;
  - lignes 95 à 97 : si ce début est une marque connue, c'est la cible, et `break` arrête la recherche (on
    garde le début le plus **court**).
- **Ligne 100 :** `marques.map(correspondance)` remplace chaque marque par sa cible.
- **Lignes 103 à 106 : la liste des fusions**, pour le journal. `zip` met côte à côte chaque marque d'origine
  et sa marque regroupée. `set` enlève les doublons, `sorted` trie par ordre alphabétique. On garde seulement
  les paires où le nom a changé.

**Déroulé complet sur un exemple :** la marque `"kellogg s produits aliment sas"`.
1. Mots : `["kellogg", "s", "produits", "aliment", "sas"]`.
2. k = 1 : début `"kellogg"`. Est-ce une marque connue ? Non.
3. k = 2 : début `"kellogg" + "s"` = `"kelloggs"`. Oui ! C'est la marque Kellogg's normalisée.
4. Cible : `"kelloggs"`. Le journal écrit : `fusion : kellogg s produits aliment sas -> kelloggs`.

**Vraies fusions du journal :** `carrefour bio -> carrefour`, `auchan bio -> auchan`,
`kelloggs extra -> kelloggs`, `alineolivier -> aline olivier`, `societe des produits nestle sa -> nestle`,
`tc bio -> terres et cereales`. En tout : **28 fusions, 177 → 149 marques**.

**Attention, une décision importante :** regrouper « carrefour bio » avec « carrefour » ne change **pas** le
caractère bio des produits. La colonne `bio` est calculée à partir du **label officiel** (morceau 4), pas du
nom de la marque. Exemple réel : la marque « Happy Bio » a des produits sans label bio : ils restent non bio.

---

### Morceau 4 : `est_bio` (lignes 110 à 115)

Code de `nutri/clean.py`, lignes 110 à 115 (le numéro de ligne est à gauche de la barre) :

```python
110 | def est_bio(tags: list) -> bool:
111 |     """Vrai si au moins un des labels du produit est un label bio."""
112 |     for tag in tags:
113 |         if tag in LABELS_BIO:
114 |             return True
115 |     return False
```

- La fonction reçoit la liste des labels d'un produit, par exemple
  `["en:no-palm-oil", "fr:ab-agriculture-biologique"]`.
- Elle parcourt chaque label. Dès qu'un label est dans `LABELS_BIO`, elle répond `True` (le `return` arrête
  la fonction tout de suite).
- Si elle a tout parcouru sans trouver, elle répond `False`.

Avec l'exemple ci-dessus : `"en:no-palm-oil"` n'est pas bio, `"fr:ab-agriculture-biologique"` l'est → `True`.

---

### Morceau 5 : `aplatir` (lignes 118 à 134)

Code de `nutri/clean.py`, lignes 118 à 134 (le numéro de ligne est à gauche de la barre) :

```python
118 | def aplatir(produits: list[dict]) -> pd.DataFrame:
119 |     """Transforme la liste JSON en tableau, une ligne par produit."""
120 |     lignes = []
121 |     for p in produits:
122 |         nutr = p.get("nutriments") or {}
123 |         ligne = {
124 |             "code": p.get("code"),
125 |             "nom": p.get("product_name"),
126 |             "marque_brute": p.get("brands"),
127 |             "labels": p.get("labels_tags") or [],
128 |             "nutriscore_brut": p.get("nutriscore_grade"),
129 |         }
130 |         for cle_off, col in NUTRIMENTS.items():
131 |             ligne[col] = nutr.get(cle_off)
132 |         lignes.append(ligne)
133 |     return pd.DataFrame(lignes, columns=["code", "nom", "marque_brute", "labels", "nutriscore_brut",
134 |                                          *NUTRIMENTS.values()])
```

**But :** chaque produit brut est un dictionnaire **emboîté** (les nutriments sont dans un sous-dictionnaire).
Un tableau pandas veut une ligne « à plat » : une valeur par colonne. « Aplatir », c'est sortir les nutriments
du sous-dictionnaire.

- **Ligne 122 :** `p.get("nutriments") or {}` prend le sous-dictionnaire des nutriments, ou un dictionnaire
  vide s'il n'existe pas. `.get` ne plante pas si la clé manque : il renvoie `None`, et `or {}` remplace ce
  `None` par `{}`.
- **Lignes 123 à 129 :** les informations générales, renommées : `product_name` devient `nom`, `brands`
  devient `marque_brute`.
- **Lignes 130 et 131 :** pour chaque paire du dictionnaire `NUTRIMENTS` (`.items()` donne les paires
  clé-valeur), on lit la valeur d'Open Food Facts et on la range dans notre colonne. Exemple :
  `ligne["sucres"] = nutr.get("sugars_100g")`.
- **Lignes 133 et 134 :** on construit le tableau. `columns=[...]` fixe l'ordre des colonnes, même si la liste
  est vide. `*NUTRIMENTS.values()` « déballe » les 9 noms de colonnes de nutriments dans la liste.

**Avant / après, sur le vrai produit « cruesly » :**
- avant : `{"brands": "PEPSICO FRANCE", "nutriments": {"carbohydrates_100g": 57, "fat_100g": 19, ...}}`
- après : une ligne avec `marque_brute = "PEPSICO FRANCE"`, `glucides = 57`, `lipides = 19`, …

---

### Morceau 6 : `nettoyer`, étapes 1 à 3 (lignes 137 à 159)

Code de `nutri/clean.py`, lignes 137 à 159 (le numéro de ligne est à gauche de la barre) :

```python
137 | def nettoyer(produits: list[dict]) -> tuple[pd.DataFrame, list[str]]:
138 |     """Renvoie (tableau propre, journal). Chaque ligne du journal décrit une décision."""
139 |     journal = []
140 |     df = aplatir(produits)
141 |     journal.append(f"Départ : {len(df)} produits.")
142 | 
143 |     # 1. doublons de code-barres
144 |     avant = len(df)
145 |     df = df.drop_duplicates(subset="code")
146 |     journal.append(f"Doublons de code-barres retirés : {avant - len(df)}.")
147 | 
148 |     # 2. produits sans nom
149 |     avant = len(df)
150 |     df = df[df["nom"].fillna("").str.strip() != ""]
151 |     journal.append(f"Produits sans nom retirés : {avant - len(df)}.")
152 | 
153 |     # 3. conversion en nombres (certaines valeurs arrivent en texte)
154 |     for col in NUTRIMENTS.values():
155 |         texte_avant = df[col].notna().sum()
156 |         df[col] = pd.to_numeric(df[col], errors="coerce")
157 |         perdus = texte_avant - df[col].notna().sum()
158 |         if perdus:
159 |             journal.append(f"{col} : {perdus} valeurs non numériques mises à vide.")
```

- **Ligne 138 :** la fonction renvoie **deux** choses : le tableau propre et le journal (un « tuple »).
- **Lignes 139 à 141 :** on commence le journal et on aplatit les produits.
- **Le schéma qui revient à chaque étape :** `avant = len(df)` (combien de lignes avant), on fait l'étape, puis
  on écrit dans le journal `avant - len(df)` (combien de lignes retirées).
- **Étape 1, lignes 144 à 146 : les doublons.** `drop_duplicates(subset="code")` garde un seul produit par
  code-barres. Sur nos données : 0 doublon.
- **Étape 2, lignes 149 à 151 : les produits sans nom.** `fillna("")` remplace les noms vides par un texte
  vide, `.str.strip()` enlève les espaces, et on garde les lignes où le nom n'est pas vide (`!= ""`). Sur nos
  données : **28 produits sans nom retirés**. Sans nom, on ne peut pas savoir ce qu'est le produit.
- **Étape 3, lignes 154 à 159 : la conversion en nombres.** Certaines valeurs arrivent en texte (`"12,5"` ou
  `"traces"`). `pd.to_numeric(..., errors="coerce")` transforme en nombre ce qui peut l'être, et met à vide ce
  qui ne peut pas (`coerce` = « forcer »). On compte les cases remplies avant et après : la différence, ce sont
  les valeurs perdues, et on ne l'écrit dans le journal que s'il y en a (`if perdus:`).

---

### Morceau 7 : étapes 4 et 5, les valeurs impossibles (lignes 161 à 178)

Code de `nutri/clean.py`, lignes 161 à 178 (le numéro de ligne est à gauche de la barre) :

```python
161 |     # 4. bornes physiques : pour 100 g, une masse est entre 0 et 100 g
162 |     for col in EN_GRAMMES:
163 |         hors = (df[col] < 0) | (df[col] > 100)
164 |         if hors.sum():
165 |             journal.append(f"{col} : {hors.sum()} valeurs hors de [0, 100] g mises à vide.")
166 |         df.loc[hors, col] = None
167 |     # 900 kcal/100 g = de la graisse pure : impossible de dépasser
168 |     hors = (df["energie_kcal"] < 0) | (df["energie_kcal"] > 900)
169 |     journal.append(f"energie_kcal : {hors.sum()} valeurs hors de [0, 900] kcal mises à vide.")
170 |     df.loc[hors, "energie_kcal"] = None
171 | 
172 |     # 5. cohérence : une partie ne peut pas dépasser le tout
173 |     incoh = df["sucres"] > df["glucides"]
174 |     journal.append(f"Sucres > glucides : {incoh.sum()} valeurs de sucres mises à vide.")
175 |     df.loc[incoh, "sucres"] = None
176 |     incoh = df["ags"] > df["lipides"]
177 |     journal.append(f"Acides gras saturés > lipides : {incoh.sum()} valeurs mises à vide.")
178 |     df.loc[incoh, "ags"] = None
```

**Étape 4, les bornes physiques.** Pour 100 g de produit, une masse est forcément entre 0 et 100 g.
- **Ligne 163 :** le masque des valeurs hors bornes : inférieures à 0 **ou** (`|`) supérieures à 100.
- **Ligne 166 :** on met ces cases à vide. **Seulement la case**, pas toute la ligne.
- **Lignes 168 à 170 :** pour l'énergie, la borne est 900 kcal : 100 g de graisse pure font 9 × 100 =
  900 kcal, rien ne peut dépasser ça.

**Vrai cas :** le produit « Pétales blé goût chocolat » (marque U) avait **2114** dans la case des kcal. C'était
en fait des **kilojoules** écrits dans la mauvaise case. 2114 > 900 : la case est vidée, puis l'étape 7 la
recalcule avec la formule INCO.

**Étape 5, la cohérence.** Une partie ne peut pas dépasser le tout :
- les sucres font partie des glucides : si sucres > glucides, la valeur des sucres est fausse → vidée ;
- les acides gras saturés (AGS) font partie des lipides : si AGS > lipides → vidée.

**Pourquoi vider une seule case et garder le produit ?** (question posée en séance 2) L'erreur ne touche qu'une
case : les autres valeurs du produit sont peut-être justes, et elles servent pour d'autres questions. Et le
contrôle INCO de l'étape 7 vérifie ensuite la cohérence du reste de la fiche.

---

### Morceau 8 : étape 6, le sel calculé (lignes 180 à 184)

Code de `nutri/clean.py`, lignes 180 à 184 (le numéro de ligne est à gauche de la barre) :

```python
180 |     # 6. RÈGLE INCO : sel = sodium x 2,5
181 |     a_completer = df["sel"].isna() & df["sodium"].notna()
182 |     df.loc[a_completer, "sel"] = df.loc[a_completer, "sodium"] * 2.5
183 |     journal.append(f"Sel calculé depuis le sodium (sel = sodium x 2,5, règlement INCO) : "
184 |                    f"{a_completer.sum()} produits.")
```

- **Ligne 181 :** le masque des produits **sans sel mais avec du sodium**.
- **Ligne 182 :** pour ces produits seulement, sel = sodium × 2,5 (règlement INCO).

**Exemple :** un produit avec 0,2 g de sodium et pas de sel → sel = 0,2 × 2,5 = **0,5 g**. (C'est exactement
le produit n° 2 des tests.)

**Pourquoi 2,5 ?** Le sel de table est du chlorure de sodium. Le sodium pèse environ 40 % de la masse du sel :
1 g de sodium correspond à environ 2,5 g de sel. Le règlement INCO fixe ce facteur.

---

### Morceau 9 : étape 7, l'énergie et le contrôle de cohérence (lignes 186 à 203)

Code de `nutri/clean.py`, lignes 186 à 203 (le numéro de ligne est à gauche de la barre) :

```python
186 |     # 7. RÈGLE INCO : énergie recalculée à partir des macronutriments
187 |     # calcul fait pour toutes les lignes d'un coup (fibres absentes comptées 0)
188 |     calcul = (4 * df["glucides"] + 4 * df["proteines"] + 9 * df["lipides"]
189 |               + 2 * df["fibres"].fillna(0))
190 |     macros_connues = df["glucides"].notna() & df["proteines"].notna() & df["lipides"].notna()
191 |     a_completer = df["energie_kcal"].isna() & macros_connues
192 |     df.loc[a_completer, "energie_kcal"] = calcul[a_completer].round(0)
193 |     journal.append(f"Énergie calculée depuis les macronutriments (règlement INCO) : "
194 |                    f"{a_completer.sum()} produits.")
195 |     # contrôle : si l'énergie déclarée s'écarte de plus de 20 % du calcul, les valeurs de la fiche se
196 |     # contredisent et on ne peut pas savoir laquelle est fausse (énergie ? glucides ? lipides ?).
197 |     # Toute la fiche est donc douteuse : on retire le produit.
198 |     ecart = (df["energie_kcal"] - calcul).abs() / calcul.where(calcul > 0)   # pas de division par 0
199 |     suspect = (ecart > 0.20).fillna(False)
200 |     avant = len(df)
201 |     df = df[~suspect]                                    # ~ = « non » : on garde les non suspects
202 |     journal.append(f"Énergie déclarée à plus de 20 % du calcul INCO (fiche incohérente), "
203 |                    f"produits retirés : {avant - len(df)}.")
```

**La formule INCO :** énergie (kcal) = 4 × glucides + 4 × protéines + 9 × lipides + 2 × fibres.
(1 g de glucides ou de protéines apporte 4 kcal, 1 g de lipides 9 kcal, 1 g de fibres 2 kcal.)

- **Lignes 188 et 189 :** le calcul est fait pour **toutes** les lignes en même temps. Les fibres absentes
  comptent 0 (`fillna(0)`), parce qu'elles sont souvent non renseignées et pèsent peu.
- **Ligne 190 :** le masque des produits dont les trois valeurs principales sont connues.
- **Lignes 191 et 192 : compléter.** Pour les produits **sans énergie** mais avec les valeurs principales, on
  écrit l'énergie calculée, arrondie à l'unité (`round(0)`). Sur nos données : 1 produit (le « Pétales » de
  l'étape 4).
- **Lignes 198 à 203 : contrôler.** On compare l'énergie **déclarée** et l'énergie **calculée** :
  - ligne 198 : l'écart relatif = |déclarée − calculée| / calculée. `calcul.where(calcul > 0)` met à vide les
    calculs égaux à 0, pour **ne pas diviser par 0** ;
  - ligne 199 : le masque des fiches où l'écart dépasse 20 %. `fillna(False)` : quand on n'a pas pu calculer
    l'écart, on ne soupçonne pas le produit ;
  - ligne 201 : `df[~suspect]` garde seulement les produits **non** suspects.

**Vrai cas :** « Muesli croustillant chocolat » déclare **437 kcal**. Le calcul donne
4 × 33 + 4 × 4,7 + 9 × 6,6 + 2 × 3,9 = 132 + 18,8 + 59,4 + 7,8 = **218 kcal**. L'écart est de 100 %.

**La décision (prise en séance 2) :** 437 kcal pour un muesli, ce n'est pas choquant. C'est donc plutôt les
autres valeurs (glucides, lipides…) qui sont fausses ou incomplètes. Mais on ne peut pas savoir **laquelle** :
toute la fiche est douteuse. On retire le produit. Sur nos données : **4 produits retirés** sur 957.

**Pourquoi 20 % ?** Les valeurs d'une étiquette sont arrondies, et la formule est approximative. Un petit écart
est normal. 20 % laisse passer les arrondis et attrape les vraies contradictions.

---

### Morceau 10 : étape 8, le Nutri-Score (lignes 205 à 209)

Code de `nutri/clean.py`, lignes 205 à 209 (le numéro de ligne est à gauche de la barre) :

```python
205 |     # 8. Nutri-Score : on ne garde que a à e
206 |     df["nutriscore"] = df["nutriscore_brut"].astype("string").str.lower().str.strip()
207 |     invalides = df["nutriscore"].notna() & ~df["nutriscore"].isin(list("abcde"))
208 |     journal.append(f"Nutri-Score non valide (unknown, not-applicable…) mis à vide : {invalides.sum()}.")
209 |     df.loc[invalides, "nutriscore"] = None
```

- **Ligne 206 :** on met le Nutri-Score en texte, en minuscules, sans espaces : `" A "` devient `"a"`.
- **Ligne 207 :** le masque des valeurs remplies (`notna`) **et** qui ne sont **pas** (`~`) une lettre de a à e
  (`isin(list("abcde"))`, avec `list("abcde")` = `["a", "b", "c", "d", "e"]`).
- **Ligne 209 :** ces valeurs sont mises à vide.

Sur nos données : **30 valeurs non valides** (« unknown » = inconnu, « not-applicable » = non concerné).

**Décision :** on **garde** ces produits. Ils ont leurs autres valeurs et servent pour toutes les questions sauf
celles sur le Nutri-Score. On a envisagé de calculer leur Nutri-Score nous-mêmes, mais pour 20 d'entre eux il
manque le sel ou les AGS (il faudrait les inventer), et 5 sont des aliments pour bébé, non concernés par le
Nutri-Score. L'outil `comparer` indique combien de produits n'ont pas de Nutri-Score (`sans_nutriscore`, 25).

---

### Morceau 11 : étapes 9 et 10, marques, bio et fin (lignes 211 à 231)

Code de `nutri/clean.py`, lignes 211 à 231 (le numéro de ligne est à gauche de la barre) :

```python
211 |     # 9. marques et label bio
212 |     df["marque"] = df["marque_brute"].map(normaliser_marque)
213 |     journal.append(f"Marques normalisées : {df['marque_brute'].nunique()} libellés bruts "
214 |                    f"-> {df['marque'].nunique()} marques.")
215 |     df["marque"], fusions = regrouper_marques(df["marque"])
216 |     journal.append(f"Marques regroupées (même début de nom, ou table écrite à la main) : "
217 |                    f"{len(fusions)} fusions -> {df['marque'].nunique()} marques.")
218 |     for f in fusions:
219 |         journal.append(f"  fusion : {f}")
220 |     df["bio"] = df["labels"].map(est_bio)   # applique est_bio à la liste de labels de chaque produit
221 |     journal.append(f"Produits bio (label AB ou bio UE) : {int(df['bio'].sum())}.")
222 | 
223 |     # 10. produits sans aucune valeur nutritionnelle
224 |     colonnes_nutr = ["energie_kcal", "glucides", "sucres", "lipides", "ags", "fibres", "proteines", "sel"]
225 |     avant = len(df)
226 |     df = df.dropna(subset=colonnes_nutr, how="all")
227 |     journal.append(f"Produits sans aucune valeur nutritionnelle retirés : {avant - len(df)}.")
228 | 
229 |     journal.append(f"Arrivée : {len(df)} produits.")
230 |     df = df[["code", "nom", "marque", "bio", "nutriscore", *colonnes_nutr]]
231 |     return df.reset_index(drop=True), journal
```

- **Ligne 212 :** `map(normaliser_marque)` applique la fonction du morceau 2 à **chaque** marque de la colonne.
- **Ligne 213 :** `nunique()` compte les valeurs différentes : 294 écritures brutes → 177 marques.
- **Ligne 215 :** le regroupement du morceau 3. La fonction renvoie deux choses, rangées dans deux variables.
- **Lignes 218 et 219 :** chaque fusion est écrite dans le journal.
- **Ligne 220 :** `map(est_bio)` applique `est_bio` à la liste de labels de chaque produit → une colonne de
  vrai / faux.
- **Étape 10, lignes 224 à 227 :** `dropna(subset=..., how="all")` retire les produits dont **toutes** les
  valeurs nutritionnelles sont vides (`how="all"`). Un produit sans aucun chiffre ne sert à rien.
  (Avec `how="any"`, on retirerait un produit dès qu'**une** valeur manque : on perdrait beaucoup trop de produits.)
- **Ligne 230 :** on garde seulement les colonnes utiles, dans l'ordre voulu. Les colonnes de travail
  (`marque_brute`, `labels`, `nutriscore_brut`, `sodium`) disparaissent.
- **Ligne 231 :** `reset_index(drop=True)` renumérote les lignes 0, 1, 2… (après les suppressions, il y avait
  des trous dans la numérotation).

---

### Morceau 12 : `main` (lignes 234 à 245)

Code de `nutri/clean.py`, lignes 234 à 245 (le numéro de ligne est à gauche de la barre) :

```python
234 | def main() -> None:
235 |     produits = json.loads(ENTREE.read_text(encoding="utf-8"))
236 |     df, journal = nettoyer(produits)
237 |     df.to_csv(SORTIE, index=False)
238 |     JOURNAL.write_text("# Journal de nettoyage\n\n" + "\n".join(f"- {l}" for l in journal) + "\n",
239 |                        encoding="utf-8")
240 |     print("\n".join(journal))
241 |     print(f"-> {SORTIE} et {JOURNAL}")
242 | 
243 | 
244 | if __name__ == "__main__":
245 |     main()
```

- **Ligne 235 :** on lit le fichier brut et on le transforme en liste Python (`json.loads` = « load string »).
- **Ligne 236 :** on nettoie.
- **Ligne 237 :** on écrit le tableau en CSV. `index=False` : on n'écrit pas la colonne des numéros de ligne.
- **Lignes 238 et 239 :** on écrit le journal : un titre, puis chaque phrase précédée de `- ` (une liste en
  Markdown). `"\n".join(...)` colle les phrases avec un retour à la ligne entre chacune.

---

## 4. Le trajet complet, de bout en bout

1000 produits bruts → aplatir → 0 doublon → 28 sans nom retirés → conversion en nombres → valeurs impossibles
vidées (1 énergie) → sel calculé (0) → énergie calculée (1) → 4 fiches incohérentes retirées → 30 Nutri-Score
non valides vidés → marques normalisées puis regroupées (149 marques) → colonne bio (547 bio) → 15 produits
sans aucune valeur retirés → **953 céréales propres**, dont 543 bio.

---

## 5. Les pièges et les erreurs fréquentes

- **Vider une case ≠ retirer une ligne.** Une valeur impossible : on vide la case, on garde le produit. Une fiche
  qui se contredit (étape 7) : on retire le produit, parce qu'on ne sait pas quelle valeur est fausse.
- **`&` et `|`, pas `and` et `or`**, entre deux masques pandas. Et des parenthèses autour de chaque comparaison :
  `(df["sel"] < 0) | (df["sel"] > 100)`.
- **`~` veut dire « non »** sur un masque.
- **Le bio vient du label, pas du nom de la marque.**
- **La règle des marques utilise des mots entiers**, sinon « lucien georgelin » irait chez « lu ».
- **Les tests ne tournent pas sur les vraies données**, mais sur 7 petits produits inventés dont on connaît la
  réponse (voir le document sur les tests).

---

## 6. Questions d'examinateur, avec leurs réponses

**Q1. Qu'est-ce qu'un masque ?** Une colonne de vrai / faux, une réponse par ligne. On s'en sert pour choisir
les lignes (`df[masque]`) ou pour modifier certaines cases (`df.loc[masque, "sel"] = None`).

**Q2. Quelle règle vient d'un document extérieur ?** Le règlement européen INCO (n° 1169/2011, annexe XIV) :
sel = sodium × 2,5 et énergie = 4 × glucides + 4 × protéines + 9 × lipides + 2 × fibres.

**Q3. Pourquoi retirer une fiche dont l'énergie s'écarte de plus de 20 % ?** Les valeurs se contredisent et on
ne sait pas laquelle est fausse. Exemple : le muesli à 437 kcal déclarées contre 218 calculées. 4 produits retirés.

**Q4. Pourquoi garder un produit dont une valeur est impossible ?** L'erreur ne touche qu'une case. On la vide,
et les autres valeurs restent utiles. Exemple : 2114 kJ écrits dans la case kcal, vidés puis recalculés.

**Q5. Comment regroupez-vous les marques ?** Une marque qui commence par les mots entiers d'une autre marque
présente est la même (carrefour bio → carrefour). Plus une table écrite à la main pour les cas difficiles.

**Q6. Pourquoi des mots entiers ?** Pour ne pas ranger « lucien georgelin » chez « lu ».

**Q7. Le regroupement de « carrefour bio » rend-il ses produits non bio ?** Non. Le bio vient du label officiel
de chaque produit, pas du nom de la marque.

**Q8. Pourquoi garder les produits sans Nutri-Score ?** Ils ont leurs autres valeurs. Calculer leur Nutri-Score
demanderait d'inventer des valeurs manquantes. Ils sont comptés à part (`sans_nutriscore`).

**Q9. À quoi sert le journal ?** À écrire chaque décision avec le nombre de produits touchés, pour que
quelqu'un d'autre puisse la vérifier ou la contester.

**Q10. Que fait `how="all"` dans `dropna` ?** Il retire seulement les produits dont **toutes** les valeurs sont
vides. Avec `how="any"`, on retirerait dès qu'une seule valeur manque.

---

## 7. Résumé en 5 phrases

1. `clean.py` transforme 1000 produits bruts et sales en 953 céréales propres, et écrit chaque décision dans un journal.
2. Il utilise des masques pandas pour trouver et corriger les valeurs impossibles (vider la case) ou retirer des lignes.
3. Il applique le règlement européen INCO pour calculer le sel et l'énergie, et pour repérer les fiches qui se contredisent.
4. Il normalise et regroupe les marques (294 écritures → 149 marques), avec une règle par mots entiers.
5. Le caractère bio vient du label officiel, et les produits sans Nutri-Score sont gardés et comptés à part.
