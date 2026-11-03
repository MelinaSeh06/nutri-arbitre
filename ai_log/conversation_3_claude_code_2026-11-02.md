# Conversation avec Claude Code — séance du 2026-11-02

Export du journal de la session (extension VS Code). Les messages sont reproduits tels quels ; les actions de l'IA (commandes, lectures, modifications de fichiers) sont résumées en une ligne.


---

## Moi (11:29)

bonjour, passons a la seance d'aujourd'hui


## Claude (11:30)


Bonjour ! Séance 3 : aujourd'hui, on fait `garde_fou.py` puis `agent.py`. Je vérifie d'abord que tout est en ordre, et je relis le garde-fou tel qu'il est maintenant.

> 🔧 Commande : Check repo state, tests, model and read garde_fou

> 🔧 Commande : Run Qwen on two portion questions to trigger the guard

> 🔧 Commande : Show raw model answers in the two blocked traces

> 🔧 Commande : Walk through the guard step by step on a real trace

> 🔧 Modification : nutri/garde_fou.py

> 🔧 Modification : tests/test_garde_fou.py

> 🔧 Commande : Run the test suite


Les 33 tests passent. J'écris la fiche du garde-fou.

> 🔧 Commande : Get line numbers in garde_fou.py

> 🔧 Écriture : explications/sources/04_garde_fou.html

> 🔧 Commande : Verify loop lines and render garde_fou fiche


La fiche venait d'être générée quand ton message est arrivé. Je la mettrai à jour selon ce qu'on décide, donc ce n'est pas un problème.

Ta question est très bonne : c'est exactement la limite qu'on vient de voir avec la question des calories. **Oui, on peut empêcher une partie des filtres erronés par le code**, mais pas tous. Voici ce qui est faisable.

## Ce qu'on peut vérifier par le code

L'erreur de Qwen à la question 2 : la question ne parlait **pas** de bio, et il a quand même filtré `bio=False`. Ça, un code peut le voir :

> **Règle** : si la question ne parle pas de bio, un outil n'a pas le droit d'utiliser le filtre `bio`. Même chose pour le Nutri-Score : pas de filtre `nutriscore` si la question ne parle pas de Nutri-Score.

« Parler de bio » se détecte avec une liste de mots : bio, biologique, AB, organic… Même méthode pour le Nutri-Score.

## Deux façons de l'appliquer

1. **Bloquer la réponse finale**, comme pour les chiffres. Mais Qwen a déjà gaspillé son tour, et l'utilisateur reçoit seulement un refus.
2. **Refuser l'appel d'outil au moment où Qwen le fait** et lui renvoyer une erreur : « la question ne parle pas de bio, n'utilise pas le filtre bio ». Qwen peut alors **corriger son appel et réessayer**, comme il le fait déjà quand il demande un nutriment qui n'existe pas. Le résultat filtré n'arrive jamais jusqu'à lui, donc il ne peut pas s'en servir.

**Je te conseille la 2.** La règle reste imposée par le code, et en plus Qwen a une chance de donner une bonne réponse au lieu d'un refus. Ça renforce aussi la brique 3 : on aura deux règles imposées par le code au lieu d'une.

## Ce que le code ne pourra pas voir

- **Un mauvais nutriment** : si Qwen prend `glucides` au lieu de `sucres`, aucune règle simple ne le détecte.
- **Les tournures imprévues** : une question comme « les céréales labellisées sont-elles… » ne contient aucun mot de la liste. La règle bloquerait alors à tort le filtre bio. On peut compléter la liste, mais jamais couvrir tous les cas.
- **Le filtre qui manque** : si la question parle de bio et que Qwen oublie le filtre, c'est plus difficile à juger. « Les céréales bio sont-elles plus sucrées ? » se traite avec `comparer(groupe="bio")`, sans filtre. On ne vérifierait donc que le sens « filtre en trop », qui est l'erreur qu'on a vue.

Ces limites iront dans la fiche, et la brique 9 mesurera combien de fois Qwen se trompe malgré tout.

