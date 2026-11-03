# Conversation avec Claude Code — séance du 2026-11-03

Export du journal de la session (extension VS Code). Les messages sont reproduits tels quels ; les actions de l'IA (commandes, lectures, modifications de fichiers) sont résumées en une ligne.


---

## Moi (12:35)

dernier jours go


## Claude (12:35)

> 🔧 Commande : Check repo state, ai_log and evidence

> 🔧 Commande : Read export script and README headers


Je commence par clore la séance 3 d'hier (export et note dans `ai_log/`), puis on attaque `evaluation.py`.

> 🔧 Commande : Export séance 3 conversation and check for personal data

> 🔧 Commande : Locate personal data occurrences


Le résumé automatique de contexte apparaissait comme un de tes messages (et il contenait un chemin personnel). Je le filtre dans l'export.

> 🔧 Commande : Filter compaction summary and re-export

> 🔧 Commande : Check start of séance 3 export


L'export est propre. J'ajoute la note de la séance 3 :

> 🔧 Commande : Write séance 3 note and commit


Séance 3 close (`3fa079c`). Maintenant, la brique 9. Je regarde d'abord les colonnes des données et ce que donnent les outils, pour écrire des questions à réponse connue.

> 🔧 Commande : Inspect data columns and tool outputs


Je code `nutri/evaluation.py`. Les réponses attendues seront calculées **directement avec pandas**, sans passer par les outils, pour avoir une vérification indépendante.

> 🔧 Écriture : nutri/evaluation.py

> 🔧 Commande : Fix types and print the 12 tasks with expected answers

> 🔧 Commande : Add minimum tolerance of 0.01

> 🔧 Écriture : tests/test_evaluation.py

> 🔧 Commande : Run tests and a quick evaluation


41 tests passent, et le mode rapide marche : 4 appels en 65 s. Je lance l'évaluation complète en arrière-plan. Il y a 72 appels à Qwen, donc environ 20 minutes.

> 🔧 Commande : Run full brique 9 evaluation


Pendant que l'évaluation tourne, je remplis EVIDENCE.md pour les briques 1, 3, 6 et 8.

> 🔧 Commande : Read cleaning journal and two traces

> 🔧 Écriture : EVIDENCE.md

> 🔧 Commande : Verify garde-fou test count


L'évaluation complète tourne en arrière-plan : 72 appels à Qwen, environ 20 minutes. Pendant ce temps, voici `nutri/evaluation.py`, le dernier code du projet.

## Ce que fait evaluation.py (la brique 9)

**1. `construire_taches`** : 12 questions dont **on connaît la bonne réponse**. Ces réponses sont calculées directement avec pandas, sans passer par tools.py, pour avoir une vérification **indépendante**. Il y a 3 types de questions :
- **nombre** (10 questions) : combien de céréales, la moyenne de sucres, de sel, etc. ;
- **texte** (1 question) : la marque la moins sucrée, ici « jardin bio etic » ;
- **prudence** (1 question) : les lipides bio / non bio. L'écart (0,21 g) est plus petit que sa marge (0,84 g), donc la bonne réponse est « on ne peut pas conclure ».

**2. `juger`** donne un verdict pour chaque réponse :
- **bloquée** : le garde-fou a refusé la réponse. Elle n'est ni juste ni fausse, puisqu'aucune réponse n'a été donnée.
- **juste** : la réponse contient un nombre à 2 % près de la bonne réponse. Pour le sel, l'écart permis est d'au moins 0,01, parce que les outils arrondissent 0,1265 à « 0,13 ».
- **fausse** : tout le reste, y compris « je n'ai pas accès aux données ».

**3. `evaluer`** pose chaque question **3 fois** au système complet, puis 3 fois au modèle seul.

**4. `resumer`** calcule le taux de réponses justes à chaque lancement, puis sa **moyenne** et son **écart type**. L'écart type montre la **dispersion**, c'est-à-dire à quel point Qwen change d'un lancement à l'autre.

**Résultat de l'essai rapide :** le système complet a eu 2 réponses justes sur 2, et le modèle seul 0 sur 2. Sans les données, Qwen ne peut pas savoir qu'il y en a 953.

## Fait depuis ce matin
- **Séance 3 close** (`3fa079c`) : la conversation d'hier est exportée et la note est écrite dans `ai_log/`. J'ai corrigé l'export : le résumé automatique de la conversation y apparaissait comme si c'était un message de toi.
- **5 tests ajoutés** pour la façon de juger, dans [tests/test_evaluation.py](tests/test_evaluation.py). En tout, **41 tests passent**.
- **[EVIDENCE.md](EVIDENCE.md) est rempli** pour les briques 1, 3, 6 et 8, avec les vraies traces, les décisions de nettoyage et la phrase « ce que ces données ne permettent pas de conclure » (biais de 57 % de bio, pas de lien de cause). La brique 9 sera remplie quand l'évaluation sera finie.

