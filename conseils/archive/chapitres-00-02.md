# Conseils Claude : chapitres 0 à 2

Format : chaque conseil commence par une ligne
`@@@ <slug de la leçon> | <titre exact de la section où le placer> | <titre du conseil>`
suivie du contenu en Markdown. Le conseil est inséré à la fin de la section indiquée.
Si la section n'est pas trouvée, il est placé à la fin de la leçon.

@@@ introduction-to-these-tutorials | Tirer le meilleur parti de ces tutoriels | Tapez le code, ne le copiez pas
Recopier les exemples **à la main**, même quand c'est long, est l'une des habitudes qui font le plus progresser au début. En tapant, vous remarquez chaque point-virgule, chaque accolade, et vos doigts apprennent la syntaxe.

Ensuite, **cassez** volontairement le code : enlevez un `;`, changez un nom, et regardez l'erreur que donne le compilateur. Vous apprendrez à reconnaître les messages d'erreur avant d'en avoir vraiment besoin.

@@@ introduction-to-these-tutorials | Tirer le meilleur parti de ces tutoriels | Bien utiliser Claude pendant le cours
Quand un passage n'est pas clair, demandez-moi de **l'expliquer autrement** : avec une analogie, un schéma, ou un exemple plus simple. C'est là que l'IA est la plus utile.

Évitez en revanche de me demander d'écrire le code des exercices : vous auriez l'impression de comprendre, mais vous ne sauriez pas le refaire seul. Demandez plutôt un **indice**, puis réessayez.

