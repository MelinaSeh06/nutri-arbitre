# Nutri-Arbitre — Fichier 4 : `garde_fou.py`, les règles imposées par le code

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

C'est la **brique 3** : « une règle imposée par le code ». Le fichier contient **deux règles**.

**Règle n° 1 : aucun chiffre qui n'a pas été calculé par un outil.** Avant d'afficher la réponse de Qwen, le
code vérifie que **chaque nombre** de la réponse vient d'un résultat d'outil (ou de la question). Si un seul
nombre n'a pas d'origine, la réponse est **bloquée** et remplacée par un message de refus.

**Règle n° 2 : pas de filtre dont la question ne parle pas.** Un outil n'a pas le droit de filtrer ou de
découper en groupes selon le bio ou le Nutri-Score si la question n'en parle pas. Cette règle est vérifiée au
moment de chaque appel d'outil, et l'erreur est renvoyée à Qwen pour qu'il se corrige.

### Pourquoi le code, et pas seulement le prompt ?
Le prompt de `agent.py` dit déjà à Qwen : « n'écris jamais un nombre que tu n'as pas reçu d'un outil ». Mais
**un prompt est une demande, pas une obligation** : le modèle peut l'ignorer. On l'a vu le 2 novembre 2026 :
à « Combien de grammes de sucre dans un bol de 40 g de céréales bio ? », Qwen a calculé lui-même
13,17 × 0,4 = « 5,3 g ». Le code, lui, s'exécute à chaque fois, et le modèle ne peut pas le contourner.

> **Le prompt dit la règle, le code la fait respecter.**

---

## 2. Les notions à connaître avant de lire le code

### Une expression régulière (regex)
Une **expression régulière** est un « modèle » de texte à rechercher. Le module Python `re` sait les utiliser.
`re.compile(motif)` prépare le modèle, et `.findall(texte)` renvoie tous les morceaux du texte qui y
correspondent. Les symboles de base :

| Symbole | Veut dire |
|---|---|
| `\d` | un chiffre (0 à 9) |
| `+` | « au moins une fois » le symbole d'avant |
| `?` | « 0 ou 1 fois » (facultatif) |
| `[.,]` | un point **ou** une virgule |
| `(?: ... )` | un groupe, pour appliquer `?` à tout le groupe |
| `\b` | une frontière de mot (début ou fin de mot) |

### Le format JSON en texte
`json.dumps(objet)` transforme un dictionnaire Python en texte. Exemple :
`{"n": 543, "moyenne": 13.17}` devient le texte `'{"n": 543, "moyenne": 13.17}'`.

### Arrondir
Quand Qwen reçoit 18,37, il écrit souvent « 18 » ou « 18,4 ». Ces **arrondis corrects** doivent être acceptés.
« 19 » ou « 18,5 », qui sont de **mauvais** arrondis, doivent être refusés.

---

## 3. Le code, morceau par morceau

### Morceau 1 : l'en-tête, le motif d'un nombre et les constantes (lignes 1 à 29)

Code de `nutri/garde_fou.py`, lignes 1 à 29 (le numéro de ligne est à gauche de la barre) :

```python
  1 | """Brique 3 : la règle « aucun chiffre qui n'a pas été calculé par le code ».
  2 | 
  3 | Le prompt demande au modèle de ne pas inventer de chiffres, mais un prompt peut être ignoré.
  4 | Ici, c'est le CODE qui vérifie la réponse finale avant de l'afficher :
  5 | chaque nombre de la réponse doit venir d'un résultat d'outil (ou de la question elle-même).
  6 | Sinon la réponse est bloquée.
  7 | 
  8 | Deuxième règle (fin du fichier) : un outil ne peut pas filtrer sur bio ou Nutri-Score si la question
  9 | n'en parle pas. Cette règle est appliquée au moment de l'appel d'outil, dans agent.py.
 10 | """
 11 | from __future__ import annotations   # « str | None » accepté aussi en Python 3.9
 12 | 
 13 | import json
 14 | import re
 15 | 
 16 | # Expression régulière qui reconnaît un nombre dans un texte. Lecture morceau par morceau :
 17 | #   -?          un signe moins, facultatif
 18 | #   \d+         un ou plusieurs chiffres            -> "12"
 19 | #   (?:[.,]\d+)? facultatif : un point ou une virgule suivi de chiffres -> ",5"
 20 | # Exemples reconnus : "12", "12,5", "12.5", "-3"
 21 | MOTIF_NOMBRE = re.compile(r"-?\d+(?:[.,]\d+)?")
 22 | 
 23 | # Constantes qu'on a le droit d'écrire sans calcul : « pour 100 g » et « marge à 95 % ».
 24 | # (Attention : les noms de champs comme "marge_95" sont lus aussi, car on cherche les nombres dans le
 25 | # texte JSON. Le 95 serait donc accepté de toute façon ; on l'écrit ici pour que ce soit voulu.)
 26 | CONSTANTES_AUTORISEES = [100.0, 95.0]
 27 | 
 28 | MESSAGE_REFUS = ("Réponse bloquée : elle contenait des chiffres qui n'ont pas été calculés par "
 29 |                  "les outils ({}). Reformulez la question pour que le calcul soit fait par le code.")
```

