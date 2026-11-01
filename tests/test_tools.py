"""Brique 1 / R2 : les outils renvoient les chiffres calculés à la main."""
import pandas as pd
import pytest

from nutri import tools


def test_decrire_sucres_bio(df):
    r = tools.decrire(df, "sucres", bio=True)
    assert r["n"] == 2 and r["moyenne"] == 15.0      # (10 + 20) / 2
    assert r["min"] == 10.0 and r["max"] == 20.0


def test_decrire_selection_vide(df):
    r = tools.decrire(df, "sucres", nutriscore="e")    # aucun produit en E
    assert r["n"] == 0 and r["moyenne"] is None


def test_comparer_bio(df):
    r = tools.comparer(df, "sucres", "bio")
    # bio : 15 ; non bio : seul le produit 3 a une valeur de sucres (30)
    assert r["ecart_bio_moins_non_bio"] == -15.0


def test_classement_ignore_petites_marques(df):
    r = tools.classement_marques(df, "sucres", min_produits=2)
    assert [m["marque"] for m in r["marques"]] == ["bio village"]


def test_nutriment_inconnu_refuse(df):
    with pytest.raises(ValueError):
        tools.decrire(df, "vitamine_c")


def test_compter(df):
    assert tools.compter(df)["n"] == 4
    assert tools.compter(df, bio=False)["n"] == 2


def _tableau(bio, non_bio):
    """Petit tableau inventé : des valeurs de sucres pour des produits bio et non bio."""
    lignes = [{"bio": True, "sucres": s} for s in bio] + [{"bio": False, "sucres": s} for s in non_bio]
    return pd.DataFrame(lignes)


def test_marge_erreur_a_la_main(df):
    # bio : 10 et 20 -> écart-type 7,07 ; erreur type 7,07 / racine(2) = 5 ; marge 1,96 x 5 = 9,8
    r = tools.decrire(df, "sucres", bio=True)
    assert r["marge_95"] == 9.8
    assert r["intervalle_95"] == [5.2, 24.8]              # 15 - 9,8 et 15 + 9,8


def test_marge_impossible_avec_une_seule_valeur(df):
    # non bio : un seul produit a une valeur de sucres -> pas de dispersion, pas de marge
    r = tools.decrire(df, "sucres", bio=False)
    assert r["n"] == 1 and r["marge_95"] is None and r["intervalle_95"] is None
    assert tools.comparer(df, "sucres", "bio")["difference_nette"] is None


def test_difference_nette():
    # bio 10 et 12 (moy. 11), non bio 30 et 32 (moy. 31) : erreur type 1 dans chaque groupe
    # écart -20 ; erreur type de l'écart racine(1 + 1) = 1,41 ; marge 1,96 x 1,41 = 2,77
    r = tools.comparer(_tableau([10, 12], [30, 32]), "sucres", "bio")
    assert r["ecart_bio_moins_non_bio"] == -20.0 and r["marge_95_ecart"] == 2.77
    assert r["difference_nette"] is True                  # [-22,77 ; -17,23] ne contient pas 0


def test_difference_pas_nette():
    # bio 10 et 30 (moy. 20), non bio 14 et 30 (moy. 22) : écart -2, mais marge de 25 environ
    r = tools.comparer(_tableau([10, 30], [14, 30]), "sucres", "bio")
    assert r["ecart_bio_moins_non_bio"] == -2.0
    assert r["difference_nette"] is False                 # 0 est dans l'intervalle : hasard possible


def test_sans_nutriscore_compte(df):
    # produit 5 : Nutri-Score « unknown » -> vide, mais il a des lipides : il est écarté et compté
    r = tools.comparer(df, "lipides", "nutriscore")
    assert r["sans_nutriscore"] == 1
    assert sum(g["n"] for g in r["groupes"]) == 3         # 4 produits - 1 sans Nutri-Score


def test_bio_en_texte(df):
    # un petit modèle envoie parfois "false" au lieu de false : ne pas inverser le filtre
    assert tools.compter(df, bio="false")["n"] == 2
    assert tools.decrire(df, "sucres", bio="true")["moyenne"] == 15.0
    with pytest.raises(ValueError):
        tools.compter(df, bio="peut-être")
