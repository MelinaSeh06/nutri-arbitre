"""Nettoie les données brutes d'Open Food Facts et écrit un journal de chaque décision.

Usage : python -m nutri.clean

Règles venues d'un document, absentes du fichier (brique 6) :
  Règlement (UE) n° 1169/2011 « INCO », annexe XIV :
  - sel = sodium x 2,5
  - énergie (kcal) = 4 x glucides + 4 x protéines + 9 x lipides + 2 x fibres
"""
from __future__ import annotations   # « str | None » accepté aussi en Python 3.9

import json
import unicodedata
from pathlib import Path

import pandas as pd

ENTREE = Path("data/raw_cereales.json")
SORTIE = Path("data/cereales_propres.csv")
JOURNAL = Path("data/journal_nettoyage.md")

# nom dans Open Food Facts -> nom de notre colonne
NUTRIMENTS = {
    "energy-kcal_100g": "energie_kcal",
    "carbohydrates_100g": "glucides",
    "sugars_100g": "sucres",
    "fat_100g": "lipides",
    "saturated-fat_100g": "ags",
    "fiber_100g": "fibres",
    "proteins_100g": "proteines",
    "salt_100g": "sel",
    "sodium_100g": "sodium",
}
EN_GRAMMES = ["glucides", "sucres", "lipides", "ags", "fibres", "proteines", "sel", "sodium"]
LABELS_BIO = {"en:organic", "en:eu-organic", "fr:ab-agriculture-biologique"}


def normaliser_marque(brut) -> str | None:
    """'KELLOGG'S, Kellogg' -> 'kelloggs' : 1re marque, minuscules, sans accents ni ponctuation."""
    if not isinstance(brut, str) or not brut.strip():
        return None
    premiere = brut.split(",")[0]                       # "KELLOGG'S, Kellogg" -> "KELLOGG'S"
    # enlever les accents : "é" est décomposé en "e" + accent, puis l'accent est jeté
    sans_accents = unicodedata.normalize("NFKD", premiere).encode("ascii", "ignore").decode()
    # garder seulement les lettres, les chiffres et les espaces : "kellogg's" -> "kelloggs"
    propre = ""
    for c in sans_accents.lower():
        if c.isalnum() or c == " ":
            propre += c
    propre = " ".join(propre.split())                   # espaces multiples -> un seul
    if propre == "":
        return None
    return propre


def est_bio(tags: list) -> bool:
    """Vrai si au moins un des labels du produit est un label bio."""
    for tag in tags:
        if tag in LABELS_BIO:
            return True
    return False


def aplatir(produits: list[dict]) -> pd.DataFrame:
    """Transforme la liste JSON en tableau, une ligne par produit."""
    lignes = []
    for p in produits:
        nutr = p.get("nutriments") or {}
        ligne = {
            "code": p.get("code"),
            "nom": p.get("product_name"),
            "marque_brute": p.get("brands"),
            "labels": p.get("labels_tags") or [],
            "nutriscore_brut": p.get("nutriscore_grade"),
        }
        for cle_off, col in NUTRIMENTS.items():
            ligne[col] = nutr.get(cle_off)
        lignes.append(ligne)
    return pd.DataFrame(lignes, columns=["code", "nom", "marque_brute", "labels", "nutriscore_brut",
                                         *NUTRIMENTS.values()])


