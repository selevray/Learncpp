"""Convertit une page cppreference (déjà traduite ou non) en Markdown lisible.

Les structures propres à cppreference (déclarations, paramètres, listes de
membres, notes de version, exemples) sont d'abord réécrites en HTML simple,
puis markdownify fait le reste.
"""
from __future__ import annotations

import re

from bs4 import BeautifulSoup, Comment, NavigableString, Tag
from markdownify import MarkdownConverter

SUPPRIMER = [".t-navbar", ".t-example-live-link", ".editsection", "#toc", ".toc",
             ".t-page-template", ".printfooter", ".t-dcl-sep", ".t-sdsc-sep",
             "script", "style", "noscript", ".catlinks"]


def _cls(el) -> set:
    if not isinstance(el, Tag):
        return set()
    c = el.get("class") or []
    return set(c if isinstance(c, list) else c.split())


def _code_text(el: Tag, compact: bool = False) -> str:
    """Texte brut d'un bloc de code, en respectant <br> et les div de lignes."""
    el = BeautifulSoup(str(el), "lxml").find(el.name)  # copie
    for br in el.find_all("br"):
        br.replace_with("\n")
    for d in el.find_all("div"):
        d.insert_after("\n")
    txt = el.get_text().replace("\xa0", " ")
    lignes = [l.rstrip() for l in txt.split("\n")]
    if compact:
        lignes = [l for l in lignes if l.strip()]
    while lignes and not lignes[0].strip():
        lignes.pop(0)
    while lignes and not lignes[-1].strip():
        lignes.pop()
    return "\n".join(lignes)


def _lang(el: Tag) -> str:
    toutes = _cls(el) | {c for d in el.find_all(True) for c in _cls(d)}
    if "source-cpp" in toutes or "cpp" in toutes:
        return "cpp"
    if "source-c" in toutes:
        return "c"
    return "text"


def _pre(soup, code: str, lang: str = "cpp") -> Tag:
    pre = soup.new_tag("pre")
    c = soup.new_tag("code", attrs={"class": f"language-{lang}"})
    c.string = code
    pre.append(c)
    return pre


def _inline_code(soup, text: str) -> Tag:
    c = soup.new_tag("code")
    c.string = re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()
    return c


def _move_children(src: Tag, dst: Tag):
    for c in list(src.children):
        dst.append(c)


def _rows(table: Tag):
    for child in table.find_all(["tr", "tbody", "thead"], recursive=False):
        if child.name == "tr":
            yield child
        else:
            yield from child.find_all("tr", recursive=False)


def _cells(tr: Tag):
    return tr.find_all(["td", "th"], recursive=False)


def _txt(el) -> str:
    return re.sub(r"\s+", " ", el.get_text(" ")).strip()


def _para(soup, contenu: Tag | str, gras=False) -> Tag:
    p = soup.new_tag("p")
    cible = p
    if gras:
        cible = soup.new_tag("strong")
        p.append(cible)
    if isinstance(contenu, Tag):
        _move_children(contenu, cible)
    else:
        cible.append(contenu)
    return p


# ---------------------------------------------------------------- tableaux

def _declarations(soup, table) -> list:
    sortie, lignes = [], []
    lang = _lang(table) if _lang(table) != "text" else "cpp"

    def vider():
        if lignes:
            sortie.append(_pre(soup, "\n\n".join(lignes), lang))
            lignes.clear()

    for tr in _rows(table):
        c = _cls(tr)
        tds = _cells(tr)
        if not tds:
            continue
        if c & {"t-dcl-h", "t-dsc-header", "t-dcl-header"}:
            vider()
            sortie.append(_para(soup, _txt(tr), gras=True))
        elif _txt(tds[0]):
            code = _code_text(tds[0], compact=True).lstrip()
            infos = " ".join(_txt(td) for td in tds[1:]).strip()
            lignes.append(code + (f"  // {infos}" if infos else ""))
    vider()
    return sortie


