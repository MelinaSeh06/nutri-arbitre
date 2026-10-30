# Plan de la présentation (environ 6 min)

Idée directrice : « un modèle qui n'a pas le droit d'inventer un chiffre ».

1. **Le problème (30 s)** : un petit modèle comme Qwen invente des chiffres avec assurance.
   Démo en direct : `python -m nutri.agent --modele-seul "Les céréales bio contiennent-elles moins de sucre ?"`
   → il répond de mémoire (« environ 25 g… »).
2. **La solution (1 min)** : schéma du trajet
   question → Qwen choisit un outil → Python calcule → garde-fou → réponse.
3. **La démo (2 min)** : même question avec le système complet
   `python -m nutri.agent "Les céréales bio contiennent-elles moins de sucre ?"`
   → on voit les lignes `[outil] ...` puis une réponse avec les vrais chiffres.
4. **La preuve que la règle tient (1 min)** : `python -m pytest tests/test_garde_fou.py -v`
   → les tests qui essaient d'enfreindre la règle et se font bloquer.
5. **Les résultats chiffrés (1 min)** : tableau de la brique 9, système complet contre modèle seul
   (bonnes réponses, chiffres inventés, réponses bloquées).
6. **Les limites (30 s)** : le dire soi-même rassure l'examinateur.
   - Échantillon biaisé : les 1 000 premiers produits renvoyés par Open Food Facts, 57 % de bio.
   - Le garde-fou vérifie les chiffres, pas le sens (Qwen a déjà répondu « Non » en citant des
     chiffres qui disaient « Oui »).

**Pas de frontend** : le terminal montre les appels d'outils en direct, et ça fait un fichier de
moins à expliquer. Une mini-interface Streamlit seulement en bonus, à la toute fin, s'il reste du temps.
