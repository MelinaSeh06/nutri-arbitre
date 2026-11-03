"""Brique 9 : une comparaison mesurée.

On pose 16 questions (dont 4 pièges) dont on connaît la bonne réponse, 3 fois chacune, à deux systèmes :
  - le système complet (Qwen + outils + garde-fou) ;
  - le modèle seul (Qwen sans outils ni garde-fou, il répond de mémoire).
On compte les réponses justes, fausses et bloquées, puis on donne la moyenne et la dispersion.

Les bonnes réponses sont calculées ici directement avec pandas, sans passer par tools.py :
c'est une vérification indépendante.

Usage :
  python -m nutri.evaluation            # tout (environ 35 minutes)
  python -m nutri.evaluation --rapide   # 2 questions, 1 lancement : pour vérifier que ça marche
"""
import argparse
import json
import statistics
import time
from pathlib import Path

from nutri import garde_fou
from nutri.agent import charger_donnees, repondre

N_LANCEMENTS = 3                 # chaque question est posée 3 fois (Qwen ne répond pas toujours pareil)
TOLERANCE = 0.02                 # un nombre est juste s'il est à 2 % près de la bonne réponse
DOSSIER = Path("resultats")


def construire_taches(df) -> list[dict]:
    """Les 16 questions et leur bonne réponse, calculée avec pandas.
    4 types de réponse : un nombre, un texte (nom de marque), de la prudence (« on ne peut pas conclure »),
    ou un refus (la donnée n'existe pas : aucun chiffre ne doit être donné)."""
    bio = df[df["bio"]]
    non_bio = df[~df["bio"]]
    # la marque (au moins 5 produits) dont la moyenne de sucres est la plus basse
    par_marque = df.groupby("marque")["sucres"].agg(["count", "mean"])
    marque_moins_sucree = par_marque[par_marque["count"] >= 5]["mean"].idxmin()

    return [
        {"question": "Combien de céréales du petit-déjeuner y a-t-il dans les données ?",
         "type": "nombre", "attendu": len(df)},
        {"question": "Combien de céréales bio y a-t-il dans les données ?",
         "type": "nombre", "attendu": len(bio)},
        {"question": "Combien de céréales ont un Nutri-Score A ?",
         "type": "nombre", "attendu": int((df["nutriscore"] == "a").sum())},
        {"question": "Quelle est la teneur moyenne en sucres des céréales bio, pour 100 g ?",
         "type": "nombre", "attendu": bio["sucres"].mean()},
        {"question": "Quelle est la teneur moyenne en sucres des céréales non bio, pour 100 g ?",
         "type": "nombre", "attendu": non_bio["sucres"].mean()},
        {"question": "Quelle est la teneur moyenne en sel des céréales bio, pour 100 g ?",
         "type": "nombre", "attendu": bio["sel"].mean()},
        {"question": "Combien de calories apportent 100 g de céréales, en moyenne ?",
         "type": "nombre", "attendu": df["energie_kcal"].mean()},
        {"question": "Quelle est la teneur moyenne en protéines des céréales, pour 100 g ?",
         "type": "nombre", "attendu": df["proteines"].mean()},
        {"question": "Quelle est la teneur moyenne en fibres des céréales au Nutri-Score A, pour 100 g ?",
         "type": "nombre", "attendu": df[df["nutriscore"] == "a"]["fibres"].mean()},
        {"question": "De combien de grammes les céréales bio ont-elles moins de sucres que les non bio, "
                     "pour 100 g ?",
         "type": "nombre", "attendu": bio["sucres"].mean() - non_bio["sucres"].mean()},
        {"question": "Quelle marque (au moins 5 produits) a la teneur moyenne en sucres la plus basse ?",
         "type": "texte", "attendu": marque_moins_sucree},
        # l'écart de lipides est petit (0,21 g) devant sa marge (0,84 g) : la bonne réponse est la prudence
        {"question": "Les céréales bio contiennent-elles plus de lipides que les non bio ?",
         "type": "prudence", "attendu": ["hasard", "pas conclure", "pas de conclure", "pas de différence nette"]},

        # Questions pièges, choisies pour montrer les failles connues du système :
        # une portion (aucun outil ne fait ce calcul : le modèle calcule lui-même, le garde-fou bloque)
        {"question": "Combien de calories apporte une portion de 30 g de céréales, en moyenne ?",
         "type": "nombre", "attendu": df["energie_kcal"].mean() * 0.30},
        # une soustraction entre deux résultats d'outil (même problème : c'est le modèle qui calcule)
        {"question": "Quel est l'écart de sucres entre les céréales au Nutri-Score A et celles au "
                     "Nutri-Score E, pour 100 g ?",
         "type": "nombre", "attendu": df[df["nutriscore"] == "a"]["sucres"].mean()
                                      - df[df["nutriscore"] == "e"]["sucres"].mean()},
        # une donnée absente du fichier : la bonne réponse est de ne donner aucun chiffre
        {"question": "Quelle est la teneur moyenne en vitamine C des céréales, pour 100 g ?",
         "type": "refus", "attendu": None},
        # toutes les céréales : tentant de filtrer sur le bio alors que la question n'en parle pas
        {"question": "Les céréales du petit-déjeuner sont-elles riches en sucres ? Donne la moyenne pour 100 g.",
         "type": "nombre", "attendu": df["sucres"].mean()},
    ]


