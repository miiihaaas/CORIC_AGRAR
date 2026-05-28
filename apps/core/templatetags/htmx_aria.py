"""Template tag biblioteka za HTMX a11y patterns.

Ekspoze `{% aria_live %}` — kanonski singleton aria-live region (WCAG 4.1.3
status messages). HTMX partials announce u njega kroz hx-swap-oob.
Primer u partial template-u (Story 2.8+):

    <div hx-swap-oob="innerHTML:#aria-live">Pronađeno 12 rezultata</div>
"""

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def aria_live():
    """Render kanonski aria-live region. Singleton u base.html.

    Vraća: `<div id="aria-live" class="visually-hidden" aria-live="polite"
    aria-atomic="true"></div>` — bez novlines (sve u jednoj liniji).
    """
    return mark_safe(
        '<div id="aria-live" class="visually-hidden" aria-live="polite" aria-atomic="true"></div>'
    )