def _liste(soup, table, kind) -> list:
    blocs, ul = [], None

    def li_new():
        nonlocal ul
        if ul is None:
            ul = soup.new_tag("ul")
            blocs.append(ul)
        li = soup.new_tag("li")
        ul.append(li)
        return li

    for tr in _rows(table):
        c = _cls(tr)
        tds = _cells(tr)
        if not tds or not tr.get_text(strip=True):
            continue
        if kind == "dsc" and "t-dsc" in c and len(tds) >= 2:
            li = li_new()
            nom = soup.new_tag("strong")
            _move_children(tds[0], nom)
            li.append(nom)
            li.append(" — ")
            for br in tds[1].find_all("br"):
                br.replace_with(" ")
            _move_children(tds[1], li)
        elif kind == "par" and "t-par" in c and len(tds) >= 3:
            li = li_new()
            li.append(_inline_code(soup, tds[0].get_text()))
            li.append(" — ")
            _move_children(tds[2], li)
        elif kind == "par" and "t-par-req" in c:
            li = li_new()
            for d in tds[0].select("div.spacer"):
                d.decompose()
            premier = next(iter(tds[0].contents), None)
            if isinstance(premier, NavigableString):
                premier.replace_with(premier.lstrip().lstrip("-").lstrip())
            _move_children(tds[0], li)
        else:
            ul = None
            p = soup.new_tag("p")
            b = soup.new_tag("strong")
            for i, td in enumerate(tds):
                if i:
                    b.append(" ")
                _move_children(td, b)
            p.append(b)
            blocs.append(p)
    return blocs


def _revisions(soup, table) -> list:
    blocs = []
    for tr in _rows(table):
        tds = _cells(tr)
        if not tds or not tr.get_text(strip=True):
            continue
        bq = soup.new_tag("blockquote")
        _move_children(tds[0], bq)
        if len(tds) > 1 and tds[1].get_text(strip=True):
            p = soup.new_tag("p")
            em = soup.new_tag("em")
            em.string = _txt(tds[1])
            p.append(em)
            bq.append(p)
        blocs.append(bq)
    return blocs


def _generique(soup, table) -> list | None:
    """Tableau ordinaire : laissé à markdownify s'il est simple et au premier
    niveau ; sinon une ligne par rangée."""
    imbrique = table.find_parent(["li", "blockquote", "td", "th"]) is not None
    complexe = any(td.find(["p", "ul", "ol", "pre", "blockquote"]) or
                   td.get("rowspan") or td.get("colspan")
                   for tr in _rows(table) for td in _cells(tr))
    if not imbrique and not complexe:
        return None
    blocs = []
    for tr in _rows(table):
        tds = _cells(tr)
        if not tr.get_text(strip=True):
            continue
        p = soup.new_tag("p")
        for i, td in enumerate(tds):
            if not td.get_text(strip=True):
                continue
            if len(p.contents):
                p.append(" | ")
            if td.name == "th":
                b = soup.new_tag("strong")
                _move_children(td, b)
                p.append(b)
            else:
                _move_children(td, p)
        blocs.append(p)
    return blocs


def _tableaux(soup, root):
    tables = root.find_all("table")
    # du plus profond au moins profond : les tableaux internes d'abord
    tables.sort(key=lambda t: len(list(t.parents)), reverse=True)
    for table in tables:
        if table.decomposed or table.attrs is None:
            continue
        c = _cls(table)
        if "t-dcl-begin" in c:
            blocs = _declarations(soup, table)
        elif "t-dsc-begin" in c:
            blocs = _liste(soup, table, "dsc")
        elif "t-par-begin" in c:
            blocs = _liste(soup, table, "par")
        elif "t-rev-begin" in c:
            blocs = _revisions(soup, table)
        else:
            blocs = _generique(soup, table)
            if blocs is None:
                continue
        for el in blocs:
            table.insert_before(el)
        table.decompose()


# ---------------------------------------------------------------- page

LIBELLES = {"(constructor)": "(constructeur)", "(destructor)": "(destructeur)",
            "[virtual]": " [virtuelle]", "[static]": " [statique]"}


