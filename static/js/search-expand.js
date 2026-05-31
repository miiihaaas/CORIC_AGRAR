/* ============================================================================
 * search-expand.js — Story 2.13 global search expand/collapse + a11y (AC5/AC9)
 *
 * Vanilla IIFE ('use strict'). Mirror Story 2.6/2.8 module konvencija.
 *
 * Ponašanje (AC5 + AC9):
 * - klik na [data-search-toggle] → toggle #coric-search-panel hidden + sync
 *   aria-expanded; on-open fokus na [data-search-input]; slide-in kroz CSS
 *   (prefers-reduced-motion: reduce → instant, JS ne forsira transform).
 * - Esc kad panel otvoren → close + fokus return na [data-search-toggle].
 * - klik van panela i toggle-a → close.
 * - ArrowDown/ArrowUp kad dropdown ima role="option" → roving aria-selected;
 *   Enter → navigira na selektovan option href.
 * - aria-expanded UVEK sinhronizovan sa panel visibility.
 *
 * NAPOMENA: JS-runtime ponašanje je manual smoke / Playwright Story 9.8 — NE pytest
 * (interface-contract § 9). Pytest asertuje samo statički ARIA markup.
 * ========================================================================= */

(function () {
  'use strict';

  var SELECTED_CLASS = 'coric-search-dropdown__option--selected';

  function init() {
    var toggle = document.querySelector('[data-search-toggle]');
    var panel = document.getElementById('coric-search-panel');
    if (!toggle || !panel) {
      return;
    }

    var input = panel.querySelector('[data-search-input]');
    var resultsContainer = panel.querySelector('#coric-search-results');

    function isOpen() {
      return !panel.hasAttribute('hidden');
    }

    function openPanel() {
      panel.removeAttribute('hidden');
      toggle.setAttribute('aria-expanded', 'true');
      if (input) {
        input.focus();
      }
    }

    function closePanel(returnFocus) {
      panel.setAttribute('hidden', '');
      toggle.setAttribute('aria-expanded', 'false');
      clearSelection();
      if (returnFocus) {
        toggle.focus();
      }
    }

    function togglePanel() {
      if (isOpen()) {
        closePanel(true);
      } else {
        openPanel();
      }
    }

    function getOptions() {
      if (!resultsContainer) {
        return [];
      }
      return Array.prototype.slice.call(
        resultsContainer.querySelectorAll('[role="option"]')
      );
    }

    function clearSelection() {
      getOptions().forEach(function (opt) {
        opt.setAttribute('aria-selected', 'false');
        opt.classList.remove(SELECTED_CLASS);
      });
    }

    function selectedIndex(options) {
      for (var i = 0; i < options.length; i += 1) {
        if (options[i].getAttribute('aria-selected') === 'true') {
          return i;
        }
      }
      return -1;
    }

    function moveSelection(delta) {
      var options = getOptions();
      if (!options.length) {
        return;
      }
      var current = selectedIndex(options);
      var next = current + delta;
      if (next < 0) {
        next = options.length - 1;
      } else if (next >= options.length) {
        next = 0;
      }
      clearSelection();
      options[next].setAttribute('aria-selected', 'true');
      options[next].classList.add(SELECTED_CLASS);
    }

    function activateSelection() {
      var options = getOptions();
      var current = selectedIndex(options);
      if (current === -1) {
        return false;
      }
      var link = options[current].querySelector('a[href]');
      if (link) {
        window.location.assign(link.getAttribute('href'));
        return true;
      }
      return false;
    }

    // --- Toggle click ---
    toggle.addEventListener('click', function (event) {
      event.preventDefault();
      togglePanel();
    });

    // --- Keyboard (Esc, Arrow nav, Enter) ---
    document.addEventListener('keydown', function (event) {
      if (!isOpen()) {
        return;
      }
      if (event.key === 'Escape' || event.key === 'Esc') {
        event.preventDefault();
        closePanel(true);
        return;
      }
      if (event.key === 'ArrowDown') {
        event.preventDefault();
        moveSelection(1);
      } else if (event.key === 'ArrowUp') {
        event.preventDefault();
        moveSelection(-1);
      } else if (event.key === 'Enter') {
        if (activateSelection()) {
          event.preventDefault();
        }
      }
    });

    // --- Click outside ---
    document.addEventListener('click', function (event) {
      if (!isOpen()) {
        return;
      }
      var target = event.target;
      if (panel.contains(target) || toggle.contains(target)) {
        return;
      }
      closePanel(false);
    });

    // HTMX swap-uje rezultate u #coric-search-results — reset selection na svaki swap.
    if (resultsContainer) {
      resultsContainer.addEventListener('htmx:afterSwap', clearSelection);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
