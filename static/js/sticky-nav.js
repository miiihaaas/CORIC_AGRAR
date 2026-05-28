/**
 * sticky-nav.js - Sticky Navigation Shrink-on-Scroll (Story 1.8).
 *
 * Vanilla JS, IIFE, no global window pollution, no jQuery.
 * IntersectionObserver detects when scroll passes sentinel (~100px from top).
 * Toggles .coric-nav--shrunk on .coric-nav AND coric-nav-shrunk on body (D13).
 * Mobile bail via matchMedia + change listener (IMP-1).
 */
(function () {
  'use strict';

  if (typeof window === 'undefined' || !('IntersectionObserver' in window)) {
    return;
  }
  if (!('matchMedia' in window)) {
    return;
  }

  var nav = document.querySelector('.coric-nav');
  var sentinel = document.querySelector('.coric-sticky-sentinel');
  if (!nav || !sentinel) {
    return;
  }

  var mobileQuery = window.matchMedia('(max-width: 767px)');

  var observer = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        var isShrunk = !entry.isIntersecting;
        nav.classList.toggle('coric-nav--shrunk', isShrunk);
        document.body.classList.toggle('coric-nav-shrunk', isShrunk);
      });
    },
    { rootMargin: '0px', threshold: 0 }
  );

  function syncObserver() {
    if (mobileQuery.matches) {
      observer.disconnect();
      nav.classList.remove('coric-nav--shrunk');
      document.body.classList.remove('coric-nav-shrunk');
    } else {
      observer.observe(sentinel);
    }
  }

  syncObserver();
  mobileQuery.addEventListener('change', syncObserver);
})();
