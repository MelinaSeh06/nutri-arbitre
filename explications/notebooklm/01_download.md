# Nutri-Arbitre — Fichier 1 : `download.py`, télécharger les données

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

`download.py` est la **première étape** du trajet. Il va chercher les céréales du petit-déjeuner vendues en
France sur le site Open Food Facts, et il les enregistre dans un fichier sur l'ordinateur :
`data/raw_cereales.json` (« raw » veut dire « brut » : les données telles qu'elles arrivent, pas encore
nettoyées).

- **Ce qui entre :** rien. On lance le fichier, il va chercher les données sur Internet.
- **Ce qui sort :** le fichier `data/raw_cereales.json`, une longue liste de produits.
- **Comment on le lance :** dans le terminal, `python -m nutri.download --pages 20`.

Dans notre projet, il a téléchargé **1000 produits** (10 pages de 100 produits). À la page 11, le serveur
d'Open Food Facts a répondu « 503 » (serveur surchargé) même après plusieurs essais. On a décidé de garder ces
1000 produits, pour que les réponses de l'évaluation restent fixes.

---

## 2. Les notions à connaître avant de lire le code

### Une API
Une **API** est une « porte d'entrée » d'un site web prévue pour les programmes, et non pour les humains. Au
lieu d'afficher une page web avec des images, elle renvoie des données brutes. Ici, l'adresse
`https://world.openfoodfacts.org/api/v2/search` est l'API de recherche d'Open Food Facts. On lui envoie une
question (« les céréales vendues en France, page 1 ») et elle renvoie la liste des produits.

### Le format JSON
**JSON** est un format de texte pour écrire des données structurées. Il ressemble beaucoup aux dictionnaires
et aux listes de Python. Voici le début d'un vrai produit reçu (raccourci) :

```json
{"brands": "PEPSICO FRANCE",
 "code": "3168930010265",
 "labels_tags": ["en:no-palm-oil", "en:nutriscore-grade-a"],
 "nutriments": {"carbohydrates_100g": 57, "energy-kcal_100g": 462, "fat_100g": 19}}
```

On reconnaît un **dictionnaire** (des paires « clé : valeur » entre accolades) qui contient une **liste**
(entre crochets) et un autre dictionnaire (`nutriments`). C'est le produit « cruesly mélange de noix ».

### Une requête HTTP
Quand un navigateur ouvre une page, il envoie une **requête** au serveur. La bibliothèque Python `requests`
fait la même chose depuis un programme. `requests.get(adresse)` demande la page, et le serveur répond avec un
**code** : `200` veut dire « tout va bien », `503` veut dire « serveur surchargé, réessayez plus tard ».

### Les paramètres d'une recherche
Quand on cherche sur un site, l'adresse contient souvent des réglages après un `?`, par exemple
`...search?page=2&page_size=100`. En Python, on les écrit dans un dictionnaire (`params`), et `requests` les
ajoute à l'adresse tout seul.

---

## 3. Le code, morceau par morceau

### Morceau 1 : les imports et les réglages (lignes 1 à 18)

Code de `nutri/download.py`, lignes 1 à 18 (le numéro de ligne est à gauche de la barre) :

```python
  1 | """Télécharge les céréales du petit-déjeuner vendues en France depuis Open Food Facts.
  2 | 
  3 | Usage : python -m nutri.download --pages 20
  4 | 
  5 | Open Food Facts demande un User-Agent qui identifie le projet
  6 | et au plus ~10 requêtes de recherche par minute : on attend donc 7 s entre deux pages.
  7 | """
  8 | import argparse
  9 | import json
 10 | import time
 11 | from pathlib import Path
 12 | 
 13 | import requests
 14 | 
 15 | URL = "https://world.openfoodfacts.org/api/v2/search"
 16 | USER_AGENT = "nutri-arbitre/0.1 (projet etudiant Coding for AI)"
 17 | FIELDS = "code,product_name,brands,labels_tags,nutriscore_grade,nutriments"
 18 | SORTIE = Path("data/raw_cereales.json")
```

**Ligne par ligne :**

