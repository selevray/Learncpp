"""Découpe une page cppreference en segments de texte à traduire, puis les réinsère.

Principe : le HTML n'est jamais envoyé au modèle.
- Chaque bloc (p, td, li, h3...) donne un ou plusieurs « segments » : le texte
  courant, avec des balises neutres à la place des éléments en ligne.
- <xN/>      = élément ATOMIQUE (code, nom de paramètre, numéro...) : son contenu
               n'est pas envoyé et sera remis tel quel, octet pour octet.
- <tN>…</tN> = élément en ligne (lien, gras...) : son texte est traduit, ses
               attributs (href, class...) sont recopiés à l'identique.
Au retour, on vérifie que chaque balise est présente une seule fois et bien
imbriquée ; sinon le segment est refusé.
"""
from __future__ import annotations

import copy
import html
import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

INLINE = {"a", "b", "i", "em", "strong", "span", "sup", "sub", "small", "u", "s",
          "abbr", "cite", "q", "font", "big", "del", "ins"}
# balises dont le contenu ne doit jamais être traduit
ATOMIC_TAGS = {"code", "tt", "kbd", "var", "samp", "pre", "math", "img", "br",
               "script", "style", "svg", "input", "wbr"}
# classes cppreference qui contiennent du code ou des noms
ATOMIC_CLASSES = {"mw-geshi", "t-c", "t-lc", "t-spar", "t-li", "texhtml", "t-v",
                  "t-lines", "source-cpp", "source-c", "t-dsc-small", "mw-math"}
# blocs à ignorer complètement (code des exemples, sorties, etc.)
SKIP_CLASSES = {"mw-geshi", "t-example-live-link-disabled"}
SKIP_TAGS = {"pre", "script", "style", "noscript"}

WS = re.compile(r"\s+")
LETTERS = re.compile(r"[A-Za-z]{2,}")


def classes(el: Tag) -> set[str]:
    c = el.get("class") or []
    return set(c if isinstance(c, list) else c.split())


def is_atomic(el: Tag) -> bool:
    if el.name in ATOMIC_TAGS:
        return True
    if classes(el) & ATOMIC_CLASSES:
        return True
    st = el.get("style") or ""
    # noms d'exigences (CopyInsertable...) affichés en italique serif
    if "font-family" in st and "Georgia" in st:
        return True
    return False


def is_inline(node) -> bool:
    if isinstance(node, NavigableString):
        return True
    return isinstance(node, Tag) and (node.name in INLINE or is_atomic(node)) \
        and not _contains_block(node)


def _contains_block(el: Tag) -> bool:
    if is_atomic(el):
        return False
    for d in el.descendants:
        if isinstance(d, Tag) and d.name not in INLINE and not is_atomic(d) \
                and not any(is_atomic(p) for p in d.parents if p is not el):
            return True
    return False


@dataclass
class Segment:
    nodes: list            # nœuds d'origine (run contigu d'enfants du parent)
    parent: Tag
    markup: str            # texte envoyé au modèle
    lead: str              # espace avant
    trail: str             # espace après
    atoms: dict = field(default_factory=dict)   # "x3" -> Tag
    shells: dict = field(default_factory=dict)  # "t2" -> Tag (coquille)
    navbar: bool = False


def _serialize(nodes, seg: Segment, counter: list[int]) -> str:
    out = []
    for n in nodes:
        if isinstance(n, Comment):
            continue
        if isinstance(n, NavigableString):
            out.append(html.escape(str(n), quote=False))
        elif isinstance(n, Tag):
            counter[0] += 1
            k = counter[0]
            if is_atomic(n):
                seg.atoms[f"x{k}"] = n
                out.append(f"<x{k}/>")
            else:
                seg.shells[f"t{k}"] = n
                inner = _serialize(list(n.children), seg, counter)
                out.append(f"<t{k}>{inner}</t{k}>")
    return "".join(out)


def _translatable_text(markup: str) -> str:
    return re.sub(r"<[^>]+>", " ", markup)


def worth_translating(markup: str) -> bool:
    txt = html.unescape(_translatable_text(markup))
    words = [w for w in re.findall(r"[A-Za-z_][A-Za-z0-9_:]*", txt)]
    # au moins un vrai mot anglais (lettres seules, ≥ 2) ...
    real = [w for w in words if w.isalpha() and len(w) >= 2]
    if not real:
        return False
    # ... et pas seulement un identifiant isolé (ex. « vector », « push_back »)
    if len(words) == 1 and not txt.strip()[:1].isupper() and not txt.strip().startswith("(") \
            and not (re.search(r"<x\d+/>", markup) and len(words[0]) >= 4 and words[0].isalpha()):
        return False
    return True


