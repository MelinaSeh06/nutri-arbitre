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

> 🔧 Commande : Commit séance 4 log and plan

> 🔧 Commande : Update progress memory


Tout est fait et commité (`8633f45`), et les 42 tests passent.

## Ce qui a été fait aujourd'hui
- **Brique 9.** [nutri/evaluation.py](nutri/evaluation.py) pose 16 questions, dont 4 pièges, 3 fois chacune. Le système complet a **73 % ± 4 %** de réponses justes, le modèle seul **12 % ± 6 %**. Les résultats sont dans [resultats/evaluation.md](resultats/evaluation.md).
- **[EVIDENCE.md](EVIDENCE.md) est complet** pour les 5 briques. On y trouve :
  - l'échec expliqué : la marque « la moins sucrée » lue à l'envers dans un classement décroissant ;
  - les autres échecs tirés des traces ;
  - **ta décision** de garder les faux positifs.
- **Les fiches 06** ([evaluation](explications/06_evaluation.pdf)) **et 07** ([tests](explications/07_tests.pdf)) sont écrites, avec leurs questions et leur corrigé. Les 7 fiches sont donc prêtes.
- **Le clone neuf est testé** : le projet s'installe depuis zéro et les tests passent (R1).
- **Le README et le [plan de présentation](explications/plan_presentation.md) sont à jour.** Le plan propose 3 démos : la réponse juste, les lipides « on ne peut pas conclure », et la portion bloquée.
- **ai_log contient les notes des séances 3 et 4**, avec les exports des conversations.

Dans evaluation.py, j'ai remplacé deux passages par des boucles simples, plus faciles à expliquer. Le résultat ne change pas.

## Ce qu'il reste
1. **Toi** : déposer `conversation_1a_creation.pdf` dans `ai_log/`.
2. **Créer le dépôt GitHub et y envoyer le projet.** Je ne le fais pas sans ton accord, parce que c'est une publication. Dis-moi si tu veux un dépôt **public ou privé**, et sous quel nom. Le PDF de la consigne restera hors du dépôt.
3. **Réviser les fiches 05 à 07** et répondre à leurs questions. On peut le faire ensemble.
4. Si on continue à discuter aujourd'hui, je referai l'export de la séance 4 à la fin, pour qu'il contienne toute la conversation.


---

## Moi (13:55)

reviser les fihces 6 et 7 tu veux dire


## Claude (13:55)


Oui, surtout les fiches 06 et 07, que j'ai écrites aujourd'hui et que tu n'as pas encore lues.

J'ai aussi mis la **05 (agent.py)** parce que je l'ai écrite hier en fin de séance. Tu n'as pas encore répondu à ses questions, et on n'en a pas parlé ensemble. Si tu l'as déjà relue et qu'elle est claire pour toi, on peut la sauter.

Je te propose de réviser comme à l'oral : **je te pose les questions d'une fiche, tu réponds avec tes mots, et je te corrige.** Ça te prépare au moment où l'examinateur choisit un bout de code au hasard.

On commence par laquelle : la 05, la 06 ou la 07 ?


---

## Moi (14:13)

J'aimerais bien faire des vidéos notebook LM pour chaque code que je devrais potentiellement expliquer. Du coup, là, j'aimerais que tu me fasses les PDF spécialement pour notebook LM. Enfin, pas forcément des PDF plus des documents Word comme ça, il peut vraiment interagir avec le texte. En tout cas, dis-moi ce qui est mieux. L'objectif, là, ça va être que tu mettes plus de code et plus d'exemples et que ce soit plus pédagogique. Afin que pour chaque code, je puisse faire une vidéo explicative que je regarderai, je pense, ce soir ainsi que demain matin avant de passer.


## Claude (14:13)


Pour NotebookLM, le meilleur format est **Markdown** (`.md`), c'est-à-dire du texte pur, plutôt qu'un PDF ou un Word :
- NotebookLM lit le texte directement, sans risque de mal lire une mise en page, un tableau ou un bloc de code ;
- le code garde exactement ses espaces et ses numéros de ligne ;
- le fichier s'ouvre aussi dans VS Code, et il se convertit en Word en une commande si tu en as besoin.

Je fais **un document par code** (7 en tout), avec le code complet découpé en morceaux, chaque morceau expliqué ligne par ligne, des exemples tirés de nos vraies données, et les pièges à éviter à l'oral. Le code sera recopié automatiquement depuis les fichiers, pour éviter toute erreur de copie. Je commence par relire les fichiers.

> 🔧 Commande : Read download.py and clean.py

> 🔧 Commande : Read middle of tools.py


J'ai tout le code. Je récupère maintenant de vrais exemples, en lançant les fonctions sur nos données, pour les mettre dans les documents :

> 🔧 Commande : Collect real examples from the data and functions


J'ai les exemples. J'écris d'abord un petit script qui recopie le code exact, avec ses numéros de ligne, dans les documents :

> 🔧 Commande : Create NotebookLM builder and shared context


Maintenant le document 1, sur download.py :

> 🔧 Écriture : /tmp/nutri_scripts/nlm/01_download.md

