# Nutri-Arbitre : un analyste nutrition qui n'a pas le droit d'inventer un chiffre

Un petit agent répond à des questions sur les céréales du petit-déjeuner vendues en France
(données ouvertes Open Food Facts). Le modèle de langage (Qwen3.5-4B) choisit les calculs,
mais ce sont des fonctions Python qui les font, et un garde-fou écrit en code bloque toute
réponse contenant un chiffre qui ne vient pas de ces fonctions.

**Modèle utilisé :** Qwen3.5-4B quantifié Q4_K_M, en local via Ollama, contexte de 8192 tokens.

## Installation (clone neuf)

```bash
git clone <URL_DU_DEPOT> nutri-arbitre && cd nutri-arbitre
python -m venv .venv && source .venv/bin/activate   # Windows : .venv\Scripts\activate
pip install -r requirements.txt
ollama pull qwen3.5:4b-q4_K_M
```

## Lancer

```bash
python -m pytest                       # tests automatiques (sans le modèle)
python -m nutri.download --pages 20    # facultatif : re-télécharger Open Food Facts (~3 min)
python -m nutri.clean                  # facultatif : refaire le nettoyage et son journal
python -m nutri.agent "Les céréales bio contiennent-elles moins de sucre ?"
python -m nutri.agent --modele-seul "Les céréales bio contiennent-elles moins de sucre ?"
python -m nutri.evaluation --rapide    # brique 9 : essai de 1 minute (2 questions)
python -m nutri.evaluation             # brique 9 : 16 questions x 3 lancements x 2 systèmes (~35 min)
```

Le fichier nettoyé `data/cereales_propres.csv` est inclus dans le dépôt : Open Food Facts change
chaque jour, et les réponses connues des tests de la brique 9 doivent rester fixes. Re-télécharger
puis re-nettoyer remplace ce fichier : les chiffres d'EVIDENCE.md ne seraient plus les mêmes.

## Structure

| Fichier | Rôle |
|---|---|
| `nutri/download.py` | télécharge les données brutes (API Open Food Facts) |
| `nutri/clean.py` | nettoie et écrit `data/journal_nettoyage.md` |
| `nutri/tools.py` | les outils de calcul que le modèle appelle |
| `nutri/garde_fou.py` | les deux règles imposées par le code |
| `nutri/agent.py` | la boucle d'agent avec Ollama, sauve les traces dans `traces/` |
| `nutri/evaluation.py` | brique 9 : système complet contre modèle seul, résultats dans `resultats/` |
| `tests/` | tests pytest à réponse connue |
| `EVIDENCE.md` | preuves, brique par brique |
| `ai_log/` | journal d'usage de l'IA |
| `explications/` | une fiche PDF d'explication par fichier de code |

Aucune clé d'API ni donnée personnelle n'est nécessaire ni présente dans le dépôt.
