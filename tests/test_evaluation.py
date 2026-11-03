"""Brique 9 : on vérifie la façon de juger les réponses, sans appeler le modèle (fausses traces)."""
from nutri.evaluation import juger, nombre_juste, resumer


def _trace(reponse, bloquee=False):
    return {"reponse": reponse, "bloquee": bloquee}


def test_nombre_juste_a_2_pourcent_pres():
    assert nombre_juste("En moyenne 13,2 g de sucres.", 13.165)      # arrondi : juste
    assert nombre_juste("Environ 13 g.", 13.165)                      # 1,3 % d'écart : juste
    assert not nombre_juste("Environ 25 g.", 13.165)                  # réponse de mémoire : fausse
    assert nombre_juste("0,13 g de sel.", 0.1265)                     # écart permis d'au moins 0,01
    assert not nombre_juste("0,1 g de sel.", 0.1265)


def test_ecart_negatif_ecrit_sans_signe():
    assert nombre_juste("Les bio ont 5,42 g de sucres en moins.", -5.42)


def test_reponse_bloquee_ni_juste_ni_fausse():
    tache = {"type": "nombre", "attendu": 953}
    # le message de refus contient des nombres : il ne faut pas le juger « juste » par accident
    assert juger(tache, _trace("Réponse bloquée (953)", bloquee=True)) == "bloquee"


def test_texte_et_prudence():
    marque = {"type": "texte", "attendu": "jardin bio etic"}
    assert juger(marque, _trace("C'est Jardin Bio Etic, avec 6,5 g.")) == "juste"
    assert juger(marque, _trace("C'est Celnat.")) == "fausse"
    prudence = {"type": "prudence", "attendu": ["hasard", "pas conclure"]}
    assert juger(prudence, _trace("L'écart peut venir du hasard.")) == "juste"
    assert juger(prudence, _trace("Oui, les bio ont plus de lipides.")) == "fausse"


def test_resume_moyenne_et_dispersion():
    r = resumer([["juste", "juste"], ["juste", "fausse"], ["bloquee", "fausse"]])
    assert r["taux_juste_par_lancement"] == [1.0, 0.5, 0.0]
    assert r["taux_juste_moyen"] == 0.5
    assert r["ecart_type"] == 0.5
    assert (r["justes"], r["fausses"], r["bloquees"], r["total"]) == (3, 2, 1, 6)


def test_refus_juste_seulement_sans_chiffre_invente():
    tache = {"type": "refus", "attendu": None}
    question = "Quelle est la teneur moyenne en vitamine C des céréales, pour 100 g ?"
    assert juger(tache, {"reponse": "Les données ne contiennent pas la vitamine C.", "bloquee": False,
                         "question": question}) == "juste"
    assert juger(tache, {"reponse": "Environ 2 mg pour 100 g.", "bloquee": False,
                         "question": question}) == "fausse"      # 2 est inventé (100 vient de la question)