Dès que les résultats arrivent, je choisis un échec, je l'explique à partir de sa trace, puis j'écris la fiche 06 (evaluation) et la fiche 07 (tests).

> 🔧 Commande : Show evaluation results

> 🔧 Commande : Inspect selected answers and costs

> 🔧 Commande : Count invented numbers in model-alone answers

> 🔧 Commande : Check results files and summary


Now I'll write the brique 9 section of EVIDENCE.md with these results.

> 🔧 Commande : Write brique 9 evidence and commit


L'évaluation est terminée et commitée (`b66aa42`). Les résultats sont dans [resultats/evaluation.md](resultats/evaluation.md).

## Les résultats (72 réponses de Qwen)

| Système | Réponses justes (moyenne ± écart type) |
|---|---|
| **Complet** (outils + garde-fou) | **100 % ± 0 %** : 36 sur 36 |
| **Modèle seul** | **3 % ± 5 %** : 1 sur 36 |

Le système complet coûte plus cher : il met **32 s** par question au lieu de 9 s, et lit **12 fois plus** de tokens.

## Ce que j'ai trouvé dans les traces
- **Le modèle seul invente des chiffres dans 9 réponses sur 36**, et il fait parfois croire qu'il a calculé (« j'ai consulté l'outil »).
- **L'échec expliqué, celui qu'attend la consigne** : à la question sur le sucre des céréales bio, il répond « **6,8 g ± 1,4 g** ». La vraie valeur est 13,17 g. Il ajoute même « le test statistique indique… », alors que sa trace montre **aucun appel d'outil**. Il a recopié la forme des réponses du système, sans en avoir les chiffres. Le garde-fou aurait bloqué cette réponse.
- **Le seul « juste » du modèle seul est en fait une erreur de ma façon de juger.** Sa réponse contenait le mot « hasard » sans rien conclure. Le vrai taux du modèle seul est donc 0 %. C'est une limite honnête à dire à l'oral.

Tout cela est écrit dans [EVIDENCE.md](EVIDENCE.md), avec les limites de la mesure.

## Une décision pour toi
Un score de 100 % peut sembler trop beau : les 12 questions demandent chacune un seul outil, donc ce sont des questions faciles. On sait pourtant que le système échoue sur d'autres questions, celles de portion et celles où Qwen ajoute un filtre que la question ne demande pas.

On peut ajouter **2 ou 3 questions difficiles**, par exemple « les calories d'une portion de 30 g ». La mesure serait plus honnête et montrerait des réponses bloquées. Il faudrait relancer l'évaluation, environ 30 minutes.

Je te conseille de les ajouter : un examinateur croira plus volontiers « 85 % avec des échecs expliqués » que « 100 % ». Tu veux qu'on le fasse, ou qu'on garde les résultats actuels ? En attendant ta réponse, je peux attaquer la fiche 07 sur les tests, qui ne dépend pas de ce choix.


---

## Moi (13:10)

Oui, je pense comme toi, ça serait plus pertinent d'ajouter certains échecs parce que concrètement, l'objectif du devoir, c'est de montrer que le modèle a ses failles. Donc, on peut ajouter certaines questions un peu tricky. Puis passer à la fiche sur les tests


## Claude (13:10)


D'accord. J'ajoute 4 questions pièges, chacune visant une faille connue :

> 🔧 Commande : Add 4 tricky questions and a refusal test


Les 42 tests passent. Je relance l'évaluation complète, avec 16 questions et 96 réponses, pour environ 35 minutes :

> 🔧 Commande : Rerun full evaluation with tricky questions


Pendant que ça tourne, j'écris la fiche 07 sur les tests. Je relis d'abord les fichiers de tests :

> 🔧 Commande : Read the test files

> 🔧 Commande : Copy shared fiche header/CSS

> 🔧 Commande : Write fiche 07 and generate PDF


Fiche 07 faite. J'écris la fiche 06 sur evaluation.py pendant que l'évaluation continue. Je relève d'abord les numéros de ligne :

> 🔧 Commande : Get line numbers in evaluation.py

> 🔧 Lecture : nutri/evaluation.py

> 🔧 Commande : Simplify comprehensions and recheck lines

> 🔧 Commande : Sanity check evaluer with a fake model

> 🔧 Commande : Print exact line ranges for fiche

> 🔧 Commande : Write fiche 06 draft with result placeholders


Je teste aussi un **clone neuf** du projet (exigence R1) pendant que l'évaluation tourne. Je copie le dépôt git dans un dossier temporaire, j'installe tout depuis zéro, puis je lance les tests.

> 🔧 Commande : Test a fresh clone install and tests


Le clone neuf s'installe et ses tests passent. Il en a 41 parce que le dernier test n'est pas encore commité. Je vérifie que le README donne les bonnes commandes :