On part sur l'option 2 ? Si oui, je l'ajoute dans `garde_fou.py`, à côté de la règle des chiffres, avec des tests. Je relance ensuite la question des calories pour voir si Qwen se corrige, puis je mets la fiche à jour.


---

## Moi (11:36)

Oui, on part sur la proposition numéro 2. Mais du coup, est-ce que c'est un défaut de ma part, le fait qu'il n'arrive pas à faire ça, ou c'est ce qui est attendu justement du devoir? Qu'il y ait des limites qu'on ne puisse pas régler?


## Claude (11:37)


Ce n'est **pas un défaut de ta part**. C'est même exactement ce que le devoir attend. Regarde ce que dit la consigne :

- **Section 1** : « un petit système d'IA bâti autour d'un modèle de langage **auquel on ne peut pas se fier d'emblée**, avec le code, les vérifications et les mesures qui rendent ses réponses fiables ». Le point de départ du devoir, c'est que Qwen se trompe.
- **Brique 9** : il faut montrer « **un échec expliqué à partir de sa trace** ». L'examinateur *demande* de voir un échec.
- **Brique 8** : il faut écrire « une phrase sur **ce que vos données ne permettent pas de conclure** ». Les limites doivent être dites.

Ce qui est noté, ce n'est donc pas un système parfait, ça n'existe pas avec un modèle de 4 milliards de paramètres. Ce sont quatre choses, et tu les fais toutes :
1. **repérer** les erreurs : on a trouvé le mauvais filtre en lisant la trace ;
2. **en corriger** une partie par le code : c'est ce qu'on va faire ;
3. **mesurer** ce qui reste : ce sera la brique 9 ;
4. **expliquer honnêtement** les limites : ce sont les fiches, et l'oral.

Un étudiant qui dit « mon système est parfait » inquiète l'examinateur. Une étudiante qui dit « voici l'erreur, voici comment je l'ai bloquée, voici ce qui reste et pourquoi » montre qu'elle comprend son système.

Je code l'option 2.

> 🔧 Modification : nutri/garde_fou.py

> 🔧 Modification : nutri/garde_fou.py


Je branche cette règle dans `agent.py`, au moment où l'outil est appelé.

> 🔧 Lecture : nutri/agent.py

> 🔧 Modification : nutri/agent.py

> 🔧 Commande : Find executer_outil signature

> 🔧 Modification : nutri/agent.py

> 🔧 Modification : nutri/agent.py

> 🔧 Modification : tests/test_garde_fou.py

> 🔧 Modification : tests/test_garde_fou.py

> 🔧 Commande : Run the test suite

> 🔧 Commande : Rerun calorie question and a bio question with Qwen

> 🔧 Commande : Inspect tool calls in the new calorie trace

> 🔧 Modification : nutri/garde_fou.py

> 🔧 Modification : tests/test_garde_fou.py

> 🔧 Commande : Run tests and rerun calorie question twice

> 🔧 Commande : Get updated line numbers in garde_fou and agent

> 🔧 Commande : Add second rule to fiche 04, fix line numbers, render

> 🔧 Commande : Run tests and commit the second guard rule

> 🔧 Modification : memory/avancement-nutri-arbitre.md


La deuxième règle est en place, elle marche avec le vrai Qwen, et tout est commité (`5b88e1d`). Les 36 tests passent. La fiche [explications/04_garde_fou.pdf](explications/04_garde_fou.pdf) est à jour.

## Le garde-fou en bref : deux règles imposées par le code

**Règle 1, aucun chiffre non calculé.** Elle est vérifiée sur la réponse finale, en trois étapes :
1. trouver tous les nombres de la réponse, avec une expression régulière ;
2. faire la liste des nombres autorisés : ceux des outils, ceux de la question, plus 100 et 95 ;
3. vérifier que chaque nombre est un **arrondi correct** d'un nombre autorisé. « 18 » passe pour 18,37, « 19 » ne passe pas.

Si un seul nombre n'a pas d'origine, la réponse est bloquée.

**Règle 2, pas de filtre dont la question ne parle pas.** Elle est vérifiée **au moment de chaque appel d'outil**. Si Qwen filtre ou découpe selon le bio ou le Nutri-Score alors que la question n'en parle pas, le calcul n'est pas fait, et Qwen reçoit une erreur qui lui permet de se corriger.

