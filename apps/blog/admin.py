"""Story 5.1 — MINIMALAN STUB admin za apps.blog (Category/Tag/Post).

PROLAZI `manage.py check` + changelist 200 + add-view 200. NIJE pun CRUD —
WYSIWYG body editor, inline image upload, color picker, multi-locale tab UI =
Epic 8 Story 8.7. 5-1 stub je za inicijalni admin pregled/unos.

BL-2 rezolucija: koristi `modeltranslation.admin.TranslationAdmin` (modeltranslation
patch-uje `prepopulated_fields` da radi sa virtuelnim translatable poljima — base
`title`/`name` su virtuelni kad je model registrovan). `search_fields` koristi
sr-suffiksovane realne DB kolone (`title_sr`/`name_sr`) da NE baci admin.E030/FieldError.

⛔ PostAdmin.view_on_site=False (IMP-1/BL-5) — Post ima get_absolute_url →
„View on site" dugme bi pozvalo reverse("blog:detail") → NoReverseMatch → HTTP 500
(blog URL-ovi NE postoje do 5.2/5.3). Re-enable u 8.7/5.3.
"""

from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from apps.blog.models import Category, Post, Tag


@admin.register(Category)
class CategoryAdmin(TranslationAdmin):
    list_display = ("name", "slug")
    search_fields = ("name_sr",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Tag)
class TagAdmin(TranslationAdmin):
    list_display = ("name", "slug")
    search_fields = ("name_sr",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Post)
class PostAdmin(TranslationAdmin):
    list_display = ("title", "category", "status", "published_at", "author")
    list_filter = ("status", "category", "tags")
    search_fields = ("title_sr",)
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "published_at"
    # IMP-1/BL-5: sprečava „View on site" → get_absolute_url → NoReverseMatch → 500.
    view_on_site = False
