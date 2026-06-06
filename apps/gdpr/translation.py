"""Story 7.1 — modeltranslation registracija za apps.gdpr.

modeltranslation auto-discovery skenira sve INSTALLED_APPS pri Django startup-u i
učitava `<app>/translation.py`. Registracija ovde generiše virtuelna polja
`title_sr/hu/en` i `body_sr/hu/en` koja se materijalizuju kao stvarne DB kolone
kroz `makemigrations gdpr` (MORA postojati PRE makemigrations da kolone uđu u
0001_initial — G-9).

`effective_date`/`created_at`/`updated_at` su jezik-neutralni (NISU translatable).
Mirror apps/pages/translation.py pattern.
"""

from modeltranslation.translator import TranslationOptions, register

from apps.gdpr.models import CookiePolicy


@register(CookiePolicy)
class CookiePolicyTranslationOptions(TranslationOptions):
    fields = ("title", "body")
