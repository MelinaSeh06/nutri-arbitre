# Plan de la présentation (environ 6 min)

Idée directrice : « un modèle qui n'a pas le droit d'inventer un chiffre ».

1. **Le problème (30 s)** : un petit modèle comme Qwen invente des chiffres avec assurance.
   Démo en direct : `python -m nutri.agent --modele-seul "Quelle est la teneur moyenne en sucres des céréales bio, pour 100 g ?"`
   → il répond de mémoire, parfois avec une fausse marge (« 6,8 g ± 1,4 g » au lieu de 13,17 g).
   Qwen ne répond pas deux fois pareil : s'il refuse en direct, montrer la trace de l'évaluation.
2. **La solution (1 min)** : schéma du trajet
   question → Qwen choisit un outil → règle n° 2 (filtres) → Python calcule → règle n° 1 (chiffres) → réponse.
3. **La démo (2 min)** : système complet
   - `python -m nutri.agent "Les céréales bio contiennent-elles moins de sucre ?"`
     → les lignes `[outil] ...`, puis les vrais chiffres avec leur marge (brique 8) ;
   - `python -m nutri.agent "Les céréales bio contiennent-elles plus de lipides que les non bio ?"`
     → écart 0,21 g ± 0,84 g : « on ne peut pas conclure » ;
   - `python -m nutri.agent "Combien de calories apporte une portion de 30 g de céréales, en moyenne ?"`
     → Qwen calcule lui-même : **réponse bloquée** (brique 3).
4. **La preuve que les règles tiennent (1 min)** : `python -m pytest tests/test_garde_fou.py -v`
   → les tests qui essaient d'enfreindre les règles, dont 3 tirés de vraies réponses de Qwen.
5. **Les résultats chiffrés (1 min)** : `resultats/evaluation.md` (brique 9)
   - système complet 73 % ± 4 %, modèle seul 12 % ± 6 % ; 8 réponses bloquées, 17 chiffres inventés par le modèle seul ;
   - l'échec expliqué : la marque « la moins sucrée » lue dans un classement décroissant (Crownfield, 18,61 g),
     laissée passer par le garde-fou parce que le chiffre vient bien d'un outil.
6. **Les limites (30 s)** : le dire soi-même rassure l'examinateur.
   - Échantillon biaisé : les 1 000 premiers produits renvoyés par Open Food Facts, 57 % de bio ; pas de cause.
   - Le garde-fou vérifie l'origine des chiffres, pas le sens des phrases.
   - Ma mesure a des faux positifs (les lipides du modèle seul), gardés volontairement.

**Avant l'oral :** lancer `ollama serve` et une première question (le premier appel charge le modèle, ~20 s).

**Pas de frontend** : le terminal montre les appels d'outils en direct, et ça fait un fichier de
moins à expliquer.
