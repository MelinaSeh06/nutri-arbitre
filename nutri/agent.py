"""La boucle d'agent : le modèle lit la question, appelle les outils, puis répond.
La réponse finale passe par le garde-fou avant d'être affichée.

Usage :
  python -m nutri.agent "Les céréales bio contiennent-elles moins de sucre ?"
  python -m nutri.agent --modele-seul "..."   # le modèle sans outils ni garde-fou (pour la brique 9)
"""
import argparse
import json
import os
import time
from pathlib import Path

import pandas as pd
from ollama import chat

from nutri import garde_fou, tools

MODELE = os.environ.get("NUTRI_MODELE", "qwen3.5:4b-q4_K_M")
OPTIONS = {"num_ctx": 8192}          # longueur de contexte fixée (cf. consigne, section 2)
MAX_TOURS = 6                        # au-delà, on arrête la boucle
DONNEES = Path("data/cereales_propres.csv")
DOSSIER_TRACES = Path("traces")

PROMPT_SYSTEME = """Tu es un analyste nutrition. Tu réponds en français à des questions sur les
céréales du petit-déjeuner vendues en France (données Open Food Facts, valeurs pour 100 g).
Pour tout chiffre, appelle un outil : n'écris jamais un nombre que tu n'as pas reçu d'un outil.
Recopie les nombres tels que les outils les donnent. Réponds en 2 à 4 phrases."""


def charger_donnees() -> pd.DataFrame:
    return pd.read_csv(DONNEES, dtype={"code": str})


def executer_outil(df, nom: str, arguments: dict) -> dict:
    """Appelle la fonction Python demandée par le modèle. Une erreur est renvoyée au modèle,
    au lieu de faire planter le programme, pour qu'il puisse corriger son appel."""
    if nom not in tools.FONCTIONS:
        return {"erreur": f"outil inconnu : {nom}"}
    fonction = tools.FONCTIONS[nom]          # ex. "decrire" -> la fonction tools.decrire
    try:
        # **arguments « déballe » le dictionnaire : avec {"nutriment": "sucres", "bio": True},
        # cette ligne revient à écrire  tools.decrire(df, nutriment="sucres", bio=True)
        return fonction(df, **arguments)
    except (ValueError, TypeError) as e:
        return {"erreur": str(e)}


def repondre(question: str, df: pd.DataFrame, avec_outils: bool = True) -> dict:
    """Pose la question et renvoie une trace complète (appels, résultats, réponse, tokens)."""
    # la conversation : le rôle du modèle (system) puis la question (user)
    messages = [{"role": "system", "content": PROMPT_SYSTEME},
                {"role": "user", "content": question}]
    # la trace garde tout ce qui s'est passé, pour la sauver en JSON (preuves)
    trace = {"question": question, "modele": MODELE, "avec_outils": avec_outils,
             "appels": [], "tokens_entree": 0, "tokens_sortie": 0}
    resultats = []           # tous les résultats d'outils : le garde-fou s'en sert à la fin
    debut = time.time()
    if avec_outils:
        outils_proposes = tools.SCHEMAS
    else:
        outils_proposes = None

    reponse_brute = None     # restera None si le modèle n'a pas fini au bout de MAX_TOURS
    for tour in range(MAX_TOURS):
        # 1. on envoie toute la conversation au modèle
        r = chat(model=MODELE, messages=messages, tools=outils_proposes,
                 options=OPTIONS, think=False)   # think=False : pas de « réflexion » cachée, plus rapide
        trace["tokens_entree"] += r.prompt_eval_count or 0
        trace["tokens_sortie"] += r.eval_count or 0
        messages.append(r.message)   # sa réponse fait désormais partie de la conversation

        # 2. s'il ne demande aucun outil, c'est sa réponse finale : on sort de la boucle
        if not r.message.tool_calls:
            reponse_brute = r.message.content or ""
            break

        # 3. sinon, on exécute chaque outil demandé et on lui renvoie le résultat
        for appel in r.message.tool_calls:
            nom = appel.function.name
            args = dict(appel.function.arguments or {})
            resultat = executer_outil(df, nom, args)
            resultats.append(resultat)
            trace["appels"].append({"outil": nom, "arguments": args, "resultat": resultat})
            messages.append({"role": "tool", "tool_name": nom,
                             "content": json.dumps(resultat, ensure_ascii=False)})
        # puis on recommence un tour : le modèle lit les résultats et continue

    if reponse_brute is None:
        reponse_brute = "Je n'ai pas réussi à répondre en un nombre raisonnable d'étapes."

    trace["reponse_brute"] = reponse_brute
    if avec_outils:   # le système complet : la barrière s'applique
        trace["reponse"] = garde_fou.filtrer_reponse(reponse_brute, resultats, question)
    else:             # le modèle seul : aucune vérification
        trace["reponse"] = reponse_brute
    trace["bloquee"] = trace["reponse"] != reponse_brute
    trace["duree_s"] = round(time.time() - debut, 1)
    return trace


def sauver_trace(trace: dict) -> Path:
    DOSSIER_TRACES.mkdir(exist_ok=True)
    chemin = DOSSIER_TRACES / f"trace_{time.strftime('%Y%m%d_%H%M%S')}.json"
    chemin.write_text(json.dumps(trace, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return chemin


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    parser.add_argument("--modele-seul", action="store_true", help="sans outils ni garde-fou")
    args = parser.parse_args()
    trace = repondre(args.question, charger_donnees(), avec_outils=not args.modele_seul)
    for a in trace["appels"]:
        print(f"[outil] {a['outil']}({a['arguments']}) -> {a['resultat']}")
    print("\n" + trace["reponse"])
    print(f"\n(trace : {sauver_trace(trace)})")
