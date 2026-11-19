"""Transforme les pages Markdown (./md) en pages HTML pour l'espace d'apprentissage.

    .venv/bin/python outils/en_html.py

Même gabarit que le cours LearnCpp (assets/style.css + assets/composants.js :
barre de recherche, thème sombre, coloration du code). Les pages sont écrites
dans ~/apprendre-cpp/cppreference/{cpp,c}/… et cpp.html / c.html (accueil).

Rendu avec markdown-it (CommonMark) : contrairement à Python-Markdown, il gère
les blocs de code à l'intérieur des citations (notes propres à une version).
"""
from __future__ import annotations

import html
import re
import sys
from multiprocessing import Pool
from pathlib import Path

from markdown_it import MarkdownIt

RACINE_CPPREF = Path(__file__).resolve().parent.parent      # ~/apprendre-cpp/cppreference
SITE = RACINE_CPPREF.parent                                   # ~/apprendre-cpp
MD = RACINE_CPPREF / "md"
SORTIE = RACINE_CPPREF

ACCUEILS = {"cpp": "Référence C++", "c": "Référence C"}

PAGE = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titre_onglet}</title>
<link rel="stylesheet" href="{rel}assets/style.css">
<script src="{rel}assets/composants.js" defer></script>
</head>
<body class="cppref">
<main>
{ariane}{corps}
</main>
</body>
</html>
"""

md = MarkdownIt("commonmark", {"html": True, "typographer": False}).enable("table")
ANCRE = re.compile(r"\s*\{#([^}\s]+)\}\s*$")
FENCE = re.compile(r"^\s*(>\s*)*(```|~~~)")


def _titre(texte_md: str) -> str:
    premiere = texte_md.split("\n", 1)[0]
    return premiere.lstrip("#").strip()


def _sans_code(t: str) -> str:
    return t.replace("`", "")


def _preparer_md(texte: str) -> tuple[str, str]:
    """Retourne (note de source en HTML, Markdown du corps prêt à rendre)."""
    lignes = texte.split("\n")
    note = ""
    # 1re ligne = titre h1 (gardé), puis la note de source en citation
    corps = [lignes[0]]
    i = 1
    while i < len(lignes) and not lignes[i].strip():
        i += 1
    if i < len(lignes) and lignes[i].startswith("> ") and "cppreference.com" in lignes[i]:
        note = md.renderInline(lignes[i][2:])
        i += 1
    dans_code = False
    for ligne in lignes[i:]:
        if FENCE.match(ligne):
            dans_code = not dans_code
        elif not dans_code:
            # sections cppreference en h3 -> h2 (comme LearnCpp, et pour la recherche)
            m = re.match(r"^(#{3,6}) ", ligne)
            if m:
                ligne = ligne[1:]
            # liens .md -> .html
            ligne = re.sub(r"\]\(([^)\s]+?)\.md(#[^)\s]*)?\)",
                           lambda m: f"]({m.group(1)}.html{m.group(2) or ''})", ligne)
        corps.append(ligne)
    return note, "\n".join(corps)


def _ancres(rendu: str) -> str:
    """« <h2>Paramètres {#Parameters}</h2> » -> « <h2 id="Parameters">Paramètres</h2> »."""
    def rep(m):
        niveau, contenu = m.group(1), m.group(2)
        a = ANCRE.search(contenu)
        if not a:
            ident = re.sub(r"[^\w-]+", "-", html.unescape(re.sub(r"<[^>]+>", "", contenu))).strip("-").lower()
            return f'<h{niveau} id="{html.escape(ident)}">{contenu}</h{niveau}>'
        return f'<h{niveau} id="{html.escape(a.group(1))}">{contenu[:a.start()]}</h{niveau}>'
    return re.sub(r"<h([1-6])>(.*?)</h\1>", rep, rendu, flags=re.S)


def _ariane(rel: Path, titres: dict[str, str]) -> str:
    """Fil d'Ariane à partir des pages parentes qui existent."""
    parties = rel.with_suffix("").parts          # ("cpp", "container", "vector", "push_back")
    liens = []
    profondeur = len(parties) - 1
    for k in range(1, len(parties)):
        parent = "/".join(parties[:k])
        if parent in titres:
            href = "../" * profondeur + parent + ".html"   # relatif à la page courante
            nom = ACCUEILS.get(parent, titres[parent])
            liens.append(f'<a href="{html.escape(href)}">{html.escape(_sans_code(nom))}</a>')
    if not liens:
        return ""
    return '<nav class="ariane" aria-label="Fil d\'Ariane">' + " › ".join(liens) + "</nav>\n"


def construire(args):
    chemin, titres = args
    rel = chemin.relative_to(MD).with_suffix(".html")
    texte = chemin.read_text(encoding="utf-8")
    titre = _titre(texte)
    note, corps_md = _preparer_md(texte)
    corps = _ancres(md.render(corps_md))
    # liens .md restés dans du HTML brut
    corps = re.sub(r'href="([^":"]+?)\.md(#[^"]*)?"', lambda m: f'href="{m.group(1)}.html{m.group(2) or ""}"', corps)
    if note:
        # la note de source juste sous le titre
        corps = re.sub(r"(</h1>\n)", r"\1" + f'<p class="ref-source">{note}</p>\n', corps, count=1)
    dest = SORTIE / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    profondeur_site = len(dest.relative_to(SITE).parts) - 1
    dest.write_text(PAGE.format(
        titre_onglet=html.escape(_sans_code(titre)) + " — cppreference (fr)",
        rel="../" * profondeur_site,
        ariane=_ariane(rel, titres),
        corps=corps,
    ), encoding="utf-8")
    return 1


def main():
    pages = sorted(MD.rglob("*.md"))
    # titres de toutes les pages, pour le fil d'Ariane
    titres = {}
    for p in pages:
        with open(p, encoding="utf-8") as f:
            titres[p.relative_to(MD).with_suffix("").as_posix()] = _titre(f.readline())
    with Pool() as pool:
        n = sum(pool.imap_unordered(construire, ((p, titres) for p in pages), chunksize=20))
    print(f"{n} pages HTML écrites dans {SORTIE}/ (accueil : cpp.html et c.html)")


if __name__ == "__main__":
    main()
