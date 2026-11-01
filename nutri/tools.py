"""Les outils que le modèle peut appeler. Ce sont eux, et eux seuls, qui calculent les chiffres.

Chaque fonction prend le tableau propre en premier argument (pratique pour les tests),
vérifie ses paramètres, et renvoie un dictionnaire de résultats arrondis à 2 décimales.

Brique 8 : chaque moyenne est donnée avec sa marge d'erreur à 95 %, et la comparaison bio /
non bio dit si l'écart est net ou s'il peut venir du hasard de l'échantillon.
"""
import math

import pandas as pd

NUTRIMENTS = ["energie_kcal", "glucides", "sucres", "lipides", "ags", "fibres", "proteines", "sel"]
GROUPES = ["bio", "nutriscore"]
Z_95 = 1.96   # pour une marge à 95 % (loi normale : 95 % des cas à moins de 1,96 erreur type)


def _verifier_nutriment(nutriment: str) -> None:
    if nutriment not in NUTRIMENTS:
        raise ValueError(f"nutriment inconnu : {nutriment!r}. Choix possibles : {NUTRIMENTS}")


def _booleen(x) -> bool:
    """Le modèle envoie parfois "false" en texte : bool("false") vaudrait True."""
    if isinstance(x, str):
        if x.strip().lower() in ("true", "vrai", "1", "oui"):
            return True
        if x.strip().lower() in ("false", "faux", "0", "non"):
            return False
        raise ValueError(f"bio doit être true ou false, pas {x!r}")
    return bool(x)


def _filtrer(df: pd.DataFrame, bio=None, nutriscore=None) -> pd.DataFrame:
    if bio is not None:
        df = df[df["bio"] == _booleen(bio)]
    if nutriscore is not None:
        df = df[df["nutriscore"] == str(nutriscore).lower()]
    return df


def _arrondi(x):
    return None if x is None or pd.isna(x) else round(float(x), 2)


def _erreur_type(valeurs):
    """Précision d'une moyenne : écart-type / racine de n.
    Plus il y a de produits, plus elle est petite. None s'il y a moins de 2 valeurs
    (avec une seule valeur, on ne peut pas mesurer la dispersion)."""
    if len(valeurs) < 2:
        return None
    return valeurs.std() / math.sqrt(len(valeurs))


def _intervalle(centre, erreur_type):
    """Intervalle de confiance à 95 % : centre ± 1,96 erreur type. None si on ne peut pas le calculer."""
    if centre is None or erreur_type is None:
        return None, None
    marge = Z_95 * erreur_type
    return marge, [centre - marge, centre + marge]


def decrire(df, nutriment, bio=None, nutriscore=None) -> dict:
    """Moyenne (avec sa marge d'erreur), médiane, min et max d'un nutriment (pour 100 g)."""
    _verifier_nutriment(nutriment)
    valeurs = _filtrer(df, bio, nutriscore)[nutriment].dropna()
    moyenne = valeurs.mean() if len(valeurs) > 0 else None   # cas limite : aucune valeur
    marge, intervalle = _intervalle(moyenne, _erreur_type(valeurs))
    return {
        "nutriment": nutriment,
        "filtres": {"bio": bio, "nutriscore": nutriscore},
        "n": int(len(valeurs)),
        "moyenne": _arrondi(moyenne),
        "marge_95": _arrondi(marge),
        "intervalle_95": None if intervalle is None else [_arrondi(b) for b in intervalle],
        "mediane": _arrondi(valeurs.median()),
        "min": _arrondi(valeurs.min()),
        "max": _arrondi(valeurs.max()),
    }


