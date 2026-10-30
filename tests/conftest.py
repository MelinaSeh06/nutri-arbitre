"""Petits produits inventés dont on connaît la réponse à la main."""
import pytest

from nutri.clean import nettoyer


def produit(code, nom="Céréales", marque="Marque", labels=(), ns="a", **nutr):
    return {"code": code, "product_name": nom, "brands": marque, "labels_tags": list(labels),
            "nutriscore_grade": ns, "nutriments": nutr}


@pytest.fixture
def produits_bruts():
    return [
        produit("1", marque="Bio Village", labels=["en:organic"], ns="a",
                **{"sugars_100g": 10, "carbohydrates_100g": 60, "fat_100g": 5,
                   "proteins_100g": 10, "fiber_100g": 8, "salt_100g": 0.5}),
        produit("2", marque="BIO VILLAGE", labels=["fr:ab-agriculture-biologique"], ns="b",
                **{"sugars_100g": 20, "carbohydrates_100g": 70, "fat_100g": 5,
                   "proteins_100g": 10, "sodium_100g": 0.2}),
        produit("3", marque="Kellogg's", ns="d",
                **{"sugars_100g": 30, "carbohydrates_100g": 80, "fat_100g": 2,
                   "proteins_100g": 6, "salt_100g": 1.0}),
        produit("3", marque="Kellogg's", ns="d", **{"sugars_100g": 30}),          # doublon
        produit("4", nom="", **{"sugars_100g": 5}),                              # sans nom
        produit("5", marque="KELLOGG’S", ns="unknown",
                **{"sugars_100g": 90, "carbohydrates_100g": 50, "fat_100g": 3,   # sucres > glucides
                   "proteins_100g": 7, "salt_100g": 150}),                       # sel impossible
        produit("6", marque="Vide"),                                             # aucune valeur
    ]


@pytest.fixture
def df(produits_bruts):
    return nettoyer(produits_bruts)[0]
