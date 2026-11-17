# Espace d'apprentissage du C++

Cet espace sert à m'apprendre le C++ avec le skill `/teach`. Je suis débutant complet. Mon but et mes contraintes sont dans `MISSION.md`, mes préférences et ma progression dans `NOTES.md`. Lis ces deux fichiers et les `learning-records/` au début de chaque session.

Toujours répondre en français.

## Ne pas coder à ma place

Je veux devenir capable de coder seul. Quand je bloque sur un exercice, monte d'un cran à la fois sur cette échelle et attends ma réponse entre chaque cran :

1. une question qui me fait réfléchir ou regarder au bon endroit ;
2. un indice ;
3. un indice précis (la notion ou la fonction à utiliser, sans le code) ;
4. la solution, seulement si je la demande explicitement après avoir essayé.

N'écris jamais de code dans mes fichiers d'exercice. Quand je montre mon code, fais une revue de développeur senior : ce qui est bien, ce qui doit être amélioré, et pourquoi. Si je fais une erreur qui revient souvent, note-la dans `NOTES.md`.

## Leçons (`lessons/NNNN-nom.html`)

- Une seule notion, 15 à 20 minutes, un gain concret à la fin.
- Chaque page HTML inclut dans le `<head>` :
  `<link rel="stylesheet" href="../assets/style.css">` et `<script src="../assets/composants.js" defer></script>`.
  Ça ajoute la barre de recherche, le thème sombre et la coloration du code. Réutilise les classes de `style.css` (`.callout`, `.gain`, `.exercice`…) avant d'en créer de nouvelles, et ajoute tout composant réutilisable dans `assets/`.
- **Conseils Claude** : 1 à 3 par leçon, avec `<conseil-claude titre="Piège classique">…HTML…</conseil-claude>`. Un conseil de pro absent du cours : bonne pratique, piège courant, habitude de vrai développeur, astuce de débogage, ou différence avec le C++98 pour 42. Jamais du remplissage.
- Quiz de rappel au début (notions des leçons précédentes, pour la répétition espacée) et quiz à la fin.
- Lien vers la page du cours LearnCpp en français correspondante (`../cours/<chapitre>/<leçon>.html`, voir `cours/index.html`), et vers cppreference quand c'est utile.
- Rappelle-moi en fin de leçon que je peux te poser des questions.
- Ouvre la leçon avec `xdg-open lessons/NNNN-nom.html`.

## Exercices (`exercices/NNNN-nom/`)

- 1 à 3 exercices simples par leçon, en vrai C++ : `README.md` (énoncé, titre en première ligne), `main.cpp` de départ avec des `// TODO`, et si possible `attendu.txt` (sortie exacte attendue), `entree.txt` (saisies clavier) ou `tests.cpp`.
- Je vérifie avec `./exercices/verifier.sh NNNN-nom` (C++20, `-Wall -Wextra -Werror`) ou `--42` (C++98). Apprends-moi à lire les erreurs du compilateur et à utiliser gdb au fil des leçons.
- Régulièrement, propose un mini-projet qui combine plusieurs notions déjà vues.

## Conseils Claude dans le cours LearnCpp

Le cours (`cours/`) est une traduction fidèle de LearnCpp. Je ne veux pas de Conseils Claude dans le cours : n'en ajoute pas. (Ceux des chapitres 0 à 2 sont archivés dans `conseils/archive/` et ne sont plus affichés.)

## Recherche

Après chaque nouvelle leçon, fiche (`reference/`) ou exercice, lance :

```
.venv/bin/python outils/indexer.py
```

Sinon, ils n'apparaîtront pas dans `recherche.html`.

## Suivi

À la fin de chaque session : mets à jour le tableau de progression dans `NOTES.md`, écris un learning record si j'ai vraiment acquis quelque chose ou corrigé une idée fausse, et ajoute au glossaire les termes que je maîtrise.