- **Lignes 1 à 7 : la docstring.** Un texte entre triples guillemets au début du fichier. Python ne l'exécute
  pas : c'est une explication pour les humains. Elle rappelle deux règles d'Open Food Facts : s'identifier
  avec un « User-Agent », et ne pas faire plus d'environ 10 recherches par minute.
- **Lignes 8 à 11 : les imports de la bibliothèque standard** (déjà incluse dans Python).
  `argparse` lit ce qu'on tape dans le terminal, `json` lit et écrit du JSON, `time` sert à attendre,
  `Path` représente un chemin de fichier.
- **Ligne 13 : `import requests`**, une bibliothèque installée en plus (elle est dans `requirements.txt`).
  Elle envoie les requêtes sur Internet.
- **Ligne 15 : `URL`**, l'adresse de l'API de recherche.
- **Ligne 16 : `USER_AGENT`**, le nom de notre programme, envoyé avec chaque requête. C'est une politesse
  demandée par Open Food Facts : ils savent qui leur envoie des requêtes.
- **Ligne 17 : `FIELDS`**, la liste des champs qu'on veut recevoir. Un produit d'Open Food Facts a des
  centaines de champs. On n'en demande que 6 : le code-barres, le nom, la marque, les labels, le Nutri-Score
  et les nutriments. La réponse est plus légère et plus rapide.
- **Ligne 18 : `SORTIE`**, le fichier où on enregistre le résultat.

**Une convention :** les noms écrits **EN MAJUSCULES** sont des **constantes**, des réglages qui ne changent
pas pendant l'exécution. Ce n'est pas une obligation de Python, c'est une habitude des programmeurs pour qu'on
les repère tout de suite.

**À dire à l'oral :** « En haut du fichier, je regroupe les réglages : l'adresse de l'API, notre nom, et les
champs demandés. Si je veux changer un réglage, je le change à un seul endroit. »

---

### Morceau 2 : télécharger une page (lignes 21 à 40)

Code de `nutri/download.py`, lignes 21 à 40 (le numéro de ligne est à gauche de la barre) :

```python
 21 | def telecharger_page(page: int, page_size: int = 100) -> list[dict]:
 22 |     """Renvoie la liste des produits d'une page de résultats."""
 23 |     params = {
 24 |         "categories_tags_en": "breakfast-cereals",
 25 |         "countries_tags_en": "france",
 26 |         "fields": FIELDS,
 27 |         "page": page,
 28 |         "page_size": page_size,
 29 |     }
 30 |     # le serveur renvoie parfois 503 (surcharge) : on réessaie en attendant de plus en plus
 31 |     for essai in range(5):
 32 |         try:
 33 |             r = requests.get(URL, params=params, headers={"User-Agent": USER_AGENT}, timeout=60)
 34 |             r.raise_for_status()
 35 |             return r.json().get("products", [])
 36 |         except requests.RequestException as e:
 37 |             attente = 15 * (essai + 1)
 38 |             print(f"page {page} : erreur ({e.__class__.__name__}), nouvel essai dans {attente} s")
 39 |             time.sleep(attente)
 40 |     raise RuntimeError(f"page {page} : échec après 5 essais")
```

**Ligne par ligne :**

- **Ligne 21 : la définition de la fonction.** `page: int` veut dire « page est un nombre entier ».
  `page_size: int = 100` : si on ne précise pas la taille, elle vaut 100 (valeur par défaut).
  `-> list[dict]` annonce ce que la fonction renvoie : une liste de dictionnaires (un dictionnaire par produit).
  Ces indications s'appellent des **annotations de type** : elles aident à lire le code, Python ne les vérifie pas.
- **Lignes 23 à 29 : les paramètres de la recherche**, dans un dictionnaire :
  - `"categories_tags_en": "breakfast-cereals"` : seulement la catégorie « céréales du petit-déjeuner » ;
  - `"countries_tags_en": "france"` : seulement les produits vendus en France ;
  - `"fields": FIELDS` : seulement les 6 champs utiles ;
  - `"page": page` et `"page_size": page_size` : quelle page, et combien de produits par page.
