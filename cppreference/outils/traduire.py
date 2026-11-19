"""Traduit cppreference en français avec Claude Haiku 5.5, segment par segment.

    .venv/bin/python outils/traduire.py --test            # 20 pages d'essai
    .venv/bin/python outils/traduire.py --pages cpp/container/vector/push_back.html ...
    .venv/bin/python outils/traduire.py --tout [--section cpp c]   (par défaut : C++ et C)
    .venv/bin/python outils/traduire.py --construire     # régénère les pages depuis le cache, sans API

- Les traductions sont gardées dans traductions.sqlite (clé = segment source) :
  un même segment n'est traduit qu'une fois, et relancer ne repaie rien.
- Chaque traduction est vérifiée (balises, identifiants C++). Un segment refusé
  est retenté une fois avec l'erreur ; s'il échoue encore, il reste en anglais
  et il est listé dans echecs.log.
- Pages produites en Markdown dans ./md/ (même arborescence que l'archive).
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import segments as S  # noqa: E402
from en_markdown import en_markdown  # noqa: E402

RACINE = Path(__file__).resolve().parent.parent
SRC = RACINE / "source" / "reference"
EN = SRC / "en"
MD = RACINE / "md"
DB = RACINE / "traductions.sqlite"
ECHECS = RACINE / "echecs.log"

MODELE = "claude-haiku-5-5"
PRIX_ENTREE, PRIX_SORTIE = 0.10, 0.50   # $ / million de tokens (prompts < 100K)
MAX_CAR_PAR_REQUETE = 12_000
MAX_SEG_PAR_REQUETE = 80

PAGES_TEST = [
    "cpp/container/vector.html", "cpp/container/vector/push_back.html",
    "cpp/container/vector/reserve.html", "cpp/container/map.html",
    "cpp/container/map/find.html", "cpp/string/basic_string.html",
    "cpp/string/basic_string/substr.html", "cpp/io/basic_ostream/operator_ltlt.html",
    "cpp/io/basic_ifstream.html", "cpp/algorithm/sort.html", "cpp/algorithm/find.html",
    "cpp/language/classes.html", "cpp/language/copy_constructor.html",
    "cpp/language/virtual.html", "cpp/language/operators.html",
    "cpp/language/reference.html", "cpp/language/ub.html",
    "cpp/error/exception.html", "cpp/memory/unique_ptr.html", "cpp/iterator.html",
    "c/io/fprintf.html", "c/memory/malloc.html",
]

SYSTEME = """Tu traduis la documentation de référence C et C++ cppreference.com de l'anglais vers le français, pour un débutant francophone qui apprend le C++.

Tu reçois une liste JSON de segments {"i": numéro, "en": texte}. Réponds avec la traduction de CHAQUE segment, même numéro.

