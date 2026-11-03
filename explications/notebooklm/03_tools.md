# Nutri-Arbitre — Fichier 3 : `tools.py`, les outils de calcul

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

`tools.py` contient les **outils** que le modèle Qwen peut appeler. Ce sont **les seules** fonctions qui
calculent des chiffres dans tout le projet. Qwen ne calcule rien : il demande « appelle `decrire` sur les
sucres des céréales bio », et c'est ce fichier qui fait la moyenne.

C'est le cœur de la **brique 1** (le modèle appelle nos propres outils) et de la **brique 8** (chaque chiffre
est donné avec sa marge d'erreur).

Les 4 outils :

| Outil | Ce qu'il fait | Exemple de question |
|---|---|---|
| `decrire` | moyenne (avec marge d'erreur), médiane, min, max d'un nutriment | « Combien de sucre en moyenne dans les céréales bio ? » |
| `comparer` | moyenne par groupe (bio / non bio, ou par Nutri-Score) et l'écart | « Les bio ont-elles moins de sucre ? » |
| `classement_marques` | les marques avec la moyenne la plus basse (ou haute) | « Quelle marque est la moins sucrée ? » |
| `compter` | le nombre de produits | « Combien de céréales ont un Nutri-Score A ? » |

**Une règle de conception :** chaque outil prend le tableau `df` en premier argument. Ainsi, les tests peuvent
lui donner un petit tableau inventé (4 produits) au lieu des 953 vrais, et vérifier le résultat à la main.

---

## 2. Les notions à connaître avant de lire le code

### Moyenne, médiane, min, max
Pour les valeurs 10, 20 et 60 :
- **moyenne** = (10 + 20 + 60) / 3 = 30 ;
- **médiane** = la valeur du milieu quand on les range : 20 (elle est moins sensible aux valeurs extrêmes) ;
- **min** = 10, **max** = 60.

### L'écart type : la dispersion des valeurs
L'**écart type** mesure à quel point les valeurs s'éloignent de la moyenne. Les valeurs 14, 15, 16 ont un petit
écart type (elles sont serrées). Les valeurs 0, 15, 30 ont un grand écart type (elles sont étalées), alors que
leur moyenne est la même (15).

### L'erreur type et la marge d'erreur (brique 8)
Nos 953 céréales ne sont qu'un **échantillon** de toutes les céréales. Si on avait pris d'autres produits, la
moyenne aurait été un peu différente. **De combien ?** C'est ce que mesure l'**erreur type** :

> **erreur type = écart type / √n** (n = le nombre de produits)

Puis la **marge d'erreur à 95 %** :

> **marge = 1,96 × erreur type**

et la **fourchette** (ou intervalle de confiance à 95 %) :

> **[moyenne − marge ; moyenne + marge]**

Le sens : « la vraie moyenne a 95 chances sur 100 d'être dans cette fourchette ». Le nombre 1,96 vient de la
loi normale (la courbe en cloche) : 95 % des cas tombent à moins de 1,96 erreur type du centre.

**Exemple réel :** les sucres des 543 céréales bio : moyenne **13,17 g**, marge **0,69 g**, fourchette
**[12,47 ; 13,86]**. On écrit : « 13,2 g ± 0,7 g ».

**Le piège (erreur faite et corrigée en séance 2) :** « avec 4 fois plus de produits, la marge est plus
grande » → **faux, c'est l'inverse.** Avec 4 fois plus de produits, √n est 2 fois plus grand, donc l'erreur
type est 2 fois plus **petite**, et la marge aussi. Plus on a de produits, plus la moyenne est précise.

| n | √n | erreur type (si écart type = 10) | marge |
|---|---|---|---|
| 25 | 5 | 10 / 5 = 2 | 1,96 × 2 = 3,92 |
| 100 | 10 | 10 / 10 = 1 | 1,96 × 1 = 1,96 |
| 400 | 20 | 10 / 20 = 0,5 | 1,96 × 0,5 = 0,98 |

### Comparer deux groupes : l'écart est-il « net » ?
Les bio ont en moyenne 13,17 g de sucres, les non bio 18,59 g. L'**écart** bio − non bio = 13,17 − 18,59 =
**−5,42 g**. **Un écart négatif veut dire que les bio en ont MOINS** (on fait toujours bio moins non bio).

Mais cet écart vient-il vraiment d'une différence, ou du hasard de l'échantillon ? L'écart a sa propre marge :

> **erreur type de l'écart = √(et_bio² + et_non_bio²)**

On n'additionne pas les deux erreurs types directement : on additionne leurs **carrés**, puis on prend la
racine. (C'est la règle pour l'incertitude d'une différence entre deux groupes indépendants. Le résultat est
plus grand que chacune des deux erreurs, mais plus petit que leur somme.)

Ensuite : marge de l'écart = 1,96 × erreur type de l'écart, et la fourchette de l'écart.

**La règle de décision :**
- si la fourchette de l'écart **contient 0**, l'écart pourrait être nul : **on ne peut pas conclure**
  (`difference_nette = False`) ;
- si elle **ne contient pas 0**, l'écart est **net** (`difference_nette = True`).

**Deux exemples réels :**

| Nutriment | Bio | Non bio | Écart | Marge de l'écart | Fourchette | Net ? |
|---|---|---|---|---|---|---|
| Sucres | 13,17 g | 18,59 g | −5,42 g | 1,07 g | [−6,49 ; −4,35] | **oui** : 0 n'est pas dedans |
| Lipides | 10,69 g | 10,48 g | +0,21 g | 0,84 g | [−0,63 ; 1,05] | **non** : 0 est dedans |

Pour les lipides, la fourchette va du négatif (les bio en ont moins) au positif (les bio en ont plus) : on ne
sait même pas dans quel sens va la différence. On dit : « l'écart peut venir du hasard ».

**Attention :** on ne soustrait pas les fourchettes des deux groupes l'une de l'autre. On calcule la fourchette
**de l'écart**, avec sa propre marge.

---

## 3. Le code, morceau par morceau

### Morceau 1 : l’en-tête et les petites fonctions d’aide (lignes 1 à 43)

Code de `nutri/tools.py`, lignes 1 à 43 (le numéro de ligne est à gauche de la barre) :

```python
  1 | """Les outils que le modèle peut appeler. Ce sont eux, et eux seuls, qui calculent les chiffres.
  2 | 
  3 | Chaque fonction prend le tableau propre en premier argument (pratique pour les tests),
  4 | vérifie ses paramètres, et renvoie un dictionnaire de résultats arrondis à 2 décimales.
  5 | 
  6 | Brique 8 : chaque moyenne est donnée avec sa marge d'erreur à 95 %, et la comparaison bio /
  7 | non bio dit si l'écart est net ou s'il peut venir du hasard de l'échantillon.
  8 | """
  9 | import math
 10 | 
 11 | import pandas as pd
 12 | 
 13 | NUTRIMENTS = ["energie_kcal", "glucides", "sucres", "lipides", "ags", "fibres", "proteines", "sel"]
 14 | GROUPES = ["bio", "nutriscore"]
 15 | Z_95 = 1.96   # pour une marge à 95 % (loi normale : 95 % des cas à moins de 1,96 erreur type)
 16 | 
 17 | 
 18 | def _verifier_nutriment(nutriment: str) -> None:
 19 |     if nutriment not in NUTRIMENTS:
 20 |         raise ValueError(f"nutriment inconnu : {nutriment!r}. Choix possibles : {NUTRIMENTS}")
 21 | 
 22 | 
 23 | def _booleen(x) -> bool:
 24 |     """Le modèle envoie parfois "false" en texte : bool("false") vaudrait True."""
 25 |     if isinstance(x, str):
 26 |         if x.strip().lower() in ("true", "vrai", "1", "oui"):
 27 |             return True
 28 |         if x.strip().lower() in ("false", "faux", "0", "non"):
 29 |             return False
 30 |         raise ValueError(f"bio doit être true ou false, pas {x!r}")
 31 |     return bool(x)
 32 | 
 33 | 
 34 | def _filtrer(df: pd.DataFrame, bio=None, nutriscore=None) -> pd.DataFrame:
 35 |     if bio is not None:
 36 |         df = df[df["bio"] == _booleen(bio)]
 37 |     if nutriscore is not None:
 38 |         df = df[df["nutriscore"] == str(nutriscore).lower()]
 39 |     return df
 40 | 
 41 | 
 42 | def _arrondi(x):
 43 |     return None if x is None or pd.isna(x) else round(float(x), 2)
```

- **Ligne 14 : `NUTRIMENTS`**, les 8 nutriments qu'on accepte. Tout autre nom est refusé.
- **Ligne 15 : `GROUPES`**, les deux façons de faire des groupes : par bio, ou par Nutri-Score.
- **Ligne 16 : `Z_95 = 1.96`**, le nombre de la marge à 95 %.
- **Lignes 19 à 21 : `_verifier_nutriment`.** Si le nutriment demandé n'existe pas, on **lève une erreur**
  (`raise ValueError`) avec la liste des choix possibles. Cette erreur sera renvoyée à Qwen, qui pourra
  corriger son appel. Le `!r` dans le f-string affiche le texte avec ses guillemets : `'vitamine_c'`.
  **Le tiret bas au début du nom** (`_verifier_nutriment`) est une convention : « fonction interne, pas un
  outil pour le modèle ».
- **Lignes 24 à 32 : `_booleen`.** Un petit modèle envoie parfois `"false"` **en texte** au lieu de `false`.
  Or, en Python, `bool("false")` vaut **True** (tout texte non vide est « vrai ») : le filtre serait inversé !
  Cette fonction lit le texte : « true », « vrai », « 1 », « oui » → True ; « false », « faux », « 0 »,
  « non » → False ; autre chose → erreur.
- **Lignes 35 à 40 : `_filtrer`**, la technique du masque :
  - `df["bio"] == _booleen(bio)` est un masque (vrai pour les produits bio si `bio=True`) ;
  - `df[masque]` garde les lignes où le masque est vrai ;
  - si `bio` vaut `None` (pas de filtre), on ne touche à rien. Même chose pour le Nutri-Score, mis en
    minuscules (`"A"` → `"a"`).
- **Lignes 42 et 43 : `_arrondi`**, arrondit à 2 décimales, ou renvoie `None` si la valeur est vide.
  `float(x)` transforme les nombres de pandas en nombres Python ordinaires (sinon l'envoi en JSON plante).

---

### Morceau 2 : l'erreur type et l'intervalle (lignes 46 à 60)

Code de `nutri/tools.py`, lignes 46 à 60 (le numéro de ligne est à gauche de la barre) :

```python
 46 | def _erreur_type(valeurs):
 47 |     """Précision d'une moyenne : écart-type / racine de n.
 48 |     Plus il y a de produits, plus elle est petite. None s'il y a moins de 2 valeurs
 49 |     (avec une seule valeur, on ne peut pas mesurer la dispersion)."""
 50 |     if len(valeurs) < 2:
 51 |         return None
 52 |     return valeurs.std() / math.sqrt(len(valeurs))
 53 | 
 54 | 
 55 | def _intervalle(centre, erreur_type):
 56 |     """Intervalle de confiance à 95 % : centre ± 1,96 erreur type. None si on ne peut pas le calculer."""
 57 |     if centre is None or erreur_type is None:
 58 |         return None, None
 59 |     marge = Z_95 * erreur_type
 60 |     return marge, [centre - marge, centre + marge]
```

- **Lignes 50 et 51 :** avec moins de 2 valeurs, on ne peut pas mesurer la dispersion (un seul produit n'a pas
  d'écart type) : on renvoie `None`.
- **Ligne 52 :** `valeurs.std()` = écart type, `math.sqrt(len(valeurs))` = √n. Erreur type = écart type / √n.
- **Lignes 57 et 58 :** si la moyenne ou l'erreur type manque, pas d'intervalle : on renvoie `None, None`
  (deux valeurs, car la fonction en renvoie toujours deux).
- **Ligne 59 :** marge = 1,96 × erreur type.
- **Ligne 60 :** on renvoie la marge **et** la fourchette `[centre − marge, centre + marge]`.

**Exemple fait à la main (c'est un vrai test) :** deux produits bio avec 10 g et 20 g de sucres.
- moyenne = 15 ;
- écart type = 7,07 ;
- erreur type = 7,07 / √2 = 7,07 / 1,414 = 5 ;
- marge = 1,96 × 5 = 9,8 ;
- fourchette = [15 − 9,8 ; 15 + 9,8] = [5,2 ; 24,8].

---

### Morceau 3 : `decrire` (lignes 63 à 79)

Code de `nutri/tools.py`, lignes 63 à 79 (le numéro de ligne est à gauche de la barre) :

```python
 63 | def decrire(df, nutriment, bio=None, nutriscore=None) -> dict:
 64 |     """Moyenne (avec sa marge d'erreur), médiane, min et max d'un nutriment (pour 100 g)."""
 65 |     _verifier_nutriment(nutriment)
 66 |     valeurs = _filtrer(df, bio, nutriscore)[nutriment].dropna()
 67 |     moyenne = valeurs.mean() if len(valeurs) > 0 else None   # cas limite : aucune valeur
 68 |     marge, intervalle = _intervalle(moyenne, _erreur_type(valeurs))
 69 |     return {
 70 |         "nutriment": nutriment,
 71 |         "filtres": {"bio": bio, "nutriscore": nutriscore},
 72 |         "n": int(len(valeurs)),
 73 |         "moyenne": _arrondi(moyenne),
 74 |         "marge_95": _arrondi(marge),
 75 |         "intervalle_95": None if intervalle is None else [_arrondi(b) for b in intervalle],
 76 |         "mediane": _arrondi(valeurs.median()),
 77 |         "min": _arrondi(valeurs.min()),
 78 |         "max": _arrondi(valeurs.max()),
 79 |     }
```

- **Ligne 65 :** on vérifie que le nutriment existe.
- **Ligne 66 :** on filtre (bio, Nutri-Score), on prend la colonne du nutriment, et `dropna()` enlève les cases
  vides. Important : un produit sans valeur de sel ne doit pas compter dans la moyenne du sel.
- **Ligne 67 :** la moyenne, sauf s'il n'y a aucune valeur (cas limite : `None`).
- **Ligne 68 :** on calcule l'erreur type, puis la marge et la fourchette.
- **Lignes 69 à 79 :** on renvoie un **dictionnaire** avec tout. `n` (le nombre de produits) est toujours
  donné : une moyenne sur 3 produits ne vaut pas une moyenne sur 500.

**Vrai résultat :** `decrire(df, "sucres", bio=True)` renvoie

```python
{"nutriment": "sucres", "filtres": {"bio": True, "nutriscore": None},
 "n": 543, "moyenne": 13.17, "marge_95": 0.69, "intervalle_95": [12.47, 13.86],
 "mediane": 14.0, "min": 0.5, "max": 37.7}
```

C'est exactement ce dictionnaire que Qwen reçoit, et c'est avec ses nombres qu'il doit écrire sa réponse.

---

### Morceau 4 : `comparer` (lignes 82 à 125)

Code de `nutri/tools.py`, lignes 82 à 125 (le numéro de ligne est à gauche de la barre) :

```python
 82 | def comparer(df, nutriment, groupe) -> dict:
 83 |     """Moyenne d'un nutriment dans chaque groupe (bio / non bio, ou chaque Nutri-Score),
 84 |     avec la marge d'erreur de chaque moyenne."""
 85 |     _verifier_nutriment(nutriment)
 86 |     if groupe not in GROUPES:
 87 |         raise ValueError(f"groupe inconnu : {groupe!r}. Choix possibles : {GROUPES}")
 88 |     connus = df.dropna(subset=[nutriment])
 89 |     resultats = []
 90 |     erreurs_types = {}          # groupe -> erreur type, pour calculer la marge de l'écart plus bas
 91 |     for valeur, sous_df in connus.dropna(subset=[groupe]).groupby(groupe):
 92 |         moyenne = sous_df[nutriment].mean()
 93 |         et = _erreur_type(sous_df[nutriment])
 94 |         marge, _ = _intervalle(moyenne, et)
 95 |         resultats.append({"groupe": str(valeur), "n": int(len(sous_df)),
 96 |                           "moyenne": _arrondi(moyenne), "marge_95": _arrondi(marge)})
 97 |         erreurs_types[str(valeur)] = et
 98 |     sortie = {"nutriment": nutriment, "groupe": groupe, "groupes": resultats}
 99 | 
100 |     if groupe == "nutriscore":
101 |         # produits sans Nutri-Score (données incomplètes ou non concernés) : écartés de ce calcul
102 |         sortie["sans_nutriscore"] = int(connus["nutriscore"].isna().sum())
103 | 
104 |     if groupe == "bio":
105 |         # on retrouve la moyenne des bio ("True") et des non bio ("False")
106 |         moy_bio, moy_non_bio = None, None
107 |         for r in resultats:
108 |             if r["groupe"] == "True":
109 |                 moy_bio = r["moyenne"]
110 |             if r["groupe"] == "False":
111 |                 moy_non_bio = r["moyenne"]
112 |         if moy_bio is not None and moy_non_bio is not None:
113 |             ecart = moy_bio - moy_non_bio
114 |             sortie["ecart_bio_moins_non_bio"] = _arrondi(ecart)
115 |             # erreur type d'un écart entre deux groupes indépendants : racine(et1² + et2²)
116 |             et_bio, et_non_bio = erreurs_types.get("True"), erreurs_types.get("False")
117 |             if et_bio is not None and et_non_bio is not None:
118 |                 marge, intervalle = _intervalle(ecart, math.sqrt(et_bio ** 2 + et_non_bio ** 2))
119 |                 sortie["marge_95_ecart"] = _arrondi(marge)
120 |                 sortie["intervalle_95_ecart"] = [_arrondi(b) for b in intervalle]
121 |                 # si 0 est dans l'intervalle, l'écart peut venir du hasard : pas de conclusion
122 |                 sortie["difference_nette"] = not (intervalle[0] <= 0 <= intervalle[1])
123 |             else:
124 |                 sortie["difference_nette"] = None   # trop peu de produits pour conclure
125 |     return sortie
```

- **Lignes 86 et 87 :** le groupe doit être `"bio"` ou `"nutriscore"`.
- **Ligne 88 :** on garde les produits qui ont une valeur pour ce nutriment.
- **Ligne 91 : `groupby(groupe)`**, la fonction clé. Elle découpe le tableau en sous-tableaux, un par valeur du
  groupe. Pour `"bio"` : un sous-tableau des non bio (`False`) et un des bio (`True`). La boucle donne à chaque
  tour la valeur du groupe (`valeur`) et son sous-tableau (`sous_df`). `dropna(subset=[groupe])` écarte
  d'abord les produits sans Nutri-Score quand on groupe par Nutri-Score.
- **Lignes 92 à 97 :** pour chaque groupe : la moyenne, l'erreur type, la marge. On range le résultat dans la
  liste `resultats`, et l'erreur type dans le dictionnaire `erreurs_types` (on en aura besoin pour l'écart).
  Le `_` à la ligne 94 veut dire « je n'ai pas besoin de cette deuxième valeur » (la fourchette).
- **Lignes 100 à 102 :** pour le Nutri-Score, on compte les produits **sans** Nutri-Score (25), pour dire
  combien ont été écartés.
- **Lignes 104 à 124 : l'écart, seulement pour bio / non bio.**
  - lignes 106 à 111 : on retrouve les deux moyennes dans la liste (les groupes sont écrits en texte, `"True"`
    et `"False"`) ;
  - ligne 113 : écart = bio − non bio ;
  - ligne 118 : la marge et la fourchette de l'écart, avec l'erreur type √(et_bio² + et_non_bio²).
    `** 2` veut dire « au carré » ;
  - ligne 122 : **`difference_nette`**. `intervalle[0] <= 0 <= intervalle[1]` est vrai si 0 est **dans** la
    fourchette. Le `not` inverse : la différence est nette si 0 n'est **pas** dedans ;
  - ligne 124 : s'il manque une erreur type (un groupe avec un seul produit), `None` : on ne peut rien dire.

**Vrai résultat :** `comparer(df, "sucres", "bio")` renvoie

```python
{"nutriment": "sucres", "groupe": "bio",
 "groupes": [{"groupe": "False", "n": 410, "moyenne": 18.59, "marge_95": 0.82},
             {"groupe": "True",  "n": 543, "moyenne": 13.17, "marge_95": 0.69}],
 "ecart_bio_moins_non_bio": -5.42, "marge_95_ecart": 1.07,
 "intervalle_95_ecart": [-6.49, -4.35], "difference_nette": True}
```

**Et par Nutri-Score :** `comparer(df, "sucres", "nutriscore")` donne A : 6,3 g (270 produits), B : 12,82 g,
C : 18,03 g, D : 23,14 g, E : 26,33 g (29 produits, marge 2,57 g : large, car peu de produits), et
`"sans_nutriscore": 25`.

---

### Morceau 5 : `classement_marques` (lignes 128 à 148)

Code de `nutri/tools.py`, lignes 128 à 148 (le numéro de ligne est à gauche de la barre) :

```python
128 | def classement_marques(df, nutriment, n=5, ordre="croissant", min_produits=5) -> dict:
129 |     """Les n marques avec la moyenne la plus basse (ou haute) d'un nutriment.
130 |     On ignore les marques avec moins de min_produits produits (une moyenne sur 1 produit ne dit rien)."""
131 |     _verifier_nutriment(nutriment)
132 |     if ordre not in ("croissant", "decroissant"):
133 |         raise ValueError("ordre doit être 'croissant' ou 'decroissant'")
134 |     # 1. garder les produits qui ont une marque ET une valeur pour ce nutriment
135 |     connus = df.dropna(subset=["marque", nutriment])
136 |     # 2. par marque : nombre de produits (count) et moyenne (mean)
137 |     stats = connus.groupby("marque")[nutriment].agg(["count", "mean"])
138 |     # 3. écarter les petites marques
139 |     stats = stats[stats["count"] >= int(min_produits)]
140 |     # 4. trier et garder les n premières
141 |     stats = stats.sort_values("mean", ascending=(ordre == "croissant")).head(int(n))
142 | 
143 |     marques = []
144 |     for nom_marque, ligne in stats.iterrows():
145 |         marques.append({"marque": nom_marque, "n_produits": int(ligne["count"]),
146 |                         "moyenne": _arrondi(ligne["mean"])})
147 |     return {"nutriment": nutriment, "ordre": ordre, "min_produits": int(min_produits),
148 |             "marques": marques}
```

- **Ligne 135 :** on garde les produits qui ont une marque **et** une valeur.
- **Ligne 137 :** `groupby("marque")` puis `agg(["count", "mean"])` : pour chaque marque, le nombre de produits
  et la moyenne. Le résultat est un petit tableau : une ligne par marque, deux colonnes.
- **Ligne 139 :** on écarte les marques de moins de `min_produits` produits (5 par défaut). Une moyenne sur un
  seul produit ne dit rien de la marque.
- **Ligne 141 :** on trie. `ascending=(ordre == "croissant")` vaut `True` pour l'ordre croissant (du plus petit
  au plus grand). `head(n)` garde les `n` premières.
- **Lignes 143 à 146 :** `iterrows()` parcourt le tableau ligne par ligne et donne le nom de la marque et ses
  valeurs. On fabrique une liste de petits dictionnaires.

**Vrai résultat (ordre croissant, sucres) :** jardin bio etic 6,5 g (5 produits), celnat 7,4 g (21), markal
8,41 g (8), joody 9,09 g (7), happy bio 9,85 g (13).

**Un vrai échec lié à cet outil (évaluation, brique 9) :** à la question « quelle marque est la moins
sucrée ? », Qwen a demandé l'ordre **décroissant**, puis il a lu la première marque (la plus sucrée) comme la
moins sucrée. L'outil a fait un calcul juste, c'est le modèle qui l'a mal lu.

---

### Morceau 6 : `compter`, et la liste des outils pour Qwen (lignes 151 à 185)

Code de `nutri/tools.py`, lignes 151 à 185 (le numéro de ligne est à gauche de la barre) :

```python
151 | def compter(df, bio=None, nutriscore=None) -> dict:
152 |     """Nombre de produits, avec filtres facultatifs."""
153 |     return {"filtres": {"bio": bio, "nutriscore": nutriscore}, "n": int(len(_filtrer(df, bio, nutriscore)))}
154 | 
155 | 
156 | FONCTIONS = {"decrire": decrire, "comparer": comparer,
157 |              "classement_marques": classement_marques, "compter": compter}
158 | 
159 | # Description des outils au format attendu par Ollama (JSON Schema)
160 | _P_NUTRIMENT = {"type": "string", "enum": NUTRIMENTS, "description": "nutriment, pour 100 g"}
161 | _P_BIO = {"type": "boolean", "description": "true = seulement bio, false = seulement non bio"}
162 | _P_NS = {"type": "string", "enum": list("abcde"), "description": "lettre du Nutri-Score"}
163 | 
164 | 
165 | def _schema(nom, description, proprietes, requis):
166 |     return {"type": "function", "function": {
167 |         "name": nom, "description": description,
168 |         "parameters": {"type": "object", "properties": proprietes, "required": requis}}}
169 | 
170 | 
171 | SCHEMAS = [
172 |     _schema("decrire", "Moyenne (avec marge d'erreur à 95 %), médiane, min, max d'un nutriment "
173 |             "des céréales du petit-déjeuner.",
174 |             {"nutriment": _P_NUTRIMENT, "bio": _P_BIO, "nutriscore": _P_NS}, ["nutriment"]),
175 |     _schema("comparer", "Moyenne d'un nutriment par groupe (bio ou nutriscore), avec marges d'erreur. "
176 |             "Pour bio : écart bio - non bio et difference_nette (true = écart net, false = peut venir du hasard).",
177 |             {"nutriment": _P_NUTRIMENT, "groupe": {"type": "string", "enum": GROUPES}},
178 |             ["nutriment", "groupe"]),
179 |     _schema("classement_marques", "Classement des marques selon la moyenne d'un nutriment.",
180 |             {"nutriment": _P_NUTRIMENT, "n": {"type": "integer"},
181 |              "ordre": {"type": "string", "enum": ["croissant", "decroissant"]},
182 |              "min_produits": {"type": "integer"}}, ["nutriment"]),
183 |     _schema("compter", "Nombre de produits, avec filtres facultatifs.",
184 |             {"bio": _P_BIO, "nutriscore": _P_NS}, []),
185 | ]
```

- **Lignes 151 à 153 : `compter`**, le nombre de lignes du tableau filtré. Exemple : `compter(df, nutriscore="a")`
  → `{"n": 270}`.
- **Lignes 156 et 157 : `FONCTIONS`**, un dictionnaire nom → fonction. Quand Qwen demande `"decrire"`,
  `agent.py` trouve ici la vraie fonction à exécuter. Une fonction Python peut être rangée dans un dictionnaire
  comme n'importe quelle valeur. **Seules ces 4 fonctions peuvent être lancées** par le modèle.
- **Lignes 160 à 185 : `SCHEMAS`**, la description des outils **pour Qwen**, au format JSON Schema (le format
  attendu par Ollama). Pour chaque outil : son nom, une phrase qui dit à quoi il sert, ses paramètres avec leur
  type (`"string"` = texte, `"boolean"` = vrai / faux, `"integer"` = entier) et, avec `"enum"`, la liste des
  valeurs permises. `"required"` dit quels paramètres sont obligatoires.
  **Qwen ne voit pas le code Python** : il ne voit que ces descriptions. C'est grâce à elles qu'il sait quel
  outil choisir et quoi lui envoyer.
- **Lignes 165 à 168 : `_schema`**, une petite fonction qui fabrique la description d'un outil, pour ne pas
  répéter quatre fois la même structure.

---

## 4. Le trajet complet, sur un exemple

Question : « Les céréales bio contiennent-elles moins de sucre ? »
1. Qwen lit les `SCHEMAS` et choisit `comparer` avec `{"nutriment": "sucres", "groupe": "bio"}`.
2. `agent.py` trouve `comparer` dans `FONCTIONS` et l'exécute sur les 953 céréales.
3. `comparer` découpe en bio / non bio, calcule les moyennes, les marges, l'écart −5,42 ± 1,07 et
   `difference_nette = True`.
4. Le dictionnaire est renvoyé à Qwen, qui écrit : « Oui, les céréales bio contiennent en moyenne moins de sucre
   (13,2 g contre 18,6 g pour 100 g)… »

---

## 5. Les pièges et les erreurs fréquentes

- **Plus de produits → marge plus PETITE**, pas plus grande (√n au dénominateur).
- **Un écart négatif** veut dire que les bio en ont moins (on calcule toujours bio − non bio).
- **On ne soustrait pas les fourchettes** : l'écart a sa propre marge, √(et₁² + et₂²) × 1,96.
- **`bool("false")` vaut True** en Python : d'où `_booleen`.
- **Une marge ne corrige pas tout :** elle mesure le hasard de l'échantillon, pas les erreurs de saisie des
  fiches, ni le biais de l'échantillon (57 % de bio, alors qu'en rayon le bio est minoritaire).
- **Un écart net n'est pas une cause :** les bio ne sont pas moins sucrées *parce qu'*elles sont bio (ce sont
  peut-être d'autres types de produits : plus de mueslis, moins de céréales pour enfants).

---

## 6. Questions d'examinateur, avec leurs réponses

**Q1. Pourquoi les calculs sont-ils dans des outils et pas faits par le modèle ?** Un petit modèle se trompe
et invente. Python calcule juste, et on peut vérifier que chaque chiffre vient d'un outil.

**Q2. Comment Qwen sait-il quels outils existent ?** Par les `SCHEMAS` : nom, description, paramètres et
valeurs permises. Il ne voit pas le code.

**Q3. Que se passe-t-il si Qwen demande « vitamine_c » ?** `_verifier_nutriment` lève une ValueError, l'agent
renvoie l'erreur à Qwen avec la liste des choix, et Qwen peut corriger.

**Q4. Qu'est-ce que l'erreur type ? La marge ?** L'erreur type = écart type / √n : la précision de la moyenne.
La marge = 1,96 × erreur type : la moyenne est « ± marge » avec 95 % de confiance.

**Q5. Si on a 4 fois plus de produits, que devient la marge ?** Elle est divisée par 2 (√4 = 2).

**Q6. Comment savez-vous si un écart est net ?** On calcule la fourchette de l'écart. Si elle contient 0,
l'écart peut venir du hasard. Sinon, il est net. Sucres : [−6,49 ; −4,35], net. Lipides : [−0,63 ; 1,05], pas net.

**Q7. Pourquoi √(et₁² + et₂²) ?** C'est l'erreur type d'une différence entre deux groupes indépendants : les
deux incertitudes s'ajoutent, mais par leurs carrés.

**Q8. Pourquoi `min_produits=5` dans le classement ?** Une moyenne sur un seul produit ne représente pas la marque.

**Q9. Pourquoi `df` est-il le premier argument de chaque outil ?** Pour que les tests puissent donner un petit
tableau inventé dont on connaît les réponses à la main.

**Q10. Que veut dire `difference_nette = None` ?** Un des groupes a moins de 2 valeurs : on ne peut pas calculer
de marge, donc on ne peut rien conclure.

---

## 7. Résumé en 5 phrases

1. `tools.py` contient les 4 seuls outils qui calculent des chiffres : `decrire`, `comparer`, `classement_marques`, `compter`.
2. Chaque moyenne est donnée avec sa marge d'erreur à 95 % : 1,96 × écart type / √n.
3. `comparer` calcule l'écart bio − non bio, sa marge √(et₁² + et₂²) × 1,96, et dit si l'écart est net (0 hors de la fourchette).
4. Les erreurs (nutriment inconnu, mauvais groupe) sont levées avec un message clair, renvoyé au modèle.
5. Qwen ne voit que les `SCHEMAS`, la description des outils, et `FONCTIONS` relie chaque nom à sa vraie fonction.