def nettoyer(produits: list[dict]) -> tuple[pd.DataFrame, list[str]]:
    """Renvoie (tableau propre, journal). Chaque ligne du journal décrit une décision."""
    journal = []
    df = aplatir(produits)
    journal.append(f"Départ : {len(df)} produits.")

    # 1. doublons de code-barres
    avant = len(df)
    df = df.drop_duplicates(subset="code")
    journal.append(f"Doublons de code-barres retirés : {avant - len(df)}.")

    # 2. produits sans nom
    avant = len(df)
    df = df[df["nom"].fillna("").str.strip() != ""]
    journal.append(f"Produits sans nom retirés : {avant - len(df)}.")

    # 3. conversion en nombres (certaines valeurs arrivent en texte)
    for col in NUTRIMENTS.values():
        texte_avant = df[col].notna().sum()
        df[col] = pd.to_numeric(df[col], errors="coerce")
        perdus = texte_avant - df[col].notna().sum()
        if perdus:
            journal.append(f"{col} : {perdus} valeurs non numériques mises à vide.")

    # 4. bornes physiques : pour 100 g, une masse est entre 0 et 100 g
    for col in EN_GRAMMES:
        hors = (df[col] < 0) | (df[col] > 100)
        if hors.sum():
            journal.append(f"{col} : {hors.sum()} valeurs hors de [0, 100] g mises à vide.")
        df.loc[hors, col] = None
    # 900 kcal/100 g = de la graisse pure : impossible de dépasser
    hors = (df["energie_kcal"] < 0) | (df["energie_kcal"] > 900)
    journal.append(f"energie_kcal : {hors.sum()} valeurs hors de [0, 900] kcal mises à vide.")
    df.loc[hors, "energie_kcal"] = None

    # 5. cohérence : une partie ne peut pas dépasser le tout
    incoh = df["sucres"] > df["glucides"]
    journal.append(f"Sucres > glucides : {incoh.sum()} valeurs de sucres mises à vide.")
    df.loc[incoh, "sucres"] = None
    incoh = df["ags"] > df["lipides"]
    journal.append(f"Acides gras saturés > lipides : {incoh.sum()} valeurs mises à vide.")
    df.loc[incoh, "ags"] = None

    # 6. RÈGLE INCO : sel = sodium x 2,5
    a_completer = df["sel"].isna() & df["sodium"].notna()
    df.loc[a_completer, "sel"] = df.loc[a_completer, "sodium"] * 2.5
    journal.append(f"Sel calculé depuis le sodium (sel = sodium x 2,5, règlement INCO) : "
                   f"{a_completer.sum()} produits.")

    # 7. RÈGLE INCO : énergie recalculée à partir des macronutriments
    # calcul fait pour toutes les lignes d'un coup (fibres absentes comptées 0)
    calcul = (4 * df["glucides"] + 4 * df["proteines"] + 9 * df["lipides"]
              + 2 * df["fibres"].fillna(0))
    macros_connues = df["glucides"].notna() & df["proteines"].notna() & df["lipides"].notna()
    a_completer = df["energie_kcal"].isna() & macros_connues
    df.loc[a_completer, "energie_kcal"] = calcul[a_completer].round(0)
    journal.append(f"Énergie calculée depuis les macronutriments (règlement INCO) : "
                   f"{a_completer.sum()} produits.")
    ecart = (df["energie_kcal"] - calcul).abs() / calcul.where(calcul > 0)   # pas de division par 0
    df["energie_suspecte"] = (ecart > 0.20).fillna(False)
    journal.append(f"Énergie déclarée à plus de 20 % du calcul INCO, marquée suspecte "
                   f"(gardée) : {int(df['energie_suspecte'].sum())} produits.")

    # 8. Nutri-Score : on ne garde que a à e
    df["nutriscore"] = df["nutriscore_brut"].astype("string").str.lower().str.strip()
    invalides = df["nutriscore"].notna() & ~df["nutriscore"].isin(list("abcde"))
    journal.append(f"Nutri-Score non valide (unknown, not-applicable…) mis à vide : {invalides.sum()}.")
    df.loc[invalides, "nutriscore"] = None

    # 9. marques et label bio
    df["marque"] = df["marque_brute"].map(normaliser_marque)
    journal.append(f"Marques normalisées : {df['marque_brute'].nunique()} libellés bruts "
                   f"-> {df['marque'].nunique()} marques.")
    df["bio"] = df["labels"].map(est_bio)   # applique est_bio à la liste de labels de chaque produit
    journal.append(f"Produits bio (label AB ou bio UE) : {int(df['bio'].sum())}.")

    # 10. produits sans aucune valeur nutritionnelle
    colonnes_nutr = ["energie_kcal", "glucides", "sucres", "lipides", "ags", "fibres", "proteines", "sel"]
    avant = len(df)
    df = df.dropna(subset=colonnes_nutr, how="all")
    journal.append(f"Produits sans aucune valeur nutritionnelle retirés : {avant - len(df)}.")

    journal.append(f"Arrivée : {len(df)} produits.")
    df = df[["code", "nom", "marque", "bio", "nutriscore", *colonnes_nutr, "energie_suspecte"]]
    return df.reset_index(drop=True), journal


def main() -> None:
    produits = json.loads(ENTREE.read_text(encoding="utf-8"))
    df, journal = nettoyer(produits)
    df.to_csv(SORTIE, index=False)
    JOURNAL.write_text("# Journal de nettoyage\n\n" + "\n".join(f"- {l}" for l in journal) + "\n",
                       encoding="utf-8")
    print("\n".join(journal))
    print(f"-> {SORTIE} et {JOURNAL}")


if __name__ == "__main__":
    main()
