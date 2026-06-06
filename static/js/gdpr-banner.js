/* ============================================================================
 * gdpr-banner.js — Story 7.2 GDPR consent banner progressive enhancement (AC7)
 *
 * Vanilla IIFE ('use strict'). Mirror search-expand.js konvencija.
 *
 * Ponašanje (AC7 + SM-D10):
 * - on-show: fokus na baner ROOT ([data-coric-gdpr-banner] sa tabindex="-1").
 *   Pinovan root-focus (NE prvo dugme).
 * - Esc SAMO kad je fokus UNUTAR banera (banner.contains(document.activeElement))
 *   → trigger „Odbij sve" submit. NIKAD globalni document Esc — baner je
 *   non-modal i na svakoj strani, pa bi globalni Esc okidao reject iz search/
 *   forme (CRITICAL-4/G-14).
 * - BEZ focus-trap (aria-modal="false").
 * - prefers-reduced-motion se rešava u CSS-u (JS ne forsira transform).
 * - opciono coric:consent-set custom event na submit.
 * - PROGRESSIVE ENHANCEMENT: baner radi BEZ JS (plain form POST → server
 *   redirect-back). JS je SAMO a11y/UX sloj.
 *
 * NAPOMENA: JS-runtime ponašanje je manual smoke / Playwright Story 9.8 — NE
 * pytest. Pytest asertuje samo statički markup hooks + eksterni script tag.
 * ========================================================================= */

(function () {
  'use strict';

  function init() {
    var banner = document.querySelector('[data-coric-gdpr-banner]');
    if (!banner) {
      return;
    }

    var form = banner.querySelector('form');

    // on-show: fokus na baner root (tabindex="-1" u template-u).
    banner.focus();

    function submitReject() {
      if (!form) {
        return;
      }
      var rejectButton = form.querySelector(
        'button[name="action"][value="reject_all"]'
      );
      if (rejectButton) {
        rejectButton.click();
      } else {
        form.submit();
      }
    }

    // Esc gate-ovan na focus-within-banner (NE globalno; CRITICAL-4).
    banner.addEventListener('keydown', function (event) {
      if (event.key !== 'Escape' && event.key !== 'Esc') {
        return;
      }
      if (!banner.contains(document.activeElement)) {
        return;
      }
      event.preventDefault();
      submitReject();
    });

    // opciono: signal da je consent postavljen (drugi skriptovi mogu da slušaju).
    if (form) {
      form.addEventListener('submit', function () {
        banner.dispatchEvent(
          new CustomEvent('coric:consent-set', { bubbles: true })
        );
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
