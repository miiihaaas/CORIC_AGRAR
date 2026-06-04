"""Views za apps.pages (Story 3.1).

HomeView je čista READ-ONLY agregacijska strana — „izlog" koji linkuje na sve
postojeće odredišne strane (brand detail, Jeegee priključna, HZM radne mašine,
polovna mehanizacija). Agregira domain modele `Brand`/`Category`/`Product`.

ARHITEKTONSKA NAPOMENA (SM-D6): `pages` je top-level app KOJEM je per
architecture.md dozvoljeno da importuje domain modele + blog. Import
`Brand`/`Category`/`Product` NIJE „izuzetak" — to je dozvoljena READ-ONLY
zavisnost (NEMA `.save()`/`.create()`/FK iz pages→domain). `apps/core` NIKAD
ne sme importovati domain apps — zato home živi ovde, NE u core.
"""

from __future__ import annotations

from django.db.models import Prefetch
from django.views.generic import TemplateView

from apps.brands.models import Brand, Category
from apps.products.models import Product

_HZM_CATEGORY_SLUG = "radne-masine"

# Mehanizacija brendovi koji vlasnički pripadaju mehanizacija landing stranama
# (Jeegee priključna / HZM radne mašine / Tulip MIX prikolice). Seed 0004 kreira
# Tulip MIX proizvode kao condition=NEW (default) bez traktori scope-a, pa goli
# condition=NEW filter ne razlučuje mehanizaciju od traktora — eksplicitno ih
# isključujemo iz Traktori „izloga" (SM-D4 intent: Jeegee/HZM/Tulip NE iscure).
#
# TODO (deferred → buduća brands/admin story, npr. 8-x): ova lista je PRIVREMENI
# guardrail vezan za TRENUTNI seed (migracija 0004 — Tulip condition=NEW default,
# Brand bez scope diskriminatora). LATENTNI BUG: budući mehanizacija brend čiji slug
# NIJE u ovoj listi, a ima objavljen condition=NEW proizvod bez subcategory, bio bi
# pogrešno klasifikovan u Traktori sekciju. Robusno rešenje je model-driven
# diskriminator — Brand.scope CharField choices (traktori/mehanizacija) ILI
# popunjavanje Product.subcategory na mehanizacija proizvodima + filter po
# products__subcategory__category__is_for. NE dodavati model polje u ovoj story
# (3-1 nema modele po dizajnu). Gap je zaključan regresionim testom
# `test_mehanizacija_brand_slug_blacklist_latent_bug` (apps/pages/tests/test_home_view.py).
_MEHANIZACIJA_BRAND_SLUGS = ("jeegee", "hzm", "tulip")


class HomeView(TemplateView):
    """Home strana — agregira 7 sekcija READ-ONLY (SM-D1)."""

    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # SM-D4 (opcija A): Traktori sekcija lista SAMO brendove koji imaju bar jedan
        # OBJAVLJEN `condition=NEW` proizvod, isključujući mehanizacija brendove
        # (Jeegee/HZM/Tulip — `_MEHANIZACIJA_BRAND_SLUGS`). Eksplicitno isključenje je
        # neophodno jer seed 0004 kreira Tulip MIX prikolice kao condition=NEW
        # (default), pa goli condition=NEW filter ne razlučuje mehanizaciju od
        # traktora. `is_coming_soon=True` brendovi SE UKLJUČUJU (prikazani sa „Uskoro"
        # pill). Reprezentativna slika dolazi iz Prefetch(to_attr="published_products")
        # (NE per-brand .first() u petlji → N+1). `.distinct()` jer products__... join
        # može duplirati brendove.
        context["traktori_brands"] = list(
            Brand.objects.filter(
                products__condition=Product.ConditionChoice.NEW,
                products__is_published=True,
            )
            .exclude(slug__in=_MEHANIZACIJA_BRAND_SLUGS)
            .distinct()
            .prefetch_related(
                Prefetch(
                    "products",
                    queryset=Product.objects.filter(is_published=True).order_by(
                        "-created_at"
                    ),
                    to_attr="published_products",
                )
            )
            .order_by("is_coming_soon", "name")
        )

        # SM-D7: forward-compat blog placeholder — Post model NE postoji (Epic 5).
        # Prazna lista → template renderuje 2 Lorem Ipsum placeholder kartice.
        context["latest_posts"] = []

        # Radne mašine: HZM radne-masine Category + njene top-level Subcategory dece.
        # Defensive guard (mirror Story 2-12): ako Category ne postoji → [] (NE crash).
        hzm_subcategories = []
        try:
            hzm_category = Category.objects.get(
                slug=_HZM_CATEGORY_SLUG,
                is_for=Category.CategoryScope.MEHANIZACIJA,
            )
            hzm_subcategories = list(
                hzm_category.subcategories.filter(parent=None).order_by(
                    "display_order", "name"
                )
            )
        except Category.DoesNotExist:
            pass
        context["hzm_subcategories"] = hzm_subcategories

        return context


class AboutView(TemplateView):
    """„O nama" statička strana (Story 3.2).

    Čisto READ-ONLY render strana — sadržaj je hardcoded-translatable Lorem
    Ipsum do CMS-a (Epic 8 Story 8.8). NE agregira domain modele (SM-D1/SM-D5);
    sadržaj (hero/priča/lenta/galerija) živi u template-u kroz `{% translate %}`.
    """

    template_name = "pages/about.html"


class ContactView(TemplateView):
    """„Kontakt" statička strana (Story 3.3).

    Čisto GET-only READ-ONLY render strana — kontakt-info + Google Maps static
    iframe + forward-compat skelet forme (disabled polja + CSRF, BEZ funkcionalnog
    submit-a). Sadržaj je hardcoded-translatable do Story 3-4 (SiteSettings); NE
    agregira domain modele (SM-D1/SM-D5).

    GET-only DETERMINISTIČKI (C3/SM-D4): `http_method_names` izostavlja `post` →
    `View.dispatch` vraća HTTP 405 za POST. Forma je skelet (disabled submit);
    funkcionalan submit (Lead/email/HTMX) dolazi iz Epic 4 (Story 4.2 — ZASEBAN
    `apps/forms` endpoint `/htmx/forme/kontakt/`), NE na ContactView. NE dodavati
    `post()` metod.
    """

    template_name = "pages/contact.html"
    http_method_names = ["get", "head", "options"]


class ServiceView(TemplateView):
    """„Servisna podrška" strana (Story 4.4, FR-22) — mirror `ContactView`.

    GET-only READ-ONLY render strana koja mount-uje aktivnu servisnu formu kroz
    container partial (forms app vlasnik je render-a + submit endpoint-a — SM-D12).
    POST ide na ZASEBAN `forms:service_request_submit` endpoint, NE na ovaj page view.

    GET-only DETERMINISTIČKI: `http_method_names` izostavlja `post` → HTTP 405 za POST.
    """

    template_name = "pages/service.html"
    http_method_names = ["get", "head", "options"]


class PartRequestView(TemplateView):
    """„Rezervni delovi" strana (Story 4.5, FR-23) — mirror `ServiceView`.

    GET-only READ-ONLY render strana koja mount-uje aktivnu rezervni-delovi formu
    kroz container partial (forms app vlasnik je render-a + submit endpoint-a — SM-D12).
    POST ide na ZASEBAN `forms:part_request_submit` endpoint, NE na ovaj page view.

    GET-only DETERMINISTIČKI: `http_method_names` izostavlja `post` → HTTP 405 za POST.
    """

    template_name = "pages/part-request.html"
    http_method_names = ["get", "head", "options"]