**Ligne 21 : le motif d'un nombre**, `-?\d+(?:[.,]\d+)?`, se lit morceau par morceau :
- `-?` : un signe moins, facultatif ;
- `\d+` : un ou plusieurs chiffres → « 12 » ;
- `(?:[.,]\d+)?` : facultatif : une virgule ou un point, puis des chiffres → « ,5 ».

Il reconnaît « 12 », « 12,5 », « 12.5 », « -3 ». Le `r` devant les guillemets (`r"..."`) veut dire « texte
brut » : Python ne touche pas aux barres obliques inverses `\`.

**Vrai exemple, lancé sur le code :** dans « 100 g contiennent 13,2 ± 0,7 g de sucre, soit -5,42 g. », la regex
trouve `['100', '13,2', '0,7', '-5,42']`.

**Ligne 26 : `CONSTANTES_AUTORISEES = [100.0, 95.0]`.** Deux nombres qu'on a le droit d'écrire sans calcul :
« pour 100 g » et « marge à 95 % ». (Une remarque faite en séance 3 : les noms de champs comme `marge_95` sont
lus aussi dans le texte JSON, donc 95 serait accepté de toute façon. On l'écrit quand même ici pour que ce soit
voulu, et pas un accident.)

**Lignes 28 et 29 : `MESSAGE_REFUS`**, le message affiché à la place d'une réponse bloquée. `{}` sera remplacé
par la liste des nombres refusés (avec `.format`).

---

### Morceau 2 : trouver les nombres et les nombres autorisés (lignes 32 à 48)

Code de `nutri/garde_fou.py`, lignes 32 à 48 (le numéro de ligne est à gauche de la barre) :

```python
 32 | def extraire_nombres(texte: str) -> list[str]:
 33 |     """Renvoie les nombres écrits dans un texte, tels qu'ils sont écrits ('12,5')."""
 34 |     return MOTIF_NOMBRE.findall(texte or "")
 35 | 
 36 | 
 37 | def en_float(ecrit: str) -> float:
 38 |     """'12,5' -> 12.5 (Python ne comprend que le point)."""
 39 |     return float(ecrit.replace(",", "."))
 40 | 
 41 | 
 42 | def nombres_autorises(objet) -> list[float]:
 43 |     """Récupère tous les nombres d'un résultat d'outil (dictionnaire, liste…).
 44 |     Astuce : on transforme le résultat en texte JSON, puis on y cherche les nombres
 45 |     avec la même expression régulière que pour la réponse.
 46 |     Ex. : {"n": 42, "moyenne": 18.37} -> '{"n": 42, "moyenne": 18.37}' -> [42.0, 18.37]"""
 47 |     texte = json.dumps(objet, ensure_ascii=False, default=str)
 48 |     return [en_float(n) for n in extraire_nombres(texte)]