## Les vraies preuves obtenues aujourd'hui (brique 3)
| Essai | Ce qui s'est passé |
|---|---|
| Bol de 40 g | Qwen a calculé 5,3 g lui-même. Le calcul est juste, mais il est **bloqué**, parce que le garde-fou ne peut pas vérifier un calcul du modèle. |
| Portion de 30 g (avant la règle 2) | Mauvais filtre (non bio seulement), et un calcul faux annoncé comme « exact ». **Bloqué** par la règle 1, mais le filtre n'avait pas été vu. |
| Portion de 30 g (après la règle 2) | Filtre refusé → **Qwen se corrige** et prend toutes les céréales → puis la règle 1 bloque son calcul de portion. Les deux règles ont fonctionné l'une après l'autre. |

## À retenir pour l'oral
- **Le prompt dit la règle, le code la fait respecter.** Malgré le prompt, Qwen a calculé lui-même.
- **Qwen ne répond pas deux fois pareil.** À la même question, il s'est trompé de trois façons différentes en 10 minutes.
- **Les limites qui restent** : un mauvais nutriment, un filtre qui manque, une phrase qui contredit ses chiffres, un nombre écrit en lettres. Ce sont précisément les « échecs expliqués » qu'attend la brique 9.

Les 9 questions d'examinateur sont dans la fiche, avec leur corrigé à part.

Une remarque : les questions de **portion** (« dans un bol de 40 g ») seront toujours bloquées, puisqu'aucun outil ne fait ce calcul. On pourrait ajouter un petit outil `pour_une_portion` pour que le système y réponde. Ce n'est pas nécessaire pour les briques, et ce blocage fait même une très bonne démo pour l'oral. Je te conseille de garder ça comme ça, sauf si tu préfères l'ajouter.

On passe à `agent.py`, le dernier code de la journée ?


---

## Moi (13:04)

explique mieux :  # écart permis = une demi-unité du dernier chiffre écrit
    # "18" -> 0,5 (18,37 est à 0,37 : ok) ; "18,4" -> 0,05 (18,37 est à 0,03 : ok)
    tolerance = 0.5 * 10 ** (-decimales)
    tolerance += 1e-9   # minuscule marge : les ordinateurs calculent 0,1 + 0,2 = 0,30000000000000004

    for a in autorises:
        if abs(valeur - a) <= tolerance:
            return True
    return False


## Claude (13:05)

> 🔧 Commande : Check float rounding examples


## Le problème à résoudre

Qwen reçoit **18,37** de l'outil, puis il écrit souvent un nombre arrondi dans sa réponse : « 18 » ou « 18,4 ». Ces arrondis sont corrects et le garde-fou doit les **accepter**. En revanche, il doit **refuser** « 19 » ou « 18,5 », qui sont de mauvais arrondis. Ces lignes servent à faire la différence.

## Étape 1 : que veut dire « 18 » ?

Écrire « 18 », c'est dire « un nombre qui s'arrondit à 18 ». Ce nombre est donc entre **17,5 et 18,5**, c'est-à-dire à **0,5 au maximum** de 18.

Écrire « 18,4 », c'est dire « entre 18,35 et 18,45 », donc à **0,05 au maximum** de 18,4.

Plus Qwen écrit de chiffres après la virgule, plus il est précis, et plus l'écart permis est petit. C'est ce que calcule la ligne 65 :

```python
tolerance = 0.5 * 10 ** (-decimales)
```

| Nombre écrit | décimales | calcul | écart permis |
|---|---|---|---|
| « 18 » | 0 | 0,5 × 1 | **0,5** |
| « 18,4 » | 1 | 0,5 × 0,1 | **0,05** |
| « 18,37 » | 2 | 0,5 × 0,01 | **0,005** |

