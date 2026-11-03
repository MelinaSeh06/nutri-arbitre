# Nutri-Arbitre — Fichier 6 : `evaluation.py`, mesurer le système (brique 9)

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

C'est la **brique 9** : « une comparaison mesurée ». La consigne demande : au moins 10 tâches dont on connaît
la réponse, au moins 3 lancements de chacune, une moyenne et une dispersion, et **un échec expliqué à partir
de sa trace**.

Ce fichier pose **16 questions** dont on connaît la bonne réponse, **3 fois chacune**, à **deux systèmes** :
- le **système complet** : Qwen + outils + garde-fou ;
- le **modèle seul** : Qwen sans outils ni garde-fou, qui répond de mémoire.

Il juge chaque réponse (**juste**, **fausse** ou **bloquée**) et calcule le taux de réponses justes, avec sa
**moyenne** et son **écart type**. En tout : 16 questions × 3 lancements × 2 systèmes = **96 réponses** de Qwen,
environ 35 minutes.

**Comment on le lance :**
```
python -m nutri.evaluation            # tout (environ 35 minutes)
python -m nutri.evaluation --rapide   # 2 questions, 1 lancement : pour vérifier que ça marche
```

**Ce qui sort :** `resultats/evaluation.md` (un tableau lisible) et `resultats/evaluation.json` (toutes les
traces, pour expliquer les échecs).

### Les résultats (3 novembre 2026)

| Système | Réponses justes (moyenne ± écart type) | par lancement | Justes | Fausses | Bloquées |
|---|---|---|---|---|---|
| Complet | **73 % ± 4 %** | 69 %, 75 %, 75 % | 35 | 5 | 8 |
| Modèle seul | **12 % ± 6 %** | 6 %, 19 %, 12 % | 6 | 42 | 0 |

---

## 2. Les notions à connaître avant de lire le code

### Une question « à réponse connue »
On calcule d'avance la bonne réponse, avec pandas, **directement sur les données**, sans passer par
`tools.py`. Exemple : la moyenne des sucres des céréales bio = `bio["sucres"].mean()` = 13,165… g.

**Pourquoi pas avec `tools.py` ?** Si un outil avait une erreur de calcul, on comparerait le code à lui-même et on
ne la verrait jamais. Avec pandas directement, c'est une **vérification indépendante**.

### Le taux de réponses justes, la moyenne, l'écart type
- À chaque lancement : **taux** = nombre de réponses justes / nombre de questions. Ex. : 12 justes sur 16 = 75 %.
- Sur les 3 lancements : la **moyenne** des 3 taux, et leur **écart type** (la dispersion) : de combien le score
  change d'un lancement à l'autre. 0 % = les 3 lancements ont donné exactement le même score.

### Pourquoi 3 lancements ?
Qwen **ne répond pas deux fois pareil** à la même question (il y a du hasard dans la façon dont il choisit ses
mots). Un seul lancement ne dirait rien de sa régularité.

---

## 3. Le code, morceau par morceau

### Morceau 1 : l'en-tête et les réglages (lignes 1 à 26)

Code de `nutri/evaluation.py`, lignes 1 à 26 (le numéro de ligne est à gauche de la barre) :

```python
  1 | """Brique 9 : une comparaison mesurée.
  2 | 
  3 | On pose 16 questions (dont 4 pièges) dont on connaît la bonne réponse, 3 fois chacune, à deux systèmes :
  4 |   - le système complet (Qwen + outils + garde-fou) ;
  5 |   - le modèle seul (Qwen sans outils ni garde-fou, il répond de mémoire).
  6 | On compte les réponses justes, fausses et bloquées, puis on donne la moyenne et la dispersion.
  7 | 
  8 | Les bonnes réponses sont calculées ici directement avec pandas, sans passer par tools.py :
  9 | c'est une vérification indépendante.
 10 | 
 11 | Usage :
 12 |   python -m nutri.evaluation            # tout (environ 35 minutes)
 13 |   python -m nutri.evaluation --rapide   # 2 questions, 1 lancement : pour vérifier que ça marche
 14 | """
 15 | import argparse
 16 | import json
 17 | import statistics
 18 | import time
 19 | from pathlib import Path
 20 | 
 21 | from nutri import garde_fou
 22 | from nutri.agent import charger_donnees, repondre
 23 | 
 24 | N_LANCEMENTS = 3                 # chaque question est posée 3 fois (Qwen ne répond pas toujours pareil)
 25 | TOLERANCE = 0.02                 # un nombre est juste s'il est à 2 % près de la bonne réponse
 26 | DOSSIER = Path("resultats")
```