def _libelles(root: Tag):
    """Libellés fixes de cppreference, laissés en anglais car dans du code."""
    for t in list(root.find_all(string=True)):
        cle = t.strip()
        if cle in LIBELLES and t.find_parent("pre") is None:
            t.replace_with(LIBELLES[cle])


def _variantes_version(soup, root: Tag):
    """Morceaux de phrase qui changent selon la version :
    <rev-inl>un tableau (jusqu'à C++11)</rev-inl><rev-inl>… (depuis C++11)</rev-inl>
    → [un tableau *(jusqu'à C++11)* | … *(depuis C++11)*]"""
    vus = set()
    for el in root.select("span.t-rev-inl"):
        if id(el) in vus:
            continue
        groupe = [el]
        suivant = el.next_sibling
        while suivant is not None:
            if isinstance(suivant, NavigableString) and not suivant.strip():
                suivant = suivant.next_sibling
                continue
            if isinstance(suivant, Tag) and "t-rev-inl" in _cls(suivant):
                groupe.append(suivant)
                suivant = suivant.next_sibling
                continue
            break
        vus.update(id(g) for g in groupe)
        for g in groupe:
            for m in g.select("span.t-mark-rev"):
                em = soup.new_tag("em")
                em.string = _txt(m)
                m.replace_with(em)
            # pas d'espace parasite juste après « [ » ou avant « ] »
            textes = [t for t in g.find_all(string=True)]
            if textes:
                textes[0].replace_with(textes[0].lstrip())
        for g in groupe:
            for em in g.find_all("em"):
                em.insert_before(" ")
        if len(groupe) >= 2:
            groupe[0].insert_before("[")
            for g in groupe[1:]:
                g.insert_before(" | ")
            groupe[-1].insert_after("]")


def preparer(soup: BeautifulSoup) -> tuple[str, Tag | None]:
    titre_el = soup.find(id="firstHeading")
    titre = re.sub(r"\s+", " ", titre_el.get_text()).strip() if titre_el else ""
    root = soup.find(id="mw-content-text")
    if root is None:
        return titre, None
    for sel in SUPPRIMER:
        for el in root.select(sel):
            el.decompose()
    for c in root.find_all(string=lambda s: isinstance(s, Comment)):
        c.extract()

    # exemples et blocs de code
    for div in root.select("div.mw-geshi"):
        if div.parent is not None and (div.find("pre") is not None
                                       or div.find_parent(class_="t-example")):
            div.replace_with(_pre(soup, _code_text(div), _lang(div)))
    for pre in root.find_all("pre"):
        if pre.find("code") is None:
            pre.replace_with(_pre(soup, _code_text(pre), "text"))

    # déclarations avant le code en ligne (elles ont besoin du texte brut)
    for table in root.select("table.t-dcl-begin"):
        if table.decomposed or table.attrs is None:   # déjà traité (tableau imbriqué)
            continue
        for el in _declarations(soup, table):
            table.insert_before(el)
        table.decompose()

    # code en ligne
    for el in root.select("span.mw-geshi, span.t-c, span.t-v, span.t-spar, tt"):
        if el.parent is None or el.find_parent("pre") is not None:
            continue
        el.replace_with(_inline_code(soup, el.get_text()))
    for el in root.select("span.t-lc"):
        a = el.find("a")
        if a is not None:
            t = a.get_text()
            a.clear()
            a.append(_inline_code(soup, t))
            el.replace_with(a)
        else:
            el.replace_with(_inline_code(soup, el.get_text()))
    for el in root.find_all("span", style=re.compile("Georgia")):
        i = soup.new_tag("em")
        i.string = el.get_text()
        el.replace_with(i)
    for el in root.select("span.t-mark"):
        em = soup.new_tag("em")
        _move_children(el, em)
        el.replace_with(em)
    _variantes_version(soup, root)
    _libelles(root)
    for el in root.select("span.t-mark-rev"):
        el.insert_before(" ")
        el.insert_after(" ")
    for el in root.find_all("div", class_=re.compile(r"^t-li\d")):
        el.name = "p"
        del el["class"]

    _tableaux(soup, root)

    # ancres d'origine des titres (#Parameters...) : « {#Parameters} » en fin de titre
    for span in root.select("span.mw-headline[id]"):
        span.append(" {#" + span["id"] + "}")

    # listes de définitions (dl/dt/dd) : pas de syntaxe Markdown standard
    # « <ul>…</ul><dl><dd>sous-liste</dd></dl> » : la sous-liste va dans le dernier point
    for dl in root.find_all("dl"):
        if dl.find("dt") is not None:
            continue
        prec = dl.find_previous_sibling(True)
        if prec is not None and prec.name in ("ul", "ol") and prec.find_all("li", recursive=False):
            dernier = prec.find_all("li", recursive=False)[-1]
            for dd in dl.find_all("dd", recursive=False):
                _move_children(dd, dernier)
            dl.decompose()
    for dt in root.find_all("dt"):
        dt.name = "p"
        b = soup.new_tag("strong")
        _move_children(dt, b)
        dt.append(b)
    for dd in root.find_all("dd"):
        dd.name = "div"
    for dl in root.find_all("dl"):
        dl.unwrap()

    for img in root.find_all("img"):
        img.replace_with(img.get("alt") or "")
    for a in root.find_all("a"):
        a.attrs.pop("title", None)
        h = a.get("href")
        if h and not re.match(r"^[a-z]+:", h):
            a["href"] = re.sub(r"\.html(?=$|#)", ".md", h)
    return titre, root