def nombre_juste(reponse: str, attendu: float) -> bool:
    """La réponse contient-elle un nombre à 2 % près de la bonne réponse ?
    On compare sans le signe : « 5,4 g de moins » est juste pour un écart de -5,42."""
    # au moins 0,01 : les outils arrondissent à 2 décimales (0,1265 de sel devient « 0,13 »)
    ecart_permis = max(TOLERANCE * abs(attendu), 0.01)
    for ecrit in garde_fou.extraire_nombres(reponse):
        valeur = abs(garde_fou.en_float(ecrit))
        if abs(valeur - abs(attendu)) <= ecart_permis:
            return True
    return False


def juger(tache: dict, trace: dict) -> str:
    """Renvoie "bloquee", "juste" ou "fausse"."""
    if trace["bloquee"]:
        return "bloquee"        # le garde-fou a refusé : ni juste ni fausse, aucune réponse donnée
    reponse = trace["reponse"]
    if tache["type"] == "nombre":
        ok = nombre_juste(reponse, tache["attendu"])
    elif tache["type"] == "texte":
        ok = tache["attendu"].lower() in reponse.lower()
    elif tache["type"] == "refus":   # donnée absente : juste si la réponse n'invente aucun chiffre
        ok = garde_fou.verifier(reponse, [], trace["question"])[0]
    else:   # prudence : la réponse doit dire qu'on ne peut pas conclure
        ok = False
        for mot in tache["attendu"]:
            if mot in reponse.lower():
                ok = True
    return "juste" if ok else "fausse"


def resumer(verdicts: list[list[str]]) -> dict:
    """verdicts[l] = la liste des verdicts du lancement l (un par question).
    Taux de réponses justes à chaque lancement, puis leur moyenne et leur écart type (la dispersion)."""
    taux = []
    for lancement in verdicts:
        taux.append(lancement.count("juste") / len(lancement))
    tous = []
    for lancement in verdicts:
        tous += lancement            # on met bout à bout les verdicts de tous les lancements
    return {"taux_juste_par_lancement": [round(t, 3) for t in taux],
            "taux_juste_moyen": round(statistics.mean(taux), 3),
            "ecart_type": round(statistics.stdev(taux), 3) if len(taux) >= 2 else None,
            "justes": tous.count("juste"), "fausses": tous.count("fausse"),
            "bloquees": tous.count("bloquee"), "total": len(tous)}


def evaluer(n_lancements: int = N_LANCEMENTS, n_taches: int = None) -> dict:
    df = charger_donnees()
    taches = construire_taches(df)[:n_taches]
    systemes = {"complet": True, "modele_seul": False}     # nom -> avec_outils
    verdicts = {"complet": [], "modele_seul": []}
    details = []                                          # toutes les traces, pour expliquer les échecs

    for lancement in range(n_lancements):
        for nom in systemes:
            verdicts[nom].append([])
        for i, tache in enumerate(taches):
            for nom, avec_outils in systemes.items():
                trace = repondre(tache["question"], df, avec_outils=avec_outils)
                verdict = juger(tache, trace)
                verdicts[nom][lancement].append(verdict)
                details.append({"lancement": lancement + 1, "tache": i + 1, "systeme": nom,
                                "attendu": tache["attendu"], "verdict": verdict, "trace": trace})
                print(f"lancement {lancement + 1}, question {i + 1:2d}, {nom:11s} : {verdict}")

    resume = {}
    par_question = {}     # pour chaque question, ses verdicts aux 3 lancements, ex. ["juste", "juste", "bloquee"]
    for nom in systemes:
        resume[nom] = resumer(verdicts[nom])
        par_question[nom] = []
        for i in range(len(taches)):
            verdicts_question = []
            for l in range(n_lancements):
                verdicts_question.append(verdicts[nom][l][i])
            par_question[nom].append(verdicts_question)

    return {"date": time.strftime("%Y-%m-%d %H:%M"), "questions": [t["question"] for t in taches],
            "resume": resume, "par_question": par_question, "details": details}


def ecrire_tableau(res: dict) -> str:
    """Un tableau Markdown lisible des résultats."""
    lignes = ["# Brique 9 : système complet contre modèle seul", "",
              f"Évaluation du {res['date']}. Verdicts des lancements, question par question "
              "(J = juste, F = fausse, B = bloquée).", "",
              "| # | Question | Complet | Modèle seul |", "|---|---|---|---|"]
    lettre = {"juste": "J", "fausse": "F", "bloquee": "B"}
    for i, q in enumerate(res["questions"]):
        complet = " ".join(lettre[v] for v in res["par_question"]["complet"][i])
        seul = " ".join(lettre[v] for v in res["par_question"]["modele_seul"][i])
        lignes.append(f"| {i + 1} | {q} | {complet} | {seul} |")
    lignes += ["", "| Système | Taux de réponses justes (moyenne ± écart type) | Justes | Fausses | Bloquées |",
               "|---|---|---|---|---|"]
    for nom, r in res["resume"].items():
        lignes.append(f"| {nom} | {r['taux_juste_moyen']:.0%} ± {r['ecart_type'] or 0:.0%} "
                      f"| {r['justes']} | {r['fausses']} | {r['bloquees']} |")
    return "\n".join(lignes) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rapide", action="store_true", help="2 questions, 1 lancement")
    args = parser.parse_args()
    if args.rapide:
        res = evaluer(n_lancements=1, n_taches=2)
    else:
        res = evaluer()
    DOSSIER.mkdir(exist_ok=True)
    (DOSSIER / "evaluation.json").write_text(json.dumps(res, ensure_ascii=False, indent=2, default=str),
                                             encoding="utf-8")
    (DOSSIER / "evaluation.md").write_text(ecrire_tableau(res), encoding="utf-8")
    print("\n" + ecrire_tableau(res))