(`10 ** (-1)` veut dire 10 puissance −1, c'est-à-dire 0,1.)

## Étape 2 : la boucle compare avec chaque nombre autorisé

```python
for a in autorises:                      # pour chaque nombre calculé par les outils
    if abs(valeur - a) <= tolerance:     # est-il assez proche du nombre écrit ?
        return True                      # oui : le nombre est justifié, on s'arrête
return False                             # aucun n'est assez proche : nombre inventé
```

- `valeur - a` est l'écart entre ce que Qwen a écrit et ce que l'outil a calculé.
- `abs(...)` donne la **valeur absolue** : on enlève le signe moins. Un arrondi peut être un peu au-dessus ou un peu en dessous, et ce qui compte, c'est seulement la **distance**. Exemple : 18 − 18,37 = −0,37, et sa distance est 0,37.
- Dès qu'**un seul** nombre autorisé est assez proche, on répond `True`. Si on a tout parcouru sans en trouver, on répond `False` : le nombre n'a pas d'origine, et la réponse sera bloquée.

**Exemples avec 18,37 calculé :**

| Qwen écrit | distance | permis | résultat |
|---|---|---|---|
| « 18 » | 0,37 | 0,5 | ✅ accepté |
| « 19 » | 0,63 | 0,5 | ❌ bloqué |
| « 18,4 » | 0,03 | 0,05 | ✅ accepté |
| « 18,5 » | 0,13 | 0,05 | ❌ bloqué |
| « 17 » | 1,37 | 0,5 | ❌ bloqué |

## Étape 3 : pourquoi `+ 1e-9` ?

`1e-9` veut dire 0,000000001, un nombre minuscule.

Un ordinateur ne calcule pas les nombres à virgule de façon parfaitement exacte. Je l'ai vérifié avec Python à l'instant : l'outil a donné **2,45** et Qwen a écrit « **2,4** ». C'est pile à la limite, donc on veut l'accepter. Or Python calcule cette distance comme **0,050000000000000266** au lieu de 0,05. Sans la petite marge, ce serait « plus grand que 0,05 », et on bloquerait une réponse correcte. Avec `+ 1e-9`, ce cas est accepté. Cette marge est bien trop petite pour laisser passer un vrai mauvais arrondi.

## La phrase à dire à l'oral

> « Un nombre écrit avec d chiffres après la virgule a le droit d'être à une demi-unité du dernier chiffre du vrai résultat. Ainsi, on accepte les arrondis corrects et on refuse les autres. Le 1e-9 compense les petites erreurs de calcul de l'ordinateur sur les nombres à virgule. »

Veux-tu que je remplace les commentaires du fichier par une version plus claire, avec la règle « 17,5 à 18,5 », et que j'ajoute dans la fiche 04 le tableau et l'exemple réel 2,4 / 2,45 ?


---

## Moi (13:19)

on passe a agent.pu


## Claude (13:20)

> 🔧 Commande : Inspect fiche 04 structure and style

> 🔧 Commande : Read the self-correction trace

> 🔧 Commande : Show tool schemas and summarize traces

> 🔧 Écriture : explications/sources/05_agent.html

> 🔧 Commande : Generate the agent fiche PDF

> 🔧 Commande : Commit the agent fiche


J'ai écrit la fiche [explications/05_agent.pdf](explications/05_agent.pdf) (7 pages, avec 10 questions d'examinateur et leur corrigé sur une page à part), et je l'ai commitée (`5db08f0`). Voici l'essentiel, en simple.

## Le rôle d'agent.py : le chef d'orchestre

**Qwen ne calcule rien et ne lance rien.** Il écrit seulement une **demande**, du genre « appelle `decrire` avec `nutriment=sucres`, `bio=True` ». C'est `agent.py` qui décide de l'exécuter, puis lui renvoie le résultat.

## Les 3 morceaux à connaître