- **Ligne 31 : `for essai in range(5):`**, une boucle qui fait au plus 5 tentatives. `range(5)` donne
  0, 1, 2, 3, 4.
- **Ligne 32 : `try:`**, « essaie ce bloc ; s'il y a une erreur, ne plante pas, va dans le `except` ».
- **Ligne 33 : la requête.** `requests.get(...)` envoie la demande avec les paramètres et le User-Agent.
  `timeout=60` : si le serveur ne répond pas en 60 secondes, on abandonne cette tentative.
- **Ligne 34 : `r.raise_for_status()`**, « si le code de réponse est une erreur (comme 503), lève une
  erreur ». Sans cette ligne, une réponse 503 passerait comme si tout allait bien.
- **Ligne 35 : on renvoie les produits.** `r.json()` transforme le texte JSON reçu en dictionnaire Python.
  `.get("products", [])` prend la valeur de la clé `"products"`, ou une liste vide si elle n'existe pas.
  Le `return` arrête la fonction : on ne fait pas les autres essais.
- **Ligne 36 : `except requests.RequestException as e:`**, on arrive ici si la requête a échoué (serveur
  surchargé, Internet coupé, délai dépassé). `e` contient l'erreur.
- **Ligne 37 : `attente = 15 * (essai + 1)`**, on attend de plus en plus longtemps : 15 s après le premier
  échec, puis 30 s, 45 s, 60 s, 75 s. C'est ce qu'on appelle un **backoff** (« recul progressif ») : on laisse
  au serveur le temps de se remettre.
- **Ligne 38 :** un message dans le terminal. `e.__class__.__name__` donne le nom du type d'erreur, par
  exemple `HTTPError`.
- **Ligne 39 : `time.sleep(attente)`**, le programme se met en pause pendant ce nombre de secondes.
- **Ligne 40 : `raise RuntimeError(...)`**, si on sort de la boucle, c'est que les 5 essais ont échoué. On
  arrête le programme avec un message clair.

**Exemple concret, ce qui s'est vraiment passé :**

```
page 11 : erreur (HTTPError), nouvel essai dans 15 s
page 11 : erreur (HTTPError), nouvel essai dans 30 s
...
```

Le serveur répondait 503. Après les essais, le programme s'est arrêté, mais les 10 premières pages étaient
déjà enregistrées (grâce au morceau 4).

**Le calcul de l'attente, pas à pas :**

| essai | calcul | attente |
|---|---|---|
| 0 | 15 × (0 + 1) | 15 s |
| 1 | 15 × (1 + 1) | 30 s |
| 2 | 15 × (2 + 1) | 45 s |
| 3 | 15 × (3 + 1) | 60 s |
| 4 | 15 × (4 + 1) | 75 s |

**À dire à l'oral :** « Le serveur d'Open Food Facts est parfois surchargé. Au lieu de planter à la première
erreur, la fonction réessaie jusqu'à 5 fois, en attendant de plus en plus longtemps. »

---

### Morceau 3 : enregistrer (lignes 43 à 45)

Code de `nutri/download.py`, lignes 43 à 45 (le numéro de ligne est à gauche de la barre) :

```python
 43 | def sauver(produits: list[dict]) -> None:
 44 |     SORTIE.parent.mkdir(exist_ok=True)
 45 |     SORTIE.write_text(json.dumps(produits, ensure_ascii=False), encoding="utf-8")
```

- **Ligne 44 : `SORTIE.parent.mkdir(exist_ok=True)`.** `SORTIE.parent` est le dossier qui contient le fichier,
  ici `data`. `mkdir` crée ce dossier. `exist_ok=True` : s'il existe déjà, ce n'est pas une erreur.
- **Ligne 45 :** `json.dumps(produits)` transforme la liste Python en texte JSON (« dumps » = « dump string »,
  « déverser en texte »). `ensure_ascii=False` garde les accents lisibles (« Céréales » au lieu de
  « C\u00e9r\u00e9ales »). `write_text(..., encoding="utf-8")` écrit le texte dans le fichier, avec
  l'encodage UTF-8 qui sait écrire tous les caractères.
