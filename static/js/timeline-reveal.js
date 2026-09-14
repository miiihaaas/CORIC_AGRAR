/**
 * timeline-reveal.js — scroll-into-view reveal za „O nama" vremensku lentu (Story 3.2).
 *
 * Vanilla JS IIFE (mirror statistic-counter.js). DVA nezavisna IntersectionObserver-a:
 *   1) root observer — dodaje `.coric-is-revealed` na [data-timeline] SAM root
 *      (threshold 0.15) → about-page.css animira centralnu liniju da „raste" odozgo.
 *   2) segment observer — dodaje `.coric-is-revealed` SVAKOM [data-timeline-segment]
 *      NEZAVISNO dok ulazi u viewport (threshold 0.3) → kartice se otkrivaju jedna po
 *      jedna dok korisnik skroluje (standardni „scroll timeline" stagger), NE sve
 *      odjednom kad ceo blok uđe u view.
 *
 * NO-JS / graceful degradation: na init dodaje `coric-js` marker klasu na root —
 * about-page.css skriva segmente/liniju (opacity:0 / scaleY(0)) SAMO pod `.coric-js`
 * prefiksom, pa bez JS-a (ili ako se modul ne učita) sve ostaje PUNO vidljivo.
 *
 * prefers-reduced-motion: reduce → sve se odmah otkriva (instant, bez animacije).
 * IntersectionObserver fallback → sve odmah `.coric-is-revealed`.
 */
(function () {
  'use strict';

  if (typeof window === 'undefined' || typeof document === 'undefined') {
    return;
  }

  var timelineRoots = document.querySelectorAll('[data-timeline]');
  if (timelineRoots.length === 0) {
    return;
  }

  var prefersReducedMotion = window.matchMedia
    ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
    : false;

  function revealAll(root) {
    root.classList.add('coric-is-revealed');
    root.querySelectorAll('[data-timeline-segment]').forEach(function (segment) {
      segment.classList.add('coric-is-revealed');
    });
  }

  // Marker klasa gejtuje CSS hidden stanje — bez JS-a marker se NE dodaje → sve vidljivo.
  timelineRoots.forEach(function (root) {
    root.classList.add('coric-js');
  });

  if (prefersReducedMotion || !('IntersectionObserver' in window)) {
    timelineRoots.forEach(revealAll);
    return;
  }

  var rootObserver = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('coric-is-revealed');
        rootObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15 });

  var segmentObserver = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('coric-is-revealed');
        segmentObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.3 });

  timelineRoots.forEach(function (root) {
    rootObserver.observe(root);
    root.querySelectorAll('[data-timeline-segment]').forEach(function (segment) {
      segmentObserver.observe(segment);
    });
  });
})();