@@@ introduction-to-programming-languages | Introduction aux langages de haut niveau | Voir le langage machine de vos propres programmes
Le site [Compiler Explorer](https://godbolt.org/) affiche, à côté de votre code C++, les instructions d'assembleur que le compilateur produit. Collez-y une petite fonction comme `int carre(int x) { return x * x; }` : vous verrez concrètement ce que veut dire « traduire un langage de haut niveau en langage machine ».

Pas besoin de comprendre l'assembleur : regardez juste combien d'instructions il faut pour une seule ligne de C++.

@@@ introduction-to-cplusplus | La philosophie du C et du C++ | C et C++ à l'école 42
Le tronc commun de 42 commence en **C** (libft, printf, get_next_line…), et les modules **C++** arrivent ensuite. Tout ce que vous apprenez ici sur les variables, les fonctions, les pointeurs ou la compilation vous servira aussi en C.

Attention par contre à ne pas mélanger les styles : en C++, on évite les habitudes du C comme `printf`, `malloc`/`free` ou les chaînes `char*`. Les modules C++ de 42 interdisent d'ailleurs en général `printf`, `malloc` et `free` (vérifiez toujours le sujet).

@@@ introduction-to-cpp-development | Étape 2 : déterminer comment vous allez résoudre le problème | Écrire la solution en français d'abord
Avant de taper la moindre ligne de code, écrivez la solution **en français**, sous forme de commentaires :

```cpp
// 1. demander un nombre à l'utilisateur
// 2. le multiplier par 2
// 3. afficher le résultat
```

Puis remplacez chaque commentaire par le code correspondant. Les développeurs expérimentés le font aussi, surtout quand le problème est nouveau pour eux. Si vous n'arrivez pas à l'écrire en français, c'est que le problème n'est pas encore clair : le code ne vous aidera pas.

@@@ introduction-to-the-compiler-linker-and-libraries | Étape 5 : éditer les liens entre les fichiers objets et les bibliothèques, puis créer le fichier de sortie souhaité | Voir les étapes de la compilation avec g++
La commande `g++ main.cpp -o programme` fait toutes les étapes d'un coup, mais vous pouvez les séparer pour les voir :

```
g++ -c main.cpp           # compile seulement : produit main.o (fichier objet)
g++ main.o -o programme   # édition des liens : produit l'exécutable
./programme               # lance le programme
```

Retenez la différence entre les deux types d'erreurs : une erreur avec `error:` et un numéro de ligne vient du **compilateur** (votre code est mal écrit). Une erreur `undefined reference to ...` vient de l'**éditeur de liens** (une fonction est déclarée mais introuvable). Vous rencontrerez souvent la seconde dans le chapitre 2.

@@@ installing-an-integrated-development-environment-ide | Choisir un IDE | Sous Linux, pas besoin d'un gros IDE
Vous êtes sous Linux : un éditeur de texte et le terminal suffisent largement pour apprendre, et c'est exactement l'environnement de l'école 42 (terminal, `make`, VS Code ou vim).

Un bon choix : **VS Code avec l'extension clangd**. Elle souligne les erreurs pendant que vous tapez, avant même de compiler. Compilez quand même dans le terminal avec `./exercices/verifier.sh` : savoir compiler sans IDE est une compétence que l'on vous demandera.

@@@ compiling-your-first-program | Si vous utilisez g++ en ligne de commande | La commande à retenir
Dans cet espace d'apprentissage, compilez toujours avec les options strictes :

```
g++ -std=c++20 -Wall -Wextra -Werror -g main.cpp -o programme
```

- `-Wall -Wextra` : active les avertissements utiles ;
- `-Werror` : transforme chaque avertissement en erreur (obligatoire à 42) ;
- `-g` : ajoute les informations nécessaires au débogueur.

Le script `./exercices/verifier.sh` lance déjà cette commande pour vous, puis vérifie la sortie de votre programme.

@@@ compiling-your-first-program | Si la compilation échoue | Ne lisez que la première erreur
Quand la compilation échoue, le compilateur peut afficher des dizaines de lignes. **Corrigez seulement la première erreur**, puis recompilez : les suivantes en sont souvent des conséquences et disparaîtront d'elles-mêmes.

Chaque erreur indique `fichier:ligne:colonne`. Si la ligne indiquée semble correcte, regardez **la ligne juste au-dessus** : un `;` oublié n'est souvent détecté qu'à la ligne suivante.

@@@ a-few-common-cpp-problems | Problèmes généraux à la compilation | Chercher un message d'erreur efficacement
Quand une erreur vous bloque, copiez la partie **générique** du message dans un moteur de recherche, sans vos noms de variables ni vos chemins de fichiers. Par exemple, cherchez `error: expected ';' before 'return'` plutôt que tout le message avec `/home/...`.

Vous pouvez aussi me coller le message complet en me demandant ce qu'il **signifie**, sans me demander la correction : vous apprendrez à le lire vous-même.

@@@ configuring-your-compiler-build-configurations | Changer de configuration de compilation | Debug et release avec g++
Avec g++, il n'y a pas de bouton « Debug » ou « Release » : ce sont simplement des options.

- **Debug** (pour apprendre et chercher les bugs) : `-g -O0`, le programme correspond exactement à votre code, ligne par ligne.
- **Release** (pour la version finale, plus rapide) : `-O2`, le compilateur réorganise le code pour l'optimiser.

Pendant tout l'apprentissage, restez en debug : un bug qui n'apparaît qu'en release est presque toujours un **comportement indéfini** dans votre code (vous verrez ce terme en leçon 1.6).

@@@ configuring-your-compiler-compiler-extensions | Désactiver les extensions du compilateur | Le piège des tableaux de taille variable
L'extension de g++ la plus piégeuse pour un débutant : elle accepte `int tab[n];` où `n` est une variable. Ce n'est **pas** du C++ standard, et un autre compilateur (ou un correcteur à 42) le refusera.

Ajoutez `-pedantic-errors` pour que g++ refuse toutes ses extensions :

```
g++ -std=c++20 -Wall -Wextra -Werror -pedantic-errors main.cpp
```

@@@ configuring-your-compiler-warning-and-error-levels | Augmenter les niveaux d'avertissement | Trois avertissements en plus qui valent le coup
En plus de `-Wall -Wextra`, ces options attrapent des bugs fréquents chez les débutants :

- `-Wshadow` : une variable locale porte le même nom qu'une autre variable et la « cache » ;
- `-Wconversion` : une conversion implicite peut perdre de l'information (par exemple un `double` rangé dans un `int`) ;
- `-Wsign-conversion` : mélange de nombres signés et non signés.

Ils ne sont pas exigés à 42, mais si votre code compile avec, il compilera partout.

@@@ configuring-your-compiler-choosing-a-language-standard | Quelle norme du langage choisir ? | C++20 ici, C++98 à 42
Ce cours enseigne le C++ moderne (C++17 et C++20). Mais les modules C++ de 42 imposent **C++98**, une version de 1998 qui ne connaît pas beaucoup de choses que vous allez apprendre :

- l'initialisation avec accolades `int x{ 5 };` (utilisez `int x = 5;`) ;
- `auto`, `nullptr`, `constexpr` et la boucle `for (int x : tableau)`.

Pas de panique : apprenez le C++ moderne, et vérifiez votre code avec `./exercices/verifier.sh <exercice> --42`. Le compilateur vous dira précisément ce qui n'existe pas en C++98. Les Conseils Claude signaleront ces différences au fil du cours.

@@@ what-language-standard-is-my-compiler-using | Problèmes de compilation ou d'exécution | Essayez avec -std=c++98
Compilez le programme de cette leçon deux fois, avec `-std=c++20` puis avec `-std=c++98`, et comparez les valeurs affichées. Avec C++98, la macro `__cplusplus` vaut `199711`.

C'est une bonne façon de vérifier que votre compilateur utilise bien la norme demandée par un sujet de 42.

@@@ statements-and-the-structure-of-a-program | Fonctions et la fonction `main` | main renvoie toujours un int
Vous verrez parfois sur Internet `void main()`. C'est **faux** en C++ : `main` doit renvoyer un `int`, et g++ refusera de compiler. Le nombre renvoyé est transmis au système : `0` signifie « tout s'est bien passé ».

Dans le terminal, après avoir lancé un programme, tapez `echo $?` pour voir la valeur renvoyée par son `main`.

@@@ statements-and-the-structure-of-a-program | Syntaxe et erreurs de syntaxe | Faites l'erreur exprès
Prenez le programme « Hello world » et provoquez volontairement les erreurs les plus courantes, une par une :

- enlevez le `;` après `std::cout << ...` ;
- écrivez `std::cout` sans le `#include <iostream>` ;
- oubliez l'accolade fermante de `main`.

Notez à chaque fois le message obtenu. Le jour où l'erreur arrivera par accident, vous la reconnaîtrez immédiatement.

@@@ comments | Bon usage des commentaires | Expliquer le pourquoi, pas le quoi
Un bon commentaire explique **pourquoi** le code fait quelque chose, car le code dit déjà **ce qu'il fait**.

```cpp
x = x + 1; // ajoute 1 à x                      ← inutile
x = x + 1; // on compte à partir de 1, pas de 0 ← utile
```

Une habitude de développeur : si vous avez besoin d'un long commentaire pour expliquer un bout de code, c'est souvent que le code peut être réécrit plus clairement, par exemple avec des noms de variables plus parlants.

@@@ comments | Mettre du code en commentaire | Le raccourci de l'éditeur
Dans la plupart des éditeurs (VS Code, Code::Blocks…), le raccourci **Ctrl + /** met en commentaire ou décommente les lignes sélectionnées. Très pratique pour désactiver temporairement un bout de code et voir si le bug vient de là.

N'oubliez pas de supprimer le code commenté une fois le problème trouvé : un fichier plein de vieux code commenté devient vite illisible.

@@@ introduction-to-objects-and-variables | Définition de plusieurs variables | Une variable par ligne
Même si `int a, b, c;` est autorisé, les développeurs expérimentés préfèrent **une définition par ligne** :

```cpp
int largeur{ 0 };
int hauteur{ 0 };
```

C'est plus lisible, chaque variable peut avoir son propre commentaire, et on évite des pièges que vous découvrirez avec les pointeurs (`int* a, b;` ne déclare qu'un seul pointeur).

@@@ variable-assignment-and-initialization | L'initialisation par liste est la forme privilégiée en C++ moderne | Attention : les accolades n'existent pas en C++98
L'initialisation avec accolades `int x{ 5 };` est apparue en C++11. Elle est recommandée en C++ moderne, mais **elle ne compile pas en C++98**, la norme imposée par les modules C++ de 42.

Pour les projets de 42, écrivez `int x = 5;` (initialisation par copie). Le principe le plus important reste le même dans les deux cas : **toujours initialiser ses variables**.

@@@ variable-assignment-and-initialization | Initialisez vos variables | Une règle sans exception au début
Prenez le réflexe de **donner une valeur à chaque variable au moment où vous la créez**, même si vous la changerez juste après (`int x{ 0 };` ou `int x{};`).

Une variable non initialisée contient une valeur imprévisible. Le programme peut sembler fonctionner pendant des semaines, puis afficher n'importe quoi le jour où la mémoire contient autre chose. C'est l'un des bugs les plus difficiles à trouver pour un débutant.

@@@ introduction-to-iostream-cout-cin-and-endl | `std::endl` contre `\n` | Quand le texte n'apparaît pas
Si votre programme plante, le texte affiché avec `'\n'` juste avant le plantage peut ne **jamais apparaître**, car il était encore dans le tampon (buffer) de `std::cout`.

Quand vous cherchez où un programme plante en ajoutant des affichages, utilisez `std::cerr` à la place de `std::cout` : il n'a pas de tampon, le texte s'affiche immédiatement.

```cpp
std::cerr << "arrivé ici, x = " << x << '\n';
```

@@@ introduction-to-iostream-cout-cin-and-endl | Le processus d'extraction de base | Que se passe-t-il si on tape des lettres ?
Testez ce programme en tapant `abc` au lieu d'un nombre :

```cpp
int x{};
std::cin >> x;
std::cout << "Vous avez tapé " << x << '\n';
```

`std::cin` n'arrive pas à lire un nombre : il met `x` à `0` et passe en **état d'échec**, et toutes les lectures suivantes échouent aussi. Ne vous inquiétez pas pour l'instant, la leçon 9.5 explique comment gérer ce cas. Retenez juste qu'un vrai programme doit toujours se méfier de ce que tape l'utilisateur.

@@@ uninitialized-variables-and-undefined-behavior | Comportement indéfini | Faire détecter le comportement indéfini
Deux outils détectent automatiquement beaucoup de comportements indéfinis à l'exécution :

- **les sanitizers** de g++ : compilez avec `-fsanitize=address,undefined` (sous Fedora, il faut d'abord `sudo dnf install libasan libubsan`). Le script `verifier.sh` les active dès qu'ils sont installés ;
- **valgrind**, très utilisé à 42 : `valgrind ./programme` (installation : `sudo dnf install valgrind`).

Un programme qui « marche » n'est pas forcément correct : le comportement indéfini peut rester caché jusqu'au jour où il casse tout.

@@@ keywords-and-naming-identifiers | Bonnes pratiques de nommage des identificateurs | Un nom doit répondre à une question
Un bon nom de variable dit **ce que contient** la variable, sans avoir à lire le reste du code :

```cpp
int n;                  // n quoi ?
int nombreDeJoueurs;    // clair
```

Choisissez une convention (`nombreDeJoueurs` ou `nombre_de_joueurs`) et gardez-la dans tout le projet. Pour les noms, l'anglais est la norme dans le monde professionnel, et souvent attendu à 42 : prenez l'habitude dès vos premiers projets personnels.

@@@ whitespace-and-basic-formatting | Mise en forme automatique | Laisser un outil formater votre code
L'outil **clang-format** remet en forme un fichier automatiquement (indentation, espaces, accolades) :

```
sudo dnf install clang-tools-extra
clang-format -i main.cpp
```

Dans VS Code, le raccourci **Ctrl + Maj + I** fait la même chose. Vous ne perdez plus de temps sur la mise en page, et votre code reste lisible pour les autres.

@@@ introduction-to-literals-and-operators | Valeurs de retour et effets de bord | Le piège = au lieu de ==
`=` affecte une valeur, `==` compare deux valeurs. Confondre les deux est l'une des erreurs les plus fréquentes :

```cpp
if (x = 5)   // affecte 5 à x : la condition est toujours vraie !
if (x == 5)  // compare x à 5
```

Bonne nouvelle : avec `-Wall -Werror`, g++ refuse de compiler la première ligne (avertissement `-Wparentheses`). C'est une bonne raison de toujours compiler avec ces options.

@@@ introduction-to-expressions | Instructions d'expression inutiles | Laissez le compilateur relire votre code
Une instruction comme `x + 2;` (dont le résultat n'est utilisé nulle part) est presque toujours une erreur : vous vouliez sans doute écrire `x = x + 2;`.

Avec `-Wall`, g++ signale ce genre d'instruction (`statement has no effect`). Les avertissements du compilateur sont un relecteur gratuit qui ne se fatigue jamais : lisez-les toujours, même quand le programme compile.

@@@ developing-your-first-program | La solution préférée | Compiler souvent, par petits pas
Les débutants écrivent souvent tout le programme d'un coup, puis se retrouvent face à vingt erreurs. Les développeurs expérimentés font l'inverse : ils écrivent **quelques lignes, compilent, testent**, puis continuent.

Une erreur apparue juste après avoir ajouté trois lignes se trouve forcément dans ces trois lignes. C'est la technique de débogage la plus efficace qui existe.

@@@ chapter-1-summary-and-quiz | Quiz | Refaire le quiz plus tard
Faites ce quiz une première fois maintenant, puis **refaites-le dans quelques jours sans relire le chapitre**. Se souvenir après un délai est bien plus efficace pour retenir que relire le cours plusieurs fois.

Vous pouvez aussi demander à Claude de vous interroger sur les notions vues il y a quelque temps.

@@@ introduction-to-functions | Appeler une fonction plusieurs fois | Une fonction, une seule tâche
Une bonne fonction fait **une seule chose**, et son nom le dit clairement. Si vous avez envie de l'appeler `lireEtAfficherEtCalculer`, c'est qu'elle devrait être découpée en trois fonctions.

Des petites fonctions bien nommées rendent `main` lisible comme une recette :

```cpp
int main()
{
    int valeur{ lireNombre() };
    afficherDouble(valeur);
}
```

@@@ function-return-values-value-returning-functions | Codes de statut | Voir le code de retour dans le terminal
Après avoir lancé un programme, la commande `echo $?` affiche la valeur renvoyée par son `main` :

```
./programme
echo $?
```

Les scripts et les outils (comme `make`) utilisent ce code pour savoir si un programme a réussi (`0`) ou échoué (autre valeur). Le script `verifier.sh` s'en sert aussi pour détecter un plantage.

@@@ function-return-values-value-returning-functions | Une fonction renvoyant une valeur qui ne renvoie pas de valeur produit un comportement indéfini | Un avertissement à ne jamais ignorer
Si une fonction qui doit renvoyer une valeur peut se terminer sans `return`, g++ affiche l'avertissement `control reaches end of non-void function`.

Avec `-Werror`, il devient une erreur, et c'est tant mieux : sans lui, le programme compilerait mais renverrait une valeur imprévisible, un bug très difficile à trouver.

@@@ void-functions-non-value-returning-functions | Les fonctions void n'ont pas besoin d'instruction return | Nommer une fonction avec un verbe
Une fonction fait une action : donnez-lui un nom qui commence par un **verbe**. `afficherScore()`, `lireNombre()`, `calculerMoyenne()` se comprennent tout de suite, alors que `score()` ou `nombre()` laissent un doute : est-ce que la fonction affiche, calcule ou modifie quelque chose ?

@@@ introduction-to-function-parameters-and-arguments | Paramètres non référencés et paramètres sans nom | Le paramètre inutilisé
Avec `-Wextra`, un paramètre jamais utilisé déclenche l'avertissement `unused parameter`, donc une erreur avec `-Werror`. Pendant que vous écrivez une fonction, ça arrive souvent.

Plutôt que de désactiver l'avertissement, terminez la fonction ou commentez le nom du paramètre comme le montre la leçon : `void f(int /*valeur*/)`. Cette syntaxe compile aussi en C++98.

@@@ introduction-to-local-scope | Où définir les variables locales | Le piège des variables qui se cachent
Si une variable locale porte le même nom qu'une autre variable visible (un paramètre, une variable d'un bloc englobant), elle la **cache** : vous croyez modifier l'une, vous modifiez l'autre.

L'option `-Wshadow` de g++ détecte ce piège. Ajoutez-la à vos commandes de compilation : elle se déclenche rarement à tort.

@@@ why-functions-are-useful-and-how-to-use-them-effectively | Pourquoi utiliser des fonctions ? | Quelle longueur pour une fonction ?
Une règle simple : une fonction devrait tenir **sur un écran**, sans faire défiler. Au-delà, elle fait probablement plusieurs choses à la fois.

Autre signal : si vous copiez-collez un bloc de code pour le réutiliser, c'est qu'il devrait devenir une fonction. Le jour où il faudra corriger un bug dans ce bloc, vous n'aurez à le faire qu'à un seul endroit.

@@@ forward-declarations | Oublier le corps de la fonction | Lire « undefined reference to »
Le message `undefined reference to 'ajouter(int, int)'` ne vient pas du compilateur mais de l'**éditeur de liens** : la fonction est déclarée, donc le compilateur accepte l'appel, mais sa définition est introuvable.

Les causes les plus fréquentes :

- la fonction n'est définie nulle part ;
- elle est définie dans un autre fichier `.cpp` que vous n'avez pas ajouté à la commande de compilation ;
- la déclaration et la définition ne correspondent pas exactement (types des paramètres différents).

@@@ programs-with-multiple-code-files | Quelque chose s'est mal passé ! | Compiler plusieurs fichiers avec g++ et make
Avec g++, il faut donner **tous** les fichiers `.cpp` dans la commande :

```
g++ -std=c++20 -Wall -Wextra -Werror main.cpp add.cpp -o programme
```

À 42, chaque exercice doit être livré avec un **Makefile** qui contient au moins les règles `all`, `clean`, `fclean` et `re`. Un Makefile retient la commande de compilation et ne recompile que les fichiers modifiés. Vous apprendrez à en écrire un quand vos projets auront plusieurs fichiers.

@@@ naming-collisions-and-an-introduction-to-namespaces | Utiliser using namespace std (et pourquoi l'éviter) | using namespace est interdit à 42
En plus des raisons données dans la leçon, les sujets des modules C++ de 42 interdisent en général `using namespace`, sous peine d'échec du projet (vérifiez toujours le sujet). Prenez donc tout de suite l'habitude d'écrire `std::cout`, `std::string`, etc.

Au bout de quelques jours, taper `std::` devient automatique, et votre code est plus clair : on voit immédiatement ce qui vient de la bibliothèque standard.

@@@ introduction-to-the-preprocessor | Macros de type objet avec texte de substitution | Préférez une constante à #define
Pour une valeur constante, préférez une vraie variable constante à une macro :

```cpp
#define MAX_JOUEURS 4          // à éviter
constexpr int maxJoueurs{ 4 }; // C++ moderne
const int maxJoueurs = 4;      // C++98 (pour 42)
```

Une constante a un type, respecte la portée, et apparaît dans le débogueur. Une macro est un simple remplacement de texte fait avant la compilation, avec des pièges que le compilateur ne peut pas détecter.

@@@ introduction-to-the-preprocessor | #include | Voir ce que fait le préprocesseur
L'option `-E` de g++ arrête la compilation juste après le préprocesseur et affiche le résultat :

```
g++ -E main.cpp | tail -20
```

Vous verrez que `#include <iostream>` a été remplacé par des dizaines de milliers de lignes ! C'est la meilleure façon de comprendre que `#include` copie-colle littéralement le contenu d'un fichier.

