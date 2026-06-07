"""Story 7.5 — `{{ value|legal_html }}` render-time XSS sanitizacija filter.

TREĆI tag/filter-modul u apps.core (uz `htmx_aria.py` / `i18n_fallback.py`).
Sanitizuje rich-text pravni `body` NA RENDER-u (PRIMARNA XSS granica; SM-D3) i
vraća `mark_safe(...)` SAMO POSLE sanitizacije.

⚠️ G-6 (safe-markiranje TEK posle sanitizacije): filter markira kao bezbedan
ISKLJUČIVO izlaz `sanitize_legal_html(...)` — NIKAD sirovu ulaznu vrednost. Razlika
od zabranjenog `|`-safe filtera (koji bi markirao SIROV body → stored-XSS):
`|legal_html` JESTE sanitizacija koju je 7-1/7-4 presedan odlagao. Mirror 6-x:
safe-markiranje pokriva VEĆ-sanitizovan/sklopljen sadržaj.

Statički guard test (`test_marksafe_wraps_only_sanitized_output`) skenira ovaj
izvor (space-stripped) i zahteva `mark_safe(sanitize_legal_html(` ALI zabranjuje
direktno markiranje sirove ulazne vrednosti — zato gornji tekst NAMERNO izbegava
taj zabranjeni token.
"""

from __future__ import annotations

from django import template
from django.utils.safestring import mark_safe

from apps.core.sanitize import sanitize_legal_html

register = template.Library()


@register.filter(name="legal_html", is_safe=True)
def legal_html(value):
    """Sanitizuj `value` kroz nh3 allowlist pa `mark_safe` — SAMO posle sanitizacije.

    None/prazno → prazan SafeString. Markira kao bezbedan TEK izlaz sanitizera,
    NIKAD sirovu ulaznu vrednost (G-6).
    """
    return mark_safe(sanitize_legal_html(value))