- **Ligne 17 : `statistics`**, un module de Python pour la moyenne (`mean`) et l'écart type (`stdev`).
- **Ligne 22 :** on réutilise `charger_donnees` et `repondre` d'`agent.py` : l'évaluation teste **le vrai
  système**, exactement celui qu'on lance dans le terminal.
- **Ligne 24 : `N_LANCEMENTS = 3`.**
- **Ligne 25 : `TOLERANCE = 0.02`** : un nombre est juste s'il est à 2 % près de la bonne réponse.
- **Ligne 26 :** le dossier des résultats.

---

### Morceau 2 : `construire_taches`, les 16 questions (lignes 29 à 82)

Code de `nutri/evaluation.py`, lignes 29 à 82 (le numéro de ligne est à gauche de la barre) :

```python
 29 | def construire_taches(df) -> list[dict]:
 30 |     """Les 16 questions et leur bonne réponse, calculée avec pandas.
 31 |     4 types de réponse : un nombre, un texte (nom de marque), de la prudence (« on ne peut pas conclure »),
 32 |     ou un refus (la donnée n'existe pas : aucun chiffre ne doit être donné)."""
 33 |     bio = df[df["bio"]]
 34 |     non_bio = df[~df["bio"]]
 35 |     # la marque (au moins 5 produits) dont la moyenne de sucres est la plus basse
 36 |     par_marque = df.groupby("marque")["sucres"].agg(["count", "mean"])
 37 |     marque_moins_sucree = par_marque[par_marque["count"] >= 5]["mean"].idxmin()
 38 | 
 39 |     return [
 40 |         {"question": "Combien de céréales du petit-déjeuner y a-t-il dans les données ?",
 41 |          "type": "nombre", "attendu": len(df)},
 42 |         {"question": "Combien de céréales bio y a-t-il dans les données ?",
 43 |          "type": "nombre", "attendu": len(bio)},
 44 |         {"question": "Combien de céréales ont un Nutri-Score A ?",
 45 |          "type": "nombre", "attendu": int((df["nutriscore"] == "a").sum())},
 46 |         {"question": "Quelle est la teneur moyenne en sucres des céréales bio, pour 100 g ?",
 47 |          "type": "nombre", "attendu": bio["sucres"].mean()},
 48 |         {"question": "Quelle est la teneur moyenne en sucres des céréales non bio, pour 100 g ?",
 49 |          "type": "nombre", "attendu": non_bio["sucres"].mean()},
 50 |         {"question": "Quelle est la teneur moyenne en sel des céréales bio, pour 100 g ?",
 51 |          "type": "nombre", "attendu": bio["sel"].mean()},
 52 |         {"question": "Combien de calories apportent 100 g de céréales, en moyenne ?",
 53 |          "type": "nombre", "attendu": df["energie_kcal"].mean()},
 54 |         {"question": "Quelle est la teneur moyenne en protéines des céréales, pour 100 g ?",
 55 |          "type": "nombre", "attendu": df["proteines"].mean()},
 56 |         {"question": "Quelle est la teneur moyenne en fibres des céréales au Nutri-Score A, pour 100 g ?",
 57 |          "type": "nombre", "attendu": df[df["nutriscore"] == "a"]["fibres"].mean()},
 58 |         {"question": "De combien de grammes les céréales bio ont-elles moins de sucres que les non bio, "
 59 |                      "pour 100 g ?",
 60 |          "type": "nombre", "attendu": bio["sucres"].mean() - non_bio["sucres"].mean()},
 61 |         {"question": "Quelle marque (au moins 5 produits) a la teneur moyenne en sucres la plus basse ?",
 62 |          "type": "texte", "attendu": marque_moins_sucree},
 63 |         # l'écart de lipides est petit (0,21 g) devant sa marge (0,84 g) : la bonne réponse est la prudence
 64 |         {"question": "Les céréales bio contiennent-elles plus de lipides que les non bio ?",
 65 |          "type": "prudence", "attendu": ["hasard", "pas conclure", "pas de conclure", "pas de différence nette"]},
 66 | 
 67 |         # Questions pièges, choisies pour montrer les failles connues du système :
 68 |         # une portion (aucun outil ne fait ce calcul : le modèle calcule lui-même, le garde-fou bloque)
 69 |         {"question": "Combien de calories apporte une portion de 30 g de céréales, en moyenne ?",
 70 |          "type": "nombre", "attendu": df["energie_kcal"].mean() * 0.30},
 71 |         # une soustraction entre deux résultats d'outil (même problème : c'est le modèle qui calcule)
 72 |         {"question": "Quel est l'écart de sucres entre les céréales au Nutri-Score A et celles au "
 73 |                      "Nutri-Score E, pour 100 g ?",
 74 |          "type": "nombre", "attendu": df[df["nutriscore"] == "a"]["sucres"].mean()
 75 |                                       - df[df["nutriscore"] == "e"]["sucres"].mean()},
 76 |         # une donnée absente du fichier : la bonne réponse est de ne donner aucun chiffre
 77 |         {"question": "Quelle est la teneur moyenne en vitamine C des céréales, pour 100 g ?",
 78 |          "type": "refus", "attendu": None},
 79 |         # toutes les céréales : tentant de filtrer sur le bio alors que la question n'en parle pas
 80 |         {"question": "Les céréales du petit-déjeuner sont-elles riches en sucres ? Donne la moyenne pour 100 g.",
 81 |          "type": "nombre", "attendu": df["sucres"].mean()},
 82 |     ]
```