@@@ header-files | Les fichiers source doivent inclure leur en-tête associé | Organisation des fichiers à 42
Dans les modules C++ de 42, chaque classe va en général dans deux fichiers : `Nom.hpp` pour les déclarations et `Nom.cpp` pour les définitions. Vous pouvez dès maintenant utiliser l'extension `.hpp` pour vos en-têtes C++ : elle indique clairement qu'il s'agit de C++ et non de C.

Le principe vu dans cette leçon reste le même : `Nom.cpp` inclut `Nom.hpp`, et tout fichier qui utilise la classe inclut `Nom.hpp`, jamais `Nom.cpp`.

@@@ header-files | Dépannage | Le piège de « ça marchait chez moi »
Si votre code utilise `std::string` sans `#include <string>`, il peut compiler chez vous parce que `<iostream>` inclut `<string>` en cachette (inclusion transitive). Mais sur un autre compilateur, ou sur la machine d'un correcteur à 42, il peut échouer.

Règle simple : **incluez l'en-tête de tout ce que vous utilisez**, même si ça compile sans.

@@@ header-guards | #pragma once | Utilisez les gardes classiques pour 42
`#pragma once` est pratique, mais ne fait pas partie de la norme C++. Pour vos projets de 42, utilisez les gardes d'en-tête classiques, nommées d'après le fichier :

