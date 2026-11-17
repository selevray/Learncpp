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

  /* Thème
   * Firefox donne à chaque fichier file:// son propre localStorage : le choix
   * enregistré sur une page n'est pas visible depuis les autres. Le thème voyage
   * donc aussi dans l'URL (?theme=dark) à chaque lien interne suivi. */
  const cle = "apprendre-cpp-theme";
  const valide = (t) => t === "light" || t === "dark";
  let theme = new URLSearchParams(location.search).get("theme");
  if (!valide(theme)) {
    try { theme = localStorage.getItem(cle); } catch (e) { theme = null; }
  }
  if (valide(theme)) {
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem(cle, theme); } catch (e) {}
  }

  /* Ajoute ?theme=… à une adresse interne (même protocole, page .html). */
  function lienAvecTheme(href) {
    const t = document.documentElement.dataset.theme;
    if (!valide(t)) return href;
    let url;
    try { url = new URL(href, location.href); } catch (e) { return href; }
    if (url.protocol !== location.protocol || !url.pathname.endsWith(".html")) return href;
    url.searchParams.set("theme", t);
    return url.href;
  }

  function propagerTheme() {
    const surLien = (e) => {
      const a = e.target.closest && e.target.closest("a[href]");
      if (a && !a.getAttribute("href").startsWith("#")) a.href = lienAvecTheme(a.href);
    };
    document.addEventListener("click", surLien, true);
    document.addEventListener("auxclick", surLien, true); // clic molette : nouvel onglet
    document.addEventListener("submit", (e) => {
      const f = e.target;
      if (!valide(document.documentElement.dataset.theme) || f.method !== "get") return;
      if (lienAvecTheme(f.action) === f.action) return; // formulaire externe
      let champ = f.querySelector('input[name="theme"]');
      if (!champ) {
        champ = document.createElement("input");
        champ.type = "hidden";
        champ.name = "theme";
        f.append(champ);
      }
      champ.value = document.documentElement.dataset.theme;
    }, true);
  }

  function basculerTheme() {
    const sombre = document.documentElement.dataset.theme
      ? document.documentElement.dataset.theme === "dark"
      : matchMedia("(prefers-color-scheme: dark)").matches;
    const nouveau = sombre ? "light" : "dark";
    document.documentElement.dataset.theme = nouveau;
    try { localStorage.setItem(cle, nouveau); } catch (e) {}
    themeHljs();
  }

  /* Les feuilles highlight.js suivent le thème choisi (data-theme),
     et seulement à défaut la préférence du système. */
  function themeHljs() {
    const clair = document.getElementById("hljs-clair");
    const sombre = document.getElementById("hljs-sombre");
    if (!clair || !sombre) return;
    const t = document.documentElement.dataset.theme;
    clair.media = t ? (t === "light" ? "all" : "not all") : "(prefers-color-scheme: light)";
    sombre.media = t ? (t === "dark" ? "all" : "not all") : "(prefers-color-scheme: dark)";
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
      css.id = "hljs-clair";
      const cssSombre = document.createElement("link");
      cssSombre.rel = "stylesheet";
      cssSombre.href = "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css";
      cssSombre.id = "hljs-sombre";
      document.head.append(css, cssSombre);
      themeHljs();
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

  /* Pour les pages qui gèrent leur propre barre (recherche.html). */
  window.ApprendreCpp = { basculerTheme, lienAvecTheme };

  function init() {
    propagerTheme();
    if (!document.body.hasAttribute("data-sans-barre")) {
      ajouterBarre();
      raccourciRecherche();
    }
    colorer(document);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