Chaque question est un petit dictionnaire : la `question`, le `type` de réponse, et la bonne réponse (`attendu`).

**Lignes 33 et 34 :** deux sous-tableaux, avec la technique du masque : `df[df["bio"]]` garde les bio,
`df[~df["bio"]]` les non bio (`~` = « non »).

**Lignes 36 et 37 : la marque la moins sucrée.** Pour chaque marque, le nombre de produits et la moyenne de sucres
(`groupby` + `agg`). On garde les marques d'au moins 5 produits (un masque), et `idxmin()` donne le **nom** de la
ligne où la moyenne est la plus petite : « jardin bio etic ».

**Les 4 types de réponse :**

| Type | Questions | Bonne réponse |
|---|---|---|
| `nombre` | combien de céréales, moyennes de sucres, de sel, de calories… | un nombre : 953, 13,17… |
| `texte` | la marque la moins sucrée | « jardin bio etic » |
| `prudence` | les bio ont-elles plus de lipides ? | « on ne peut pas conclure » (écart 0,21 g, marge 0,84 g) |
| `refus` | la vitamine C | aucun chiffre : la donnée n'existe pas |

**Les vraies bonnes réponses calculées :** 953 céréales ; 543 bio ; 270 au Nutri-Score A ; sucres bio 13,17 g ;
sucres non bio 18,59 g ; sel bio 0,126 g ; calories 409,45 kcal ; protéines 10,22 g ; fibres du Nutri-Score A
10,22 g ; écart de sucres bio − non bio −5,42 g ; marque la moins sucrée : jardin bio etic.

**Lignes 67 à 81 : les 4 questions pièges.** Une première évaluation, avec seulement les 12 premières questions,
donnait **100 %** au système complet : ces questions demandent chacune un seul outil, elles sont faciles. On a
**décidé** d'ajouter 4 pièges qui visent les failles connues, parce que le but du devoir est de montrer les
limites du modèle, pas d'avoir un score parfait :
1. **une portion de 30 g** (bonne réponse : 409,45 × 0,30 = 122,83 kcal). Aucun outil ne fait ce calcul : si
   Qwen le fait lui-même, le garde-fou bloque ;
2. **l'écart de sucres entre Nutri-Score A et E** (−20,03 g). L'outil donne les deux moyennes, mais la
   soustraction est faite par Qwen ;
3. **la vitamine C**, absente des données. La bonne réponse est de le dire, sans inventer de chiffre ;
4. **« les céréales sont-elles riches en sucres ? »** (15,5 g). La question ne parle pas de bio, mais Qwen est
   tenté de comparer bio et non bio (la règle n° 2 du garde-fou).

---

### Morceau 3 : `nombre_juste` (lignes 85 à 94)