```

- **Lignes 32 à 34 : `extraire_nombres`.** `MOTIF_NOMBRE.findall(...)` renvoie les nombres **tels qu'ils sont
  écrits** (en texte, avec la virgule). `texte or ""` : si le texte est `None`, on cherche dans un texte vide.
- **Lignes 37 à 39 : `en_float`.** Python ne comprend que le point comme séparateur décimal : `"12,5"` devient
  `"12.5"`, puis le nombre 12.5.
- **Lignes 42 à 48 : `nombres_autorises`, l'astuce du JSON.** Les résultats d'outils sont des dictionnaires et
  des listes **emboîtés** les uns dans les autres. Pour trouver tous leurs nombres, on pourrait parcourir la
  structure à la main, niveau par niveau. L'astuce : on transforme tout en **texte JSON**, puis on cherche les
  nombres avec **la même regex** que pour la réponse.
  `default=str` : si une valeur ne sait pas se mettre en JSON, on la met en texte au lieu de planter.

**Vrai exemple :** `nombres_autorises({"n": 543, "moyenne": 13.17, "marge_95": 0.69})` renvoie
`[543.0, 13.17, 95.0, 0.69]`. On voit le 95 qui vient du nom du champ `marge_95`.

---

### Morceau 3 : un nombre est-il justifié ? (lignes 51 à 71)

Code de `nutri/garde_fou.py`, lignes 51 à 71 (le numéro de ligne est à gauche de la barre) :

```python
 51 | def nombre_justifie(ecrit: str, autorises: list[float]) -> bool:
 52 |     """Le nombre écrit est-il un arrondi correct d'un nombre calculé par les outils ?
 53 |     Ex. avec 18.37 calculé : "18" oui, "18,4" oui, "19" non, "18,5" non."""
 54 |     valeur = en_float(ecrit)
 55 | 
 56 |     # combien de chiffres après la virgule ? "18,4" -> 1, "18" -> 0
 57 |     ecrit = ecrit.replace(",", ".")
 58 |     if "." in ecrit:
 59 |         decimales = len(ecrit.split(".")[1])
 60 |     else:
 61 |         decimales = 0
 62 | 
 63 |     # écart permis = une demi-unité du dernier chiffre écrit
 64 |     # "18" -> 0,5 (18,37 est à 0,37 : ok) ; "18,4" -> 0,05 (18,37 est à 0,03 : ok)
 65 |     tolerance = 0.5 * 10 ** (-decimales)
 66 |     tolerance += 1e-9   # minuscule marge : les ordinateurs calculent 0,1 + 0,2 = 0,30000000000000004
 67 | 
 68 |     for a in autorises:
 69 |         if abs(valeur - a) <= tolerance:
 70 |             return True
 71 |     return False
```

**Lignes 56 à 61 : combien de chiffres après la virgule ?** `ecrit.split(".")` coupe au point : `"18.4"` →
`["18", "4"]`, et `[1]` prend la partie après le point. Sa longueur est le nombre de décimales. Sans point,
0 décimale.

**Lignes 63 à 65 : l'écart permis.** Écrire « 18 », c'est dire « un nombre qui s'arrondit à 18 » : un nombre
entre **17,5 et 18,5**, donc à **0,5 au plus** de 18. Écrire « 18,4 », c'est dire « entre 18,35 et 18,45 »,
donc à **0,05 au plus**. Plus on écrit de décimales, plus on est précis, et plus l'écart permis est petit :

| Nombre écrit | décimales | calcul `0.5 * 10 ** (-decimales)` | écart permis |
|---|---|---|---|
| « 18 » | 0 | 0,5 × 1 | **0,5** |
| « 18,4 » | 1 | 0,5 × 0,1 | **0,05** |
| « 18,37 » | 2 | 0,5 × 0,01 | **0,005** |

(`10 ** (-1)` veut dire 10 puissance −1, c'est-à-dire 0,1.)

**Ligne 66 : `+ 1e-9`.** `1e-9` = 0,000000001. Un ordinateur ne calcule pas les nombres à virgule de façon
parfaitement exacte (il les écrit en binaire). Exemple vérifié : un outil donne **2,45** et Qwen écrit
« **2,4** » : c'est pile à la limite, on veut l'accepter. Mais Python calcule la distance
|2,4 − 2,45| = **0,050000000000000266**, un tout petit peu plus que 0,05. Sans la petite marge, cette réponse
correcte serait bloquée. La marge est bien trop petite pour laisser passer un vrai mauvais arrondi.

**Lignes 68 à 71 : la boucle.** Pour chaque nombre autorisé `a`, on calcule la distance `abs(valeur - a)`
(`abs` = valeur absolue : on enlève le signe moins, car seule la distance compte, que l'arrondi soit au-dessus
ou en dessous). Dès qu'**un** nombre autorisé est assez proche, on répond `True`. Si aucun ne l'est : `False`.

**Exemples avec 18,37 calculé par un outil :**

| Qwen écrit | distance | écart permis | résultat |
|---|---|---|---|
| « 18 » | 0,37 | 0,5 | ✅ accepté |
| « 19 » | 0,63 | 0,5 | ❌ refusé |
| « 18,4 » | 0,03 | 0,05 | ✅ accepté |
| « 18,5 » | 0,13 | 0,05 | ❌ refusé |
| « 17 » | 1,37 | 0,5 | ❌ refusé |

**À dire à l'oral :** « Un nombre écrit avec d décimales a le droit d'être à une demi-unité du dernier chiffre
du vrai résultat. On accepte les arrondis corrects et on refuse les autres. »

---

### Morceau 4 : le verdict, `verifier` et `filtrer_reponse` (lignes 74 à 91)

Code de `nutri/garde_fou.py`, lignes 74 à 91 (le numéro de ligne est à gauche de la barre) :

```python
 74 | def verifier(reponse: str, resultats_outils: list, question: str = "") -> tuple[bool, list[str]]:
 75 |     """Renvoie (autorisée ?, liste des nombres non justifiés)."""
 76 |     # les nombres qu'on a le droit d'écrire : ceux des outils, ceux de la question, et 100
 77 |     autorises = nombres_autorises(resultats_outils) + nombres_autorises(question) + CONSTANTES_AUTORISEES
 78 |     # un écart de -20 peut s'écrire « 20 g de moins » : on autorise aussi la valeur sans signe
 79 |     autorises += [abs(a) for a in autorises]
 80 | 
 81 |     non_justifies = []
 82 |     for n in extraire_nombres(reponse):
 83 |         if not nombre_justifie(n, autorises):
 84 |             non_justifies.append(n)
 85 |     return (len(non_justifies) == 0, non_justifies)
 86 | 
 87 | 
 88 | def filtrer_reponse(reponse: str, resultats_outils: list, question: str = "") -> str:
 89 |     """La barrière : renvoie la réponse si elle est propre, sinon un message de refus."""
 90 |     ok, fautifs = verifier(reponse, resultats_outils, question)
 91 |     return reponse if ok else MESSAGE_REFUS.format(", ".join(fautifs))
