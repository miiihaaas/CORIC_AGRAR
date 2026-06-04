"""Story 5.1 — modeltranslation registracija za apps.blog.

modeltranslation auto-discovery (apps.blog POSLE `modeltranslation` u
INSTALLED_APPS) skenira INSTALLED_APPS pri startup-u i učitava translation.py.
Registracija generiše virtuelna polja `title_sr/_hu/_en`, `perex_*`, `body_*`,
`name_*` (Category+Tag), `description_*` → materijalizuju se kao DB kolone kroz
`makemigrations blog`.

slug NIJE u fields (SM-D7 — jezik-neutralan ASCII slug; mirror products).
sr fallback kroz MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",) (base.py).
"""

from modeltranslation.translator import TranslationOptions, register

from apps.blog.models import Category, Post, Tag


@register(Post)
class PostTranslationOptions(TranslationOptions):
    fields = ("title", "perex", "body")


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ("name", "description")


@register(Tag)
class TagTranslationOptions(TranslationOptions):
    fields = ("name",)
