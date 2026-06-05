// Blog Copy-link — Story 5.3 (SM-D6). Vanilla JS (NIKAD jQuery).
// navigator.clipboard.writeText(share_url) na [data-share-copy] klik + aria-live najava.
(function () {
  "use strict";

  function announce(message) {
    var live = document.getElementById("aria-live");
    if (live) {
      live.textContent = message;
    }
  }

  function onCopyClick(event) {
    var button = event.currentTarget;
    var url = button.getAttribute("data-copy-url");
    if (!url || !navigator.clipboard || !navigator.clipboard.writeText) {
      return; // graceful no-op (stari browser / non-secure context)
    }
    navigator.clipboard.writeText(url).then(function () {
      var copied = button.getAttribute("data-copied-label") || "Link kopiran";
      announce(copied);
      document.dispatchEvent(
        new CustomEvent("coric:link-copied", { detail: { url: url } })
      );
    });
  }

  function init() {
    var buttons = document.querySelectorAll("[data-share-copy]");
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].addEventListener("click", onCopyClick);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
