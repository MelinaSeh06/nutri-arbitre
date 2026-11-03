"""Brique 3 : la règle « aucun chiffre qui n'a pas été calculé par le code ».

Le prompt demande au modèle de ne pas inventer de chiffres, mais un prompt peut être ignoré.
Ici, c'est le CODE qui vérifie la réponse finale avant de l'afficher :
chaque nombre de la réponse doit venir d'un résultat d'outil (ou de la question elle-même).
Sinon la réponse est bloquée.

Deuxième règle (fin du fichier) : un outil ne peut pas filtrer sur bio ou Nutri-Score si la question
n'en parle pas. Cette règle est appliquée au moment de l'appel d'outil, dans agent.py.
"""
from __future__ import annotations   # « str | None » accepté aussi en Python 3.9

import json
import re

# Expression régulière qui reconnaît un nombre dans un texte. Lecture morceau par morceau :
#   -?          un signe moins, facultatif
#   \d+         un ou plusieurs chiffres            -> "12"
#   (?:[.,]\d+)? facultatif : un point ou une virgule suivi de chiffres -> ",5"
# Exemples reconnus : "12", "12,5", "12.5", "-3"
MOTIF_NOMBRE = re.compile(r"-?\d+(?:[.,]\d+)?")

# Constantes qu'on a le droit d'écrire sans calcul : « pour 100 g » et « marge à 95 % ».
# (Attention : les noms de champs comme "marge_95" sont lus aussi, car on cherche les nombres dans le
# texte JSON. Le 95 serait donc accepté de toute façon ; on l'écrit ici pour que ce soit voulu.)
CONSTANTES_AUTORISEES = [100.0, 95.0]

MESSAGE_REFUS = ("Réponse bloquée : elle contenait des chiffres qui n'ont pas été calculés par "
                 "les outils ({}). Reformulez la question pour que le calcul soit fait par le code.")


def extraire_nombres(texte: str) -> list[str]:
    """Renvoie les nombres écrits dans un texte, tels qu'ils sont écrits ('12,5')."""
    return MOTIF_NOMBRE.findall(texte or "")


def en_float(ecrit: str) -> float:
    """'12,5' -> 12.5 (Python ne comprend que le point)."""
    return float(ecrit.replace(",", "."))


def nombres_autorises(objet) -> list[float]:
    """Récupère tous les nombres d'un résultat d'outil (dictionnaire, liste…).
    Astuce : on transforme le résultat en texte JSON, puis on y cherche les nombres
    avec la même expression régulière que pour la réponse.
    Ex. : {"n": 42, "moyenne": 18.37} -> '{"n": 42, "moyenne": 18.37}' -> [42.0, 18.37]"""
    texte = json.dumps(objet, ensure_ascii=False, default=str)
    return [en_float(n) for n in extraire_nombres(texte)]


def nombre_justifie(ecrit: str, autorises: list[float]) -> bool:
    """Le nombre écrit est-il un arrondi correct d'un nombre calculé par les outils ?
    Ex. avec 18.37 calculé : "18" oui, "18,4" oui, "19" non, "18,5" non."""
    valeur = en_float(ecrit)

    # combien de chiffres après la virgule ? "18,4" -> 1, "18" -> 0
    ecrit = ecrit.replace(",", ".")
    if "." in ecrit:
        decimales = len(ecrit.split(".")[1])
    else:
        decimales = 0

    # écart permis = une demi-unité du dernier chiffre écrit
    # "18" -> 0,5 (18,37 est à 0,37 : ok) ; "18,4" -> 0,05 (18,37 est à 0,03 : ok)
    tolerance = 0.5 * 10 ** (-decimales)
    tolerance += 1e-9   # minuscule marge : les ordinateurs calculent 0,1 + 0,2 = 0,30000000000000004

    for a in autorises:
        if abs(valeur - a) <= tolerance:
            return True
    return False


def verifier(reponse: str, resultats_outils: list, question: str = "") -> tuple[bool, list[str]]:
    """Renvoie (autorisée ?, liste des nombres non justifiés)."""
    # les nombres qu'on a le droit d'écrire : ceux des outils, ceux de la question, et les constantes 100 et 95
    autorises = nombres_autorises(resultats_outils) + nombres_autorises(question) + CONSTANTES_AUTORISEES
    # un écart de -20 peut s'écrire « 20 g de moins » : on autorise aussi la valeur sans signe
    autorises += [abs(a) for a in autorises]

    non_justifies = []
    for n in extraire_nombres(reponse):
        if not nombre_justifie(n, autorises):
            non_justifies.append(n)
    return (len(non_justifies) == 0, non_justifies)


def filtrer_reponse(reponse: str, resultats_outils: list, question: str = "") -> str:
    """La barrière : renvoie la réponse si elle est propre, sinon un message de refus."""
    ok, fautifs = verifier(reponse, resultats_outils, question)
    return reponse if ok else MESSAGE_REFUS.format(", ".join(fautifs))


# Deuxième règle : un outil n'a pas le droit de filtrer sur un critère dont la question ne parle pas.
# (Vrai cas du 02/11/2026 : « calories d'une portion de céréales » -> Qwen a filtré les seules non bio.)
# \b = début ou fin de mot : « bio » est trouvé dans « céréales bio », pas dans « biologie » ni « cabio ».
PARLE_DE_BIO = re.compile(r"\b(bio|bios|biologique|biologiques|organic|ab)\b", re.IGNORECASE)
PARLE_DE_NUTRISCORE = re.compile(r"nutri[- ]?score", re.IGNORECASE)


def verifier_filtres(question: str, arguments: dict) -> str | None:
    """Renvoie un message d'erreur si l'appel d'outil filtre ou découpe en groupes selon un critère
    dont la question ne parle pas, sinon None. Le message est renvoyé au modèle, qui peut corriger."""
    utilise_bio = arguments.get("bio") is not None or arguments.get("groupe") == "bio"
    if utilise_bio and not PARLE_DE_BIO.search(question):
        return ("la question ne parle pas de bio : ne filtre pas et ne compare pas selon le bio, "
                "utilise decrire sur toutes les céréales")
    utilise_ns = arguments.get("nutriscore") is not None or arguments.get("groupe") == "nutriscore"
    if utilise_ns and not PARLE_DE_NUTRISCORE.search(question):
        return ("la question ne parle pas de Nutri-Score : ne filtre pas et ne compare pas selon le "
                "Nutri-Score, utilise decrire sur toutes les céréales")
    return None
