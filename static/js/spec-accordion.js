/**
 * spec-accordion.js — smooth expand/collapse za <details> spec akordeone
 * (product-detail specifikacije + brand-page extended layout).
 *
 * Vanilla JS IIFE (isti obrazac kao testimonials-slider.js). Web Animations API
 * animira `height` na CELOM <details> elementu (summary + telo), open atribut se
 * postavlja NA POČETKU otvaranja / NA KRAJU zatvaranja — čist pandan poznatom
 * "Animating to height: auto" details/summary receptu.
 *
 * ZAŠTO OVDE JS a ne čisti CSS (grid-template-rows 0fr→1fr trik): taj trik radi
 * pouzdano SAMO na prvom toggle-u u nekim Chromium verzijama — nakon prvog
 * ciklusa otvori/zatvori, naredne tranzicije postaju trenutne (poznata flakiness
 * kombinacije <details> native toggle-a + grid-track interpolacije). WAAPI na
 * `height` je pouzdanija cross-browser tehnika za baš ovaj slučaj.
 *
 * Respektuje prefers-reduced-motion: reduce (native instant toggle, bez JS
 * intercept-a uopšte — nema animate() poziva).
 */
(function () {
  'use strict';

  if (typeof window === 'undefined' || typeof document === 'undefined') return;
  if (typeof Element === 'undefined' || !Element.prototype.animate) return;

  var prefersReducedMotion = window.matchMedia
    ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
    : false;
  if (prefersReducedMotion) return;

  var DURATION_MS = 300;
  var EASING = 'ease';
  var SELECTOR =
    '.coric-product-specs__accordion, .coric-product-row__accordion';

  document.querySelectorAll(SELECTOR).forEach(function (details) {
    var summary = details.querySelector(':scope > summary');
    if (!summary) return;

    var animation = null;
    var isClosing = false;
    var isExpanding = false;

    summary.addEventListener('click', function (event) {
      event.preventDefault();
      details.style.overflow = 'hidden';

      if (isClosing || !details.open) {
        expand();
      } else if (isExpanding || details.open) {
        collapse();
      }
    });

    function collapse() {
      isClosing = true;
      var startHeight = details.offsetHeight + 'px';
      var endHeight = summary.offsetHeight + 'px';
      if (animation) animation.cancel();
      animation = details.animate(
        { height: [startHeight, endHeight] },
        { duration: DURATION_MS, easing: EASING }
      );
      animation.onfinish = function () { onFinish(false); };
      animation.oncancel = function () { isClosing = false; };
    }

    function expand() {
      details.style.height = details.offsetHeight + 'px';
      details.open = true;
      window.requestAnimationFrame(grow);
    }

    function grow() {
      isExpanding = true;
      var startHeight = details.offsetHeight + 'px';
      // scrollHeight na <details> uključuje summary + telo (open je već true u
      // ovom trenutku, posle expand()-a) — direktan cilj, bez ručnog sabiranja.
      var endHeight = details.scrollHeight + 'px';
      if (animation) animation.cancel();
      animation = details.animate(
        { height: [startHeight, endHeight] },
        { duration: DURATION_MS, easing: EASING }
      );
      animation.onfinish = function () { onFinish(true); };
      animation.oncancel = function () { isExpanding = false; };
    }

    function onFinish(open) {
      details.open = open;
      animation = null;
      isClosing = false;
      isExpanding = false;
      details.style.height = '';
      details.style.overflow = '';
    }
  });
})();
