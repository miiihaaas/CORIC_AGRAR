/* Story 8.7 — Minimalni vanilla-JS WYSIWYG za blog Post.body (SM-D2 GRANA B).
 *
 * Progressive enhancement IZNAD plain <textarea class="wysiwyg" data-wysiwyg>:
 * ako JS otkaže/ne učita, admin i dalje radi (Marijana piše HTML/plain u textarea,
 * save prolazi). 0 dep, NIKAD jQuery, no build-pipeline (project-context HARD).
 *
 * Toolbar je BOUNDED na tagove unutar nh3 allowlist-a (apps.core.sanitize):
 *   bold, italic, h2/h3/h4, link, ul, ol.  NIKAD img/iframe/div/span/style (XSS/strip).
 *
 * Sanitizacija je NEZAVISNA render-time odbrana (nh3) — ovaj editor je čisto UX.
 * Bind preko addEventListener (CSP-friendlier — OQ-5 forward), bez inline onclick.
 */
(function () {
  "use strict";

  var COMMANDS = [
    { label: "B", title: "Podebljano", cmd: "bold" },
    { label: "I", title: "Kurziv", cmd: "italic", style: "font-style:italic" },
    { label: "H2", title: "Naslov 2", cmd: "formatBlock", arg: "h2" },
    { label: "H3", title: "Naslov 3", cmd: "formatBlock", arg: "h3" },
    { label: "H4", title: "Naslov 4", cmd: "formatBlock", arg: "h4" },
    { label: "• Lista", title: "Nabrajanje", cmd: "insertUnorderedList" },
    { label: "1. Lista", title: "Numerisana lista", cmd: "insertOrderedList" },
    { label: "Link", title: "Ubaci link", cmd: "createLink" },
  ];

  function enhance(textarea) {
    if (textarea.dataset.wysiwygReady === "true") {
      return;
    }
    textarea.dataset.wysiwygReady = "true";

    var wrapper = document.createElement("div");
    wrapper.className = "wysiwyg-wrapper";

    var toolbar = document.createElement("div");
    toolbar.className = "wysiwyg-toolbar";

    var editable = document.createElement("div");
    editable.className = "wysiwyg-editable";
    editable.setAttribute("contenteditable", "true");
    editable.style.minHeight = "200px";
    editable.style.border = "1px solid #ccc";
    editable.style.padding = "8px";
    editable.style.background = "#fff";
    editable.innerHTML = textarea.value || "";

    COMMANDS.forEach(function (c) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = c.label;
      btn.title = c.title;
      if (c.style) {
        btn.setAttribute("style", c.style);
      }
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        editable.focus();
        if (c.cmd === "createLink") {
          var url = window.prompt("Unesite URL (http/https/mailto):", "https://");
          if (url) {
            document.execCommand("createLink", false, url);
          }
        } else if (c.arg) {
          document.execCommand(c.cmd, false, c.arg);
        } else {
          document.execCommand(c.cmd, false, null);
        }
        sync();
      });
      toolbar.appendChild(btn);
    });

    function sync() {
      textarea.value = editable.innerHTML;
    }

    editable.addEventListener("input", sync);
    editable.addEventListener("blur", sync);

    // Sakrij raw textarea ali ga zadrži u DOM-u (form submit nosi njegovu vrednost).
    textarea.style.display = "none";
    textarea.parentNode.insertBefore(wrapper, textarea);
    wrapper.appendChild(toolbar);
    wrapper.appendChild(editable);
    wrapper.appendChild(textarea);

    // Sinhronizuj pre submit-a (osiguranje ako blur nije okinuo).
    var form = textarea.closest("form");
    if (form) {
      form.addEventListener("submit", sync);
    }
  }

  function init() {
    var fields = document.querySelectorAll("textarea.wysiwyg, textarea[data-wysiwyg]");
    Array.prototype.forEach.call(fields, enhance);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
