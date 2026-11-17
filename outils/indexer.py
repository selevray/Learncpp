#!/usr/bin/env python3
"""Met à jour la recherche de l'espace d'apprentissage.

1. Convertit (si besoin) le cours LearnCpp traduit (~/learncpp/cours, Markdown)
   en pages HTML lisibles dans le navigateur : ./cours/
2. Construit l'index de recherche ./assets/index-recherche.js à partir de :
   - ./lessons/*.html      (vos leçons)
   - ./reference/*.html    (vos fiches mémo)
   - ./exercices/*/README.md
   - ./cours/**/*.html     (le cours LearnCpp)

À lancer après chaque nouvelle leçon, fiche ou exercice :
    .venv/bin/python outils/indexer.py
"""
from __future__ import annotations

import html
import json
import re
import shutil
import sys
from html.parser import HTMLParser
from pathlib import Path

import markdown
from markdown.extensions.toc import slugify_unicode

RACINE = Path(__file__).resolve().parent.parent
SOURCE_COURS = Path.home() / "learncpp" / "cours"
SOURCE_IMAGES = Path.home() / "learncpp" / "images"
COURS = RACINE / "cours"
INDEX = RACINE / "assets" / "index-recherche.js"


# ------------------------------------------------------------ Markdown -> HTML

CALLOUT = re.compile(r"^\[!(\w+)\](-?)\s*(.*)$")


def rendre(md_texte: str) -> str:
    """Markdown -> HTML, avec les encadrés Obsidian « > [!type] Titre »."""
    lignes = md_texte.split("\n")
    sortie, blocs, i = [], [], 0
    while i < len(lignes):
        ligne = lignes[i]
        m = re.match(r"^> ?(.*)$", ligne)
        tete = CALLOUT.match(m.group(1)) if m else None
        if not tete:
            sortie.append(ligne)
            i += 1
            continue
        groupe = []
        while i < len(lignes) and lignes[i].startswith(">"):
            groupe.append(re.sub(r"^> ?", "", lignes[i], count=1))
            i += 1
        genre, replie, titre = tete.group(1).lower(), tete.group(2) == "-", tete.group(3)
        corps = rendre("\n".join(groupe[1:]))
        titre_html = markdown.markdown(titre)[3:-4] if titre else genre.capitalize()
        if replie:
            bloc = f'<details class="callout {genre}"><summary>{titre_html}</summary>\n{corps}\n</details>'
        else:
            bloc = f'<div class="callout {genre}"><p class="callout-title">{titre_html}</p>\n{corps}\n</div>'
        blocs.append(bloc)
        sortie += ["", f"CALLOUT{len(blocs) - 1}FIN", ""]
    rendu = markdown.markdown("\n".join(sortie), extensions=["fenced_code", "tables", "sane_lists", "toc"],
                              extension_configs={"toc": {"slugify": slugify_unicode}})
    return re.sub(r"<p>CALLOUT(\d+)FIN</p>", lambda m: blocs[int(m.group(1))], rendu)