- `-> None` : la fonction ne renvoie rien, elle fait seulement une action (écrire un fichier).

---

### Morceau 4 : le programme principal (lignes 48 à 58)

Code de `nutri/download.py`, lignes 48 à 58 (le numéro de ligne est à gauche de la barre) :

```python
 48 | def main(nb_pages: int) -> None:
 49 |     produits = []
 50 |     for page in range(1, nb_pages + 1):
 51 |         lot = telecharger_page(page)
 52 |         print(f"page {page} : {len(lot)} produits")
 53 |         if not lot:  # plus aucun produit : on s'arrête
 54 |             break
 55 |         produits.extend(lot)
 56 |         sauver(produits)  # on écrit après chaque page : une panne ne fait pas tout perdre
 57 |         time.sleep(7)     # respecter la limite de l'API
 58 |     print(f"{len(produits)} produits écrits dans {SORTIE}")
```

- **Ligne 49 :** une liste vide, qui va recevoir tous les produits.
- **Ligne 50 : `for page in range(1, nb_pages + 1):`**. Attention : `range(1, 21)` donne 1, 2, …, 20. Le
  deuxième nombre est **exclu**, d'où le `+ 1`. Les pages d'Open Food Facts commencent à 1, pas à 0.
- **Ligne 51 :** on télécharge une page avec la fonction du morceau 2. `lot` = les 100 produits de cette page.
- **Ligne 52 :** un message de suivi, par exemple `page 3 : 100 produits`.
- **Lignes 53 et 54 :** si la page est vide (`not lot` est vrai pour une liste vide), il n'y a plus de
  produits : `break` sort de la boucle.
- **Ligne 55 : `produits.extend(lot)`** ajoute **chaque** produit du lot à la liste. Différence importante :
  `append(lot)` ajouterait la liste entière comme **un seul** élément, et on aurait une liste de listes.
- **Ligne 56 : `sauver(produits)` après chaque page.** Si le programme plante à la page 11, les pages 1 à 10
  sont déjà écrites sur le disque. C'est exactement ce qui nous a sauvés.
- **Ligne 57 : `time.sleep(7)`**, 7 secondes de pause entre deux pages : environ 8 pages par minute, sous la
  limite d'environ 10 recherches par minute d'Open Food Facts.
- **Ligne 58 :** le bilan, par exemple `1000 produits écrits dans data/raw_cereales.json`.

**Exemple :** `extend` contre `append`

```python
produits = [1, 2]
produits.extend([3, 4])   # -> [1, 2, 3, 4]
produits.append([5, 6])   # -> [1, 2, 3, 4, [5, 6]]   (une liste DANS la liste)
```

---

### Morceau 5 : le lancement depuis le terminal (lignes 61 à 64)

Code de `nutri/download.py`, lignes 61 à 64 (le numéro de ligne est à gauche de la barre) :

```python
 61 | if __name__ == "__main__":
 62 |     parser = argparse.ArgumentParser()
 63 |     parser.add_argument("--pages", type=int, default=20)
 64 |     main(parser.parse_args().pages)
```

- **Ligne 61 : `if __name__ == "__main__":`**. Quand on lance le fichier directement
  (`python -m nutri.download`), Python donne à `__name__` la valeur `"__main__"`, et ce bloc s'exécute. Quand
  un autre fichier **importe** celui-ci, `__name__` vaut `"nutri.download"`, et le bloc ne s'exécute pas : on
  peut réutiliser les fonctions sans lancer le téléchargement.
- **Ligne 62 :** on crée le lecteur de la ligne de commande.
- **Ligne 63 :** on déclare l'option `--pages`, un nombre entier (`type=int`), qui vaut 20 si on ne l'écrit pas.
- **Ligne 64 :** `parser.parse_args()` lit ce qu'on a tapé, `.pages` prend la valeur de l'option, et on la
  donne à `main`. Avec `python -m nutri.download --pages 5`, on télécharge 5 pages.

---

## 4. Le trajet complet, de bout en bout

