#!/usr/bin/env bash
# Compile, lance et vérifie un exercice.
#
#   ./exercices/verifier.sh 0001-bonjour          C++ moderne (C++20)
#   ./exercices/verifier.sh 0001-bonjour --42     mode école 42 (C++98, comme les modules CPP)
#
# Dans le dossier de l'exercice :
#   *.cpp          vos fichiers sources (tous compilés ensemble)
#   entree.txt     (facultatif) ce qui est tapé au clavier pendant le programme
#   attendu.txt    (facultatif) la sortie exacte attendue
#   tests.cpp      (facultatif) des tests : compilés à la place de main.cpp avec vos autres fichiers
set -u

ROUGE=$'\e[31m'; VERT=$'\e[32m'; JAUNE=$'\e[33m'; GRAS=$'\e[1m'; FIN=$'\e[0m'
ici="$(cd "$(dirname "$0")" && pwd)"

if [ $# -lt 1 ]; then
  echo "Usage : $0 <dossier-exercice> [--42]"
  echo "Exercices disponibles :"; ls -1 "$ici" | grep -v '\.sh$' | sed 's/^/  /'
  exit 1
fi

dossier="$1"; [ -d "$dossier" ] || dossier="$ici/$1"
[ -d "$dossier" ] || { echo "${ROUGE}Exercice introuvable : $1${FIN}"; exit 1; }
mode42=0; [ "${2:-}" = "--42" ] && mode42=1

binaire="$(mktemp -d)/programme"
if [ $mode42 -eq 1 ]; then
  options=(-std=c++98 -Wall -Wextra -Werror -g)
  echo "${GRAS}Mode 42${FIN} : c++ ${options[*]}"
else
  options=(-std=c++20 -Wall -Wextra -Werror -pedantic -g)
  # Détecteurs d'erreurs mémoire (AddressSanitizer / UBSan), s'ils sont installés
  if echo 'int main(){}' | g++ -x c++ -fsanitize=address,undefined - -o /dev/null 2>/dev/null; then
    options+=(-fsanitize=address,undefined)
  else
    echo "${JAUNE}(Détecteurs d'erreurs mémoire absents. Pour les installer : sudo dnf install libasan libubsan)${FIN}"
  fi
fi

# Avec tests.cpp, on compile les tests à la place de main.cpp
mapfile -t sources < <(find "$dossier" -maxdepth 1 -name '*.cpp' | sort)
if [ -f "$dossier/tests.cpp" ]; then
  mapfile -t sources < <(printf '%s\n' "${sources[@]}" | grep -v '/main\.cpp$')
else
  mapfile -t sources < <(printf '%s\n' "${sources[@]}" | grep -v '/tests\.cpp$')
fi
[ ${#sources[@]} -gt 0 ] || { echo "${ROUGE}Aucun fichier .cpp dans $dossier${FIN}"; exit 1; }

echo "${GRAS}1. Compilation${FIN} (${sources[*]##*/})"
if ! g++ "${options[@]}" -I"$dossier" "${sources[@]}" -o "$binaire"; then
  echo
  echo "${ROUGE}✗ La compilation a échoué.${FIN} Lisez la PREMIÈRE erreur en haut : c'est souvent elle la vraie cause."
  exit 1
fi
echo "${VERT}✓ Compilé sans erreur ni avertissement${FIN}"

echo "${GRAS}2. Exécution${FIN}"
sortie="$(mktemp)"
if [ -f "$dossier/entree.txt" ]; then
  timeout 10 "$binaire" < "$dossier/entree.txt" > "$sortie" 2>&1; code=$?
else
  timeout 10 "$binaire" < /dev/null > "$sortie" 2>&1; code=$?
fi
cat "$sortie"
if [ $code -eq 124 ]; then echo "${ROUGE}✗ Le programme ne s'arrête pas (plus de 10 s) : boucle infinie ?${FIN}"; exit 1; fi
if [ $code -ne 0 ]; then echo "${ROUGE}✗ Le programme s'est terminé avec le code $code${FIN} (plantage ou erreur détectée)"; exit 1; fi

if [ -f "$dossier/attendu.txt" ]; then
  echo "${GRAS}3. Comparaison avec la sortie attendue${FIN}"
  if diff -u --label attendu --label "votre programme" "$dossier/attendu.txt" "$sortie"; then
    echo "${VERT}${GRAS}✓ Réussi ! La sortie est exactement celle attendue.${FIN}"
  else
    echo "${JAUNE}✗ La sortie diffère : lignes « - » attendues, lignes « + » obtenues.${FIN}"
    exit 1
  fi
else
  echo "${VERT}✓ Le programme s'exécute sans erreur.${FIN}"
fi
