"""Brique 6 / R2 : le nettoyage donne le résultat calculé à la main."""
import pandas as pd

from nutri.clean import nettoyer, normaliser_marque


def test_lignes_retirees(produits_bruts):
    df, journal = nettoyer(produits_bruts)
    # 7 produits : -1 doublon, -1 sans nom, -1 sans aucune valeur = 4
    assert len(df) == 4
    assert "Doublons de code-barres retirés : 1." in journal
    assert "Produits sans nom retirés : 1." in journal


def test_regle_inco_sel_depuis_sodium(df):
    # produit 2 : sodium 0,2 g -> sel 0,5 g
    assert df.loc[df["code"] == "2", "sel"].item() == 0.5


def test_regle_inco_energie_calculee(df):
    # produit 1 : 4*60 + 4*10 + 9*5 + 2*8 = 341 kcal
    assert df.loc[df["code"] == "1", "energie_kcal"].item() == 341


def test_fiche_incoherente_retiree():
    # vrai cas des données : « Muesli croustillant chocolat » déclare 437 kcal,
    # mais 4*33 + 4*4,7 + 9*6,6 + 2*3,9 = 218 kcal : écart de 100 %, on ne sait pas qui est faux
    from tests.conftest import produit
    nutr = {"carbohydrates_100g": 33, "proteins_100g": 4.7, "fat_100g": 6.6, "fiber_100g": 3.9}
    incoherent = produit("10", **nutr, **{"energy-kcal_100g": 437})
    coherent = produit("11", **nutr, **{"energy-kcal_100g": 230})        # écart de 5 % : gardé
    df, journal = nettoyer([incoherent, coherent])
    assert list(df["code"]) == ["11"]
    assert any("fiche incohérente), produits retirés : 1." in l for l in journal)


def test_valeurs_impossibles_mises_a_vide(df):
    p5 = df[df["code"] == "5"].iloc[0]
    assert pd.isna(p5["sucres"])       # sucres (90) > glucides (50)
    assert pd.isna(p5["sel"])          # 150 g de sel pour 100 g : impossible
    assert pd.isna(p5["nutriscore"])   # 'unknown' -> vide


def test_bio_et_marques(df):
    assert df["bio"].sum() == 2
    assert set(df["marque"]) == {"bio village", "kelloggs"}


def test_marque_cas_limites():
    assert normaliser_marque(None) is None
    assert normaliser_marque("   ") is None
    assert normaliser_marque("Nestlé, Nestle France") == "nestle"


def test_liste_vide():
    df, journal = nettoyer([])
    assert len(df) == 0
    assert journal[-1] == "Arrivée : 0 produits."
