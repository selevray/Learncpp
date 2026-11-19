"""Repère les traductions suspectes dans traductions.sqlite.

    .venv/bin/python outils/verifier.py            # résumé + exemples
    .venv/bin/python outils/verifier.py --tout     # écrit tout dans suspects.jsonl

Contrôles (en plus de ceux faits à la traduction) :
- restee_anglais  : la traduction contient encore des mots anglais courants
- identique       : traduction == source alors que la source est une vraie phrase
- longueur        : rapport de longueur français/anglais anormal
- glossaire       : terme anglais traduit autrement que dans le glossaire
- bavardage       : le modèle a ajouté un commentaire (« Voici », « Note : »…)
"""
import html
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DB = RACINE / "traductions.sqlite"
SORTIE = RACINE / "suspects.jsonl"

MOTS_ANGLAIS = {"the", "is", "are", "of", "and", "which", "that", "with", "from",
                "this", "if", "when", "returns", "otherwise", "must", "be", "an",
                "for", "not", "only", "used", "behavior", "function", "value"}
# terme anglais -> forme(s) française(s) attendue(s)
GLOSSAIRE = {
    r"(?<!non-)\bmember functions?\b": ["fonction membre", "fonctions membres", "fonctions non membres", "fonction non membre"],
    r"\bundefined behaviou?r\b": ["comportement indéfini"],
    r"\bfunction templates?\b": ["modèle de fonction", "modèles de fonction"],
    r"\bclass templates?\b": ["modèle de classe", "modèles de classe"],
    r"\biterators?\b": ["itérateur"],
    r"\bcontainers?\b": ["conteneur"],
    r"\bnamespaces?\b": ["espace de noms", "espaces de noms"],
    r"\bmove constructors?\b": ["déplacement"],
    r"\bcopy constructors?\b": ["constructeur de copie", "constructeurs de copie"],
    r"\bill-formed\b": ["mal formé"],
    r"\bsmart pointers?\b": ["pointeur intelligent", "pointeurs intelligents"],
}
BAVARDAGE = re.compile(r"^(Voici|Traduction|Note ?:|Remarque ?:)|\(traduction|\btranslated\b", re.I)


def texte(m: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", " ", m))


def mots(t: str):
    return re.findall(r"[A-Za-zÀ-ÿ']+", t)


def analyser(en: str, fr: str):
    pbs = []
    te, tf = texte(en), texte(fr)
    me = [w.lower() for w in mots(te)]
    mf = [w.lower() for w in mots(tf)]
    code = len(re.findall(r"[;=(){}<>&]|::|->", te)) >= 2
    if len(me) >= 4 and en == fr and not code:
        pbs.append("identique")
    elif len(mf) >= 6:
        ang = sum(1 for w in mf if w in MOTS_ANGLAIS)
        if ang / len(mf) > 0.15:
            pbs.append("restee_anglais")
    le, lf = len(te.strip()), len(tf.strip())
    if le >= 40 and not (0.6 <= lf / le <= 2.2):
        pbs.append("longueur")
    tfl = tf.lower()
    for motif, attendus in GLOSSAIRE.items():
        if re.search(motif, te, re.I) and not any(a in tfl for a in attendus):
            # l'anglais peut être resté dans un nom propre ou du code : on tolère
            if not re.search(motif, tf, re.I):
                pbs.append("glossaire:" + motif.strip("\\b").split("\\")[0])
    if BAVARDAGE.search(tf.strip()) and not BAVARDAGE.search(te.strip()):
        pbs.append("bavardage")
    return pbs


def main():
    con = sqlite3.connect(DB)
    lignes = con.execute("SELECT en, fr FROM seg").fetchall()
    stats = Counter()
    exemples = defaultdict(list)
    sortie = open(SORTIE, "w", encoding="utf-8") if "--tout" in sys.argv else None
    for en, fr in lignes:
        pbs = analyser(en, fr)
        for p in pbs:
            cat = p.split(":")[0]
            stats[cat] += 1
            if len(exemples[cat]) < 6:
                exemples[cat].append((en, fr, p))
        if pbs and sortie:
            sortie.write(json.dumps({"en": en, "fr": fr, "pb": pbs}, ensure_ascii=False) + "\n")
    print(f"{len(lignes)} segments traduits")
    for cat, n in stats.most_common():
        print(f"\n== {cat} : {n}")
        for en, fr, p in exemples[cat]:
            print(f"  [{p}]\n    EN: {en[:200]}\n    FR: {fr[:200]}")
    if sortie:
        print(f"\ndétails : {SORTIE}")


if __name__ == "__main__":
    main()
