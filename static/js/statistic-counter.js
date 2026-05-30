/**
 * statistic-counter.js — count-up animacija za 4-medallion grid (Story 2.6).
 *
 * Vanilla JS IIFE. Pri scroll-into-view (IntersectionObserver), animira tekst
 * svakog [data-count-target] elementa od 0 do target vrednosti.
 * Respektuje prefers-reduced-motion: reduce (instant set).
 */
(function () {
  'use strict';

  if (typeof window === 'undefined' || typeof document === 'undefined') {
    return;
  }

  var counterRoots = document.querySelectorAll('[data-statistic-counters]');
  if (counterRoots.length === 0) {
    return;
  }

  var prefersReducedMotion = window.matchMedia
    ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
    : false;

  function animateCounter(el) {
    var target = parseInt(el.getAttribute('data-count-target'), 10);
    var duration = parseInt(el.getAttribute('data-count-duration') || '1500', 10);
    if (isNaN(target)) return;

    if (prefersReducedMotion) {
      el.textContent = target.toString();
      return;
    }

    var startTime = null;
    function step(timestamp) {
      if (!startTime) startTime = timestamp;
      var progress = Math.min((timestamp - startTime) / duration, 1);
      var eased = 1 - Math.pow(1 - progress, 3);
      var current = Math.round(target * eased);
      el.textContent = current.toString();
      if (progress < 1) {
        window.requestAnimationFrame(step);
      }
    }
    window.requestAnimationFrame(step);
  }

  if (!('IntersectionObserver' in window)) {
    counterRoots.forEach(function (root) {
      root.querySelectorAll('[data-count-target]').forEach(animateCounter);
    });
    return;
  }

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.querySelectorAll('[data-count-target]').forEach(animateCounter);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.3 });

  counterRoots.forEach(function (root) {
    observer.observe(root);
  });
})();
