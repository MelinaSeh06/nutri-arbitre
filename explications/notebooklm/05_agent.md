# Nutri-Arbitre — Fichier 5 : `agent.py`, le chef d'orchestre

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

`agent.py` relie tout. Il envoie la question à Qwen, exécute les outils que Qwen demande, lui renvoie les
résultats, recommence jusqu'à ce que Qwen donne sa réponse finale, puis fait passer cette réponse par le
garde-fou avant de l'afficher. Il enregistre aussi une **trace** de tout ce qui s'est passé.

**L'idée la plus importante : Qwen ne lance rien lui-même.** Il écrit seulement une **demande** (« appelle
`decrire` avec `nutriment="sucres"`, `bio=True` »). C'est `agent.py` qui décide de l'exécuter ou non, et c'est
Python qui fait le calcul. C'est la **brique 1** (appel d'outils).

**Comment on le lance :**
```
python -m nutri.agent "Les céréales bio contiennent-elles moins de sucre ?"
python -m nutri.agent --modele-seul "Les céréales bio contiennent-elles moins de sucre ?"
```

**Le trajet d'une question :**
```
question ──► Qwen ──► « appelle decrire(sucres, bio=True) »
                           │
         agent.py vérifie les filtres (règle n° 2), puis exécute tools.decrire
                           │
         résultat {"n": 543, "moyenne": 13.17, ...} ──► renvoyé à Qwen
                           │
         Qwen écrit sa réponse en français (plus aucun outil demandé)
                           │
         règle n° 1 : chaque nombre vient-il d'un outil ? ──► réponse affichée ou bloquée
```

---

## 2. Les notions à connaître avant de lire le code

### Ollama et la fonction `chat`
**Ollama** est le logiciel qui fait tourner Qwen sur l'ordinateur. La bibliothèque Python `ollama` permet de
lui parler avec la fonction `chat(...)` : on lui donne le nom du modèle et la conversation, il renvoie la
réponse du modèle.

### Une conversation = une liste de messages
Un modèle de langage **n'a pas de mémoire** d'un appel à l'autre. À chaque fois, on lui renvoie **toute** la
conversation, sous forme d'une liste de messages. Chaque message a un **rôle** :

| Rôle | Qui parle | Contenu |
|---|---|---|
| `system` | nous, une fois au début | le prompt système (les règles du jeu) |
| `user` | l'utilisateur | la question |
| `assistant` | Qwen | une demande d'outil, ou sa réponse finale |
| `tool` | nos outils Python | le résultat d'un calcul, en texte JSON |

