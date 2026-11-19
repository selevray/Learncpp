# cppreference en français

Traduction automatique (Claude Haiku 5.5) de [cppreference.com](https://en.cppreference.com/), sous licence CC-BY-SA 3.0, à partir de l'archive hors ligne officielle (version du 9 février 2025).

**Licence** : comme l'original, cette traduction est publiée sous licence [CC-BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/deed.fr). Chaque page indique sa source sur cppreference.com.

- Accueil : [`cpp.html`](cpp.html) (C++) et [`c.html`](c.html) (C)
- Recherche : `recherche.html`, filtre « Référence cppreference »

## Ce qui est publié et ce qui ne l'est pas

Publié (dans git) : les pages HTML (`cpp/`, `c/`, `cpp.html`, `c.html`), les outils et ce README.

Ignoré (voir `../.gitignore`) : la clé API `.cle_api`, l'archive `source/`, le Markdown intermédiaire `md/`, le cache `traductions.sqlite`, les journaux et l'environnement Python `.venv/`.

## Chaîne de fabrication

Toutes les commandes se lancent depuis `~/apprendre-cpp/cppreference`.

1. **Traduire** (seuls les segments absents du cache sont envoyés à l'API) :
   ```
   .venv/bin/python outils/traduire.py --tout                 # C++ et C
   .venv/bin/python outils/traduire.py --pages cpp.html c.html  # pages d'accueil
   ```
   `--construire` régénère le Markdown depuis le cache, sans appel à l'API.
2. **Contrôler** les traductions suspectes : `.venv/bin/python outils/verifier.py --tout`
3. **Générer les pages HTML** : `.venv/bin/python outils/en_html.py`
4. **Mettre à jour la recherche** (depuis `~/apprendre-cpp`) : `.venv/bin/python outils/indexer.py`

## Fichiers

| Fichier | Rôle |
| --- | --- |
| `outils/segments.py` | découpe une page en segments de texte ; le code n'est jamais envoyé (balises `<xN/>`), seuls les commentaires de code sont traduits |
| `outils/traduire.py` | appels à l'API, règles et glossaire, vérifications, cache |
| `outils/en_markdown.py` | page traduite → Markdown (déclarations, paramètres, listes de membres, notes de version) |
| `outils/en_html.py` | Markdown → HTML avec le gabarit du cours (style, recherche, thème, fil d'Ariane) |
| `outils/verifier.py` | repère les segments restés en anglais, hors glossaire, etc. |
| `outils/mesurer.py` | mesure le volume et vérifie l'aller-retour découpage/réinsertion |

## Corriger une traduction

Les traductions sont dans `traductions.sqlite` (table `seg`, colonnes `en` et `fr`). Corriger une ligne, puis relancer `traduire.py --tout --construire`, `en_html.py` et `indexer.py`. La correction s'applique à toutes les pages qui contiennent ce segment.
