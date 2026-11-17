# Notes

## Préférences de l'utilisateur

- Tout en français.
- Débutant complet, moins de 3 h par semaine : leçons de 15 à 20 minutes, une seule notion à la fois.
- Veut devenir autonome : jamais de solution directe. Échelle d'aide : question → indice → indice précis → solution seulement sur demande explicite après un essai.
- Veut des « Conseils Claude » dans chaque leçon (composant `<conseil-claude>`), utiles et jamais du remplissage.
- Vise l'école 42 : signaler les différences avec le C++98 quand une notion moderne n'existe pas en C++98.
- Veut retrouver vite une leçon : la page `recherche.html` doit rester à jour (lancer `outils/indexer.py`).

## Progression

| # | Leçon | Date | Exercices réussis | À revoir |
|---|-------|------|-------------------|----------|
| 0 | Test de l'installation | | 0000 | |

## Erreurs fréquentes à surveiller

(à remplir au fil des sessions)

## Notes de travail

- `libasan`/`libubsan` ne sont pas installés : `verifier.sh` compile sans les détecteurs d'erreurs mémoire. Proposer `sudo dnf install libasan libubsan` avant les leçons sur les pointeurs.