```

- **Ligne 77 : la liste des nombres autorisés** = ceux des résultats d'outils + ceux de la **question** (si
  l'utilisateur écrit « un bol de 40 g », Qwen a le droit de répéter 40) + les constantes 100 et 95.
- **Ligne 79 : la valeur sans signe.** Les outils donnent un écart bio − non bio **négatif** (−5,42) quand les bio
  en ont moins. En français, on écrit « 5,42 g de moins », sans le signe moins. On ajoute donc la version sans
  signe de chaque nombre, sinon cette phrase correcte serait bloquée.
- **Lignes 81 à 85 :** chaque nombre de la réponse est vérifié. Les nombres non justifiés sont rangés dans une
  liste. La fonction renvoie **deux** valeurs : « est-ce autorisé ? » (vrai si la liste est vide) et la liste
  des fautifs.
- **Lignes 88 à 91 : `filtrer_reponse`, la barrière.** Si tout va bien, on renvoie la réponse telle quelle.
  Sinon, le message de refus, avec les nombres fautifs. `", ".join(fautifs)` colle la liste en un texte :
  `["122,84", "0,30"]` → `"122,84, 0,30"`.

**Vrai cas bloqué (trace du 2 novembre 2026) :**
- question : « Combien de grammes de sucre y a-t-il dans un bol de 40 g de céréales bio ? » ;
- l'outil a donné : n = 543, moyenne 13,17, marge 0,69 ;
- Qwen a écrit : « 100 g contiennent 13,2 ± 0,7 g de sucre. Pour un bol de 40 g, environ **5,3 g**. »
- vérification : 100 (constante) ✅, 13,2 (arrondi de 13,17) ✅, 0,7 (arrondi de 0,69) ✅, 40 (dans la
  question) ✅, **5,3 ❌** (ne vient d'aucun outil) ;
- résultat : « Réponse bloquée : elle contenait des chiffres qui n'ont pas été calculés par les outils (5,3). »

Le calcul de Qwen était **juste** (13,17 × 0,4 = 5,27). Mais le garde-fou ne vérifie pas si un calcul du modèle
est juste : il vérifie **d'où vient** le nombre. Et le même jour, à une autre question, Qwen a annoncé « 124,9 kcal
exactement » pour un calcul faux : on ne peut pas faire confiance au modèle au cas par cas.

**Un cas accepté :** « Les bio ont 13,2 g de sucres, contre 19 g » avec le résultat de `comparer` (13,17 et
18,59) → accepté : 13,2 arrondit 13,17, et 19 arrondit 18,59.

---

### Morceau 5 : la deuxième règle, `verifier_filtres` (lignes 94 à 112)

Code de `nutri/garde_fou.py`, lignes 94 à 112 (le numéro de ligne est à gauche de la barre) :

```python
 94 | # Deuxième règle : un outil n'a pas le droit de filtrer sur un critère dont la question ne parle pas.
 95 | # (Vrai cas du 02/11/2026 : « calories d'une portion de céréales » -> Qwen a filtré les seules non bio.)
 96 | # \b = début ou fin de mot : « bio » est trouvé dans « céréales bio », pas dans « biologie » ni « cabio ».
 97 | PARLE_DE_BIO = re.compile(r"\b(bio|bios|biologique|biologiques|organic|ab)\b", re.IGNORECASE)
 98 | PARLE_DE_NUTRISCORE = re.compile(r"nutri[- ]?score", re.IGNORECASE)
 99 | 