Code de `nutri/evaluation.py`, lignes 85 à 94 (le numéro de ligne est à gauche de la barre) :

```python
 85 | def nombre_juste(reponse: str, attendu: float) -> bool:
 86 |     """La réponse contient-elle un nombre à 2 % près de la bonne réponse ?
 87 |     On compare sans le signe : « 5,4 g de moins » est juste pour un écart de -5,42."""
 88 |     # au moins 0,01 : les outils arrondissent à 2 décimales (0,1265 de sel devient « 0,13 »)
 89 |     ecart_permis = max(TOLERANCE * abs(attendu), 0.01)
 90 |     for ecrit in garde_fou.extraire_nombres(reponse):
 91 |         valeur = abs(garde_fou.en_float(ecrit))
 92 |         if abs(valeur - abs(attendu)) <= ecart_permis:
 93 |             return True
 94 |     return False
```

- **Ligne 89 : l'écart permis** = 2 % de la bonne réponse, mais **au moins 0,01**. Pourquoi ce minimum ? Le sel
  des céréales bio vaut 0,1265 g. L'outil l'arrondit à 2 décimales : « 0,13 », qui est à 0,0035 de la vraie
  valeur. Or 2 % de 0,1265, c'est seulement 0,0025. Sans le minimum, une réponse juste serait comptée fausse.
  `max(a, b)` prend le plus grand des deux.
- **Ligne 90 :** on **réutilise** le garde-fou pour trouver les nombres de la réponse (la même regex).
- **Lignes 91 et 92 :** `abs` des deux côtés : on compare sans le signe. « 5,42 g de moins » est juste pour un
  écart de −5,42.
- **Lignes 93 et 94 :** il suffit qu'**un** nombre de la réponse soit juste.

**Exemples (ce sont des tests) :**

| Réponse | Bonne réponse | Écart permis | Verdict |
|---|---|---|---|
| « 13,2 g » | 13,165 | 0,26 | juste (0,035) |
| « Environ 13 g » | 13,165 | 0,26 | juste (0,165) |
| « Environ 25 g » | 13,165 | 0,26 | faux |
| « 0,13 g de sel » | 0,1265 | 0,01 | juste (0,0035) |
| « 0,1 g de sel » | 0,1265 | 0,01 | faux (0,0265) |

---

### Morceau 4 : `juger`, le verdict (lignes 97 à 113)

Code de `nutri/evaluation.py`, lignes 97 à 113 (le numéro de ligne est à gauche de la barre) :

```python
 97 | def juger(tache: dict, trace: dict) -> str:
 98 |     """Renvoie "bloquee", "juste" ou "fausse"."""
 99 |     if trace["bloquee"]:
100 |         return "bloquee"        # le garde-fou a refusé : ni juste ni fausse, aucune réponse donnée
101 |     reponse = trace["reponse"]
102 |     if tache["type"] == "nombre":
103 |         ok = nombre_juste(reponse, tache["attendu"])
104 |     elif tache["type"] == "texte":
105 |         ok = tache["attendu"].lower() in reponse.lower()
106 |     elif tache["type"] == "refus":   # donnée absente : juste si la réponse n'invente aucun chiffre
107 |         ok = garde_fou.verifier(reponse, [], trace["question"])[0]
108 |     else:   # prudence : la réponse doit dire qu'on ne peut pas conclure
109 |         ok = False
110 |         for mot in tache["attendu"]:
111 |             if mot in reponse.lower():
112 |                 ok = True
113 |     return "juste" if ok else "fausse"
```

- **Lignes 99 et 100 : d'abord, la réponse est-elle bloquée ?** C'est important : le message de refus contient
  les nombres refusés, par exemple « … (122,84, 0,30) ». Sans ce test en premier, un refus qui contient par hasard
  le bon nombre serait compté « juste ». Une réponse bloquée n'est **ni juste ni fausse** : le système n'a rien
  affirmé, mais l'utilisateur n'a pas de réponse non plus. On la compte à part.
- **Lignes 102 et 103 : `nombre`**, avec la fonction du morceau 3.
- **Lignes 104 et 105 : `texte`**, le nom de la marque est-il dans la réponse ? `.lower()` met tout en
  minuscules, pour que « Jardin Bio Etic » compte aussi.
