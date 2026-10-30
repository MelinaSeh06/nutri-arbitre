"""Brique 1 / R2 : les outils renvoient les chiffres calculés à la main."""
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


def test_bio_en_texte(df):
    # un petit modèle envoie parfois "false" au lieu de false : ne pas inverser le filtre
    assert tools.compter(df, bio="false")["n"] == 2
    assert tools.decrire(df, "sucres", bio="true")["moyenne"] == 15.0
    with pytest.raises(ValueError):
        tools.compter(df, bio="peut-être")