def _make_segment(run, parent, navbar) -> Segment | None:
    seg = Segment(nodes=run, parent=parent, markup="", lead="", trail="", navbar=navbar)
    markup = _serialize(run, seg, [0])
    if not worth_translating(markup):
        return None
    m = re.match(r"^\s*", markup)
    seg.lead = " " if m.group() else ""
    seg.trail = " " if re.search(r"\s$", markup) else ""
    seg.markup = WS.sub(" ", markup).strip()
    # renuméroter pour que des segments identiques aient la même clé de cache
    seg.markup = _renumber(seg)
    return seg


def _renumber(seg: Segment) -> str:
    mapping, atoms, shells = {}, {}, {}
    n = [0]

    def rep(m):
        kind, k, closing, selfc = m.group(2), m.group(3), m.group(1), m.group(4)
        old = f"{kind}{k}"
        if old not in mapping:
            n[0] += 1
            mapping[old] = f"{kind}{n[0]}"
            if kind == "x":
                atoms[mapping[old]] = seg.atoms[old]
            else:
                shells[mapping[old]] = seg.shells[old]
        return f"<{closing}{mapping[old]}{selfc}>"

    out = re.sub(r"<(/?)([xt])(\d+)(/?)>", rep, seg.markup)
    seg.atoms, seg.shells = atoms, shells
    return out


def extract(soup: BeautifulSoup) -> list[Segment]:
    root = soup.find(id="mw-content-text")
    if root is None:
        return []
    segs: list[Segment] = []

    def walk(el: Tag, navbar: bool):
        if el.name in SKIP_TAGS or classes(el) & SKIP_CLASSES:
            return
        # 1re colonne d'une ligne de paramètres = nom du paramètre (identifiant)
        if el.name == "td" and el.parent is not None and "t-par" in classes(el.parent) \
                and el.find_previous_sibling("td") is None:
            return
        nav = navbar or "t-navbar" in classes(el)
        run = []
        for child in list(el.children):
            if is_inline(child):
                run.append(child)
            else:
                if run:
                    s = _make_segment(run, el, nav)
                    if s:
                        segs.append(s)
                    run = []
                if isinstance(child, Tag):
                    walk(child, nav)
        if run:
            s = _make_segment(run, el, nav)
            if s:
                segs.append(s)

    titre = soup.find(id="firstHeading")
    if titre is not None:
        walk(titre, False)
    walk(root, False)
    segs.extend(_commentaires(root))
    return segs


# commentaires dans le code : seul leur texte est traduit
_DEBUT_COM = re.compile(r"^(/\*+!?|//+!?<?)([ \t]*)")
_FIN_COM = re.compile(r"([ \t]*)(\*+/)?([ \t]*)$")
_COUPURE = re.compile(r"(\n[ \t]*(?:\*(?!/)[ \t]*)?)")


def _commentaires(root: Tag) -> list[Segment]:
    segs = []
    for span in root.select("span.co1, span.coMULTI"):
        enfants = list(span.children)
        if len(enfants) != 1 or not isinstance(enfants[0], NavigableString):
            continue
        texte = str(enfants[0])
        d = _DEBUT_COM.match(texte)
        if not d:
            continue
        reste = texte[d.end():]
        f = _FIN_COM.search(reste)
        corps, fin = reste[:f.start()], reste[f.start():]
        seg = Segment(nodes=enfants, parent=span, markup="", lead=d.group(0), trail=fin)
        morceaux = _COUPURE.split(corps)   # texte, séparateur, texte, ...
        out = []
        for i, m in enumerate(morceaux):
            if i % 2:
                k = f"x{len(seg.atoms) + 1}"
                seg.atoms[k] = NavigableString(m)
                out.append(f"<{k}/>")
            else:
                out.append(html.escape(m, quote=False))
        seg.markup = "".join(out)
        if seg.markup.strip() and worth_translating(seg.markup):
            segs.append(seg)
    return segs


# ---------------------------------------------------------------- réinsertion

TOKEN = re.compile(r"<(/?)([xt])(\d+)(/?)>")


class InvalidTranslation(ValueError):
    pass