RÈGLES STRICTES (une seule erreur rend le segment inutilisable) :
1. Les balises <x1/>, <x2/>… représentent du code déjà en place. Recopie-les EXACTEMENT, chacune une fois, sans rien ajouter dedans ni autour. Tu peux les déplacer si la phrase française l'exige.
2. Les paires <t1>…</t1>, <t2>…</t2>… entourent un lien ou une mise en forme. Garde chaque paire exactement une fois, bien imbriquée, autour des mots français correspondants. Traduis le texte à l'intérieur.
3. N'ajoute AUCUNE autre balise, aucun Markdown, aucune explication, aucune note.
4. Ne traduis jamais le code ni les identifiants : std::vector, push_back, size_type, operator<<, noexcept, constexpr, T, Allocator, nullptr, true/false, noms de fonctions, de types, de macros, de paramètres et d'en-têtes (<vector>). Garde-les à l'identique, casse comprise.
5. Garde les marques de version telles quelles en les traduisant : « (since C++11) » → « (depuis C++11) », « (until C++17) » → « (jusqu'à C++17) », « (removed in C++20) » → « (supprimé en C++20) », « (deprecated in C++17) » → « (obsolète en C++17) », « (constexpr since C++20) » → « (constexpr depuis C++20) ».
6. Traduction fidèle et précise : c'est une référence technique, ne simplifie pas, ne résume pas, n'ajoute rien. Style neutre et concis, comme une documentation française de qualité. Garde la ponctuation et les espaces de début/fin équivalents.
7. Les noms d'exigences nommées en CamelCase (CopyInsertable, LegacyRandomAccessIterator, Container…) restent en anglais.
8. Certains segments sont des COMMENTAIRES de code (sans le « // » ni « /* », déjà en place), souvent mélangés à du code. Traduis TOUJOURS la partie en langage courant, même courte ou mélangée à du code, et garde le code tel quel. Exemples :
   « Error: operator== is not defined » → « Erreur : operator== n'est pas défini »
   « myInt1 == myInt2;  // Error: x is const » → « myInt1 == myInt2;  // Erreur : x est const »
   « calls f(2), then calls g() with the result » → « appelle f(2), puis appelle g() avec le résultat »
   « UB: operands of operator- do not refer to » → « UB : les opérandes de operator- ne désignent pas »
   Ne recopie à l'identique que du code pur, les chaînes entre guillemets et les messages réels de compilateur cités mot pour mot. Garde les espaces d'alignement de début de ligne.
9. Un segment qui n'a rien à traduire (nom propre, identifiant) est recopié tel quel. Les titres d'articles, de livres et de propositions du comité (P1234R5) restent en anglais.

GLOSSAIRE (utilise toujours ces termes ; en particulier JAMAIS « classe modèle », « classe template », « template de classe » ni « fonction modèle » : dis « modèle de classe » et « modèle de fonction ») :
member function → fonction membre ; non-member function → fonction non membre ; member type → type membre ; public member function → fonction membre publique ; function template → modèle de fonction ; class template → modèle de classe ; template parameter → paramètre de modèle ; template argument → argument de modèle ; specialization → spécialisation ; overload / overloaded → surcharge / surchargé ; overload resolution → résolution de surcharge ; iterator → itérateur ; container → conteneur ; allocator → allocateur ; undefined behavior → comportement indéfini ; unspecified → non spécifié ; implementation-defined → défini par l'implémentation ; ill-formed → mal formé ; well-formed → bien formé ; no diagnostic required → aucun diagnostic requis ; namespace → espace de noms ; header → en-tête ; scope → portée ; lifetime → durée de vie ; storage duration → durée de stockage ; linkage → liaison ; lvalue / rvalue / glvalue / prvalue / xvalue → inchangés ; move constructor → constructeur de déplacement ; copy constructor → constructeur de copie ; copy/move assignment operator → opérateur d'affectation par copie / par déplacement ; destructor → destructeur ; to throw an exception → lever une exception ; strong exception guarantee → garantie forte d'exception ; amortized constant → constant amorti ; complexity → complexité ; return value → valeur de retour ; parameters → paramètres ; type requirements → exigences sur les types ; see also → voir aussi ; example → exemple ; possible output → sortie possible ; output → sortie ; notes → notes ; defect reports → rapports de défauts ; run this code → exécuter ce code ; range → intervalle (plage pour « ranges library » : bibliothèque des plages) ; element → élément ; reallocation → réallocation ; invalidated → invalidé ; smart pointer → pointeur intelligent ; reference → référence ; pointer → pointeur ; literal → littéral ; specifier → spécificateur ; qualifier → qualificateur ; cv-qualified → qualifié cv ; expression → expression ; statement → instruction ; declaration → déclaration ; definition → définition ; feature-test macro → macro de test de fonctionnalité ; standard library → bibliothèque standard ; trivially copyable → trivialement copiable ; constant expression → expression constante ; synopsis → synopsis."""

SCHEMA = {
    "type": "object",
    "properties": {
        "t": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"i": {"type": "integer"}, "fr": {"type": "string"}},
                "required": ["i", "fr"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["t"],
    "additionalProperties": False,
}

verrou = threading.Lock()
usage = {"in": 0, "out": 0, "req": 0}


# ------------------------------------------------------------------ cache

def db():
    con = sqlite3.connect(DB, check_same_thread=False)
    con.execute("CREATE TABLE IF NOT EXISTS seg (en TEXT PRIMARY KEY, fr TEXT, modele TEXT, date TEXT)")
    return con


def deja_traduits(con, sources):
    out = {}
    sources = list(sources)
    for k in range(0, len(sources), 500):
        lot = sources[k:k + 500]
        q = "SELECT en, fr FROM seg WHERE en IN (%s)" % ",".join("?" * len(lot))
        out.update(dict(con.execute(q, lot).fetchall()))
    return out


# ------------------------------------------------------------------ API

def client():
    import os
    import anthropic
    cle = RACINE / ".cle_api"
    if not os.environ.get("ANTHROPIC_API_KEY") and cle.exists():
        os.environ["ANTHROPIC_API_KEY"] = cle.read_text().strip()
    try:
        return anthropic.Anthropic()
    except Exception as e:  # noqa: BLE001
        sys.exit(f"Impossible de créer le client API ({e}).\n"
                 "Ajoute ta clé dans ~/.zshrc : export ANTHROPIC_API_KEY=sk-ant-…")


def appel(cl, segs: list[tuple[int, str]], indication: str = "") -> dict[int, str]:
    contenu = json.dumps([{"i": i, "en": t} for i, t in segs], ensure_ascii=False)
    if indication:
        contenu = indication + "\n\n" + contenu
    for essai in range(5):
        try:
            r = cl.messages.create(
                model=MODELE,
                max_tokens=16000,
                system=SYSTEME,
                output_config={"effort": "low",
                               "format": {"type": "json_schema", "schema": SCHEMA}},
                messages=[{"role": "user", "content": contenu}],
            )
            break
        except Exception as e:  # noqa: BLE001
            if essai == 4:
                raise
            time.sleep(2 ** essai * 3)
            last = e  # noqa: F841
    with verrou:
        usage["in"] += r.usage.input_tokens
        usage["out"] += r.usage.output_tokens
        usage["req"] += 1
    if r.stop_reason != "end_turn":
        return {}
    texte = next((b.text for b in r.content if b.type == "text"), "{}")
    try:
        return {d["i"]: d["fr"] for d in json.loads(texte)["t"]}
    except (json.JSONDecodeError, KeyError, TypeError):
        return {}


def lots(sources: list[str]):
    lot, taille = [], 0
    for s in sources:
        if lot and (taille + len(s) > MAX_CAR_PAR_REQUETE or len(lot) >= MAX_SEG_PAR_REQUETE):
            yield lot
            lot, taille = [], 0
        lot.append(s)
        taille += len(s)
    if lot:
        yield lot


def traduire_lot(cl, lot: list[str]) -> tuple[dict[str, str], list[tuple[str, str]]]:
    rep = appel(cl, list(enumerate(lot)))
    ok, a_refaire = {}, []
    for i, src in enumerate(lot):
        fr = rep.get(i)
        try:
            if fr is None:
                raise S.InvalidTranslation("segment absent de la réponse")
            S.check(src, fr)
            ok[src] = fr
        except S.InvalidTranslation as e:
            a_refaire.append((src, str(e)))
    # 2e chance, segment par segment, avec l'erreur expliquée
    echecs = []
    for src, err in a_refaire:
        rep = appel(cl, [(0, src)], f"Ta traduction précédente de ce segment a été refusée : {err}. "
                                    "Respecte exactement les règles sur les balises et les identifiants.")
        fr = rep.get(0)
        try:
            if fr is None:
                raise S.InvalidTranslation("segment absent de la réponse")
            S.check(src, fr)
            ok[src] = fr
        except S.InvalidTranslation as e:
            echecs.append((src, f"{err} | 2e essai : {e}"))
    return ok, echecs


# ------------------------------------------------------------------ pages

def segments_de(rel):
    soup = S.load(EN / rel)
    return soup, S.extract(soup)


def construire(rel, cache) -> tuple[int, int]:
    soup, segs = segments_de(rel)
    faits = 0
    for s in segs:
        fr = cache.get(s.markup)
        if fr is not None:
            try:
                S.apply(s, fr, soup)
                faits += 1
            except S.InvalidTranslation:
                pass
    url = "https://en.cppreference.com/w/" + rel[:-len(".html")]
    md = en_markdown(soup, url, traduit=faits > 0)
    dest = MD / rel.replace(".html", ".md")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(md, encoding="utf-8")
    return faits, len(segs)


_CACHE = {}


def _init_cache(c):
    global _CACHE
    _CACHE = c


def _construire_sur(rel):
    try:
        return rel, construire(rel, _CACHE)
    except Exception as e:  # noqa: BLE001
        return rel, f"{type(e).__name__}: {e}"


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--test", action="store_true")
    g.add_argument("--pages", nargs="+")
    g.add_argument("--tout", action="store_true")
    ap.add_argument("--construire", action="store_true", help="sans API, depuis le cache")
    ap.add_argument("--section", nargs="+", default=["cpp", "c"], choices=["cpp", "c"])
    ap.add_argument("--paralleles", type=int, default=8)
    a = ap.parse_args()

    if a.test:
        pages = PAGES_TEST
    elif a.pages:
        pages = a.pages
    else:
        pages = [str(p.relative_to(EN)) for sec in a.section for p in sorted((EN / sec).rglob("*.html"))]

    con = db()
    # 1. segments uniques des pages demandées
    uniques: dict[str, None] = {}
    for rel in pages:
        for s in segments_de(rel)[1]:
            uniques.setdefault(s.markup)
    cache = deja_traduits(con, uniques)
    manquants = [u for u in uniques if u not in cache]
    print(f"{len(pages)} pages, {len(uniques)} segments uniques, "
          f"{len(cache)} déjà en cache, {len(manquants)} à traduire "
          f"({sum(map(len, manquants))/1e3:.0f} k car.)")

    # 2. traduction
    if manquants and not a.construire:
        cl = client()
        tous_echecs = []
        les_lots = list(lots(manquants))
        with ThreadPoolExecutor(a.paralleles) as pool:
            futs = [pool.submit(traduire_lot, cl, lot) for lot in les_lots]
            for n, f in enumerate(as_completed(futs), 1):
                ok, echecs = f.result()
                with verrou:
                    con.executemany("INSERT OR REPLACE INTO seg VALUES (?,?,?,datetime('now'))",
                                    [(k, v, MODELE) for k, v in ok.items()])
                    con.commit()
                cache.update(ok)
                tous_echecs += echecs
                cout = usage["in"] / 1e6 * PRIX_ENTREE + usage["out"] / 1e6 * PRIX_SORTIE
                print(f"\r  lot {n}/{len(les_lots)} — {usage['in']:,} tokens entrée, "
                      f"{usage['out']:,} sortie — {cout:.3f} $", end="", flush=True)
        print()
        if tous_echecs:
            with open(ECHECS, "a", encoding="utf-8") as f:
                for src, err in tous_echecs:
                    f.write(json.dumps({"en": src, "erreur": err}, ensure_ascii=False) + "\n")
        print(f"segments refusés (restés en anglais) : {len(tous_echecs)} → {ECHECS.name}")

    # 3. pages françaises
    total_f = total_s = 0
    erreurs_pages = []
    from multiprocessing import Pool
    with Pool(initializer=_init_cache, initargs=(cache,)) as pool:
        for rel, res in pool.imap_unordered(_construire_sur, pages, chunksize=10):
            if isinstance(res, str):
                erreurs_pages.append(f"{rel}: {res}")
            else:
                total_f += res[0]
                total_s += res[1]
    if erreurs_pages:
        (RACINE / "erreurs_pages.log").write_text("\n".join(erreurs_pages), encoding="utf-8")
        print(f"pages en erreur : {len(erreurs_pages)} → erreurs_pages.log")
    print(f"pages Markdown écrites dans {MD}/ : {total_f}/{total_s} segments en français")
    if usage["req"]:
        cout = usage["in"] / 1e6 * PRIX_ENTREE + usage["out"] / 1e6 * PRIX_SORTIE
        print(f"coût de cette exécution : {cout:.3f} $ ({usage['req']} requêtes)")


if __name__ == "__main__":
    main()