class Conv(MarkdownConverter):
    def convert_pre(self, el, text, *args, **kwargs):
        code = el.find("code")
        lang = ""
        if code is not None:
            for c in _cls(code):
                if c.startswith("language-"):
                    lang = c[len("language-"):]
        contenu = (code or el).get_text()
        return f"\n\n```{lang}\n{contenu}\n```\n\n"


def _echapper_chevrons(ligne: str) -> str:
    """« <vector> » hors du code serait pris pour une balise HTML."""
    morceaux = re.split(r"(`[^`]*`)", ligne)
    for i in range(0, len(morceaux), 2):
        morceaux[i] = re.sub(r"<(?=[A-Za-z/!])", "&lt;", morceaux[i])
    return "".join(morceaux)


def _nettoyer(md: str) -> str:
    out, dans_code = [], False
    for ligne in md.split("\n"):
        if re.match(r"^\s*(>\s*)*```", ligne):
            dans_code = not dans_code
        elif not dans_code:
            retour_force = ligne.endswith("  ") and ligne.strip() != ""
            ligne = re.sub(r"(?<=\S) {2,}", " ", ligne).rstrip()
            if retour_force:
                ligne += "  "
            ligne = ligne.replace("\u200b", "")
            # bouts de code collés : `a``b` -> `ab`
            avant = None
            while avant != ligne:
                avant = ligne
                ligne = re.sub(r"`([^`\n]+)``([^`\n]+)`", r"`\1\2`", ligne)
            ligne = _echapper_chevrons(ligne)
        out.append(ligne)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()


def en_markdown(soup: BeautifulSoup, source_url: str, traduit: bool) -> str:
    titre, root = preparer(soup)
    corps = ""
    if root is not None:
        corps = Conv(heading_style="ATX", bullets="-", escape_underscores=False,
                     escape_asterisks=False, strip=["span", "div"]).convert_soup(root)
    corps = _nettoyer(corps)
    if "::" in titre or "<" in titre or " " not in titre.strip():
        h1 = f"# `{titre}`"
    else:
        h1 = f"# {titre}"
    note = ("Traduction automatique (Claude Haiku 5.5) de " if traduit else "Source : ") + \
        f"[cppreference.com]({source_url}), sous licence CC-BY-SA 3.0."
    return f"{h1}\n\n> {note}\n\n{corps}\n"