```cpp
#ifndef JOUEUR_HPP
#define JOUEUR_HPP

// déclarations

#endif
```

Les sujets de 42 exigent en général que chaque en-tête soit protégé contre la double inclusion. Prenez l'habitude d'écrire ces trois lignes avant tout le reste, à chaque nouveau fichier `.hpp`.

@@@ how-to-design-your-first-programs | Étape 4 de conception : décomposer les problèmes difficiles en problèmes faciles | Si c'est encore difficile, découpez encore
Un bon test : chaque petite tâche doit pouvoir s'écrire en **5 à 15 lignes de code**. Si vous ne voyez pas comment l'écrire, ce n'est pas que vous êtes mauvais : c'est que la tâche n'est pas encore assez découpée.

« Faire un jeu de morpion » est trop gros. « Afficher une grille de 3 × 3 cases vides » est parfait pour commencer.

@@@ how-to-design-your-first-programs | Conseils pour l'écriture de programmes | Sauvegardez avec git
Avant d'avoir un programme qui fonctionne, prenez l'habitude d'utiliser **git** : chaque fois qu'une étape marche, enregistrez-la (`git add .` puis `git commit -m "affiche la grille"`). Si vous cassez tout ensuite, vous pouvez revenir à la dernière version qui marchait.

À 42, tous les projets sont rendus avec git : autant apprendre en douceur dès vos premiers programmes.

@@@ chapter-2-summary-and-quiz | Temps du quiz | Mini-projet pour ancrer le chapitre
Avant de passer au chapitre suivant, écrivez un petit programme **réparti en trois fichiers** (`main.cpp`, `calculs.cpp`, `calculs.hpp`) : il demande deux nombres et affiche leur somme, leur différence et leur produit, chaque opération étant une fonction.

Compilez-le sans regarder le cours. Si vous y arrivez, vous maîtrisez les fonctions, les en-têtes, les gardes d'en-tête et la compilation multi-fichiers : les bases de tous les projets de 42.