### Les tokens
Un modèle ne lit pas des mots mais des **tokens** (des morceaux de mots, environ 3 à 4 lettres en moyenne).
On compte les tokens **lus** (l'entrée) et **écrits** (la sortie) : c'est le coût de chaque réponse.

### La longueur de contexte
C'est le nombre maximal de tokens que le modèle peut lire en une fois. On l'a fixée à **8192** (la consigne
demande de la fixer). Toute la conversation doit tenir dedans.

---

## 3. Le code, morceau par morceau

### Morceau 1 : l'en-tête et les réglages (lignes 1 à 23)

Code de `nutri/agent.py`, lignes 1 à 23 (le numéro de ligne est à gauche de la barre) :

```python
  1 | """La boucle d'agent : le modèle lit la question, appelle les outils, puis répond.
  2 | La réponse finale passe par le garde-fou avant d'être affichée.
  3 | 
  4 | Usage :
  5 |   python -m nutri.agent "Les céréales bio contiennent-elles moins de sucre ?"
  6 |   python -m nutri.agent --modele-seul "..."   # le modèle sans outils ni garde-fou (pour la brique 9)
  7 | """
  8 | import argparse
  9 | import json
 10 | import os
 11 | import time
 12 | from pathlib import Path
 13 | 
 14 | import pandas as pd
 15 | from ollama import chat
 16 | 
 17 | from nutri import garde_fou, tools
 18 | 
 19 | MODELE = os.environ.get("NUTRI_MODELE", "qwen3.5:4b-q4_K_M")
 20 | OPTIONS = {"num_ctx": 8192}          # longueur de contexte fixée (cf. consigne, section 2)
 21 | MAX_TOURS = 6                        # au-delà, on arrête la boucle
 22 | DONNEES = Path("data/cereales_propres.csv")
 23 | DOSSIER_TRACES = Path("traces")
```

- **Ligne 15 : `from ollama import chat`**, la fonction pour parler à Qwen.
- **Ligne 17 :** on importe nos propres fichiers, le garde-fou et les outils.
- **Ligne 19 : `MODELE`.** `os.environ.get("NUTRI_MODELE", ...)` lit une **variable d'environnement** (un
  réglage de l'ordinateur). Si elle n'existe pas, on prend la valeur par défaut : le modèle imposé par la
  consigne. On peut ainsi tester un autre modèle sans changer le code.
- **Ligne 20 : `OPTIONS`**, la longueur de contexte : 8192 tokens.
- **Ligne 21 : `MAX_TOURS = 6`**, une sécurité. Si Qwen demande des outils sans jamais conclure, on arrête au bout
  de 6 tours au lieu de tourner à l'infini.
- **Lignes 22 et 23 :** les données propres, et le dossier où ranger les traces.

---

### Morceau 2 : le prompt système (lignes 25 à 30)

Code de `nutri/agent.py`, lignes 25 à 30 (le numéro de ligne est à gauche de la barre) :

```python
 25 | PROMPT_SYSTEME = """Tu es un analyste nutrition. Tu réponds en français à des questions sur les
 26 | céréales du petit-déjeuner vendues en France (données Open Food Facts, valeurs pour 100 g).
 27 | Pour tout chiffre, appelle un outil : n'écris jamais un nombre que tu n'as pas reçu d'un outil.
 28 | Recopie les nombres tels que les outils les donnent. Réponds en 2 à 4 phrases.
 29 | Quand un outil donne une marge d'erreur (marge_95), écris-la : « 13,2 g ± 0,9 g ».
 30 | Si difference_nette vaut false, dis que l'écart peut venir du hasard et qu'on ne peut pas conclure."""
```

C'est le texte qui explique à Qwen son rôle, envoyé au début de chaque conversation. Il fixe :
- le **rôle** (analyste nutrition) et le **sujet** (céréales vendues en France, valeurs pour 100 g) ;
- la **règle** : tout chiffre vient d'un outil, et on recopie les nombres tels quels ;
- la **forme** : 2 à 4 phrases ; la marge d'erreur écrite « 13,2 g ± 0,9 g » (brique 8) ;
- la **prudence** : si `difference_nette` vaut false, dire que l'écart peut venir du hasard.

**Le prompt demande, le garde-fou impose.** Qwen ne respecte pas toujours ce prompt : il oublie parfois la marge,
ou calcule lui-même une portion. C'est pour ça que la règle des chiffres est aussi vérifiée par le code.

---

### Morceau 3 : charger les données (lignes 33 et 34)

Code de `nutri/agent.py`, lignes 33 à 34 (le numéro de ligne est à gauche de la barre) :

```python
 33 | def charger_donnees() -> pd.DataFrame:
 34 |     return pd.read_csv(DONNEES, dtype={"code": str})
```

`dtype={"code": str}` : la colonne `code` (le code-barres) est lue comme du **texte**. Sinon pandas la lirait
comme un nombre et supprimerait les zéros du début (« 0012345 » deviendrait 12345), ou l'écrirait en notation
scientifique.

---

### Morceau 4 : `executer_outil`, exécuter la demande de Qwen (lignes 37 à 52)

Code de `nutri/agent.py`, lignes 37 à 52 (le numéro de ligne est à gauche de la barre) :

```python
 37 | def executer_outil(df, nom: str, arguments: dict, question: str = "") -> dict:
 38 |     """Appelle la fonction Python demandée par le modèle. Une erreur est renvoyée au modèle,
 39 |     au lieu de faire planter le programme, pour qu'il puisse corriger son appel."""
 40 |     if nom not in tools.FONCTIONS:
 41 |         return {"erreur": f"outil inconnu : {nom}"}
 42 |     # garde-fou n° 2 : pas de filtre bio / Nutri-Score si la question n'en parle pas
 43 |     probleme = garde_fou.verifier_filtres(question, arguments)
 44 |     if probleme is not None:
 45 |         return {"erreur": probleme}
 46 |     fonction = tools.FONCTIONS[nom]          # ex. "decrire" -> la fonction tools.decrire
 47 |     try:
 48 |         # **arguments « déballe » le dictionnaire : avec {"nutriment": "sucres", "bio": True},
 49 |         # cette ligne revient à écrire  tools.decrire(df, nutriment="sucres", bio=True)
 50 |         return fonction(df, **arguments)
 51 |     except (ValueError, TypeError) as e:
 52 |         return {"erreur": str(e)}
```

Trois contrôles, dans l'ordre :

1. **L'outil existe-t-il ? (lignes 40 et 41)** `tools.FONCTIONS` est le dictionnaire nom → fonction. Si Qwen
   invente un outil, on refuse. **Seules nos 4 fonctions peuvent être lancées** : Qwen ne peut pas exécuter
   n'importe quel code sur l'ordinateur. Vrai cas de l'évaluation : Qwen a appelé « descrire » (faute de frappe)
   et a reçu `{"erreur": "outil inconnu : descrire"}`.
2. **Les filtres sont-ils permis ? (lignes 43 à 45)** C'est la règle n° 2 du garde-fou : pas de filtre bio ou
   Nutri-Score si la question n'en parle pas. C'est pour ça que la fonction reçoit aussi la `question`.
3. **Les arguments sont-ils corrects ? (lignes 47 à 52)** On exécute dans un `try`. Si Qwen demande un nutriment
   qui n'existe pas, `tools.py` lève une `ValueError`. S'il envoie un argument inconnu (par exemple `nutriments`
   au lieu de `nutriment`), Python lève une `TypeError`. On **attrape** l'erreur avec `except`, et `str(e)`
   donne son message.

**Ligne 46 :** `tools.FONCTIONS[nom]` prend la vraie fonction. Exemple : `"decrire"` → la fonction `tools.decrire`.

**Ligne 50 : `fonction(df, **arguments)`, les deux étoiles.** Qwen envoie ses arguments en dictionnaire :
`{"nutriment": "sucres", "bio": True}`. Les deux étoiles « déballent » le dictionnaire en arguments nommés :
la ligne revient à écrire `tools.decrire(df, nutriment="sucres", bio=True)`. Une seule ligne marche pour les
4 outils, quels que soient leurs arguments.

**Pourquoi renvoyer l'erreur au lieu de planter ?** L'erreur est renvoyée **à Qwen**, comme un résultat d'outil.
Il la lit au tour suivant et peut corriger son appel. Si le programme plantait, l'utilisateur n'aurait aucune
réponse. Vrai cas : Qwen a appelé `classement_marques(nutriments=...)`, a reçu l'erreur
« got an unexpected keyword argument 'nutriments' », et a refait l'appel avec `nutriment`.

---

### Morceau 5 : `repondre`, la préparation (lignes 55 à 70)

Code de `nutri/agent.py`, lignes 55 à 70 (le numéro de ligne est à gauche de la barre) :

```python
 55 | def repondre(question: str, df: pd.DataFrame, avec_outils: bool = True) -> dict:
 56 |     """Pose la question et renvoie une trace complète (appels, résultats, réponse, tokens)."""
 57 |     # la conversation : le rôle du modèle (system) puis la question (user)
 58 |     messages = [{"role": "system", "content": PROMPT_SYSTEME},
 59 |                 {"role": "user", "content": question}]
 60 |     # la trace garde tout ce qui s'est passé, pour la sauver en JSON (preuves)
 61 |     trace = {"question": question, "modele": MODELE, "avec_outils": avec_outils,
 62 |              "appels": [], "tokens_entree": 0, "tokens_sortie": 0}
 63 |     resultats = []           # tous les résultats d'outils : le garde-fou s'en sert à la fin
 64 |     debut = time.time()
 65 |     if avec_outils:
 66 |         outils_proposes = tools.SCHEMAS
 67 |     else:
 68 |         outils_proposes = None
 69 | 
 70 |     reponse_brute = None     # restera None si le modèle n'a pas fini au bout de MAX_TOURS
```

- **Lignes 58 et 59 :** la conversation commence avec deux messages : le prompt système et la question.
- **Lignes 61 et 62 : la trace**, un dictionnaire qui gardera tout : la question, le modèle, la liste des appels
  d'outils, et les compteurs de tokens (à 0 au départ).
- **Ligne 63 : `resultats`**, la liste de tous les résultats d'outils. Le garde-fou s'en servira à la fin pour
  savoir quels nombres sont autorisés.
- **Ligne 64 :** l'heure de départ, pour mesurer la durée.
- **Lignes 65 à 68 : avec ou sans outils.** Si `avec_outils` est faux, on ne propose **aucun** outil à Qwen :
  c'est le « modèle seul », qui doit répondre de mémoire. On le compare au système complet dans la brique 9.
- **Ligne 70 :** `reponse_brute` vaut `None` au départ. Elle restera `None` si Qwen n'a pas fini au bout de
  6 tours.

---

### Morceau 6 : la boucle, 3 étapes par tour (lignes 71 à 93)

Code de `nutri/agent.py`, lignes 71 à 93 (le numéro de ligne est à gauche de la barre) :

```python
 71 |     for tour in range(MAX_TOURS):
 72 |         # 1. on envoie toute la conversation au modèle
 73 |         r = chat(model=MODELE, messages=messages, tools=outils_proposes,
 74 |                  options=OPTIONS, think=False)   # think=False : pas de « réflexion » cachée, plus rapide
 75 |         trace["tokens_entree"] += r.prompt_eval_count or 0
 76 |         trace["tokens_sortie"] += r.eval_count or 0
 77 |         messages.append(r.message)   # sa réponse fait désormais partie de la conversation
 78 | 
 79 |         # 2. s'il ne demande aucun outil, c'est sa réponse finale : on sort de la boucle
 80 |         if not r.message.tool_calls:
 81 |             reponse_brute = r.message.content or ""
 82 |             break
 83 | 
 84 |         # 3. sinon, on exécute chaque outil demandé et on lui renvoie le résultat
 85 |         for appel in r.message.tool_calls:
 86 |             nom = appel.function.name
 87 |             args = dict(appel.function.arguments or {})
 88 |             resultat = executer_outil(df, nom, args, question)
 89 |             resultats.append(resultat)
 90 |             trace["appels"].append({"outil": nom, "arguments": args, "resultat": resultat})
 91 |             messages.append({"role": "tool", "tool_name": nom,
 92 |                              "content": json.dumps(resultat, ensure_ascii=False)})
 93 |         # puis on recommence un tour : le modèle lit les résultats et continue
```

**Étape 1 : on envoie toute la conversation à Qwen (lignes 73 à 77).**
- `chat(...)` reçoit le modèle, la conversation, la liste des outils (`tools.SCHEMAS`, ou `None` pour le modèle
  seul) et les options.
- `think=False` coupe la « réflexion » cachée de Qwen (un long texte qu'il écrit avant de répondre). Mesure
  faite en séance 1 : 71 secondes par question avec la réflexion, 29 secondes sans.
- Lignes 75 et 76 : on ajoute les tokens lus et écrits. `or 0` : si Ollama ne donne pas le nombre (`None`), on
  ajoute 0 au lieu de planter.
- Ligne 77 : la réponse de Qwen est **ajoutée à la conversation**. Au tour suivant, il verra ce qu'il a demandé.

**Étape 2 : pas d'outil demandé ? C'est la réponse finale (lignes 80 à 82).** `r.message.tool_calls` est la liste
des outils que Qwen demande. Si elle est vide, Qwen a écrit sa réponse : on la garde et `break` sort de la
boucle. `or ""` : si le contenu est vide, un texte vide.

**Étape 3 : sinon, on exécute chaque outil demandé (lignes 85 à 92).** Qwen peut demander plusieurs outils d'un
coup. Pour chacun :
- son nom et ses arguments (`dict(... or {})` : un outil sans argument, comme `compter`, peut arriver avec `None`) ;
- on l'exécute avec `executer_outil` ;
- on garde le résultat pour le garde-fou et pour la trace ;
- on ajoute le résultat à la conversation avec le rôle `tool`. `json.dumps` transforme le dictionnaire en texte,
  car un message est toujours du texte. `ensure_ascii=False` garde les accents.

Puis la boucle recommence : Qwen lit les résultats et continue.

---

### Morceau 7 : la fin, le garde-fou (lignes 95 à 105)

Code de `nutri/agent.py`, lignes 95 à 105 (le numéro de ligne est à gauche de la barre) :

```python
 95 |     if reponse_brute is None:
 96 |         reponse_brute = "Je n'ai pas réussi à répondre en un nombre raisonnable d'étapes."
 97 | 
 98 |     trace["reponse_brute"] = reponse_brute
 99 |     if avec_outils:   # le système complet : la barrière s'applique
100 |         trace["reponse"] = garde_fou.filtrer_reponse(reponse_brute, resultats, question)
101 |     else:             # le modèle seul : aucune vérification
102 |         trace["reponse"] = reponse_brute
103 |     trace["bloquee"] = trace["reponse"] != reponse_brute
104 |     trace["duree_s"] = round(time.time() - debut, 1)
105 |     return trace
```

- **Lignes 95 et 96 :** si `reponse_brute` vaut encore `None`, les 6 tours sont passés sans réponse finale : on
  met un message d'échec.
- **Lignes 99 et 100 : la règle n° 1 du garde-fou**, seulement pour le système complet. `filtrer_reponse` renvoie
  la réponse si elle est propre, sinon le message de refus.
- **Lignes 101 et 102 :** pour le modèle seul, aucune vérification (c'est le but : voir ce qu'il fait sans aide).
- **Ligne 103 : `bloquee`** vaut `True` si la réponse affichée est différente de celle de Qwen, donc si le
  garde-fou l'a remplacée.
- **Ligne 104 :** la durée, arrondie à 0,1 seconde.

La trace garde **les deux versions** : `reponse_brute` (ce que Qwen a écrit) et `reponse` (ce qui est affiché).
C'est ce qui permet d'expliquer un blocage après coup.

---

### Morceau 8 : enregistrer la trace (lignes 108 à 112)

Code de `nutri/agent.py`, lignes 108 à 112 (le numéro de ligne est à gauche de la barre) :

```python
108 | def sauver_trace(trace: dict) -> Path:
109 |     DOSSIER_TRACES.mkdir(exist_ok=True)
110 |     chemin = DOSSIER_TRACES / f"trace_{time.strftime('%Y%m%d_%H%M%S')}.json"
111 |     chemin.write_text(json.dumps(trace, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
112 |     return chemin
```

- **Ligne 109 :** on crée le dossier `traces/` s'il n'existe pas.
- **Ligne 110 :** le nom du fichier contient la date et l'heure : `trace_20261102_113921.json` = le 2 novembre
  2026 à 11 h 39 min 21 s. Chaque trace a un nom différent, aucune n'en écrase une autre.
- **Ligne 111 :** on écrit la trace en JSON lisible (`indent=2` ajoute des retraits).

Les traces sont **les preuves** du projet (EVIDENCE.md) : on peut y relire chaque appel d'outil et chaque réponse.

---

### Morceau 9 : le lancement dans le terminal (lignes 115 à 124)

Code de `nutri/agent.py`, lignes 115 à 124 (le numéro de ligne est à gauche de la barre) :

```python
115 | if __name__ == "__main__":
116 |     parser = argparse.ArgumentParser()
117 |     parser.add_argument("question")
118 |     parser.add_argument("--modele-seul", action="store_true", help="sans outils ni garde-fou")
119 |     args = parser.parse_args()
120 |     trace = repondre(args.question, charger_donnees(), avec_outils=not args.modele_seul)
121 |     for a in trace["appels"]:
122 |         print(f"[outil] {a['outil']}({a['arguments']}) -> {a['resultat']}")
123 |     print("\n" + trace["reponse"])
124 |     print(f"\n(trace : {sauver_trace(trace)})")
```

- **Ligne 115 :** le bloc ne tourne que si on lance le fichier directement (pas quand les tests l'importent).
- **Lignes 116 à 119 :** `argparse` lit la question, et l'option `--modele-seul`. `action="store_true"` :
  l'option vaut `True` si on l'écrit, `False` sinon.
- **Ligne 120 :** `avec_outils=not args.modele_seul` : avec l'option, pas d'outils ni de garde-fou.
- **Lignes 121 à 124 :** on affiche chaque appel d'outil (`[outil] decrire({...}) -> {...}`), la réponse, et le
  chemin de la trace.

---

## 4. Un exemple réel complet, tour par tour

**Trace `traces/trace_20261102_113921.json`**, question : « Combien de calories apporte une portion de 30 g de
céréales, en moyenne ? »

| Tour | Ce qui se passe |
|---|---|
| 1 | Qwen demande `decrire(nutriment="energie_kcal", bio=False)`. `executer_outil` refuse (règle n° 2) : « la question ne parle pas de bio… utilise decrire sur toutes les céréales ». Ce refus est ajouté à la conversation (rôle `tool`). |
| 2 | Qwen se corrige : `decrire(nutriment="energie_kcal")` → n = 953, moyenne 409,45 kcal, marge 2,54. |
| 3 | Plus d'outil demandé : réponse finale. « La moyenne… est de 409,45 kcal pour 100 g. Pour une portion de 30 g, cela représente environ 122,84 kcal (409,45 × 0,30)… » |
| fin | Règle n° 1 : 122,84 et 0,30 ne viennent pas d'un outil → **bloquée**. `bloquee = True`. 3 497 tokens lus en tout, 17,8 secondes. |

**Et une réponse acceptée** (trace `trace_20261102_113831.json`) : « Quelle est la teneur moyenne en sel des
céréales bio ? » → un seul appel, `decrire(sel, bio=True)` → « La teneur moyenne en sel des céréales bio est de
0,13 g pour 100 g, avec une marge d'erreur de ± 0,02 g. Cela représente une fourchette comprise entre 0,11 et
0,15 g. » Tous les nombres viennent de l'outil : la réponse est affichée.

---

## 5. Les pièges et les erreurs fréquentes

- **Qwen n'exécute rien :** il écrit une demande, `agent.py` l'exécute.
- **Le modèle n'a pas de mémoire :** c'est pour ça qu'on renvoie toute la liste `messages` à chaque tour, et que
  le nombre de tokens lus augmente à chaque tour (environ 2 300 avec un outil, 3 500 avec deux tours d'outils).
- **`**arguments`** déballe un dictionnaire en arguments nommés.
- **Une erreur d'outil n'arrête pas le programme :** elle est renvoyée à Qwen.
- **Qwen ne répond pas deux fois pareil :** à la même question, il a choisi trois filtres différents en 10 minutes.

---

## 6. Questions d'examinateur, avec leurs réponses

**Q1. Qui fait le calcul de la moyenne : Qwen ou Python ?** Python. Qwen écrit seulement une demande ; `agent.py`
exécute la fonction de `tools.py` et renvoie le résultat à Qwen avec le rôle `tool`.

**Q2. Pourquoi renvoie-t-on toute la liste `messages` à chaque tour ?** Le modèle n'a pas de mémoire. Pour qu'il
connaisse la question, ses demandes et les résultats, il faut tout lui renvoyer.

**Q3. À quoi sert `MAX_TOURS` ?** À éviter une boucle sans fin : au bout de 6 tours, on s'arrête avec un message
d'échec. C'est arrivé dans l'évaluation : Qwen a fait 7 appels filtrés refusés.

**Q4. Comment la boucle sait-elle que Qwen a fini ?** Sa réponse ne contient aucune demande d'outil
(`tool_calls` vide).

**Q5. Expliquez `fonction(df, **arguments)`.** Les deux étoiles déballent le dictionnaire : avec
`{"nutriment": "sucres", "bio": True}`, c'est `tools.decrire(df, nutriment="sucres", bio=True)`.

**Q6. Pourquoi renvoyer `{"erreur": ...}` au lieu de planter ?** Pour que Qwen lise l'erreur et corrige son appel.

**Q7. Qwen peut-il exécuter n'importe quel code ?** Non : seulement les 4 outils de `tools.FONCTIONS`. Un autre
nom donne « outil inconnu ».

**Q8. Différence entre `reponse_brute` et `reponse` ?** `reponse_brute` est ce que Qwen a écrit ; `reponse` est ce
qui est affiché après le garde-fou. Si elles diffèrent, la réponse a été bloquée.

**Q9. À quoi sert `--modele-seul` ?** À lancer Qwen sans outils ni garde-fou, pour mesurer dans la brique 9 ce
qu'apportent les outils et la règle.

**Q10. À quoi sert `think=False` ?** À couper la réflexion cachée de Qwen : 29 secondes par question au lieu de 71.

---

## 7. Résumé en 5 phrases

1. `agent.py` envoie la question et toute la conversation à Qwen, avec la liste des outils disponibles.
2. Quand Qwen demande un outil, `executer_outil` vérifie qu'il existe, que ses filtres sont permis, puis l'exécute et renvoie le résultat (ou l'erreur) à Qwen.
3. La boucle recommence jusqu'à ce que Qwen réponde sans demander d'outil, avec au plus 6 tours.
4. La réponse finale passe par le garde-fou : si un nombre ne vient pas d'un outil, elle est bloquée.
5. Tout est enregistré dans une trace JSON : ce sont les preuves du projet.