- **Lignes 106 et 107 : `refus`.** On passe la réponse dans le garde-fou **sans aucun résultat d'outil** (la liste
  vide `[]`). Si elle contient un nombre qui ne vient pas de la question (ni 100 ou 95), elle a inventé : fausse.
  `[0]` prend la première des deux valeurs renvoyées par `verifier` (« autorisée ? »).
- **Lignes 108 à 112 : `prudence`**, la réponse contient-elle un des mots « hasard », « pas conclure »,
  « pas de conclure », « pas de différence nette » ?
- **Ligne 113 :** « juste » ou « fausse ». Attention : « fausse » comprend aussi les **non-réponses** (« je n'ai pas
  réussi à répondre », « j'ai besoin d'un outil »).

---

### Morceau 5 : `resumer`, moyenne et dispersion (lignes 116 à 129)

Code de `nutri/evaluation.py`, lignes 116 à 129 (le numéro de ligne est à gauche de la barre) :

```python
116 | def resumer(verdicts: list[list[str]]) -> dict:
117 |     """verdicts[l] = la liste des verdicts du lancement l (un par question).
118 |     Taux de réponses justes à chaque lancement, puis leur moyenne et leur écart type (la dispersion)."""
119 |     taux = []
120 |     for lancement in verdicts:
121 |         taux.append(lancement.count("juste") / len(lancement))
122 |     tous = []
123 |     for lancement in verdicts:
124 |         tous += lancement            # on met bout à bout les verdicts de tous les lancements
125 |     return {"taux_juste_par_lancement": [round(t, 3) for t in taux],
126 |             "taux_juste_moyen": round(statistics.mean(taux), 3),
127 |             "ecart_type": round(statistics.stdev(taux), 3) if len(taux) >= 2 else None,
128 |             "justes": tous.count("juste"), "fausses": tous.count("fausse"),
129 |             "bloquees": tous.count("bloquee"), "total": len(tous)}
```

- **L'entrée :** `verdicts` est une liste de listes, une liste par lancement. Exemple avec 2 questions et
  3 lancements : `[["juste", "juste"], ["juste", "fausse"], ["bloquee", "fausse"]]`.
- **Lignes 119 à 121 :** le taux de chaque lancement. `lancement.count("juste")` compte les « juste » de la liste.
  Exemple : 2/2 = 1,0 ; 1/2 = 0,5 ; 0/2 = 0,0.
