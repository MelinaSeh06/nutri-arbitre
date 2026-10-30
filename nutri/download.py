"""Télécharge les céréales du petit-déjeuner vendues en France depuis Open Food Facts.

Usage : python -m nutri.download --pages 20

Open Food Facts demande un User-Agent qui identifie le projet
et au plus ~10 requêtes de recherche par minute : on attend donc 7 s entre deux pages.
"""
import argparse
import json
import time
from pathlib import Path

import requests

URL = "https://world.openfoodfacts.org/api/v2/search"
USER_AGENT = "nutri-arbitre/0.1 (projet etudiant Coding for AI)"
FIELDS = "code,product_name,brands,labels_tags,nutriscore_grade,nutriments"
SORTIE = Path("data/raw_cereales.json")


def telecharger_page(page: int, page_size: int = 100) -> list[dict]:
    """Renvoie la liste des produits d'une page de résultats."""
    params = {
        "categories_tags_en": "breakfast-cereals",
        "countries_tags_en": "france",
        "fields": FIELDS,
        "page": page,
        "page_size": page_size,
    }
    # le serveur renvoie parfois 503 (surcharge) : on réessaie en attendant de plus en plus
    for essai in range(5):
        try:
            r = requests.get(URL, params=params, headers={"User-Agent": USER_AGENT}, timeout=60)
            r.raise_for_status()
            return r.json().get("products", [])
        except requests.RequestException as e:
            attente = 15 * (essai + 1)
            print(f"page {page} : erreur ({e.__class__.__name__}), nouvel essai dans {attente} s")
            time.sleep(attente)
    raise RuntimeError(f"page {page} : échec après 5 essais")


def sauver(produits: list[dict]) -> None:
    SORTIE.parent.mkdir(exist_ok=True)
    SORTIE.write_text(json.dumps(produits, ensure_ascii=False), encoding="utf-8")


def main(nb_pages: int) -> None:
    produits = []
    for page in range(1, nb_pages + 1):
        lot = telecharger_page(page)
        print(f"page {page} : {len(lot)} produits")
        if not lot:  # plus aucun produit : on s'arrête
            break
        produits.extend(lot)
        sauver(produits)  # on écrit après chaque page : une panne ne fait pas tout perdre
        time.sleep(7)     # respecter la limite de l'API
    print(f"{len(produits)} produits écrits dans {SORTIE}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=int, default=20)
    main(parser.parse_args().pages)