PAGE = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titre}</title>
<link rel="stylesheet" href="{rel}assets/style.css">
<script src="{rel}assets/composants.js" defer></script>
</head>
<body>
<main>
{corps}
</main>
</body>
</html>
"""


CONSEILS = RACINE / "conseils"


def lire_conseils() -> dict[str, list[tuple[str, str, str]]]:
    """conseils/*.md -> {slug: [(section, titre, html), ...]}"""
    resultat: dict[str, list] = {}
    for f in sorted(CONSEILS.glob("*.md")) if CONSEILS.exists() else []:
        for bloc in re.split(r"^@@@ ", f.read_text(), flags=re.M)[1:]:
            entete, _, corps = bloc.partition("\n")
            parties = [p.strip() for p in entete.split("|")]
            if len(parties) != 3:
                print(f"  Conseil ignoré (en-tête invalide) dans {f.name} : {entete}")
                continue
            slug, section, titre = parties
            contenu = markdown.markdown(corps.strip(), extensions=["fenced_code", "tables", "sane_lists"])
            resultat.setdefault(slug, []).append((section, titre, contenu))
    return resultat


def inserer_conseils(corps: str, conseils: list[tuple[str, str, str]], slug: str) -> str:
    """Place chaque conseil à la fin de sa section (juste avant le titre <h2> suivant)."""
    def texte(h: str) -> str:
        return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", h))).strip().lower()

    for section, titre, contenu in conseils:
        bloc = f'\n<conseil-claude titre="{html.escape(titre)}">\n{contenu}\n</conseil-claude>\n'
        titres = list(re.finditer(r"<h2>(.*?)</h2>", corps, flags=re.S))
        idx = next((i for i, m in enumerate(titres) if texte(m.group(1)) == section.replace("`", "").strip().lower()), None)
        if idx is None:
            print(f"  Section introuvable pour un conseil de {slug} : « {section} » (placé à la fin)")
            pos = len(corps)
        else:
            pos = titres[idx + 1].start() if idx + 1 < len(titres) else len(corps)
        corps = corps[:pos] + bloc + corps[pos:]
    return corps


def convertir_cours() -> None:
    if not SOURCE_COURS.exists():
        print(f"Cours introuvable dans {SOURCE_COURS}, étape ignorée.")
        return
    sources = list(SOURCE_COURS.rglob("*.md"))

    def cible(s: Path) -> Path:
        return COURS / "index.html" if s.name == "Sommaire.md" else (COURS / s.relative_to(SOURCE_COURS)).with_suffix(".html")

    derniers_conseils = max((f.stat().st_mtime for f in CONSEILS.glob("*.md")), default=0) if CONSEILS.exists() else 0
    a_jour = COURS.exists() and all(
        cible(s).exists() and cible(s).stat().st_mtime >= max(s.stat().st_mtime, derniers_conseils)
        for s in sources)
    if a_jour:
        return
    if COURS.exists():
        shutil.rmtree(COURS)
    if SOURCE_IMAGES.exists():
        shutil.copytree(SOURCE_IMAGES, COURS / "images")
    conseils = lire_conseils()
    places = 0
    for s in sources:
        rel = s.relative_to(SOURCE_COURS)
        texte = s.read_text()
        texte = texte.replace("](../../images/", "](../images/")
        # « \<iostream> » (échappement Markdown) : Python-Markdown ne le comprend pas
        morceaux = re.split(r"(```.*?```)", texte, flags=re.S)
        texte = "".join(m if m.startswith("```") else m.replace("\\<", "&lt;") for m in morceaux)
        texte = re.sub(r"\]\(([^)\s]+?)\.md(#[^)\s]*)?\)", lambda m: f"]({m.group(1)}.html{m.group(2) or ''})", texte)
        premiere = texte.splitlines()[0] if texte else ""
        titre = premiere.lstrip("# ").strip() or rel.stem
        dest = cible(s)
        dest.parent.mkdir(parents=True, exist_ok=True)
        profondeur = len(dest.relative_to(RACINE).parts) - 1
        corps = rendre(texte)
        m = re.search(r"learncpp\.com/cpp-tutorial/([^/>]+)/", texte)
        if m and m.group(1) in conseils:
            corps = inserer_conseils(corps, conseils[m.group(1)], m.group(1))
            places += len(conseils[m.group(1)])
        dest.write_text(PAGE.format(titre=html.escape(titre), rel="../" * profondeur, corps=corps))
    print(f"Cours converti en HTML : {len(sources)} pages dans {COURS}, {places} Conseils Claude insérés")
    inconnus = set(conseils) - {re.search(r"cpp-tutorial/([^/>]+)/", s.read_text()).group(1)
                                for s in sources if re.search(r"cpp-tutorial/([^/>]+)/", s.read_text())}
    if inconnus:
        print(f"  Conseils pour des leçons inconnues : {', '.join(sorted(inconnus))}")


# ------------------------------------------------------------ index

class Texte(HTMLParser):
    def __init__(self):
        super().__init__()
        self.morceaux, self.titre, self.h1, self._dans = [], "", "", []

    def handle_starttag(self, tag, attrs):
        self._dans.append(tag)

    def handle_endtag(self, tag):
        while self._dans and self._dans.pop() != tag:
            pass

    def handle_data(self, data):
        if "script" in self._dans or "style" in self._dans:
            return
        if "title" in self._dans:
            self.titre += data
            return
        if "h1" in self._dans:
            self.h1 += data
        self.morceaux.append(data)


def texte_html(chemin: Path) -> tuple[str, str]:
    p = Texte()
    p.feed(chemin.read_text(errors="replace"))
    titre = (p.h1 or p.titre or chemin.stem).strip()
    return re.sub(r"\s+", " ", titre), re.sub(r"\s+", " ", " ".join(p.morceaux)).strip()


def sections_html(chemin: Path) -> tuple[str, list[tuple[str, str, str]]]:
    """Découpe une page aux titres <h2 id="..."> : (titre de la page, [(ancre, titre de section, texte)])."""
    source = chemin.read_text(errors="replace")
    titre_page, texte_page = texte_html(chemin)
    corps = source.split("<main>", 1)[-1]
    coupes = list(re.finditer(r'<h2 id="([^"]+)"[^>]*>(.*?)</h2>', corps, flags=re.S))
    if not coupes:
        return titre_page, [("", "", texte_page)]
    sections = []
    debut = corps[: coupes[0].start()]
    for i, m in enumerate(coupes):
        fin = coupes[i + 1].start() if i + 1 < len(coupes) else len(corps)
        p = Texte()
        p.feed(corps[m.end():fin])
        titre_section = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", m.group(2)))).strip()
        sections.append((m.group(1), titre_section, re.sub(r"\s+", " ", " ".join(p.morceaux)).strip()))
    p = Texte()
    p.feed(debut)
    intro = re.sub(r"\s+", " ", " ".join(p.morceaux)).strip()
    if intro.replace(titre_page, "").strip():
        sections.insert(0, ("", "", intro))
    return titre_page, sections


def construire_index() -> None:
    entrees = []

    def ajouter(genre: str, chemin: Path, titre: str, texte: str, ancre: str = "", section: str = "") -> None:
        entrees.append({"genre": genre, "url": chemin.relative_to(RACINE).as_posix(), "ancre": ancre,
                        "titre": titre, "section": section, "texte": texte})

    def ajouter_page(genre: str, chemin: Path) -> None:
        titre, sections = sections_html(chemin)
        for ancre, section, texte in sections:
            ajouter(genre, chemin, titre, texte, ancre, section)

    for f in sorted((RACINE / "lessons").glob("*.html")):
        ajouter_page("lecon", f)
    for f in sorted((RACINE / "reference").glob("*.html")):
        ajouter_page("fiche", f)
    for f in sorted((RACINE / "exercices").glob("*/README.md")):
        t = f.read_text()
        titre = (t.splitlines() or [f.parent.name])[0].lstrip("# ").strip()
        ajouter("exercice", f, titre, re.sub(r"\s+", " ", t))
    for f in sorted(COURS.rglob("*.html")) if COURS.exists() else []:
        if f.name != "index.html":
            ajouter_page("cours", f)

    INDEX.write_text("window.INDEX_RECHERCHE = " + json.dumps(entrees, ensure_ascii=False) + ";\n")
    pages = {g: len({e["url"] for e in entrees if e["genre"] == g}) for g in ("lecon", "fiche", "exercice", "cours")}
    print(f"Index de recherche : {pages['lecon']} leçons, {pages['fiche']} fiches, {pages['exercice']} exercices, "
          f"{pages['cours']} pages du cours ({len(entrees)} sections)")


if __name__ == "__main__":
    if "--forcer" in sys.argv and COURS.exists():
        shutil.rmtree(COURS)
    convertir_cours()
    construire_index()