def comparer(df, nutriment, groupe) -> dict:
    """Moyenne d'un nutriment dans chaque groupe (bio / non bio, ou chaque Nutri-Score),
    avec la marge d'erreur de chaque moyenne."""
    _verifier_nutriment(nutriment)
    if groupe not in GROUPES:
        raise ValueError(f"groupe inconnu : {groupe!r}. Choix possibles : {GROUPES}")
    connus = df.dropna(subset=[nutriment])
    resultats = []
    erreurs_types = {}          # groupe -> erreur type, pour calculer la marge de l'écart plus bas
    for valeur, sous_df in connus.dropna(subset=[groupe]).groupby(groupe):
        moyenne = sous_df[nutriment].mean()
        et = _erreur_type(sous_df[nutriment])
        marge, _ = _intervalle(moyenne, et)
        resultats.append({"groupe": str(valeur), "n": int(len(sous_df)),
                          "moyenne": _arrondi(moyenne), "marge_95": _arrondi(marge)})
        erreurs_types[str(valeur)] = et
    sortie = {"nutriment": nutriment, "groupe": groupe, "groupes": resultats}

    if groupe == "nutriscore":
        # produits sans Nutri-Score (données incomplètes ou non concernés) : écartés de ce calcul
        sortie["sans_nutriscore"] = int(connus["nutriscore"].isna().sum())

    if groupe == "bio":
        # on retrouve la moyenne des bio ("True") et des non bio ("False")
        moy_bio, moy_non_bio = None, None
        for r in resultats:
            if r["groupe"] == "True":
                moy_bio = r["moyenne"]
            if r["groupe"] == "False":
                moy_non_bio = r["moyenne"]
        if moy_bio is not None and moy_non_bio is not None:
            ecart = moy_bio - moy_non_bio
            sortie["ecart_bio_moins_non_bio"] = _arrondi(ecart)
            # erreur type d'un écart entre deux groupes indépendants : racine(et1² + et2²)
            et_bio, et_non_bio = erreurs_types.get("True"), erreurs_types.get("False")
            if et_bio is not None and et_non_bio is not None:
                marge, intervalle = _intervalle(ecart, math.sqrt(et_bio ** 2 + et_non_bio ** 2))
                sortie["marge_95_ecart"] = _arrondi(marge)
                sortie["intervalle_95_ecart"] = [_arrondi(b) for b in intervalle]
                # si 0 est dans l'intervalle, l'écart peut venir du hasard : pas de conclusion
                sortie["difference_nette"] = not (intervalle[0] <= 0 <= intervalle[1])
            else:
                sortie["difference_nette"] = None   # trop peu de produits pour conclure
    return sortie


def classement_marques(df, nutriment, n=5, ordre="croissant", min_produits=5) -> dict:
    """Les n marques avec la moyenne la plus basse (ou haute) d'un nutriment.
    On ignore les marques avec moins de min_produits produits (une moyenne sur 1 produit ne dit rien)."""
    _verifier_nutriment(nutriment)
    if ordre not in ("croissant", "decroissant"):
        raise ValueError("ordre doit être 'croissant' ou 'decroissant'")
    # 1. garder les produits qui ont une marque ET une valeur pour ce nutriment
    connus = df.dropna(subset=["marque", nutriment])
    # 2. par marque : nombre de produits (count) et moyenne (mean)
    stats = connus.groupby("marque")[nutriment].agg(["count", "mean"])
    # 3. écarter les petites marques
    stats = stats[stats["count"] >= int(min_produits)]
    # 4. trier et garder les n premières
    stats = stats.sort_values("mean", ascending=(ordre == "croissant")).head(int(n))

    marques = []
    for nom_marque, ligne in stats.iterrows():
        marques.append({"marque": nom_marque, "n_produits": int(ligne["count"]),
                        "moyenne": _arrondi(ligne["mean"])})
    return {"nutriment": nutriment, "ordre": ordre, "min_produits": int(min_produits),
            "marques": marques}


def compter(df, bio=None, nutriscore=None) -> dict:
    """Nombre de produits, avec filtres facultatifs."""
    return {"filtres": {"bio": bio, "nutriscore": nutriscore}, "n": int(len(_filtrer(df, bio, nutriscore)))}


FONCTIONS = {"decrire": decrire, "comparer": comparer,
             "classement_marques": classement_marques, "compter": compter}

# Description des outils au format attendu par Ollama (JSON Schema)
_P_NUTRIMENT = {"type": "string", "enum": NUTRIMENTS, "description": "nutriment, pour 100 g"}
_P_BIO = {"type": "boolean", "description": "true = seulement bio, false = seulement non bio"}
_P_NS = {"type": "string", "enum": list("abcde"), "description": "lettre du Nutri-Score"}


def _schema(nom, description, proprietes, requis):
    return {"type": "function", "function": {
        "name": nom, "description": description,
        "parameters": {"type": "object", "properties": proprietes, "required": requis}}}


SCHEMAS = [
    _schema("decrire", "Moyenne (avec marge d'erreur à 95 %), médiane, min, max d'un nutriment "
            "des céréales du petit-déjeuner.",
            {"nutriment": _P_NUTRIMENT, "bio": _P_BIO, "nutriscore": _P_NS}, ["nutriment"]),
    _schema("comparer", "Moyenne d'un nutriment par groupe (bio ou nutriscore), avec marges d'erreur. "
            "Pour bio : écart bio - non bio et difference_nette (true = écart net, false = peut venir du hasard).",
            {"nutriment": _P_NUTRIMENT, "groupe": {"type": "string", "enum": GROUPES}},
            ["nutriment", "groupe"]),
    _schema("classement_marques", "Classement des marques selon la moyenne d'un nutriment.",
            {"nutriment": _P_NUTRIMENT, "n": {"type": "integer"},
             "ordre": {"type": "string", "enum": ["croissant", "decroissant"]},
             "min_produits": {"type": "integer"}}, ["nutriment"]),
    _schema("compter", "Nombre de produits, avec filtres facultatifs.",
            {"bio": _P_BIO, "nutriscore": _P_NS}, []),
]