def check(source: str, translated: str) -> None:
    """Lève InvalidTranslation si les balises ne correspondent pas exactement."""
    def tags(s):
        return sorted(m.group(0) for m in TOKEN.finditer(s))
    if tags(source) != tags(translated):
        raise InvalidTranslation(
            f"balises différentes : attendu {tags(source)}, reçu {tags(translated)}")
    stack = []
    for m in TOKEN.finditer(translated):
        closing, kind, k, selfc = m.group(1), m.group(2), m.group(3), m.group(4)
        if kind == "x":
            if closing or not selfc:
                raise InvalidTranslation(f"balise atomique mal formée : {m.group(0)}")
        elif closing:
            if not stack or stack.pop() != k:
                raise InvalidTranslation(f"imbrication incorrecte près de {m.group(0)}")
        else:
            stack.append(k)
    if stack:
        raise InvalidTranslation("balise non fermée")
    if re.search(r"<(?![xt]\d|/t\d)[a-zA-Z/]", translated):
        raise InvalidTranslation("balise HTML inattendue dans la traduction")
    # les identifiants C++ visibles (std::xxx, foo_bar, f()) doivent rester intacts
    src_ids = set(re.findall(r"\b\w+::\w+|\b\w+_\w+\b|\b\w+\(\)", html.unescape(source)))
    for ident in src_ids:
        if ident not in html.unescape(translated):
            raise InvalidTranslation(f"identifiant modifié ou perdu : {ident}")
    # les symboles de code (souvent dans les commentaires) ne doivent pas bouger
    src_u, tr_u = html.unescape(_translatable_text(source)), html.unescape(_translatable_text(translated))
    for ch in "{}=&[]#":
        if src_u.count(ch) != tr_u.count(ch):
            raise InvalidTranslation(f"symbole de code modifié : « {ch} »")
    # « ; » : la typo française en ajoute parfois un à la place d'une virgule ;
    # on n'accepte un écart que pour des « ; » de prose (précédés d'une espace)
    pv_src, pv_tr = src_u.count(";"), tr_u.count(";")
    pv_prose_tr = len(re.findall(r"[ \u00a0\u202f];", tr_u))
    if not (pv_tr == pv_src or (pv_tr > pv_src and pv_tr - pv_src <= pv_prose_tr)):
        raise InvalidTranslation("symbole de code modifié : « ; »")
    for ch in "":
            raise InvalidTranslation(f"symbole de code modifié : « {ch} »")
    if not _translatable_text(translated).strip() and _translatable_text(source).strip():
        raise InvalidTranslation("traduction vide")


def _build(markup: str, seg: Segment, soup: BeautifulSoup, used: set):
    """Transforme le markup traduit en liste de nœuds BeautifulSoup."""
    root: list = []
    stack: list[tuple[Tag, list]] = []
    cur = root
    pos = 0

    def add_text(t):
        if t:
            cur.append(NavigableString(html.unescape(t)))

    for m in TOKEN.finditer(markup):
        add_text(markup[pos:m.start()])
        pos = m.end()
        closing, kind, k = m.group(1), m.group(2), m.group(3)
        key = f"{kind}{k}"
        if kind == "x":
            atom = seg.atoms[key]
            cur.append(atom if key not in used else copy.copy(atom))
            used.add(key)
        elif not closing:
            shell = copy.copy(seg.shells[key])
            shell.clear()
            stack.append((shell, cur))
            cur.append(shell)
            cur = []
            shell._fr_children = cur  # type: ignore[attr-defined]
        else:
            shell, parent_list = stack.pop()
            for c in shell._fr_children:  # type: ignore[attr-defined]
                shell.append(c)
            cur = parent_list
    add_text(markup[pos:])
    return root


def apply(seg: Segment, translated: str, soup: BeautifulSoup) -> None:
    check(seg.markup, translated)
    # repère à la place de l'ancien texte, puis on détache l'ancien contenu
    marker = soup.new_tag("fr-marker")
    seg.nodes[0].insert_before(marker)
    for n in seg.nodes:
        n.extract()
    new_nodes = _build(translated, seg, soup, set())
    if seg.lead:
        new_nodes.insert(0, NavigableString(seg.lead))
    if seg.trail:
        new_nodes.append(NavigableString(seg.trail))
    for n in new_nodes:
        marker.insert_before(n)
    marker.extract()


def load(path) -> BeautifulSoup:
    with open(path, encoding="utf-8") as f:
        return BeautifulSoup(f.read(), "lxml")
