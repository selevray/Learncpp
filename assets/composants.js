/* Composants communs à toutes les pages.
 *
 * Utilisation dans une page :
 *   <link rel="stylesheet" href="../assets/style.css">
 *   <script src="../assets/composants.js" defer></script>
 *
 * Fournit :
 *   - une barre en haut avec retour à l'accueil et recherche (touche « / » pour y aller) ;
 *   - un bouton pour changer de thème clair / sombre ;
 *   - le composant <conseil-claude titre="Piège classique"> … </conseil-claude>,
 *     qui affiche un bouton « 💡 Conseil Claude » ouvrant une fenêtre pop-up ;
 *   - la coloration syntaxique du code C++.
 */
(function () {
  const script = document.currentScript;
  const racine = script ? script.src.replace(/assets\/composants\.js.*$/, "") : "./";

  /* Thème */
  const cle = "apprendre-cpp-theme";
  try {
    const t = localStorage.getItem(cle);
    if (t) document.documentElement.dataset.theme = t;
  } catch (e) {}

  function basculerTheme() {
    const sombre = document.documentElement.dataset.theme
      ? document.documentElement.dataset.theme === "dark"
      : matchMedia("(prefers-color-scheme: dark)").matches;
    const nouveau = sombre ? "light" : "dark";
    document.documentElement.dataset.theme = nouveau;
    try { localStorage.setItem(cle, nouveau); } catch (e) {}
  }

  /* Conseil Claude */
  class ConseilClaude extends HTMLElement {
    connectedCallback() {
      if (this._pret) return;
      this._pret = true;
      const titre = this.getAttribute("titre") || "Conseil de pro";
      const contenu = this.innerHTML;
      this.innerHTML = "";

      const bouton = document.createElement("button");
      bouton.type = "button";
      bouton.className = "conseil-btn";
      bouton.innerHTML = '<span class="badge">💡 Conseil Claude</span>' +
        '<span class="titre"></span><span class="ouvrir">ouvrir ›</span>';
      bouton.querySelector(".titre").textContent = titre;

      const dlg = document.createElement("dialog");
      dlg.className = "conseil";
      dlg.innerHTML = '<header><strong>💡 Conseil Claude</strong><span class="t"></span>' +
        '<button type="button" aria-label="Fermer">×</button></header><div class="contenu"></div>';
      dlg.querySelector(".t").textContent = "· " + titre;
      dlg.querySelector(".contenu").innerHTML = contenu;
      dlg.querySelector("header button").addEventListener("click", () => dlg.close());
      dlg.addEventListener("click", (e) => { if (e.target === dlg) dlg.close(); });
      bouton.addEventListener("click", () => dlg.showModal());

      this.append(bouton, dlg);
      colorer(dlg);
    }
  }
  if (!customElements.get("conseil-claude")) customElements.define("conseil-claude", ConseilClaude);

  /* Barre du haut */
  function ajouterBarre() {
    if (document.body.hasAttribute("data-sans-barre")) return;
    const barre = document.createElement("nav");
    barre.className = "barre";
    barre.innerHTML =
      '<a class="maison" href="' + racine + 'recherche.html">🏠 Apprendre le C++</a>' +
      '<form action="' + racine + 'recherche.html" method="get" role="search">' +
      '<input type="search" name="q" placeholder="Rechercher une notion… (touche /)" aria-label="Rechercher"></form>' +
      '<button type="button" class="theme-btn" title="Thème clair / sombre">◐</button>';
    barre.querySelector(".theme-btn").addEventListener("click", basculerTheme);
    document.body.prepend(barre);
  }

  function raccourciRecherche() {
    document.addEventListener("keydown", (e) => {
      if (e.key !== "/" || e.ctrlKey || e.metaKey) return;
      const cible = e.target;
      if (cible && (cible.tagName === "INPUT" || cible.tagName === "TEXTAREA" || cible.isContentEditable)) return;
      const champ = document.querySelector('input[type="search"]');
      if (champ) { e.preventDefault(); champ.focus(); champ.select(); }
    });
  }

  /* Coloration syntaxique (highlight.js, chargé à la demande) */
  let hljsPromesse = null;
  function chargerHljs() {
    if (hljsPromesse) return hljsPromesse;
    hljsPromesse = new Promise((ok) => {
      const css = document.createElement("link");
      css.rel = "stylesheet";
      css.href = "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css";
      css.media = "(prefers-color-scheme: light)";
      const cssSombre = document.createElement("link");
      cssSombre.rel = "stylesheet";
      cssSombre.href = "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css";
      cssSombre.media = "(prefers-color-scheme: dark)";
      document.head.append(css, cssSombre);
      const s = document.createElement("script");
      s.src = "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js";
      s.onload = () => ok(window.hljs);
      s.onerror = () => ok(null); // hors ligne : le code reste lisible sans couleurs
      document.head.append(s);
    });
    return hljsPromesse;
  }
  function colorer(racineDom) {
    const blocs = (racineDom || document).querySelectorAll("pre code");
    if (!blocs.length) return;
    chargerHljs().then((hljs) => {
      if (!hljs) return;
      blocs.forEach((b) => {
        if (!b.className.includes("language-")) b.classList.add("language-cpp");
        if (!b.dataset.highlighted) hljs.highlightElement(b);
      });
    });
  }

  function init() {
    ajouterBarre();
    raccourciRecherche();
    colorer(document);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