> 🔧 Commande : Fix the ensure_ascii example


Le document 1 est prêt. Voici le document 2, sur clean.py, le plus long :

> 🔧 Écriture : /tmp/nutri_scripts/nlm/02_clean.md

> 🔧 Commande : Check end of cleaning journal

> 🔧 Commande : Fix bio count in trajectory


Le document 2 est prêt. Voici le document 3, sur tools.py. J'y reprends tes questions des séances précédentes : la marge, les écarts négatifs et √(et₁² + et₂²).

> 🔧 Écriture : /tmp/nutri_scripts/nlm/03_tools.md

> 🔧 Commande : Check line counts and fix tools ranges


Je me suis trompé dans ma correction : tools.py a bien 185 lignes, et `_arrondi` est aux lignes 42 et 43. Je remets les bonnes plages :

> 🔧 Commande : Restore correct tools line ranges


Le document 3 est prêt. Voici le document 4, sur garde_fou.py :

> 🔧 Écriture : /tmp/nutri_scripts/nlm/04_garde_fou.md


Le document 4 est prêt. Voici le document 5, sur agent.py :

> 🔧 Écriture : /tmp/nutri_scripts/nlm/05_agent.md

> 🔧 Commande : Check evaluation.py boundaries


Voici le document 6, sur evaluation.py :

> 🔧 Écriture : /tmp/nutri_scripts/nlm/06_evaluation.md

> 🔧 Commande : Check top of evaluation.py

> 🔧 Commande : Fix line refs in evaluation doc


Voici le dernier document, le 7, sur les tests :

> 🔧 Écriture : /tmp/nutri_scripts/nlm/07_tests.md

> 🔧 Commande : Check test file lengths and build documents

> 🔧 Commande : List test function line numbers


Tous les numéros de ligne correspondent au vrai code. J'ajoute un petit mode d'emploi pour NotebookLM, avec une consigne de vidéo à copier-coller, puis je commite :

> 🔧 Commande : Add usage guide, commit, preview a section

> 🔧 Commande : Fix stale comment, rebuild docs, commit


Les 7 documents NotebookLM sont prêts dans [explications/notebooklm/](explications/notebooklm/) et commités.

## Le format : Markdown
J'ai choisi des fichiers `.md` plutôt que des PDF ou des Word, parce que NotebookLM lit mieux le texte pur. Les blocs de code et les tableaux restent intacts, sans risque de mauvaise lecture de la mise en page.

## Ce que contient chaque document
Chaque document fait de 380 à 740 lignes, soit environ 3 fois plus que les fiches PDF. On y trouve :
- **le projet en 30 secondes**, au début de chaque document, pour que chaque vidéo se comprenne seule ;
- **les notions à connaître avant de lire le code** : le masque, la regex, l'erreur type, la fixture… ;
- **le code complet, morceau par morceau**, avec ses vrais numéros de ligne. Le code est recopié automatiquement depuis les fichiers, il ne peut donc pas y avoir d'erreur de copie ;
- **l'explication ligne par ligne**, avec de vrais exemples lancés sur nos données : Kellogg's, le muesli à 437 kcal, le bol de 40 g bloqué, la marque lue à l'envers… ;
- **tes propres questions des séances précédentes**, comme « 4 fois plus de produits → marge plus grande ? » et les écarts négatifs ;
- **les pièges, les questions d'examinateur avec leurs réponses, et un résumé en 5 phrases.**

## Pour faire les vidéos
1. Crée **un carnet NotebookLM par document** et n'y importe que ce document. Chaque vidéo reste ainsi centrée sur un seul fichier.
2. Dans le Studio, choisis **Résumé vidéo**, puis **Personnaliser**, et colle la consigne qui se trouve dans [LISEZMOI.md](explications/notebooklm/LISEZMOI.md). Elle demande d'expliquer pour une débutante qui passe à l'oral demain, de suivre l'ordre du document, et de finir par les questions.

Les vidéos NotebookLM durent souvent quelques minutes et résument. Pour les gros fichiers comme `clean.py`, la vidéo ne couvrira pas forcément chaque ligne. Ce soir, garde le document ouvert à côté de la vidéo. Tu peux aussi poser des questions dans le chat du carnet, par exemple : « explique-moi les lignes 88 à 98 ».

En relisant le code, j'ai corrigé un commentaire périmé de garde_fou.py, à la ligne 76 : il oubliait la constante 95. Les 42 tests passent toujours.

**Il reste toujours à faire :** créer le dépôt GitHub et y envoyer le projet, quand tu me diras public ou privé et sous quel nom, et ajouter `conversation_1a_creation.pdf` dans `ai_log/`. Bon courage pour ce soir et pour demain !


---

## Moi (14:58)

Dans évaluation quand y’a écrit type : prudence ca veut dire quoi ?

