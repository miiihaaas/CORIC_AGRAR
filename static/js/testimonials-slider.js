/**
 * testimonials-slider.js — testimonijal slider sa pause/play + keyboard nav (Story 2.6).
 *
 * Vanilla JS IIFE. Auto-advance svakih [data-autoadvance-ms] ms (default 6000).
 * Pauzira na focus/hover/manual interaction; resume na focusout/mouseleave ako
 * nije manualno pauziran. Sluša coric:lightbox-open/close eventove (Story 2.5).
 * Respektuje prefers-reduced-motion: reduce (NEMA auto-advance).
 */
(function () {
  'use strict';

  if (typeof window === 'undefined' || typeof document === 'undefined') return;

  var sliders = document.querySelectorAll('[data-testimonials-slider]');
  if (sliders.length === 0) return;

  var prefersReducedMotion = window.matchMedia
    ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
    : false;

  sliders.forEach(function (slider) {
    var slides = slider.querySelectorAll('.coric-testimonials-slider__slide');
    if (slides.length < 2) {
      var controls = slider.querySelector('.coric-testimonials-slider__controls');
      if (controls) controls.style.display = 'none';
      return;
    }

    var current = 0;
    var manuallyPaused = false;
    var autoTimer = null;
    var autoMs = parseInt(slider.getAttribute('data-autoadvance-ms') || '6000', 10);
    var live = slider.querySelector('[data-slider-live]');
    var pauseBtn = slider.querySelector('[data-slider-pause]');

    function showSlide(idx) {
      slides.forEach(function (s, i) {
        var active = i === idx;
        s.classList.toggle('is-active', active);
        s.setAttribute('aria-hidden', active ? 'false' : 'true');
      });
      current = idx;
      if (live) {
        live.textContent = (idx + 1) + ' / ' + slides.length;
      }
    }

    function next() { showSlide((current + 1) % slides.length); }
    function prev() { showSlide((current - 1 + slides.length) % slides.length); }

    function startAuto() {
      if (prefersReducedMotion || manuallyPaused) return;
      stopAuto();
      autoTimer = window.setInterval(next, autoMs);
    }
    function stopAuto() {
      if (autoTimer) { window.clearInterval(autoTimer); autoTimer = null; }
    }

    var prevBtn = slider.querySelector('[data-slider-prev]');
    var nextBtn = slider.querySelector('[data-slider-next]');
    if (prevBtn) prevBtn.addEventListener('click', function () { stopAuto(); prev(); });
    if (nextBtn) nextBtn.addEventListener('click', function () { stopAuto(); next(); });

    if (pauseBtn) {
      pauseBtn.addEventListener('click', function () {
        manuallyPaused = !manuallyPaused;
        pauseBtn.setAttribute('aria-pressed', manuallyPaused ? 'true' : 'false');
        pauseBtn.textContent = manuallyPaused ? '▶' : '⏸';
        if (manuallyPaused) { stopAuto(); } else { startAuto(); }
      });
    }

    slider.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowLeft') { e.preventDefault(); stopAuto(); prev(); }
      if (e.key === 'ArrowRight') { e.preventDefault(); stopAuto(); next(); }
    });

    slider.addEventListener('focusin', stopAuto);
    slider.addEventListener('focusout', startAuto);
    slider.addEventListener('mouseenter', stopAuto);
    slider.addEventListener('mouseleave', startAuto);

    window.addEventListener('coric:lightbox-open', stopAuto);
    window.addEventListener('coric:lightbox-close', startAuto);

    showSlide(0);
    startAuto();
  });
})();