100 | 
101 | def verifier_filtres(question: str, arguments: dict) -> str | None:
102 |     """Renvoie un message d'erreur si l'appel d'outil filtre ou découpe en groupes selon un critère
103 |     dont la question ne parle pas, sinon None. Le message est renvoyé au modèle, qui peut corriger."""
104 |     utilise_bio = arguments.get("bio") is not None or arguments.get("groupe") == "bio"
105 |     if utilise_bio and not PARLE_DE_BIO.search(question):
106 |         return ("la question ne parle pas de bio : ne filtre pas et ne compare pas selon le bio, "
107 |                 "utilise decrire sur toutes les céréales")
108 |     utilise_ns = arguments.get("nutriscore") is not None or arguments.get("groupe") == "nutriscore"
109 |     if utilise_ns and not PARLE_DE_NUTRISCORE.search(question):
110 |         return ("la question ne parle pas de Nutri-Score : ne filtre pas et ne compare pas selon le "
111 |                 "Nutri-Score, utilise decrire sur toutes les céréales")
112 |     return None
```

**Pourquoi cette règle (une décision de la séance 3) :** à la question « Combien de calories apporte une portion
de 30 g de céréales, en moyenne ? », Qwen a appelé `decrire(energie_kcal, bio=False)` : il a filtré les seules
céréales **non bio**, alors que la question parle de **toutes** les céréales. La règle n° 1 ne voyait rien :
les chiffres venaient bien d'un outil, mais du **mauvais calcul**.

- **Ligne 97 : `PARLE_DE_BIO`**, une regex qui cherche les mots « bio », « bios », « biologique(s) »,
  « organic », « ab ». Les `\b` imposent des **mots entiers** : « bio » est trouvé dans « céréales bio », mais pas
  dans « biologie » ni dans « cabio ». `re.IGNORECASE` : majuscules et minuscules comptent pareil.
- **Ligne 98 : `PARLE_DE_NUTRISCORE`**, trouve « nutriscore », « nutri-score » ou « nutri score » (`[- ]?` = un
  tiret ou un espace, facultatif).
- **Ligne 101 :** la fonction renvoie un message d'erreur (`str`) ou `None` (`str | None`).
- **Ligne 104 : l'appel utilise-t-il le bio ?** Oui si l'argument `bio` est donné (`is not None`), **ou** si on
  découpe en groupes bio / non bio (`groupe == "bio"`). `arguments.get("bio")` renvoie `None` si l'argument
  n'existe pas.
- **Lignes 105 à 107 :** s'il utilise le bio et que la question n'en parle pas (`not PARLE_DE_BIO.search(question)`),
  on renvoie un message qui dit aussi **quoi faire** : « utilise decrire sur toutes les céréales ».
- **Lignes 108 à 111 :** la même chose pour le Nutri-Score.
- **Ligne 112 :** tout va bien : `None`.

**Elle a marché avec le vrai Qwen (trace du 2 novembre 2026) :**
1. Qwen demande `decrire(energie_kcal, bio=False)` → refusé, il reçoit le message d'erreur ;
2. il se corrige : `decrire(energie_kcal)` sur les 953 céréales → 409,45 kcal ;
3. il écrit « 122,84 kcal pour une portion de 30 g (409,45 × 0,30) » → la règle n° 1 bloque 122,84 et 0,30.

Les deux règles ont fonctionné l'une après l'autre.

**Vrais exemples de la règle (ce sont des tests) :**

| Question | Arguments | Résultat |
|---|---|---|
| « Les céréales bio sont-elles sucrées ? » | `bio=True` | accepté |
| « Et les produits issus de l'agriculture biologique ? » | `bio=True` | accepté |
| « Sucre des céréales au Nutri-Score A ? » | `nutriscore="a"` | accepté |
| « Sucre des céréales A ? » | `nutriscore="a"` | **refusé** (pas de « Nutri-Score ») |
| « Qui fabrique la biologie ? » | `bio=True` | **refusé** (« biologie » n'est pas « bio ») |
| « Calories d'une portion de 30 g ? » | `groupe="bio"` | **refusé** |

---

## 4. Les limites (à dire soi-même à l'oral)

Ce ne sont pas des fautes : la consigne demande justement de montrer et d'expliquer les échecs (brique 9).
- **Le garde-fou ne vérifie pas le sens.** Qwen a déjà répondu « Non » en citant des chiffres qui disaient
  « Oui ». Et dans l'évaluation, il a lu un classement décroissant à l'envers : « Crownfield, 18,61 g, est la
  marque la moins sucrée » (c'est l'une des plus sucrées). Le chiffre venait d'un outil : réponse acceptée.
- **Le choix du nutriment n'est pas vérifié** (glucides au lieu de sucres, par exemple).
- **Une coïncidence passe :** un chiffre inventé qui tombe par hasard sur un nombre autorisé est accepté.
- **Un nombre écrit en lettres** (« treize grammes ») n'est pas détecté par la regex.
- **Les questions de portion sont toujours bloquées**, puisqu'aucun outil ne fait ce calcul.
- **La règle n° 2 peut empêcher de répondre :** dans l'évaluation, Qwen s'est obstiné à filtrer, a reçu 7 refus,
  et la boucle s'est arrêtée sans réponse.

---

## 5. Questions d'examinateur, avec leurs réponses

**Q1. Pourquoi une règle dans le code alors que le prompt l'interdit déjà ?** Un prompt est une demande, le
modèle peut l'ignorer : Qwen a calculé « 5,3 g » malgré le prompt. Le code s'exécute à chaque fois.

**Q2. Expliquez l'expression régulière.** Un signe moins facultatif, des chiffres, puis éventuellement une virgule
ou un point suivi de chiffres. Dans « 13,2 ± 0,7 g », elle trouve « 13,2 » et « 0,7 ».

**Q3. Quels nombres sont autorisés ?** Ceux des résultats d'outils, ceux de la question, 100 et 95, et chacun
de ces nombres sans son signe.

**Q4. Pourquoi « 18 » est accepté pour 18,37 et pas « 19 » ?** Sans décimale, l'écart permis est 0,5. 18,37 est à
0,37 de 18 (accepté) et à 0,63 de 19 (refusé).

**Q5. À quoi sert le `1e-9` ?** À compenser les minuscules erreurs de calcul de l'ordinateur sur les nombres à
virgule : |2,4 − 2,45| donne 0,050000000000000266 au lieu de 0,05.

**Q6. Pourquoi passer par le texte JSON ?** Pour trouver tous les nombres d'un résultat emboîté avec la même
regex, sans parcourir la structure à la main.

**Q7. Pourquoi un calcul juste est-il bloqué ?** Le garde-fou ne sait pas si un calcul du modèle est juste. Il
vérifie seulement d'où vient le nombre. Et le modèle se trompe parfois en disant que c'est « exact ».

**Q8. Pourquoi ajouter la valeur sans signe ?** Un écart de −5,42 s'écrit « 5,42 g de moins ».

**Q9. Que fait la deuxième règle, et quand est-elle appliquée ?** Elle refuse un filtre ou un découpage bio /
Nutri-Score dont la question ne parle pas. Elle est appliquée **au moment de l'appel d'outil** : le calcul filtré
n'est jamais fait, et Qwen reçoit l'erreur pour corriger son appel.

**Q10. Donnez une erreur que le garde-fou ne détecte pas.** Une phrase qui contredit ses chiffres, un mauvais
nutriment, une marque lue à l'envers dans un classement, un nombre écrit en lettres, une coïncidence.

---

## 6. Résumé en 5 phrases

1. Le garde-fou impose par le code deux règles que le prompt seul ne garantit pas.
2. Règle n° 1 : chaque nombre de la réponse doit être un arrondi correct d'un nombre des outils ou de la question, sinon la réponse est bloquée.
3. L'écart permis est une demi-unité du dernier chiffre écrit, plus une minuscule marge pour les erreurs de calcul de l'ordinateur.
4. Règle n° 2 : pas de filtre bio ou Nutri-Score si la question n'en parle pas ; l'erreur est renvoyée à Qwen pour qu'il se corrige.
5. Le garde-fou vérifie l'origine des chiffres, pas le sens des phrases : c'est sa principale limite.
