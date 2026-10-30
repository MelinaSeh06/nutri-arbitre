"""Brique 3 : on ESSAIE d'enfreindre la règle « aucun chiffre non calculé » et on vérifie
que le code bloque. Aucun appel au modèle : on simule ses réponses."""
from nutri.agent import executer_outil
from nutri.garde_fou import filtrer_reponse, verifier

RESULTAT = [{"nutriment": "sucres", "n": 42, "moyenne": 18.37}]


def test_chiffre_invente_bloque():
    reponse = "Les céréales bio contiennent en moyenne 12,5 g de sucre."
    ok, fautifs = verifier(reponse, RESULTAT)
    assert not ok and fautifs == ["12,5"]
    assert filtrer_reponse(reponse, RESULTAT).startswith("Réponse bloquée")


def test_reponse_sans_outil_bloquee():
    # le modèle répond de mémoire, sans avoir appelé d'outil
    assert not verifier("Environ 25 g de sucre pour 100 g.", [])[0]


def test_chiffre_calcule_autorise_avec_arrondi():
    reponse = "Sur 42 produits, la moyenne est de 18,4 g pour 100 g."
    assert filtrer_reponse(reponse, RESULTAT) == reponse


def test_arrondi_trop_large_bloque():
    assert not verifier("La moyenne est de 17 g.", RESULTAT)[0]   # 18,37 n'est pas « 17 »


def test_mauvais_arrondi_bloque():
    assert verifier("La moyenne est de 18 g.", RESULTAT)[0]       # 18,37 s'arrondit à 18
    assert not verifier("La moyenne est de 19 g.", RESULTAT)[0]   # mais pas à 19
    assert not verifier("La moyenne est de 18,5 g.", RESULTAT)[0] # ni à 18,5


def test_reponse_sans_chiffre_autorisee():
    assert verifier("Je ne peux pas répondre à cette question.", [])[0]


def test_chiffre_de_la_question_autorise():
    assert verifier("En 2024, je n'ai pas de données datées.", [], "Et en 2024 ?")[0]


def test_outil_inconnu_ne_plante_pas():
    assert "erreur" in executer_outil(None, "rm_rf", {})


def test_mauvais_argument_renvoye_au_modele(df):
    assert "erreur" in executer_outil(df, "decrire", {"nutriment": "vitamine_c"})


def test_ecart_negatif_ecrit_en_positif_autorise():
    resultat = [{"ecart_bio_moins_non_bio": -20.0}]
    assert verifier("Les bio ont 20 g de sucre en moins.", resultat)[0]
    assert not verifier("Les bio ont 20 g de moins sur 3 produits.", resultat)[0]  # le 3 est inventé
