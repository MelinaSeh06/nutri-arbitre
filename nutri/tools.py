"""Les outils que le modèle peut appeler. Ce sont eux, et eux seuls, qui calculent les chiffres.

Chaque fonction prend le tableau propre en premier argument (pratique pour les tests),
vérifie ses paramètres, et renvoie un dictionnaire de résultats arrondis à 2 décimales.
"""
import pandas as pd

NUTRIMENTS = ["energie_kcal", "glucides", "sucres", "lipides", "ags", "fibres", "proteines", "sel"]
GROUPES = ["bio", "nutriscore"]


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
    return None if pd.isna(x) else round(float(x), 2)


def decrire(df, nutriment, bio=None, nutriscore=None) -> dict:
    """Moyenne, médiane, min et max d'un nutriment (pour 100 g), avec filtres facultatifs."""
    _verifier_nutriment(nutriment)
    valeurs = _filtrer(df, bio, nutriscore)[nutriment].dropna()
    return {
        "nutriment": nutriment,
        "filtres": {"bio": bio, "nutriscore": nutriscore},
        "n": int(len(valeurs)),
        "moyenne": _arrondi(valeurs.mean()),   # None si aucune valeur (cas limite : liste vide)
        "mediane": _arrondi(valeurs.median()),
        "min": _arrondi(valeurs.min()),
        "max": _arrondi(valeurs.max()),
    }


def comparer(df, nutriment, groupe) -> dict:
    """Moyenne d'un nutriment dans chaque groupe (bio / non bio, ou chaque Nutri-Score)."""
    _verifier_nutriment(nutriment)
    if groupe not in GROUPES:
        raise ValueError(f"groupe inconnu : {groupe!r}. Choix possibles : {GROUPES}")
    resultats = []
    for valeur, sous_df in df.dropna(subset=[groupe, nutriment]).groupby(groupe):
        resultats.append({"groupe": str(valeur), "n": int(len(sous_df)),
                          "moyenne": _arrondi(sous_df[nutriment].mean())})
    sortie = {"nutriment": nutriment, "groupe": groupe, "groupes": resultats}
    if groupe == "bio":
        # on retrouve la moyenne des bio ("True") et des non bio ("False")
        moy_bio, moy_non_bio = None, None
        for r in resultats:
            if r["groupe"] == "True":
                moy_bio = r["moyenne"]
            if r["groupe"] == "False":
                moy_non_bio = r["moyenne"]
        if moy_bio is not None and moy_non_bio is not None:
            sortie["ecart_bio_moins_non_bio"] = _arrondi(moy_bio - moy_non_bio)
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
    _schema("decrire", "Moyenne, médiane, min, max d'un nutriment des céréales du petit-déjeuner.",
            {"nutriment": _P_NUTRIMENT, "bio": _P_BIO, "nutriscore": _P_NS}, ["nutriment"]),
    _schema("comparer", "Moyenne d'un nutriment par groupe (bio ou nutriscore).",
            {"nutriment": _P_NUTRIMENT, "groupe": {"type": "string", "enum": GROUPES}},
            ["nutriment", "groupe"]),
    _schema("classement_marques", "Classement des marques selon la moyenne d'un nutriment.",
            {"nutriment": _P_NUTRIMENT, "n": {"type": "integer"},
             "ordre": {"type": "string", "enum": ["croissant", "decroissant"]},
             "min_produits": {"type": "integer"}}, ["nutriment"]),
    _schema("compter", "Nombre de produits, avec filtres facultatifs.",
            {"bio": _P_BIO, "nutriscore": _P_NS}, []),
]