> 🔧 Commande : Read README

> 🔧 Commande : Update README commands and structure


Le README est à jour : il donne maintenant les commandes de l'évaluation, et il prévient qu'en re-téléchargeant les données, on change les chiffres d'EVIDENCE.md. J'attends la fin de l'évaluation (environ 15 minutes encore) pour remplir les résultats dans EVIDENCE.md et dans la fiche 06.

> 🔧 Commande : Show new results and inspect tricky answers


L'évaluation est finie. Les pièges ont bien fonctionné, mais en lisant les traces, j'ai trouvé un défaut dans ma façon de juger. J'ai besoin de ta décision pour le corriger.

## Les résultats (96 réponses)

| Système | Réponses justes (moyenne ± écart type) | Justes | Fausses | Bloquées |
|---|---|---|---|---|
| **Complet** | **73 % ± 4 %** | 35 | 5 | 8 |
| **Modèle seul** | **12 % ± 6 %** | 6 | 42 | 0 |

Le modèle seul a **inventé des chiffres dans 17 réponses sur 48**.

## Ce que montrent les traces du système complet
- **Les pièges marchent.**
  - Portion de 30 g et écart A / E : Qwen fait le calcul lui-même, et le garde-fou bloque.
  - Vitamine C : Qwen dit que la donnée n'existe pas (3 réponses justes sur 3).
- **Bonus** : à la question 4, Qwen a écrit « **4,42** g de moins » au lieu de 5,42. Ce chiffre faux a été **bloqué**.
- **Le meilleur échec à expliquer, la question 11 (marque la moins sucrée), fausse 3 fois sur 3** :
  - Qwen a demandé le classement en ordre **décroissant**, donc les marques les plus sucrées d'abord.
  - Il a ensuite lu la première marque comme « la moins sucrée » : Crownfield, 18,61 g.
  - Le garde-fou laisse passer cette réponse, parce que 18,61 vient bien d'un outil. Il vérifie l'origine des chiffres, pas le sens de la phrase.
  - **Au premier passage d'évaluation, ce matin, la même question était juste 3 fois sur 3.** Qwen n'est donc pas régulier d'une heure à l'autre.
- **La règle n° 2 a aussi un défaut.** Quand Qwen s'obstine à filtrer sur le bio, il atteint la limite de 6 tours et ne répond pas (question 13, lancement 3). Une autre fois, il a appelé 3 fois un outil « descrire » qui n'existe pas, puis a répondu de mémoire, et le garde-fou l'a bloqué.

## Le défaut de mon jugement
Pour la question des lipides, le modèle seul est compté **juste 3 fois sur 3**. C'est faux : il invente des moyennes (« 3,2 g ± 0,4 g » au lieu de 10,69 g) et ajoute « pas significatif ». Ma règle « prudence » cherche seulement le mot « hasard » ou « pas conclure ». Elle ne vérifie pas les chiffres.

**Ma proposition** : une réponse « prudente » ne serait juste que si elle **n'invente aucun chiffre**. On peut **rejuger les 96 réponses déjà enregistrées**, sans relancer Qwen. Il faut ajouter une option `--rejuger` d'une dizaine de lignes. Le modèle seul passerait d'environ 12 % à 6 %.

Pour rester honnête, EVIDENCE.md donnerait **les deux chiffres**, avant et après la correction, en expliquant que j'ai corrigé le jugement **après** avoir vu les résultats. Un examinateur peut le reprocher si on le cache, pas si on l'explique.

On corrige comme ça, ou tu préfères garder le jugement actuel et présenter ce faux positif comme une limite ?


---

## Moi (13:52)

Moi, je pense que c'est important de garder des faux positifs et de garder à l'esprit que ce modèle présente de nombreuses limites. Enfin, malgré tous les outils et le garde-fou et tout le processus qu'on lui a donné, le prompt, etc., il arrive à se tromper. Et je pense que c'est important de le mettre . C'est peut-être un risque, mais je peux le prendre. Et je préfère le prendre.


## Claude (13:52)


C'est noté : on garde le jugement tel quel, et le faux positif est présenté comme une limite. Je l'écris comme **ta décision** dans EVIDENCE.md et dans le journal.

> 🔧 Commande : Write brique 9 evidence with new results

> 🔧 Commande : Fix counts in brique 9 evidence


Maintenant, je remplis les résultats dans la fiche 06 :

> 🔧 Commande : Fill results into fiche 06 and render PDF

> 🔧 Commande : Commit and read presentation plan

> 🔧 Écriture : explications/plan_presentation.md


Le plan de présentation est à jour, avec les vraies démos et les résultats. J'écris maintenant la note de la séance 4 et j'exporte la conversation d'aujourd'hui :

> 🔧 Commande : Write séance 4 note and export today's conversation
