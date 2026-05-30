/**
 * lightbox-init.js - GLightbox initialization (Story 2.5).
 *
 * Vanilla JS, IIFE, no global window pollution beyond GLightbox global,
 * no legacy DOM libs. Initializes GLightbox 3.x for all `.glightbox` selectors on
 * DOMContentLoaded; re-initializes on htmx:afterSwap to pick up new gallery
 * items from HTMX filter responses (Story 2.8 tractor listing, Story 2.13
 * search dropdown — out-of-scope here, but the contract honors them).
 *
 * Respects prefers-reduced-motion: disables open/close animations (per
 * EXPERIENCE.md § Animacije linija 271 — Lightbox fade-in 200ms ease, but
 * reduced-motion users see instant transition).
 *
 * Idempotency: stores instance on window._coricLightbox to prevent double-
 * init from competing scripts; reload() called on htmx:afterSwap for new
 * selectors.
 *
 * Emits coric:lightbox-open and coric:lightbox-close custom events on
 * window with detail.instance payload (per project-context.md § JavaScript
 * style — coric: namespace) so other modules can hook (e.g., pause auto-
 * advance slider while Lightbox is open — Story 2.6 testimonijal slider).
 */
(function () {
  'use strict';

  if (typeof window === 'undefined' || typeof document === 'undefined') {
    return;
  }
  if (typeof window.GLightbox !== 'function') {
    // GLightbox vendor script not loaded — bail silently. Tests AC2 + AC4
    // verify the script tag is present in base.html, but defensive guard
    // protects against vendor-asset 404 not breaking the page.
    return;
  }

  // i18n: <html lang> attribute is set by Story 1.4 LocaleMiddleware.
  // Maps locale to GLightbox "More" button text; fallback to sr.
  var MORE_TEXT = {
    sr: 'Vise',
    hu: 'Tobb',
    en: 'More'
  };

  function getLocale() {
    return (document.documentElement.lang || 'sr').slice(0, 2);
  }

  function buildOptions() {
    // Compute prefers-reduced-motion INSIDE buildOptions so each re-init
    // (htmx:afterSwap, matchMedia change) picks up the current OS preference.
    var prefersReducedMotion = window.matchMedia
      ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
      : false;

    return {
      selector: '.glightbox',
      touchNavigation: true,
      loop: false,
      zoomable: true,
      draggable: !prefersReducedMotion,
      openEffect: prefersReducedMotion ? 'none' : 'fade',
      closeEffect: prefersReducedMotion ? 'none' : 'fade',
      slideEffect: prefersReducedMotion ? 'none' : 'slide',
      moreText: MORE_TEXT[getLocale()] || MORE_TEXT.sr,
      descPosition: 'bottom',
      // Anti-CDN guard (Security review iter 1 — SEC-MEDIUM): GLightbox 3.3.1
      // vendor source ima hard-coded `cdn.plyr.io` URL-ove za video player.
      // Eksplicitan `plyr: false` neutralise tu code path — buduce stories
      // koje uvedu video lightbox NECE silently fetch-ovati sa third-party CDN.
      // Re-enable tek kad Plyr bude lokalno hostovan (future story).
      plyr: false
    };
  }

  // Defensive open-state check (Architect BUG #2): GLightbox 3.x dokumentuje
  // open()/close()/destroy()/reload() public methods, ali `instance.opened`
  // boolean NIJE u public API. Ako 4.x preimenuje property bez major-bump
  // warning-a, fallback na DOM-based proveru spreava da nam guard otkaze.
  function isLightboxOpen() {
    if (
      window._coricLightbox &&
      typeof window._coricLightbox.opened === 'boolean'
    ) {
      return window._coricLightbox.opened;
    }
    // Fallback: vendor renderuje `.glightbox-container.glightbox-open` dok
    // je modal vidljiv. Provera radi i kad je `_coricLightbox` null.
    return !!document.querySelector('.glightbox-container.glightbox-open');
  }

  // Helper za re-init sa zajednickim guard-om (Architect BUG #1 — DRY):
  // matchMedia `change` i htmx:afterSwap oba moraju respektovati open-modal
  // guard. Bez ovog wrapper-a, OS toggle reduced-motion preference-a dok je
  // Lightbox otvoren destroy-uje modal mid-interaction i orphan-uje focus
  // (krsi UX-DR-13 focus restoration contract).
  function safeReinit() {
    if (isLightboxOpen()) {
      return;
    }
    initLightbox();
  }

  function initLightbox() {
    // Idempotency: destroy previous instance before re-init (HTMX swap path).
    // typeof guard defensive — sprecava throw ako _coricLightbox ima neocekivan tip.
    if (
      typeof window._coricLightbox === 'object' &&
      window._coricLightbox &&
      typeof window._coricLightbox.destroy === 'function'
    ) {
      window._coricLightbox.destroy();
      window._coricLightbox = null;
    }
    var instance = window.GLightbox(buildOptions());
    window._coricLightbox = instance;

    // Custom events on window — coric: namespace per project-context.md.
    // Other modules (slider auto-advance pause, future analytics) can hook
    // to pause/resume during Lightbox open. detail.instance daje konzumentima
    // referencu na aktivni GLightbox instance (instance.getActiveSlideIndex?.()
    // pruza indeks trenutne slike).
    if (instance && typeof instance.on === 'function') {
      instance.on('open', function () {
        window.dispatchEvent(new CustomEvent('coric:lightbox-open', {
          detail: { instance: instance }
        }));
      });
      instance.on('close', function () {
        window.dispatchEvent(new CustomEvent('coric:lightbox-close', {
          detail: { instance: instance }
        }));
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLightbox);
  } else {
    initLightbox();
  }

  // HTMX integration: re-init after swap so new .glightbox elements work.
  // Listener is safe even if django-htmx is not in flight on this page
  // (event simply never fires). No tight coupling to django-htmx.
  document.body.addEventListener('htmx:afterSwap', function () {
    // PERF guard (Dev B review iter 1): preskoci re-init ako swap ne sadrzi
    // nijedan .glightbox element (npr. language switcher, OOB updates, Story
    // 2.13 search dropdown). Sprecava destroy+init churn na svakom HTMX swap-u.
    if (!document.querySelector('.glightbox')) {
      return;
    }
    // Open-modal guard: skip re-init ako je Lightbox otvoren — HTMX OOB updates
    // ne smeju yank-ovati fokus iz modal-a. Delegirano `safeReinit()` helper-u
    // koji deli isti guard sa matchMedia listener-om (DRY).
    safeReinit();
  });

  // Live-update on OS preference change (mirror sticky-nav.js pattern).
  // BUG #1 fix: koristi safeReinit() umesto direktnog initLightbox() — ako
  // korisnik toggle-uje reduced-motion preference DOK je modal otvoren, ne
  // destroy-uj modal mid-interaction (focus restoration safety per UX-DR-13).
  var motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
  if (motionQuery.addEventListener) {
    motionQuery.addEventListener('change', safeReinit);
  }
})();
