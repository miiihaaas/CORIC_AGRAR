/**
 * timeline-reveal.js — scroll-into-view reveal za „O nama" vremensku lentu (Story 3.2).
 *
 * Vanilla JS IIFE (mirror statistic-counter.js). Pri ulasku [data-timeline] root-a u
 * vidno polje (IntersectionObserver, threshold 0.3) dodaje `.coric-is-revealed` segmentima
 * (CSS animira opacity+transform 800ms ease-in-out).
 *
 * NO-JS / graceful degradation: na init dodaje `coric-js` marker klasu na root —
 * about-page.css skriva segmente (opacity:0) SAMO pod `.coric-js` prefiksom, pa bez
 * JS-a (ili ako se modul ne učita) segmenti ostaju PUNO vidljivi.
 *
 * prefers-reduced-motion: reduce → segmenti se odmah otkrivaju (instant, bez animacije).
 * IntersectionObserver fallback → svi segmenti odmah `.coric-is-revealed`.
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

  function revealRoot(root) {
    var segments = root.querySelectorAll('[data-timeline-segment]');
    segments.forEach(function (segment) {
      segment.classList.add('coric-is-revealed');
    });
  }

  // Marker klasa gejtuje CSS hidden stanje — bez JS-a marker se NE dodaje → segmenti vidljivi.
  timelineRoots.forEach(function (root) {
    root.classList.add('coric-js');
  });

  if (prefersReducedMotion) {
    timelineRoots.forEach(revealRoot);
    return;
  }

  if (!('IntersectionObserver' in window)) {
    timelineRoots.forEach(revealRoot);
    return;
  }

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        revealRoot(entry.target);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.3 });

  timelineRoots.forEach(function (root) {
    observer.observe(root);
  });
})();
