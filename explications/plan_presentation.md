# Plan de la présentation (environ 6 min)

Idée directrice : « un modèle qui n'a pas le droit d'inventer un chiffre ».

**Règle d'or :** dans le terminal, copier seulement ce qui est dans les blocs gris, **sans** les accents graves `` ` ``,
et toujours sur **une seule ligne**.

---

## 0. Avant de passer (5 minutes avant, pas devant l'examinateur)

1. Ouvrir VS Code sur le dossier du projet, puis un terminal (menu **Terminal → Nouveau terminal**).
2. Aller dans le dossier du projet (inutile si la ligne finit déjà par `nutri-arbitre %`) :
   ```
   cd ~/PGE3S1/coding_for_ai/nutri-arbitre
   ```
3. Activer l'environnement du projet :
   ```
   source .venv/bin/activate
   ```
   ✅ **Vérifier que la ligne commence par `(.venv)`.** Sans lui : « No module named 'ollama' ».
4. Vérifier qu'Ollama et le modèle sont là :
   ```
   ollama list
   ```
   ✅ On doit voir `qwen3.5:4b-q4_K_M`. (Pas besoin de `ollama serve` : Ollama tourne déjà tout seul.)
5. Charger le modèle avec une première question (la première réponse met environ 20 s) :
   ```
   python -m nutri.agent "Combien de céréales bio y a-t-il dans les données ?"
   ```
6. Vérifier que les tests passent :
   ```
   python -m pytest -q
   ```
   ✅ `42 passed`.
7. Ouvrir à l'avance `resultats/evaluation.md` dans VS Code, puis **Cmd + Maj + V** (l'aperçu, avec de vrais tableaux).
8. Effacer le terminal pour partir propre : **Cmd + K**.

---

## 1. Le problème (30 s)

Un petit modèle comme Qwen invente des chiffres avec assurance. Le modèle seul, sans outils :
```
python -m nutri.agent --modele-seul "Quelle est la teneur moyenne en sucres des céréales bio, pour 100 g ?"
```
- S'il répond « 13,2 g ± 0,9 g » : « Ça a l'air juste, mais il n'a appelé aucun outil : il a recopié l'exemple écrit
  dans mon prompt. La vraie marge est 0,69 g. Personne ne peut vérifier d'où vient ce chiffre. »
- S'il invente un autre chiffre : « La vraie valeur est 13,17 g. Il l'a inventé. »
- S'il refuse : « Ici il refuse, mais dans mon évaluation il a inventé des chiffres 17 fois sur 48, par exemple
  6,8 g ± 1,4 g. »

## 2. La solution (1 min)

Le trajet, à dire :
question → Qwen choisit un outil → règle n° 2 (le filtre est-il demandé ?) → Python calcule (avec la marge) →
Qwen écrit → règle n° 1 (chaque chiffre vient-il d'un outil ?) → réponse affichée ou bloquée.

## 3. La démo (2 min)

**a. Une réponse juste, avec sa marge (briques 1 et 8) :**
```
python -m nutri.agent "Les céréales bio contiennent-elles moins de sucre ?"
```
Montrer la ligne `[outil] comparer(...)` : Qwen n'a rien calculé. Puis : 13,17 contre 18,59, écart −5,42 ± 1,07,
fourchette sans 0 → écart net. Ajouter : « ce n'est pas une cause, et l'échantillon a 57 % de bio ».

**b. Un écart qui n'est pas net (brique 8) :**
```
python -m nutri.agent "Les céréales bio contiennent-elles plus de lipides que les non bio ?"
```
Écart 0,21 g ± 0,84 g : la fourchette contient 0 → « on ne peut pas conclure ».

**c. Une réponse bloquée (brique 3) :**
```
python -m nutri.agent "Combien de calories apporte une portion de 30 g de céréales, en moyenne ?"
```
Aucun outil ne calcule une portion : Qwen calcule lui-même → **Réponse bloquée**. On voit parfois aussi la règle
n° 2 : un filtre bio refusé, puis Qwen qui se corrige.

## 4. La preuve que les règles tiennent (1 min)

```
python -m pytest tests/test_garde_fou.py -v
```
Les 15 tests qui essaient d'enfreindre les règles, dont 3 tirés de vraies réponses de Qwen (le bol de 40 g).

## 5. Les résultats chiffrés (1 min)

Passer à l'onglet `resultats/evaluation.md` déjà ouvert (étape 0.7). Sinon, dans le terminal :
```
cat resultats/evaluation.md
```
- Système complet **73 % ± 4 %**, modèle seul **12 % ± 6 %** ; 8 réponses bloquées ; 17 chiffres inventés par le
  modèle seul.
- L'échec expliqué, question 11 (F F F) : Qwen demande le classement en ordre décroissant et lit la marque la plus
  sucrée (Crownfield, 18,61 g) comme la moins sucrée. Le garde-fou laisse passer : le chiffre vient d'un outil.

## 6. Les limites (30 s)

- Échantillon biaisé : les 1 000 premiers produits d'Open Food Facts, 57 % de bio ; pas de lien de cause.
- Le garde-fou vérifie l'origine des chiffres, pas le sens des phrases.
- Ma mesure a des faux positifs (les lipides du modèle seul), gardés volontairement.
- L'exemple du prompt (« 13,2 g ± 0,9 g ») est recopié par le modèle seul.

---

## Si quelque chose ne va pas

| Ce que je vois | Ce que ça veut dire | Ce que je fais |
|---|---|---|
| `No module named 'ollama'` (ou `pandas`) | l'environnement n'est pas activé : pas de `(.venv)` au début de la ligne | `source .venv/bin/activate`, puis relancer |
| `dquote>` | il manque le guillemet de fin | **Ctrl + C**, puis retaper la commande sur une seule ligne |
| `command not found: Je` (ou un autre mot) | j'ai copié les accents graves `` ` `` | retaper la commande sans eux |
| `permission denied: resultats/evaluation.md` | j'ai tapé un nom de fichier comme une commande | `cat resultats/evaluation.md`, ou l'ouvrir dans VS Code |
| `address already in use` après `ollama serve` | Ollama tourne déjà : ce n'est pas une erreur | rien, continuer |
| `Connection refused` / `Failed to connect to Ollama` | Ollama n'est pas lancé | ouvrir l'application Ollama (ou `ollama serve` dans un **autre** terminal), attendre 5 s, relancer |
| `No such file or directory: data/cereales_propres.csv` | je ne suis pas dans le dossier du projet | `cd ~/PGE3S1/coding_for_ai/nutri-arbitre` |
| la réponse met longtemps (20 à 40 s) | Qwen se charge ou réfléchit | attendre, et en profiter pour expliquer ce qu'on attend |
| Qwen répond autre chose que prévu | il ne répond jamais deux fois pareil | le commenter : « vous voyez, il a choisi tel outil… » ; c'est même une preuve du besoin du garde-fou |
| la commande tourne sans fin | Qwen est bloqué | **Ctrl + C**, relancer une fois ; sinon montrer une trace déjà enregistrée dans `traces/` |

**Pas de frontend** : le terminal montre les appels d'outils en direct, et ça fait un fichier de
moins à expliquer.