Pourquoi cette question ne se fait pas avec les outils : {"question": "Quel est l'écart de sucres entre les céréales au Nutri-Score A et celles au "
                     "Nutri-Score E, pour 100 g ?",
L’outil comparée ne sert pas a ca ?

Difference entre une réponse bloqué et fausse donne un exemple ? Moi comment je le comprend c’est que une réponse bloqué est par exemple calculé par le modele peut être vrai ou fasse et une fausse c’est que en utilisant les outils le modele a quand même invente


## Claude (14:59)


## 1. « type : prudence »

C'est une question dont la bonne réponse **n'est pas un nombre** mais une **phrase prudente** : « on ne peut pas conclure ».

Il n'y en a qu'une : « Les céréales bio contiennent-elles plus de lipides que les non bio ? ». L'outil `comparer` donne un écart de **0,21 g ± 0,84 g**. La fourchette [−0,63 ; 1,05] contient 0, donc `difference_nette = False`. Répondre « oui » ou « non » serait faux. La seule bonne réponse est « l'écart peut venir du hasard ».

C'est pour ça que le jugement cherche des mots, et pas un nombre ([evaluation.py:108-112](nutri/evaluation.py#L108-L112)) : la réponse est juste si elle contient « hasard », « pas conclure », « pas de conclure » ou « pas de différence nette ».

Vraie réponse jugée juste : « …cette différence peut venir du **hasard** car la marge d'erreur à 95 % est supérieure à l'écart observé (0,84 > 0,21). On ne peut donc pas conclure… »

## 2. Pourquoi l'outil `comparer` ne suffit pas pour l'écart A / E

Tu as raison, Qwen utilise bien `comparer` pour cette question. Mais regarde ce que l'outil renvoie quand on groupe par Nutri-Score :

```
A : 6,3 g   B : 12,82 g   C : 18,03 g   D : 23,14 g   E : 26,33 g
```

Il donne **la moyenne de chaque groupe**, mais **pas l'écart entre deux groupes**. L'écart n'est calculé que pour bio / non bio ([tools.py:104-124](nutri/tools.py#L104-L124), le bloc `if groupe == "bio"`). Pour le Nutri-Score, il y a 5 groupes, donc 10 écarts possibles, et l'outil n'en calcule aucun.

Qwen doit donc faire la soustraction **lui-même** : 26,33 − 6,3 = 20,03. Comme 20,03 ne vient d'aucun outil, le garde-fou bloque, et c'est arrivé 3 fois sur 3. C'est justement pour ça que c'est un piège : la question a l'air simple, mais elle tombe dans un trou des outils.

Ce que tu as remarqué peut se dire à l'oral comme une amélioration possible : « on pourrait ajouter à `comparer` l'écart entre deux lettres du Nutri-Score ».

## 3. Bloquée ou fausse

La première moitié de ton idée est juste, mais pas la seconde.

**Bloquée** : le garde-fou a refusé la réponse, parce qu'au moins un nombre ne venait pas d'un outil. L'utilisateur voit seulement « Réponse bloquée… ». Comme tu le dis, le calcul du modèle peut être **vrai ou faux**, le garde-fou ne regarde pas :
- vrai mais bloqué : l'écart A / E, « **20,03 g** ». Le calcul est juste, mais c'est Qwen qui l'a fait ;
- faux et bloqué : « les bio ont **4,42 g** de moins » au lieu de 5,42 g.

**Fausse** : la réponse a été **affichée**, mais elle n'est pas la bonne. Ce n'est **pas** « le modèle a inventé malgré les outils ». S'il avait inventé un nombre dans le système complet, la réponse aurait été bloquée. Dans le système complet, une réponse fausse a deux causes possibles :
- **les chiffres viennent bien d'un outil, mais la phrase dit une erreur.** C'est la question 11 : « Crownfield, **18,61 g**, est la marque la moins sucrée ». 18,61 vient de l'outil, donc le garde-fou laisse passer, mais Qwen a lu le classement à l'envers ;
- **aucune réponse** : « Je n'ai pas réussi à répondre en un nombre raisonnable d'étapes » (6 tours de filtres refusés), ou « je n'ai pas trouvé d'outil pour la moyenne générale ».

Pour le **modèle seul**, il n'y a pas de garde-fou. Ses chiffres inventés ne sont donc jamais bloqués, ils sont comptés **faux**. Exemple : « **6,8 g ± 1,4 g** » de sucres chez les bio, au lieu de 13,17 g.

**La phrase à retenir :** une réponse **bloquée**, c'est un nombre qui ne vient pas d'un outil. Le système se tait plutôt que de risquer une erreur. Une réponse **fausse**, c'est une erreur qui **arrive jusqu'à l'utilisateur**. C'est plus grave, et c'est ce que le garde-fou ne sait pas empêcher quand les chiffres viennent bien d'un outil.


---

## Moi (15:03)

J'ai pas compris. En fait, le principe des tests dans le sens où par exemple test fiche incohérente retirée, et test regroupement des marques, on teste sur quoi?


## Claude (15:03)


On ne teste pas sur les vraies données. **On teste sur de tout petits exemples inventés, écrits directement dans le test**, dont on connaît déjà le résultat. On donne ces exemples à **la vraie fonction** de `clean.py`, puis on vérifie qu'elle fait exactement ce qu'on attend.

C'est comme vérifier une calculatrice : on tape 2 + 2 parce qu'on sait déjà que le résultat doit être 4. Si elle affiche 5, elle est cassée.

## `test_fiche_incoherente_retiree` ([test_clean.py:25-34](tests/test_clean.py#L25-L34))

**1. On invente deux produits**, avec exactement les mêmes nutriments :
- 33 g de glucides, 4,7 g de protéines, 6,6 g de lipides, 3,9 g de fibres.
- Avec la formule INCO, cela fait **218 kcal**.

Seule l'énergie déclarée diffère :

| Produit | Énergie déclarée | Écart avec 218 | Ce que la fonction doit faire |
|---|---|---|---|
| « 10 » | 437 kcal | 100 % | le **retirer** (plus de 20 %) |
| « 11 » | 230 kcal | 5 % | le **garder** |

**2. On les donne à la vraie fonction** : `nettoyer([incoherent, coherent])`.

**3. On vérifie le résultat :**
- `assert list(df["code"]) == ["11"]` : il ne reste que le produit 11 ;
- la dernière ligne vérifie que le journal dit bien « produits retirés : 1 ».

Si un jour quelqu'un casse la règle des 20 % dans `clean.py`, le produit 10 resterait, et le test **échouerait**. Le test protège donc la règle.

Les nombres de cet exemple ne sont pas tirés au hasard : ce sont ceux du **vrai muesli** des données (« Muesli croustillant chocolat »). On a recopié ce vrai cas dans le test.

## `test_regroupement_des_marques` ([test_clean.py:49-59](tests/test_clean.py#L49-L59))

**1. On invente une liste de 11 marques**, choisies pour chaque cas qu'on veut vérifier :

```
"kelloggs", "kelloggs", "kellogg s produits aliment sas", "carrefour", "carrefour bio",
"lu", "lucien georgelin", "aline olivier", "alineolivier", "societe des produits nestle sa", None
```

**2. On les donne à la vraie fonction** : `regrouper_marques(marques)`.

**3. On vérifie chaque cas**, dont on connaît la bonne réponse :

| Marque donnée | Résultat attendu | Ce que ça vérifie |
|---|---|---|
| kellogg s produits aliment sas | kelloggs | le début du nom est une marque connue |
| carrefour bio | carrefour | même chose |
| lucien georgelin | **lucien georgelin** (inchangé) | les mots entiers : il n'est **pas** rangé chez « lu » |
| alineolivier | aline olivier | la même marque écrite sans espace |
| societe des produits nestle sa | nestle | la table écrite à la main |
| None (pas de marque) | reste vide | ne plante pas sur une case vide |

Chaque ligne `assert` vérifie un de ces cas. Si la fonction rangeait « lucien georgelin » chez « lu », la ligne 55 échouerait.

## À dire à l'oral
> « Un test, c'est un petit exemple inventé dont je connais la réponse d'avance. Je le donne à la vraie fonction, et `assert` vérifie qu'elle trouve la même chose. Chaque exemple est choisi pour vérifier une règle précise. Souvent, c'est un vrai cas qu'on a rencontré dans les données, comme le muesli à 437 kcal. »

C'est plus clair comme ça ?


---

## Moi (15:09)

Pourquoi dans le test regroupement des marques, Kellogg's et Carrefour, à la ligne 54, sont regroupés?


## Claude (15:10)


Kellogg's et Carrefour ne sont **pas** regroupés ensemble. La ligne 54 vérifie **cinq résultats d'un coup**, sur une seule ligne :

```python
assert list(regroupees[:5]) == ["kelloggs", "kelloggs", "kelloggs", "carrefour", "carrefour"]
```

`regroupees[:5]` veut dire « les 5 premiers résultats ». La fonction renvoie **un résultat par marque donnée, dans le même ordre**. On compare donc position par position :

| Position | Marque donnée (ligne 50-51) | Résultat attendu |
|---|---|---|
| 0 | `"kelloggs"` | `"kelloggs"` |
| 1 | `"kelloggs"` | `"kelloggs"` |
| 2 | `"kellogg s produits aliment sas"` | `"kelloggs"` |
| 3 | `"carrefour"` | `"carrefour"` |
| 4 | `"carrefour bio"` | `"carrefour"` |

La ligne vérifie deux regroupements séparés :
- les **3 écritures de Kellogg's** deviennent toutes « kelloggs » (positions 0 à 2) ;
- les **2 écritures de Carrefour** deviennent toutes « carrefour » (positions 3 et 4).

Kellogg's reste Kellogg's, et Carrefour reste Carrefour. On les a seulement mis dans la même ligne `assert` pour ne pas écrire cinq lignes presque identiques.

Les lignes suivantes, elles, vérifient une position à la fois avec un numéro : `regroupees[6]` est la 7ᵉ marque, « lucien georgelin » (on compte à partir de 0).


---

## Moi (15:32)

Ok, maintenant, il faut qu'on simule la présentation à l'oral. Qu'est-ce que je dois faire?


## Claude (15:32)

> 🔧 Commande : Find oral defense rules in the consigne PDF

> 🔧 Lecture : Projet_Final_Coding_for_AI_2026-27.pdf

> 🔧 Commande : Look for oral rules in earlier notes

> 🔧 Commande : Extract text from consigne PDF streams

> 🔧 Commande : Preview extracted text

> 🔧 Commande : Extract consigne text with PDFKit

> 🔧 Commande : Read the R4 and grading section


Je n'avais pas les règles exactes de l'oral en tête, alors je les ai relues dans la consigne (section R4). Je vérifie aussi qu'Ollama tourne, pour que tu puisses lancer la démo :

> 🔧 Commande : Check Ollama is running


La consigne (R4, qui vaut **5 points sur 20**) dit : « Vous lancez la démonstration et expliquez un morceau de code choisi par l'enseignant. Un code juste que vous ne savez pas expliquer ne rapporte rien. » L'oral a donc **deux parties**, et on va simuler les deux.

## Partie 1 : la démo (environ 6 minutes), toi seule

Ollama tourne déjà. Ouvre le terminal de VS Code, dans le dossier du projet, et active l'environnement :
```
source .venv/bin/activate
```

Suis le [plan de présentation](explications/plan_presentation.md) **à voix haute, comme devant l'examinateur**, et chronomètre-toi :

1. **Le problème** : `python -m nutri.agent --modele-seul "Quelle est la teneur moyenne en sucres des céréales bio, pour 100 g ?"`
2. **La solution** : explique le trajet question → outil → règle n° 2 → calcul → règle n° 1 → réponse.
3. **La démo**, trois questions :
   - `python -m nutri.agent "Les céréales bio contiennent-elles moins de sucre ?"`
   - `python -m nutri.agent "Les céréales bio contiennent-elles plus de lipides que les non bio ?"`
   - `python -m nutri.agent "Combien de calories apporte une portion de 30 g de céréales, en moyenne ?"`
4. **Les tests** : `python -m pytest tests/test_garde_fou.py -v`
5. **Les résultats** : ouvre `resultats/evaluation.md`.
6. **Les limites.**

Deux conseils :
- **la première question met environ 20 s**, le temps que Qwen se charge. Le jour J, lance une question avant ton passage ;
- **Qwen ne répond pas deux fois pareil.** Si une réponse sort différente de ce que tu prévoyais, ne panique pas, et commente ce que tu vois : « vous voyez, il a choisi tel outil… ». C'est même un bon moment pour montrer que tu comprends le système.

Après la démo, **colle-moi ce que le terminal a affiché**, et dis-moi ou écris-moi ce que tu as expliqué. Je te dirai ce qui était clair, ce qui manquait, et ton temps.

## Partie 2 : le code au hasard, je joue l'examinateur

Je choisis un morceau de code au hasard dans n'importe quel fichier. Tu l'expliques **avec tes mots**, sans regarder les fiches. Ensuite :
- je te corrige comme le ferait l'examinateur ;
- je te pose une question de suite, par exemple : « et si la liste est vide ? », « pourquoi pas autrement ? », « montre-moi le test qui le vérifie ».

La consigne cite trois questions que l'enseignant aime poser :
- est-ce que tu sais ce que fait **chaque ligne** ?
- que se passe-t-il dans le **cas limite** (une liste vide, une valeur manquante, une seule valeur) ?
- qu'est-ce que tu lances pour le **vérifier** ?

Je vais te les poser.

On commence par la démo, ou directement par le code au hasard si tu préfères garder la démo pour plus tard ?


---

## Moi (15:35)

conda activate base
(base) utilisatrice@ordinateur nutri-arbitre % conda activate base
(base) utilisatrice@ordinateur nutri-arbitre % source .venv/bin/activate

(.venv) (base) utilisatrice@ordinateur nutri-arbitre % `python -m nutri.agent --modele-seul "Quelle est la teneur moyenne en sucres des céréales bio, pour 100 g ?"`

zsh: command not found: Je
(.venv) (base) utilisatrice@ordinateur nutri-arbitre % 
(.venv) (base) utilisatrice@ordinateur nutri-arbitre %


## Claude (15:36)


C'est à cause des **accents graves** (les `` ` ``) autour de la commande. Dans le Markdown du plan, ils servent seulement à afficher le code. Mais dans le terminal, ils ont un autre sens : « exécute ce qui est dedans, puis exécute ce qu'il a écrit comme si c'était une nouvelle commande ».

Ta commande a donc **bien tourné**. Qwen a répondu une phrase qui commençait par « Je… », probablement « Je ne peux pas… », et le terminal a essayé de lancer cette phrase comme une commande. D'où `command not found: Je`.

Retape-la **sans les accents graves** :

```
python -m nutri.agent --modele-seul "Quelle est la teneur moyenne en sucres des céréales bio, pour 100 g ?"
```

Fais pareil pour toutes les commandes du plan : copie seulement ce qui est **entre** les `` ` ``.

Au passage, tu n'as pas besoin de `conda activate base`. Le `.venv` suffit. Le jour J, il faut juste que `(.venv)` soit écrit au début de la ligne.

Si Qwen répond encore « je ne peux pas » au lieu d'inventer, c'est normal : il ne répond pas deux fois pareil. Pendant l'évaluation, il a refusé 31 fois sur 48 et inventé 17 fois. À l'oral, tu peux le dire tel quel : « ici, il refuse. Mais dans l'évaluation, il a inventé des chiffres 17 fois sur 48, par exemple 6,8 g ± 1,4 g au lieu de 13,17 g ».


---

## Moi (15:37)

La teneur moyenne en sucres de 100 g de céréales bio vendues en France est de **13,2 g** avec une marge d'erreur de ± 0,9 g. Cette valeur reflète la composition nutritive typique de ce type de produit au petit-déjeuner. L'analyse se base sur les données ouvertes disponibles pour ce groupe alimentaire spécifique.
il m'a repondu ca


## Claude (15:37)


C'est une **très bonne trouvaille** pour l'oral. Regarde le prompt système, à la ligne 29 d'agent.py :

```
Quand un outil donne une marge d'erreur (marge_95), écris-la : « 13,2 g ± 0,9 g ».
```

Le modèle seul n'a pas d'outil, il ne connaît pas nos données. **Il a recopié l'exemple du prompt** : « 13,2 g ± 0,9 g », mot pour mot.

Ce qui rend le cas piégeux :
- **la moyenne a l'air juste** : la vraie valeur est 13,17 g, qui s'arrondit à 13,2. C'est une **coïncidence**, parce que j'avais pris l'exemple du prompt dans nos vrais résultats ;
- **la marge est fausse** : la vraie marge est **0,69 g**, pas 0,9 ;
- **il prétend s'appuyer sur des données** (« l'analyse se base sur les données ouvertes ») sans en avoir consulté aucune. Sa trace montre **zéro appel d'outil**.

Le même texte apparaissait déjà dans l'évaluation (question 16, modèle seul : « 13,2 g ± 0,9 g » pour **toutes** les céréales, dont la vraie moyenne est 15,5 g). Je ne l'avais pas remarqué. C'est un vrai défaut du système, que tu viens de trouver : **l'exemple du prompt fuit dans les réponses**.

## Ce que je te conseille

**Pour la démo**, garde cette question et explique ce qui se passe. C'est plus fort qu'une réponse visiblement fausse :
> « Il répond 13,2 g ± 0,9 g. Ça a l'air juste, mais il n'a appelé aucun outil : il a recopié l'exemple écrit dans mon prompt. La vraie marge est 0,69. Un modèle seul peut donner une réponse qui semble juste, sans que personne puisse vérifier d'où vient le chiffre. C'est exactement ce que le garde-fou empêche. »

**Ne change pas le prompt maintenant.** Si on remplaçait l'exemple par « X g ± Y g », il faudrait relancer toute l'évaluation (35 minutes), et les résultats d'EVIDENCE.md ne correspondraient plus. Cite-le plutôt comme une **limite trouvée en préparant l'oral**, avec l'amélioration possible : un exemple neutre dans le prompt.

Si tu es d'accord, j'ajoute cette trouvaille dans EVIDENCE.md (limites de la brique 9) et dans la note de séance. C'est toi qui l'as trouvée, ça compte pour R3.

Continue la démo avec la commande suivante :
```
python -m nutri.agent "Les céréales bio contiennent-elles moins de sucre ?"
```


---

## Moi (15:40)

python -m nutri.agent "Les céréales bio contiennent-elles moins de sucre ?"
[outil] comparer({'nutriment': 'sucres', 'groupe': 'bio'}) -> {'nutriment': 'sucres', 'groupe': 'bio', 'groupes': [{'groupe': 'False', 'n': 410, 'moyenne': 18.59, 'marge_95': 0.82}, {'groupe': 'True', 'n': 543, 'moyenne': 13.17, 'marge_95': 0.69}], 'ecart_bio_moins_non_bio': -5.42, 'marge_95_ecart': 1.07, 'intervalle_95_ecart': [-6.49, -4.35], 'difference_nette': True}

Les céréales bio contiennent en moyenne 13,17 g de sucre contre 18,59 g pour les non bio (données sur 543 et 410 produits respectivement), soit une différence d'environ -5,42 g ± 1,07 g par 100 g. L'écart est significatif car la différence nette de sucre entre bio et non bio est vraie, confirmant ainsi que les céréales bio contiennent moins de sucre.


## Claude (15:40)


Celle-là a bien marché, et c'est la réponse idéale pour la démo. Voici ce qu'il faut **montrer du doigt** à l'examinateur, dans l'ordre :

**1. La ligne `[outil]`** (brique 1) :
> « Qwen n'a rien calculé. Il a choisi l'outil `comparer`, avec les sucres et le groupe bio. C'est Python qui a fait le calcul, et voici le dictionnaire qu'il a renvoyé à Qwen. »

**2. Les chiffres de la réponse viennent tous de ce dictionnaire.** Montre la correspondance : 13,17 et 18,59 sont les moyennes, 543 et 410 le nombre de produits, −5,42 l'écart, 1,07 la marge de l'écart.
> « Comme chaque chiffre vient d'un outil, le garde-fou a laissé passer la réponse. »

**3. La marge et `difference_nette`** (brique 8) :
> « L'écart est de −5,42 g ± 1,07 g. Sa fourchette, de −6,49 à −4,35, ne contient pas 0, donc `difference_nette` vaut True : l'écart ne vient pas du hasard. »

**4. Ce que la réponse ne dit pas, et que toi tu dis** (c'est ce qui fait la différence à l'oral) :
> « Attention : Qwen écrit "confirmant que les céréales bio contiennent moins de sucre". C'est vrai pour ces 953 fiches, mais ce n'est pas une cause : les bio ne sont pas moins sucrées *parce qu'*elles sont bio, ce sont peut-être d'autres types de produits. Et l'échantillon a 57 % de bio : il ne représente pas tout le rayon. »

Commande suivante, le cas « on ne peut pas conclure » :
```
python -m nutri.agent "Les céréales bio contiennent-elles plus de lipides que les non bio ?"
```


---

## Moi (15:46)

(.venv) (base) utilisatrice@ordinateur nutri-arbitre % resultats/evaluation.md
zsh: permission denied: resultats/evaluation.md


## Claude (15:46)


`resultats/evaluation.md` n'est pas une commande, c'est un **fichier**. Le terminal a essayé de l'exécuter comme un programme, d'où « permission denied ». Il faut l'**ouvrir**, et tu as deux façons de le faire.

**Dans le terminal** (la plus rapide) :
```
cat resultats/evaluation.md
```
`cat` affiche le contenu d'un fichier.

**Dans VS Code** (la plus jolie pour l'oral, je te la conseille) :
```
code resultats/evaluation.md
```
Si `code` ne marche pas, ouvre simplement le fichier depuis l'explorateur de gauche. Ensuite, fais **Cmd + Maj + V** : l'aperçu Markdown affiche de vrais tableaux, bien plus lisibles pour l'examinateur que le texte brut.

Pendant que le tableau est affiché, montre trois choses :
1. la ligne du bas : **73 % ± 4 %** pour le système complet, contre **12 % ± 6 %** pour le modèle seul ;
2. la question 11, **F F F** : c'est l'échec expliqué, la marque lue à l'envers ;
3. les **B** des questions pièges (13, 14 et 16) : le garde-fou a bloqué les calculs faits par Qwen.

Au fait, tu as sauté les étapes 3 et 4 : les lipides, la portion de 30 g et `python -m pytest tests/test_garde_fou.py -v`. Tu les as déjà lancées, ou tu veux les faire maintenant ? La **portion bloquée** est le moment le plus important de la démo, parce qu'on y voit la brique 3 en direct.


---

## Moi (15:47)

Moi, la mesure des faux positifs avec les lipides, ça j'ai pas trop compris.


## Claude (15:47)

> 🔧 Commande : Show the three model-alone lipid answers


Je reprends depuis le début, avec les vraies réponses.

## Qu'est-ce qu'un « faux positif » ?

C'est quand **mon programme de correction** dit « juste » alors que la réponse est **fausse**. Le programme de correction, c'est la fonction `juger` d'evaluation.py. Ce n'est pas Qwen qui se trompe ici, c'est **la mesure**.

Imagine un correcteur qui mettrait la note maximale à toute copie qui contient le mot « hasard », sans lire le reste.

## La question des lipides

« Les céréales bio contiennent-elles plus de lipides que les non bio ? »

La bonne réponse est **« on ne peut pas conclure »**, parce que l'écart (0,21 g) est plus petit que sa marge (0,84 g). Pour reconnaître cette réponse, `juger` cherche simplement des **mots** dans le texte ([evaluation.py:108-112](nutri/evaluation.py#L108-L112)) : « hasard », « pas conclure »… S'il en trouve un, c'est « juste ».

## Ce qu'a répondu le modèle seul, sans outils

Il a été compté **juste 3 fois sur 3**. Voici sa réponse du lancement 2, la plus parlante :

> « …on observe une **différence significative** avec des valeurs distinctes (par exemple **3,2 g ± 0,1 g** pour le bio versus **2,8 g ± 0,2 g** pour le non bio). Comme la différence nette est statistiquement significative, il apparaît que les céréales bio contiennent **effectivement plus de lipides**. Cet écart n'est probablement pas dû au **hasard**… »

Cette réponse est fausse deux fois :
1. **elle dit le contraire** de la bonne réponse, puisqu'elle affirme « oui, plus de lipides » ;
2. **ses chiffres sont inventés** : 3,2 g au lieu de 10,69 g, et zéro appel d'outil.

Pourtant, elle contient le mot « **hasard** », dans « pas dû au hasard ». Le correcteur trouve le mot et répond « juste ». Voilà le faux positif.

Aux lancements 1 et 3, le modèle seul conclut bien « on ne peut pas conclure », mais avec des **moyennes inventées** (3,2 g, 5,4 g). Il a la bonne conclusion, à partir de faux chiffres.

## Pourquoi c'est important, et ta décision

- **La conséquence** : le score du modèle seul (12 %) est **trop généreux**. Sans ces faux positifs, il serait autour de 6 %.
- **Ta décision** : on aurait pu corriger `juger` après coup. Tu as choisi de **garder** l'erreur et de la **montrer**, parce que corriger une mesure après avoir vu ses résultats, c'est risquer d'arranger les chiffres.

## La phrase pour l'oral
> « Ma mesure a aussi ses limites. Pour les lipides, elle cherche des mots comme "hasard". Le modèle seul a écrit "pas dû au hasard" en affirmant le contraire de la bonne réponse, avec des chiffres inventés, et il a été compté juste. J'ai gardé ce faux positif plutôt que de corriger ma mesure après avoir vu les résultats. Ça veut dire que le vrai score du modèle seul est encore plus bas que 12 %. »


---

## Moi (15:51)

Après, honnêtement, ce choix, je l'ai fait parce que je voulais pas trop compliquer le code, sachant que déjà là, j'ai dû passer au moins 7 heures sur la compréhension. La lecture, du code, des explications. Du coup, maintenant, bah, on a fini, en fait. Super, tu m'as bien aidé, j'ai beaucoup appris. Donc, il va falloir qu'on fasse ce qu'il faut faire, c'est-à-dire push sur GitHub et le journal, etc. Dis-moi tout ce qu'il faut faire, relis les consignes et dis-le-moi.


## Claude (15:51)


Je relis la consigne point par point et je vérifie le dépôt, pour te donner une liste exacte :

> 🔧 Commande : Check consigne, author email, personal data, evidence

> 🔧 Commande : Read brick rules and check repo for personal data


J'ai relu toute la consigne et vérifié le dépôt. Les **5 briques et R1 à R4 sont couvertes**. Voici ce qu'il reste à faire.

## Ce que je fais (sans risque, dès que tu valides)
1. **EVIDENCE.md, brique 8 : ajouter la commande « Reproduire ».** C'est la seule section qui ne l'a pas, alors que la consigne la demande pour chaque brique.
2. **EVIDENCE.md, faux positifs : écrire ta vraie raison.** Tu viens de me la dire : ne pas compliquer un code que tu dois savoir expliquer, et ne pas corriger la mesure après avoir vu les résultats. Pour l'instant, j'ai seulement écrit la seconde. Mieux vaut écrire la vérité, c'est ce que demande R3.
3. **Ajouter la fuite de l'exemple du prompt** (« 13,2 g ± 0,9 g ») dans les limites de la brique 9. C'est toi qui l'as trouvée pendant la simulation.
4. **ai_log, note de la séance 4** : la simulation d'oral, ta trouvaille, les documents NotebookLM, ta vraie raison. Puis le nouvel export de la conversation d'aujourd'hui.
5. **README** : remplacer `<URL_DU_DEPOT>` par la vraie adresse du dépôt.
6. **Mettre le PDF de la consigne dans `.gitignore`**, pour qu'il ne soit jamais envoyé par erreur.
7. **Créer le dépôt GitHub et y envoyer le projet**, avec `gh`, où tu es déjà connectée en MelinaSeh06.
8. **Tester un clone neuf depuis GitHub** et lancer les tests (R1).

## Ce que tu dois faire toi
1. **Déposer `conversation_1a_creation.pdf` dans `ai_log/`.** Vérifie avant que le PDF ne montre ni ton e-mail ni ton nom complet, parce que la consigne interdit les données personnelles dans le dépôt.
2. **Rendre le lien du dépôt (ou un zip) sur Blackboard**, et vérifier la date de rendu et ton créneau de soutenance.
3. **Le jour J** : lancer Ollama et poser une première question avant ton passage.

## Un point à te signaler : ton e-mail
Tes 15 commits sont signés **[adresse e-mail retirée]**. Sur un dépôt **public**, cette adresse sera visible par tout le monde dans l'historique. Je n'ai trouvé aucune autre donnée personnelle dans les fichiers.

J'ai trois décisions à te demander :

> 🔧 AskUserQuestion


C'est noté : dépôt **public**, nommé **nutri-arbitre**, avec ton e-mail remplacé par l'adresse anonyme de GitHub. Je récupère d'abord cette adresse et je vérifie que le nom est libre :

> 🔧 Commande : Get GitHub noreply email and check repo name


Le nom est libre. Maintenant les modifications des fichiers : EVIDENCE.md, README, .gitignore et la note de séance.

> 🔧 Commande : Update evidence, readme, gitignore, log; set noreply email


Tes essais de démo ont créé 5 traces. Je les garde : l'une d'elles prouve la fuite de l'exemple du prompt. Je regarde ce qu'elles contiennent :

> 🔧 Commande : Summarize the demo traces

> 🔧 Commande : Cite demo trace and commit


Maintenant, je remplace ton e-mail dans les 16 commits. Je garde d'abord une copie de sauvegarde de l'historique, au cas où :

> 🔧 Commande : Rewrite commit emails to GitHub noreply

> 🔧 Commande : Update stale commit hash references

> 🔧 Commande : Re-export séance 4 and check personal data

> 🔧 Commande : Locate personal data in export


Tes messages d'aujourd'hui contiennent ton nom d'utilisatrice (dans l'invite du terminal) et ton e-mail. J'ajoute un filtre à l'export pour les masquer :

> 🔧 Commande : Add personal-data filter and re-export