- **Lignes 122 à 124 :** on met bout à bout les verdicts des 3 lancements dans une seule liste `tous`
  (`+=` ajoute une liste au bout d'une autre), pour compter les totaux.
- **Ligne 126 :** la moyenne des taux : (1,0 + 0,5 + 0,0) / 3 = 0,5.
- **Ligne 127 :** l'écart type des taux : 0,5. `stdev` a besoin d'au moins 2 valeurs (on ne mesure pas la
  dispersion d'un seul nombre) : d'où le `None` en mode rapide, avec un seul lancement.

C'est exactement le test `test_resume_moyenne_et_dispersion`.

---

### Morceau 6 : `evaluer`, la grande boucle (lignes 132 à 163)

Code de `nutri/evaluation.py`, lignes 132 à 163 (le numéro de ligne est à gauche de la barre) :

```python
132 | def evaluer(n_lancements: int = N_LANCEMENTS, n_taches: int = None) -> dict:
133 |     df = charger_donnees()
134 |     taches = construire_taches(df)[:n_taches]
135 |     systemes = {"complet": True, "modele_seul": False}     # nom -> avec_outils
136 |     verdicts = {"complet": [], "modele_seul": []}
137 |     details = []                                          # toutes les traces, pour expliquer les échecs
138 | 
139 |     for lancement in range(n_lancements):
140 |         for nom in systemes:
141 |             verdicts[nom].append([])
142 |         for i, tache in enumerate(taches):
143 |             for nom, avec_outils in systemes.items():
144 |                 trace = repondre(tache["question"], df, avec_outils=avec_outils)
145 |                 verdict = juger(tache, trace)
146 |                 verdicts[nom][lancement].append(verdict)
147 |                 details.append({"lancement": lancement + 1, "tache": i + 1, "systeme": nom,
148 |                                 "attendu": tache["attendu"], "verdict": verdict, "trace": trace})
149 |                 print(f"lancement {lancement + 1}, question {i + 1:2d}, {nom:11s} : {verdict}")
150 | 
151 |     resume = {}
152 |     par_question = {}     # pour chaque question, ses verdicts aux 3 lancements, ex. ["juste", "juste", "bloquee"]
153 |     for nom in systemes:
154 |         resume[nom] = resumer(verdicts[nom])
155 |         par_question[nom] = []
156 |         for i in range(len(taches)):
157 |             verdicts_question = []
158 |             for l in range(n_lancements):
159 |                 verdicts_question.append(verdicts[nom][l][i])
160 |             par_question[nom].append(verdicts_question)
161 | 
162 |     return {"date": time.strftime("%Y-%m-%d %H:%M"), "questions": [t["question"] for t in taches],
163 |             "resume": resume, "par_question": par_question, "details": details}
```

- **Ligne 134 :** `construire_taches(df)[:n_taches]` garde les `n_taches` premières questions. Avec `None` (par
  défaut), `[:None]` les garde **toutes**. Le mode rapide met `n_taches=2`.
- **Ligne 135 :** les deux systèmes, sous forme nom → `avec_outils`.
- **Lignes 139 à 149 : trois boucles l'une dans l'autre** (lancements, puis questions, puis systèmes) :
  - lignes 140 et 141 : au début de chaque lancement, une liste vide de verdicts pour chaque système ;
  - ligne 142 : `enumerate` donne le numéro de la question (`i`, à partir de 0) en plus de la question ;
  - ligne 144 : **on pose vraiment la question à Qwen**, avec la fonction `repondre` d'`agent.py` ;
  - ligne 145 : le verdict ;
  - lignes 147 et 148 : on garde **toute la trace** dans `details` : c'est là qu'on va chercher un échec ;
  - ligne 149 : une ligne de suivi dans le terminal, par exemple `lancement 1, question  4, complet     : juste`.
- **Lignes 151 à 160 :** le résumé de chaque système, et les verdicts rangés **par question** (ex.
  `["juste", "juste", "bloquee"]`), pour le tableau.
- **Lignes 162 et 163 :** tout est renvoyé dans un grand dictionnaire.

---

### Morceau 7 : le tableau et le lancement (lignes 166 à 197)

Code de `nutri/evaluation.py`, lignes 166 à 197 (le numéro de ligne est à gauche de la barre) :

```python
166 | def ecrire_tableau(res: dict) -> str:
167 |     """Un tableau Markdown lisible des résultats."""
168 |     lignes = ["# Brique 9 : système complet contre modèle seul", "",
169 |               f"Évaluation du {res['date']}. Verdicts des lancements, question par question "
170 |               "(J = juste, F = fausse, B = bloquée).", "",
171 |               "| # | Question | Complet | Modèle seul |", "|---|---|---|---|"]
172 |     lettre = {"juste": "J", "fausse": "F", "bloquee": "B"}
173 |     for i, q in enumerate(res["questions"]):
174 |         complet = " ".join(lettre[v] for v in res["par_question"]["complet"][i])
175 |         seul = " ".join(lettre[v] for v in res["par_question"]["modele_seul"][i])
176 |         lignes.append(f"| {i + 1} | {q} | {complet} | {seul} |")
177 |     lignes += ["", "| Système | Taux de réponses justes (moyenne ± écart type) | Justes | Fausses | Bloquées |",
178 |                "|---|---|---|---|---|"]
179 |     for nom, r in res["resume"].items():
180 |         lignes.append(f"| {nom} | {r['taux_juste_moyen']:.0%} ± {r['ecart_type'] or 0:.0%} "
181 |                       f"| {r['justes']} | {r['fausses']} | {r['bloquees']} |")
182 |     return "\n".join(lignes) + "\n"
183 | 
184 | 
185 | if __name__ == "__main__":
186 |     parser = argparse.ArgumentParser()
187 |     parser.add_argument("--rapide", action="store_true", help="2 questions, 1 lancement")
188 |     args = parser.parse_args()
189 |     if args.rapide:
190 |         res = evaluer(n_lancements=1, n_taches=2)
191 |     else:
192 |         res = evaluer()
193 |     DOSSIER.mkdir(exist_ok=True)
194 |     (DOSSIER / "evaluation.json").write_text(json.dumps(res, ensure_ascii=False, indent=2, default=str),
195 |                                              encoding="utf-8")
196 |     (DOSSIER / "evaluation.md").write_text(ecrire_tableau(res), encoding="utf-8")
197 |     print("\n" + ecrire_tableau(res))
```

- **`ecrire_tableau` :** fabrique le tableau Markdown, avec une lettre par verdict (J = juste, F = fausse,
  B = bloquée). `" ".join(...)` colle les lettres avec un espace : `"J J B"`. `:.0%` affiche un nombre en
  pourcentage sans décimale : 0,729 → « 73% ».
- **Le lancement (lignes 185 à 197) :** l'option `--rapide` ; on écrit le JSON et le tableau ; on affiche le tableau.

---

## 4. Les résultats en détail, et ce qu'ils montrent

**Le vrai tableau (J = juste, F = fausse, B = bloquée ; un verdict par lancement) :**

| # | Question | Complet | Modèle seul |
|---|---|---|---|
| 1 | Combien de céréales y a-t-il dans les données ? | J J J | F F F |
| 2 | Combien de céréales bio ? | J J J | F F F |
| 3 | Combien ont un Nutri-Score A ? | J J J | F F F |
| 4 | Sucres des céréales bio ? | B J J | F J F |
| 5 | Sucres des non bio ? | J J J | F F F |
| 6 | Sel des bio ? | J J J | F F F |
| 7 | Calories pour 100 g ? | J J J | F F F |
| 8 | Protéines ? | J J J | F F F |
| 9 | Fibres au Nutri-Score A ? | J J J | F F F |
| 10 | Écart de sucres bio − non bio ? | J J J | F F F |
| 11 | Marque la moins sucrée ? | F F F | F F F |
| 12 | Plus de lipides chez les bio ? | J J J | J J J |
| 13 | Portion de 30 g (piège) | B B F | F F F |
| 14 | Écart A / E (piège) | B B B | F F F |
| 15 | Vitamine C (piège) | J J J | F J J |
| 16 | Riches en sucres ? (piège) | B B F | F F F |

**Ce que montrent les traces :**
- **Les outils changent tout.** Sans eux, Qwen ne connaît pas nos données : il dit « j'ai besoin d'un outil », ou
  il **invente** (17 réponses sur 48), souvent avec une fausse marge et en prétendant avoir consulté un outil.
  Exemple : « 6,8 g ± 1,4 g » pour les sucres des bio (la vraie valeur est 13,17 g).
- **Le garde-fou a bloqué 8 réponses, toutes à raison :** 5 calculs faits par Qwen (portion, écart A / E), un
  « 4,42 g de moins » au lieu de 5,42 (question 4), et 2 réponses de mémoire après des appels refusés.
- **Le coût :** le système complet met environ 19 secondes par question et lit en moyenne 2 668 tokens ; le modèle
  seul 13 secondes et 196 tokens.

### L'échec expliqué à partir de sa trace (question 11, système complet, lancement 1)
« Quelle marque (au moins 5 produits) a la teneur moyenne en sucres la plus basse ? » Bonne réponse : jardin bio
etic, 6,5 g.
1. Qwen appelle `classement_marques(nutriment="sucres", n=10, ordre="decroissant", min_produits=5)`. Il a choisi
   l'ordre **décroissant** : l'outil renvoie les marques les **plus** sucrées en premier.
2. Il lit la première de la liste comme la moins sucrée : « la marque Crownfield a la teneur moyenne en sucres la
   plus basse avec 18,61 g ».
3. Le garde-fou laisse passer : 18,61 vient bien d'un outil. **Il vérifie l'origine des chiffres, pas le sens de
   la phrase.**

Fausse aux 3 lancements. Mais lors de la première évaluation, 30 minutes plus tôt, la même question était juste
3 fois sur 3 (avec `ordre="croissant"`). Le comportement de Qwen change d'un passage à l'autre.

### D'autres échecs tirés des traces
- **La règle n° 2 peut empêcher de répondre** (question 13, lancement 3) : Qwen fait 7 appels filtrés, reçoit
  7 refus, et la boucle s'arrête à `MAX_TOURS` sans réponse.
- **Un nom d'outil inventé** (question 16, lancement 2) : 3 appels à « descrire », refusés, puis une réponse de
  mémoire (« entre 12 et 25 g »), bloquée.

### Les faux positifs du jugement, gardés volontairement (une décision de la séance 4)
- **Question 12, modèle seul, « juste » 3 fois sur 3 :** les trois réponses **inventent** des moyennes
  (« 3,2 g ± 0,4 g » au lieu de 10,69 g) mais écrivent « pas significatif ». Le jugement « prudence » ne cherche
  que des mots : il ne vérifie pas les chiffres.
- **Question 4, modèle seul, lancement 2 :** il invente 4 valeurs et en donne la moyenne ; l'une d'elles, 13,2 g,
  tombe à 2 % de la bonne réponse. Juste par chance.
- **La décision :** on aurait pu corriger le jugement et rejuger les traces (le modèle seul serait descendu vers
  6 %). On a choisi de **garder ces faux positifs et de les montrer** : malgré les outils, le garde-fou et le
  prompt, le système se trompe, et la mesure elle-même a des erreurs. Corriger un chiffre après avoir vu les
  résultats aurait été moins honnête.

---

## 5. Les limites (à dire soi-même)

- 16 questions et 3 lancements, c'est peu : la question 11 a changé d'un passage à l'autre.
- Le jugement par nombres et par mots-clés ne lit pas le sens (les faux positifs ci-dessus).
- Le modèle seul garde le même prompt, qui lui parle d'outils qu'il n'a pas : il répond souvent « j'ai besoin
  d'un outil ».
- Les questions sont écrites par nous : un vrai utilisateur poserait des questions plus variées.

---

## 6. Questions d'examinateur, avec leurs réponses

**Q1. Que compare la brique 9 ?** Le système complet (Qwen + outils + garde-fou) et le modèle seul, sur 16
questions à réponse connue, 3 lancements chacune. On mesure ce qu'apportent les outils et le garde-fou.

**Q2. Comment connaissez-vous les bonnes réponses ?** Calculées directement avec pandas, sans `tools.py` : une
vérification indépendante.

**Q3. Pourquoi 3 lancements ?** Qwen ne répond pas deux fois pareil : il faut une moyenne et une dispersion.

**Q4. Que veut dire « à 2 % près », et pourquoi un minimum de 0,01 ?** Un nombre est juste s'il s'écarte de moins de
2 % de la bonne réponse. Le minimum vient des arrondis à 2 décimales des outils (0,13 pour 0,1265).

**Q5. Pourquoi tester `bloquee` en premier ?** Le message de refus contient les nombres refusés : sans ce test, un
refus pourrait être compté juste par accident.

**Q6. Une réponse bloquée est-elle un échec ?** Ni une erreur (rien de faux n'a été affirmé), ni une réussite
(pas de réponse) : on la compte à part.

**Q7. Que mesure l'écart type ici ?** De combien le taux de réponses justes change d'un lancement à l'autre :
4 % pour le système complet, 6 % pour le modèle seul.

**Q8. Pourquoi des questions pièges ?** Sans elles, le système avait 100 % : les questions étaient trop faciles.
Les pièges montrent ses failles connues.

**Q9. Racontez un échec à partir de sa trace.** Question 11 : Qwen demande le classement des marques en ordre
décroissant, puis lit la plus sucrée (Crownfield, 18,61 g) comme la moins sucrée. Le garde-fou laisse passer,
car 18,61 vient d'un outil.

**Q10. Pourquoi avoir gardé les faux positifs ?** Pour montrer honnêtement que la mesure a aussi des erreurs,
plutôt que de corriger un chiffre après avoir vu les résultats.

---

## 7. Résumé en 5 phrases

1. `evaluation.py` pose 16 questions à réponse connue (dont 4 pièges), 3 fois chacune, au système complet et au modèle seul.
2. Les bonnes réponses sont calculées avec pandas, indépendamment des outils.
3. Chaque réponse est jugée juste (à 2 % près, ou bon texte, ou prudence, ou aucun chiffre inventé), fausse ou bloquée.
4. Résultat : 73 % ± 4 % de réponses justes pour le système complet, 12 % ± 6 % pour le modèle seul, qui invente des chiffres.
5. L'échec expliqué : un classement décroissant lu à l'envers, que le garde-fou laisse passer car il ne vérifie pas le sens.
