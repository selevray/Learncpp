"""Mesure le volume à traduire (segments uniques) et teste l'aller-retour.

    .venv/bin/python outils/mesurer.py [cpp|c]
"""
import re
import sys
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import segments as S  # noqa: E402

RACINE = Path(__file__).resolve().parent.parent
EN = RACINE / "source" / "reference" / "en"


def visible_text(soup):
    root = soup.find(id="mw-content-text")
    return re.sub(r"\s+", " ", root.get_text(" ")).strip() if root else ""


def traiter(path):
    soup = S.load(path)
    avant = visible_text(soup)
    segs = S.extract(soup)
    erreurs = []
    # aller-retour « identité » : réinsérer le texte source tel quel
    for s in segs:
        try:
            S.apply(s, s.markup, soup)
        except Exception as e:  # noqa: BLE001
            erreurs.append(f"{type(e).__name__}: {e}")
    apres = visible_text(soup)
    norm = lambda t: re.sub(r"\s+", "", t)  # noqa: E731
    if norm(avant) != norm(apres):
        erreurs.append("le texte visible a changé après l'aller-retour")
    return str(path.relative_to(EN)), [(s.markup, s.navbar) for s in segs], erreurs


def main():
    section = sys.argv[1] if len(sys.argv) > 1 else "cpp"
    pages = sorted((EN / section).rglob("*.html"))
    total = Counter()
    uniques: dict[str, bool] = {}
    pages_ko = []
    with Pool() as pool:
        for rel, segs, err in pool.imap_unordered(traiter, pages, chunksize=20):
            for m, nav in segs:
                total["segments"] += 1
                total["car"] += len(m)
                uniques.setdefault(m, nav)
            if err:
                pages_ko.append((rel, err[:2]))
    car_u = sum(len(m) for m in uniques)
    car_nav = sum(len(m) for m, nav in uniques.items() if nav)
    print(f"pages : {len(pages)}")
    print(f"segments : {total['segments']}  ({total['car']/1e6:.1f} M car. avec doublons)")
    print(f"segments uniques : {len(uniques)}  ({car_u/1e6:.2f} M car., dont navigation {car_nav/1e6:.2f} M)")
    print(f"pages avec erreur d'aller-retour : {len(pages_ko)}")
    for rel, err in pages_ko[:15]:
        print("  ", rel, err)


if __name__ == "__main__":
    main()
