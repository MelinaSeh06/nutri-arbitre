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
```

Le fichier nettoyé `data/cereales_propres.csv` est inclus dans le dépôt : Open Food Facts change
chaque jour, et les réponses connues des tests de la brique 9 doivent rester fixes.

## Structure

| Fichier | Rôle |
|---|---|
| `nutri/download.py` | télécharge les données brutes (API Open Food Facts) |
| `nutri/clean.py` | nettoie et écrit `data/journal_nettoyage.md` |
| `nutri/tools.py` | les outils de calcul que le modèle appelle |
| `nutri/garde_fou.py` | la règle imposée par le code |
| `nutri/agent.py` | la boucle d'agent avec Ollama, sauve les traces dans `traces/` |
| `tests/` | tests pytest à réponse connue |
| `EVIDENCE.md` | preuves, brique par brique |
| `ai_log/` | journal d'usage de l'IA |

Aucune clé d'API ni donnée personnelle n'est nécessaire ni présente dans le dépôt.