**1. `executer_outil` ([agent.py:37-52](nutri/agent.py#L37-L52)) fait trois contrôles avant d'exécuter :**
1. L'outil existe-t-il ? Seuls nos 4 outils sont permis, donc Qwen ne peut pas lancer n'importe quel code.
2. Les filtres sont-ils permis ? C'est la règle n° 2 du garde-fou.
3. Les arguments sont-ils bons ? Le `try / except` attrape les erreurs. Une erreur est **renvoyée à Qwen** pour qu'il se corrige, au lieu de faire planter le programme.

Et `**arguments` « déballe » le dictionnaire : `{"nutriment": "sucres", "bio": True}` devient `decrire(df, nutriment="sucres", bio=True)`.

**2. La boucle de `repondre` ([agent.py:71-93](nutri/agent.py#L71-L93)) fait 3 étapes par tour :**
1. On envoie **toute** la conversation à Qwen, parce qu'il n'a pas de mémoire d'un appel à l'autre.
2. S'il ne demande aucun outil, c'est sa réponse finale, et on sort avec `break`.
3. Sinon, on exécute les outils, on ajoute les résultats à la conversation (rôle `tool`), et on refait un tour.

`MAX_TOURS = 6` empêche une boucle sans fin.

**3. La fin ([agent.py:95-105](nutri/agent.py#L95-L105)) :** le garde-fou n° 1 vérifie la réponse. La trace garde `reponse_brute` (ce que Qwen a écrit) et `reponse` (ce qui est affiché). Si les deux sont différentes, `bloquee = True`.

## L'exemple réel de la fiche (trace 113921)
| Tour | Ce qui se passe |
|---|---|
| 1 | Qwen filtre `bio=False`. C'est refusé, et l'erreur lui est renvoyée. |
| 2 | Qwen se corrige : il prend toutes les céréales, soit 953 produits et 409,45 kcal en moyenne. |
| 3 | Qwen répond « 122,84 kcal », un nombre qu'il a calculé lui-même. Le garde-fou le bloque. |

On voit ici toute la boucle : 3 appels à Qwen, une correction qu'il fait seul, puis la barrière finale.

## La phrase pour l'oral
> « Qwen choisit l'outil, Python fait le calcul, et le code vérifie à la fois la demande d'outil et la réponse finale. »

Avec cette fiche, les deux codes prévus aujourd'hui sont expliqués. Tu veux qu'on revoie un passage d'agent.py, ou qu'on termine la séance avec l'export de la conversation et la note de séance 3 dans `ai_log/` ?


---

## Moi (19:33)

demain il nous restera bcp de code ? il nous restera quoi


## Claude (19:33)


Non, il reste **un seul vrai code à écrire** : `nutri/evaluation.py`, pour la brique 9. Tout le reste est déjà codé et expliqué : download, clean, tools, garde_fou et agent.

## Demain (séance 4)

**1. Coder `evaluation.py`, environ 80 à 100 lignes.** Il fera trois choses :
- une liste d'**au moins 10 questions** dont on connaît déjà la bonne réponse, calculée par pandas. On y mettra la question des lipides bio / non bio, dont l'écart « n'est pas net » ;
- il pose **chaque question 3 fois** au système complet, puis 3 fois au modèle seul (`--modele-seul`) ;
- il compte les **bonnes réponses** et les **réponses bloquées**, puis il calcule la **moyenne** et la **dispersion**, c'est-à-dire à quel point les résultats changent d'un lancement à l'autre.

Il ne contient rien de nouveau à apprendre : il réutilise `repondre` d'agent.py dans une boucle. Il sera plus simple qu'agent.py.

**2. Lancer l'évaluation.** Elle tourne seule pendant environ 30 minutes. On en profite pour attaquer la suite.

**3. Expliquer un échec à partir de sa trace**, comme la consigne le demande. On a déjà un bon candidat : la trace des calories avec le mauvais filtre.

**4. Écrire deux fiches :** la 06 pour evaluation.py, et la 07 pour les tests. Les tests sont courts : chacun fait quelques lignes et vérifie une seule chose.

## Ensuite, sans code
- Remplir **EVIDENCE.md** avec les preuves de chaque brique. On a déjà presque toutes les traces.
- Tester un **clone neuf** du projet, pour vérifier que tout s'installe et marche (R1).
- Créer le dépôt **GitHub** et y envoyer le projet. Je te demanderai avant de le faire.
- Toi : ajouter `conversation_1a_creation.pdf` dans `ai_log/`.
- Mettre à jour le plan de présentation.

**Pour aujourd'hui,** il reste juste à clore la séance 3 : l'export de la conversation et la note dans `ai_log/`. Je le fais maintenant ?