1. On tape `python -m nutri.download --pages 20`.
2. Le bloc `if __name__ == "__main__"` lit `--pages 20` et appelle `main(20)`.
3. `main` fait une boucle sur les pages 1 à 20. Pour chaque page :
   - `telecharger_page` envoie la requête (jusqu'à 5 essais en cas d'erreur) et renvoie 100 produits ;
   - les produits sont ajoutés à la liste, et la liste est enregistrée dans `data/raw_cereales.json` ;
   - on attend 7 secondes.
4. Dans notre cas : les pages 1 à 10 ont marché (1000 produits), la page 11 a échoué 5 fois, le programme
   s'est arrêté, mais les 1000 produits étaient déjà sur le disque.

---

## 5. Les pièges et les erreurs fréquentes

- **Confondre `extend` et `append`** (voir le morceau 4).
- **Oublier que `range(1, n + 1)` s'arrête avant `n + 1`.**
- **Penser que `try / except` « répare » l'erreur.** Non : il l'attrape pour qu'on décide quoi faire (ici,
  attendre et réessayer). Si tout échoue, on lève quand même une erreur à la ligne 40.
- **Pourquoi enregistrer après chaque page, et pas une seule fois à la fin ?** Parce qu'une panne au milieu
  ferait tout perdre. Cela coûte un peu de temps, mais protège le travail déjà fait.
- **Le fichier brut n'est pas dans le dépôt GitHub** (il est dans `.gitignore`) : il est gros, et on peut le
  retélécharger. Le fichier nettoyé, lui, est dans le dépôt, pour que les résultats restent les mêmes.

---

## 6. Questions d'examinateur, avec leurs réponses

**Q1. Que fait ce fichier, en une phrase ?**
Il télécharge les céréales du petit-déjeuner vendues en France depuis l'API d'Open Food Facts, page par page,
et les enregistre dans `data/raw_cereales.json`.

**Q2. Pourquoi un User-Agent ?**
Open Food Facts le demande pour savoir quel programme envoie les requêtes. C'est une règle d'usage de leur API.

**Q3. Pourquoi attendre 7 secondes entre deux pages ?**
Open Food Facts limite les recherches à environ 10 par minute. Avec 7 secondes, on en fait environ 8.

**Q4. Que se passe-t-il si le serveur répond 503 ?**
`raise_for_status` lève une erreur, le `except` l'attrape, on attend 15 s, puis 30 s, 45 s… et on réessaie,
jusqu'à 5 fois. Après 5 échecs, le programme s'arrête avec un message clair.

**Q5. Pourquoi `sauver` est-il appelé dans la boucle ?**
Pour qu'une panne ne fasse pas tout perdre. C'est ce qui s'est passé : la page 11 a échoué, mais les 1000
produits des pages 1 à 10 étaient déjà enregistrés.

**Q6. À quoi sert `FIELDS` ?**
À ne demander que les 6 champs utiles au lieu de centaines : la réponse est plus légère et plus rapide.

**Q7. Différence entre `extend` et `append` ?**
`extend` ajoute chaque élément d'une liste ; `append` ajoute un seul élément (ici, la liste entière).

**Q8. À quoi sert `if __name__ == "__main__":` ?**
Le bloc ne s'exécute que si on lance le fichier directement, pas quand un autre fichier l'importe.

**Q9. Pourquoi seulement 1000 produits ?**
La page 11 a échoué 5 fois (erreur 503). On a décidé de garder ces 1000 produits plutôt que de retélécharger :
les réponses de l'évaluation restent fixes. Le défaut : c'est un échantillon biaisé (les premiers produits
renvoyés, avec 57 % de bio), ce qui est écrit dans EVIDENCE.md.

---

## 7. Résumé en 5 phrases

1. `download.py` va chercher les céréales vendues en France sur l'API d'Open Food Facts.
2. Il demande les produits page par page, 100 à la fois, avec seulement 6 champs utiles.
3. En cas d'erreur du serveur, il réessaie jusqu'à 5 fois en attendant de plus en plus longtemps.
4. Il enregistre la liste après chaque page, pour ne rien perdre en cas de panne.
5. Il attend 7 secondes entre deux pages pour respecter la limite de l'API.
