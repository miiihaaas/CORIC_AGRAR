/**
 * tractor-filters.js — Range slider init + HTMX dispatch (Story 2.8).
 *
 * Vanilla JS IIFE. Inicijalizuje noUiSlider widget na svakom [data-range-slider]
 * container-u; on slider change, sync-uje hidden input vrednosti + visible display
 * + dispatch-uje input event na hidden input (HTMX hx-trigger="input changed
 * delay:300ms, change delay:300ms" picks up coalesced event per 300ms).
 *
 * Behaviors:
 * - SM-D20 A11Y-S: handleAttributes config sa aria-label-min/max iz data attrs
 * - SM-D19 URL: toggleDisabledForDefaults — disable inputs na default extremes
 *   za clean URL bez empty params
 * - SM-D21 HIST: htmx:historyRestore listener za widget re-init posle back-button
 * - RED fix N4: animate: !prefersReducedMotion (instant thumb pozicija ako
 *   korisnik preferira reduced motion)
 */
(function () {
  'use strict';

  if (typeof window === 'undefined' || typeof document === 'undefined') {
    return;
  }

  var prefersReducedMotion = window.matchMedia
    ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
    : false;

  function toggleDisabledForDefaults(container) {
    var minInput = container.querySelector('[data-range-min-input]');
    var maxInput = container.querySelector('[data-range-max-input]');
    if (!minInput || !maxInput) return;
    var defaultMin = parseFloat(container.dataset.min);
    var defaultMax = parseFloat(container.dataset.max);
    var currentMin = parseFloat(minInput.value);
    var currentMax = parseFloat(maxInput.value);
    // SM-D19 — clean URL hygiene: disabled inputs su skipped u form serialization
    minInput.disabled = !isNaN(currentMin) && currentMin === defaultMin;
    maxInput.disabled = !isNaN(currentMax) && currentMax === defaultMax;
  }

  function initRangeSlider(container) {
    if (typeof window.noUiSlider === 'undefined') return;

    var track = container.querySelector('.coric-range-slider__track');
    var minInput = container.querySelector('[data-range-min-input]');
    var maxInput = container.querySelector('[data-range-max-input]');
    var minDisplay = container.querySelector('[data-range-value-min]');
    var maxDisplay = container.querySelector('[data-range-value-max]');
    if (!track || !minInput || !maxInput) return;

    var min = parseFloat(container.dataset.min) || 0;
    var max = parseFloat(container.dataset.max) || 100;
    var step = parseFloat(container.dataset.step) || 1;
    var startMin = parseFloat(container.dataset.valueMin);
    var startMax = parseFloat(container.dataset.valueMax);
    if (isNaN(startMin)) startMin = min;
    if (isNaN(startMax)) startMax = max;

    var ariaMin = container.dataset.ariaLabelMin || 'Minimum';
    var ariaMax = container.dataset.ariaLabelMax || 'Maksimum';

    window.noUiSlider.create(track, {
      start: [startMin, startMax],
      connect: true,
      range: { min: min, max: max },
      step: step,
      animate: !prefersReducedMotion,
      handleAttributes: [
        { 'aria-label': ariaMin },
        { 'aria-label': ariaMax }
      ]
    });

    track.noUiSlider.on('update', function (values) {
      var newMin = Math.round(parseFloat(values[0]));
      var newMax = Math.round(parseFloat(values[1]));
      // Re-enable inputs pre value assignment-a (disabled blocks .value updates u nekim browserima)
      minInput.disabled = false;
      maxInput.disabled = false;
      minInput.value = newMin;
      maxInput.value = newMax;
      if (minDisplay) minDisplay.textContent = newMin;
      if (maxDisplay) maxDisplay.textContent = newMax;
      toggleDisabledForDefaults(container);
    });

    track.noUiSlider.on('change', function () {
      // Trigger HTMX hx-trigger="input changed" pickup
      minInput.dispatchEvent(new Event('input', { bubbles: true }));
    });
  }

  function init() {
    var sliders = document.querySelectorAll('[data-range-slider]');
    sliders.forEach(initRangeSlider);
  }

  function handleHistoryRestore() {
    // SM-D21 HIST — refresh slider state from refreshed hidden inputs after popstate
    document.querySelectorAll('[data-range-slider]').forEach(function (container) {
      var track = container.querySelector('.coric-range-slider__track');
      if (track && track.noUiSlider) {
        var minInput = container.querySelector('[data-range-min-input]');
        var maxInput = container.querySelector('[data-range-max-input]');
        var newMin = parseFloat(minInput.value);
        var newMax = parseFloat(maxInput.value);
        if (isNaN(newMin)) newMin = parseFloat(container.dataset.min);
        if (isNaN(newMax)) newMax = parseFloat(container.dataset.max);
        track.noUiSlider.set([newMin, newMax]);
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  document.body && document.body.addEventListener('htmx:historyRestore', handleHistoryRestore);
})();
