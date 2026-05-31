"""Story 2.10 — Jeegee priključna landing templates + partials tests (RED phase TDD).

Pokriva AC3 (page structure) + AC4 (hero variant=jeegee) + AC5 (3-card showcase + CTA) +
AC8 (i18n + a11y semantic HTML5).

Test scope (14 tests):
- AC3 page structure (4 tests):
  - test_jeegee_prikljucna_renders_exactly_one_h1
  - test_jeegee_prikljucna_renders_exactly_one_main
  - test_jeegee_prikljucna_sections_render_in_correct_order
  - test_outer_section_has_aria_label_not_aria_labelledby  (CRITICAL-1 regression guard)
- AC4 hero (2 tests):
  - test_jeegee_hero_renders_jeegee_variant_repeating_element  (SM-D9 regression guard)
  - test_jeegee_hero_brand_logo_guard_works_when_logo_missing
- AC5 category showcase (5 tests):
  - test_category_showcase_renders_3_cards
  - test_pagination_url_pattern_uses_language_code_bare  (IMP-5 regression guard)
  - test_category_card_cta_aria_label_includes_category_name
  - test_empty_state_renders_when_zero_categories
  - test_categories_whitelist_only_seeded_slugs_appear  (IMP-3 regression guard)
- AC8 i18n + a11y (3 tests):
  - test_html_lang_attribute_set_correctly
  - test_no_cirillic_characters_in_rendered_html
  - test_vary_header_not_required_for_static_page

Pokrenuti sa:
    docker compose -f compose/local.yml exec django pytest \\
        apps/brands/tests/test_jeegee_prikljucna_templates.py -v

Refs:
- 2-10-jeegee-prikljucna-mehanizacija-strana.md (AC3, AC4, AC5, AC8)
- 2-10-interface-contract.md (§ 4 Templates + § 8 data-testid surface)
"""

from __future__ import annotations

import re

import pytest
from django.utils.translation import activate

from apps.brands.models import Brand, Category

pytestmark = pytest.mark.django_db


# =============================================================================
# AC3 — Page structure (single h1, single main, section order, aria-label CRITICAL-1)
# =============================================================================


def test_jeegee_prikljucna_renders_exactly_one_h1(client):
    """AC3 + AC8: TAČNO 1 <h1> na strani (brand.name iz hero_overlay_card partial-a)."""
    activate("sr")
    url = "/sr/mehanizacija/prikljucna/"

    response = client.get(url)
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    h1_pattern = re.compile(r"<h1\b[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)
    h1_matches = h1_pattern.findall(html)

    assert len(h1_matches) == 1, (
        f"jeegee_prikljucna.html MORA imati TAČNO 1 <h1>, pronađeno {len(h1_matches)}. "
        f"H1 contents: {h1_matches!r}. h1 dolazi iz hero_overlay_card partial-a "
        f"(linija 8: <h1 class='coric-hero-overlay-card__title'>{{ title }}</h1>)."
    )
    # Sadržaj <h1> mora sadržati brand.name = "Jeegee"
    h1_text = h1_matches[0]
    assert "Jeegee" in h1_text, (
        f"<h1> MORA sadržati 'Jeegee' (brand.name iz seed 0003 migracije), "
        f"dobio: {h1_text!r}."
    )


def test_jeegee_prikljucna_renders_exactly_one_main(client):
    """AC3 + AC8: TAČNO 1 <main> element (base.html provider; outer wrapper je <section>).

    Single-main regression guard, mirror Story 2-6/2-7/2-8/2-9. HTML5 spec zabranjuje
    nested <main> elemente.
    """
    activate("sr")
    url = "/sr/mehanizacija/prikljucna/"

    response = client.get(url)
    assert response.status_code == 200, (
        f"GET {url} treba HTTP 200 pre HTML parse-a, dobio {response.status_code}. "
        "Test bi pao vacuously na 404 page-u koji nema <main> elementa."
    )
    html = response.content.decode("utf-8")

    main_pattern = re.compile(r"<main\b[^>]*>", re.IGNORECASE)
    main_matches = main_pattern.findall(html)

    assert len(main_matches) == 1, (
        f"jeegee_prikljucna.html MORA imati TAČNO 1 <main> element (HTML5 spec — "
        f"nested <main> je invalid). base.html provider renderuje "
        f"<main id='main-content'>; outer wrapper u jeegee_prikljucna.html je "
        f"<section class='coric-brand-detail coric-jeegee-prikljucna'>, NIJE drugi "
        f"<main>. Pronađeno: {len(main_matches)}: {main_matches!r}."
    )


def test_jeegee_prikljucna_sections_render_in_correct_order(client):
    """AC3: hero → categories → opciono catalog_cta (TAČAN redosled)."""
    activate("sr")
    url = "/sr/mehanizacija/prikljucna/"

    response = client.get(url)
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    hero_idx = html.find('id="jeegee-prikljucna-hero"')
    categories_idx = html.find('id="jeegee-prikljucna-categories"')

    assert hero_idx >= 0, (
        "id='jeegee-prikljucna-hero' MORA postojati u render-u (AC3 § 1)."
    )
    assert categories_idx >= 0, (
        "id='jeegee-prikljucna-categories' MORA postojati u render-u (AC3 § 2)."
    )
    assert hero_idx < categories_idx, (
        f"Section order BROKEN: hero={hero_idx} categories={categories_idx}. "
        f"Hero MORA biti PRE categories sekcije."
    )

    # Catalog CTA je opciono (samo ako brand.catalog_pdf postoji); Jeegee iz 0003
    # seed migracije NEMA catalog_pdf, pa ne treba da se renderuje
    cta_idx = html.find('id="jeegee-prikljucna-catalog-cta"')
    assert cta_idx == -1, (
        f"id='jeegee-prikljucna-catalog-cta' NE SME postojati kad brand.catalog_pdf "
        f"nije postavljen (seed migracija ne postavlja catalog_pdf). Pronađeno na "
        f"poziciji {cta_idx}. Conditional render kroz `{{% if brand.catalog_pdf %}}` "
        f"guard u jeegee_prikljucna.html."
    )


def test_catalog_cta_banner_renders_when_catalog_pdf_present(client):
    """AC3 § 3: opcioni catalog CTA banner renderuje SAMO kad brand.catalog_pdf postoji.

    Seed 0003 ne postavlja catalog_pdf; test ga eksplicitno postavi na seeded Jeegee
    brand i verifikuje:
    - <section id="jeegee-prikljucna-catalog-cta"> postoji
    - download <a data-testid="jeegee-catalog-download"> postoji sa href ka pdf url-u
    - Wave Divider partial je include-ovan iznad banner-a (mirror Story 2-6 pattern)

    Komplement test_jeegee_prikljucna_sections_render_in_correct_order koji testira
    ABSENT path (catalog_pdf nepostavljen → banner se NE renderuje).
    """
    from django.core.files.base import ContentFile

    activate("sr")
    # Postavi catalog_pdf na seeded Jeegee brand (FileField.save persistuje fajl).
    # RED phase: 0003 migracija ne postoji još pa brand nije seed-ovan — fail sa
    # jasnom AC-vezanom porukom (NE opaque DoesNotExist crash).
    jeegee = Brand.objects.filter(slug="jeegee").first()
    assert jeegee is not None, (
        "Jeegee Brand MORA postojati kroz 0003 seed migraciju pre nego što catalog "
        "CTA banner može biti testiran (Dev MORA kreirati migraciju 0003 per AC7)."
    )
    jeegee.catalog_pdf.save("jeegee-katalog.pdf", ContentFile(b"%PDF-1.4 stub"), save=True)

    url = "/sr/mehanizacija/prikljucna/"
    response = client.get(url)
    assert response.status_code == 200, (
        f"GET {url} treba HTTP 200 pre HTML parse-a, dobio {response.status_code}."
    )
    html = response.content.decode("utf-8")

    # Catalog CTA sekcija MORA postojati kad catalog_pdf postoji
    assert 'id="jeegee-prikljucna-catalog-cta"' in html, (
        "Kad brand.catalog_pdf postoji, <section id='jeegee-prikljucna-catalog-cta'> "
        "MORA biti renderovan (AC3 § 3 conditional `{% if brand.catalog_pdf %}` guard)."
    )
    # Download CTA <a> sa data-testid surface (contract § 8)
    assert 'data-testid="jeegee-catalog-download"' in html, (
        "Catalog CTA banner MORA imati download <a data-testid='jeegee-catalog-download'> "
        "(contract § 8 data-testid surface)."
    )
    # Href MORA pokazivati na catalog_pdf.url (media URL)
    assert jeegee.catalog_pdf.url in html, (
        f"Download CTA href MORA biti brand.catalog_pdf.url ({jeegee.catalog_pdf.url!r}); "
        f"render ne sadrži taj URL."
    )
    # Wave Divider partial include-ovan iznad banner-a (mirror Story 2-6)
    assert "coric-wave-divider" in html, (
        "Catalog CTA sekcija MORA include-ovati Wave Divider partial "
        "(`{% include 'partials/wave_divider.html' %}`) iznad banner-a."
    )

    # Cleanup uploaded stub file da ne ostane u media storage-u
    jeegee.catalog_pdf.delete(save=False)


def test_outer_section_has_aria_label_not_aria_labelledby(client):
    """AC3 + AC8 + SM-D8 LOCK (CRITICAL-1 regression guard).

    Outer <section class="coric-brand-detail coric-jeegee-prikljucna"> MORA imati
    aria-label atribut (NE aria-labelledby), jer <h1> u Story 1-7 hero_overlay_card.html
    partial-u NEMA id atribut. Dangling aria-labelledby je a11y bug.

    SM-D8 lock: sve buduće landing strane sa hero_overlay_card include-om koriste
    aria-label dok partial ne dobije title_id kwarg podršku (potencijalno Story 9-10).
    """
    activate("sr")
    url = "/sr/mehanizacija/prikljucna/"

    response = client.get(url)
    assert response.status_code == 200, (
        f"GET {url} treba HTTP 200 pre HTML parse-a, dobio {response.status_code}. "
        "Test bi pao vacuously na 404 page-u koji nema outer section."
    )
    html = response.content.decode("utf-8")

    # Outer wrapper: <section class="coric-brand-detail coric-jeegee-prikljucna" ...>
    # Pattern matchuje sva atribute u outer section tag-u
    outer_pattern = re.compile(
        r'<section[^>]*\bcoric-jeegee-prikljucna\b[^>]*>',
        re.IGNORECASE,
    )
    outer_matches = outer_pattern.findall(html)
    assert outer_matches, (
        "Outer <section class='coric-brand-detail coric-jeegee-prikljucna'> "
        "MORA postojati u render-u."
    )
    # Multiple matches mogu da postoje (inner sections referenciraju klasu); uzmi
    # prvi koji NIJE inner section (proverava na coric-brand-detail klasu prisutno)
    outer_tag = None
    for tag in outer_matches:
        if "coric-brand-detail" in tag:
            outer_tag = tag
            break
    assert outer_tag is not None, (
        f"Outer wrapper sa OBE klase 'coric-brand-detail' AND 'coric-jeegee-prikljucna' "
        f"MORA postojati. Pronađeno: {outer_matches!r}"
    )

    # MORA imati aria-label
    assert "aria-label=" in outer_tag, (
        f"Outer <section> MORA imati 'aria-label' atribut (SM-D8 LOCK / CRITICAL-1 "
        f"regression guard). Pronađen tag: {outer_tag!r}"
    )
    # NE SME imati aria-labelledby (dangling reference na nepostojeći id)
    assert "aria-labelledby=" not in outer_tag, (
        f"Outer <section> NE SME imati 'aria-labelledby' atribut. SM-D8 LOCK: <h1> u "
        f"hero_overlay_card.html partial-u NEMA id atribut, pa aria-labelledby bi "
        f"bila dangling reference (a11y bug). Pronađen tag: {outer_tag!r}"
    )

    # aria-label sadrži „priključna mehanizacija" (blocktranslate-wrapped)
    assert "priključna mehanizacija" in outer_tag, (
        f"aria-label MORA sadržati 'priključna mehanizacija' (blocktranslate sa "
        f"brand.name interpolacijom — '{{ brand }} priključna mehanizacija'). "
        f"Pronađen tag: {outer_tag!r}"
    )


# =============================================================================
# AC4 — Hero (variant=jeegee SM-D9 + brand.logo guard)
# =============================================================================


def test_jeegee_hero_renders_jeegee_variant_repeating_element(client):
    """AC4 + SM-D9 LOCK: rendered HTML sadrži klasu coric-repeating-element--jeegee.

    Regression guard — Story 2-6 _hero_section.html koristi variant="blue" koji NE
    postoji kao CSS klasa (dormant bug). Story 2-10 koristi TAČAN variant="jeegee"
    koji mapira na .coric-repeating-element--jeegee (live `static/css/components/
    repeating-element.css:14`).

    Verifikuje NE postoji --blue ni --jeegee-blue varijante (sprečava regression).
    """
    activate("sr")
    url = "/sr/mehanizacija/prikljucna/"

    response = client.get(url)
    assert response.status_code == 200, (
        f"GET {url} treba HTTP 200 pre HTML parse-a, dobio {response.status_code}. "
        "Test bi pao vacuously na 404 page-u koji nema repeating-element klase."
    )
    html = response.content.decode("utf-8")

    assert "coric-repeating-element--jeegee" in html, (
        "Hero MORA renderovati klasu 'coric-repeating-element--jeegee' (SM-D9 LOCK). "
        "_jeegee_hero.html include MORA prosediti `variant='jeegee'` (NE 'blue', "
        "NE 'jeegee-blue') u hero_overlay_card.html partial."
    )
    # Sprečava regression: NE SME postojati --blue ni --jeegee-blue varijante
    assert "coric-repeating-element--blue" not in html, (
        "Hero NE SME renderovati klasu 'coric-repeating-element--blue' "
        "(Story 2-6 dormant bug — variant='blue' NE postoji u CSS-u)."
    )
    assert "coric-repeating-element--jeegee-blue" not in html, (
        "Hero NE SME renderovati klasu 'coric-repeating-element--jeegee-blue' "
        "(invalid variant naming)."
    )


def test_jeegee_hero_brand_logo_guard_works_when_logo_missing(client):
    """AC4: brand bez logo polja → hero section renderuje ali bez <img> tag-a.

    Seed 0003 migracija ne postavlja brand.logo (image upload je admin task);
    `{% if brand.logo %}` guard u _jeegee_hero.html sprečava ValueError od
    brand.logo.url accessor-a na empty FileField.
    """
    activate("sr")
    url = "/sr/mehanizacija/prikljucna/"

    response = client.get(url)
    assert response.status_code == 200, (
        "Hero MORA renderovati bez crash-a čak i kad brand.logo nije postavljen "
        "(defensive guard). Jeegee brand iz 0003 migracije nema logo polje "
        "popunjeno."
    )
    html = response.content.decode("utf-8")

    # Hero wrapper MORA postojati
    assert 'data-testid="jeegee-hero"' in html, (
        "Hero wrapper sa data-testid='jeegee-hero' MORA postojati."
    )

    # Hero <img> sa brand_logo NE SME postojati (jer brand.logo je prazan)
    # hero_overlay_card.html renderuje <img src="{{ brand_logo }}"> SAMO ako
    # brand_logo nije empty (linija 3-7 — `{% if brand_logo %}` guard)
    img_in_hero_pattern = re.compile(
        r'<div[^>]*coric-hero-overlay-card__brand-lockup[^>]*>',
        re.IGNORECASE,
    )
    assert not img_in_hero_pattern.search(html), (
        "Kad brand.logo NIJE postavljen, hero NE SME renderovati "
        "<div class='coric-hero-overlay-card__brand-lockup'> wrapper sa <img>. "
        "_jeegee_hero.html MORA imati `{% if brand.logo %}` guard."
    )


# =============================================================================
# AC5 — Category showcase (3 cards, CTA href bare LANGUAGE_CODE, aria-label, empty, whitelist)
# =============================================================================


def test_category_showcase_renders_3_cards(client):
    """AC5: 3-card grid za 3 seeded mehanizacija kategorije.

    Verifikuje TAČNO 3 article.coric-category-card instance-i renderuju se.
    """
    activate("sr")
    url = "/sr/mehanizacija/prikljucna/"

    response = client.get(url)
    assert response.status_code == 200, (
        f"GET {url} treba HTTP 200 pre HTML parse-a, dobio {response.status_code}. "
        "Test bi pao vacuously na 404 page-u koji nema kartica."
    )
    html = response.content.decode("utf-8")

    card_pattern = re.compile(
        r'<article[^>]*\bcoric-category-card\b[^>]*>',
        re.IGNORECASE,
    )
    card_matches = card_pattern.findall(html)
    assert len(card_matches) == 3, (
        f"jeegee_prikljucna MORA renderovati TAČNO 3 .coric-category-card kartice "
        f"(3 seeded mehanizacija kategorije iz 0003 migracije), pronađeno "
        f"{len(card_matches)}."
    )

    # Verifikuj data-testid per kartica
    for slug in ("osnovna-obrada-zemljista", "priprema-zemljista", "masine-za-setvu"):
        expected_testid = f'data-testid="category-card-{slug}"'
        assert expected_testid in html, (
            f"Kartica za slug={slug!r} MORA imati '{expected_testid}' atribut."
        )


def test_pagination_url_pattern_uses_language_code_bare(client):
    """AC5 + SM-D5 + IMP-5 regression guard: CTA href koristi bare LANGUAGE_CODE.

    href = `/{{ LANGUAGE_CODE }}/mehanizacija/prikljucna/{{ category.slug }}/` —
    direct string interpolation (NE {% url %} jer subcategory URL pattern dolazi u
    Story 2-11). bare {{ LANGUAGE_CODE }} (NE request.LANGUAGE_CODE) per codebase
    konvencija (IMP-5 fix).

    Sprečava regression: //mehanizacija/... (double slash kad LANGUAGE_CODE empty).
    """
    activate("sr")
    url = "/sr/mehanizacija/prikljucna/"

    response = client.get(url)
    assert response.status_code == 200, (
        f"GET {url} treba HTTP 200 pre HTML parse-a, dobio {response.status_code}. "
        "Test bi pao vacuously na 404 page-u koji nema CTA href-ova."
    )
    html = response.content.decode("utf-8")

    # Locale-prefiksiran URL MORA biti present za sve 3 kartice
    expected_hrefs = [
        "/sr/mehanizacija/prikljucna/osnovna-obrada-zemljista/",
        "/sr/mehanizacija/prikljucna/priprema-zemljista/",
        "/sr/mehanizacija/prikljucna/masine-za-setvu/",
    ]
    for href in expected_hrefs:
        assert href in html, (
            f"CTA href '{href}' MORA biti u render-u (SM-D5 direct string "
            f"interpolation `/{{{{ LANGUAGE_CODE }}}}/mehanizacija/prikljucna/"
            f"{{{{ category.slug }}}}/`)."
        )

    # Regression guard: NE SME biti '//mehanizacija/' (LANGUAGE_CODE empty fallback)
    assert "//mehanizacija/" not in html, (
        "Render NE SME imati '//mehanizacija/' substring — to bi značilo da "
        "LANGUAGE_CODE template variable rezolvira u empty string (Django context "
        "processor nije pravilno wired). Verifikuj 'django.template.context_"
        "processors.i18n' je u TEMPLATES OPTIONS context_processors u settings."
    )


def test_category_card_cta_aria_label_includes_category_name(client):
    """AC5: CTA aria-label sadrži „Pogledaj kategoriju: {category.name}".

    WCAG 2.1 SC 2.4.4 (link purpose in context) — bez aria-label, screen reader
    najavi samo „POGLEDAJ KATEGORIJU, link" 3 puta uzastopno (ambiguous).
    """
    activate("sr")
    url = "/sr/mehanizacija/prikljucna/"

    response = client.get(url)
    assert response.status_code == 200, (
        f"GET {url} treba HTTP 200 pre HTML parse-a, dobio {response.status_code}. "
        "Test bi pao vacuously na 404 page-u koji nema aria-label atribute."
    )
    html = response.content.decode("utf-8")

    # Per Category.name (sr): "Osnovna obrada zemljišta", "Priprema zemljišta",
    # "Mašine za setvu"
    expected_aria_labels = [
        "Pogledaj kategoriju: Osnovna obrada zemljišta",
        "Pogledaj kategoriju: Priprema zemljišta",
        "Pogledaj kategoriju: Mašine za setvu",
    ]
    for label in expected_aria_labels:
        # aria-label="..." substring match — escape-uju se potencijalni HTML
        # entities u Category.name (nema specijalnih u v1)
        assert f'aria-label="{label}"' in html, (
            f"CTA dugme MORA imati 'aria-label=\"{label}\"' (blocktranslate sa "
            f"category.name interpolacijom). HTML render renderuje pune "
            f"dijakritike (č/ć/ž/š/đ)."
        )


def test_empty_state_renders_when_zero_categories(client):
    """AC5: {% empty %} clause renderuje „Kategorije priključne mehanizacije su u pripremi.".

    Defensive — ako admin manualno obriše 3 seeded kategorije (ili migracija nije
    primenjena), strana prikazuje empty state umesto prazne sekcije.
    """
    activate("sr")
    # Obriši svih 3 mehanizacija kategorije
    Category.objects.filter(
        is_for=Category.CategoryScope.MEHANIZACIJA,
        slug__in=[
            "osnovna-obrada-zemljista",
            "priprema-zemljista",
            "masine-za-setvu",
        ],
    ).delete()

    url = "/sr/mehanizacija/prikljucna/"
    response = client.get(url)
    assert response.status_code == 200, (
        "Strana MORA renderovati HTTP 200 čak i bez kategorija (empty state, NE crash)."
    )
    html = response.content.decode("utf-8")

    # Empty state poruka
    assert "Kategorije priključne mehanizacije su u pripremi." in html, (
        "Empty state MORA renderovati poruku 'Kategorije priključne mehanizacije "
        "su u pripremi.' kroz `{% empty %}` clause u _category_showcase.html."
    )
    # CSS klasa
    assert 'class="coric-empty-state"' in html, (
        "Empty state poruka MORA imati klasu 'coric-empty-state' (IMP-2 fix — "
        "CSS rule u category-showcase.css)."
    )

    # NE renderuju se kartice
    card_pattern = re.compile(
        r'<article[^>]*\bcoric-category-card\b[^>]*>',
        re.IGNORECASE,
    )
    card_matches = card_pattern.findall(html)
    assert len(card_matches) == 0, (
        f"Kad nema kategorija, NE SMEJU se renderovati .coric-category-card "
        f"kartice, pronađeno {len(card_matches)}."
    )


def test_categories_whitelist_only_seeded_slugs_appear(client):
    """AC5 + IMP-3 partial-degradation regression guard.

    Kreiraj 4. MEHANIZACIJA Category sa non-whitelist slug-om 'random-slug';
    verifikuj rendered HTML ima TAČNO 3 kartice (samo whitelist), NE 4. View
    queryset MORA imati slug__in=_PRIKLJUCNA_CATEGORY_SLUGS filter.

    Mitigation: ako admin u Story 8-5 manuelno doda 4. mehanizacija kategoriju,
    Story 2-10 view je defensivno protected — strana renderuje SAMO 3 whitelist
    kartice (silent ignore non-whitelisted).
    """
    activate("sr")
    Category.objects.create(
        name="Random Kategorija",
        slug="random-slug",
        is_for=Category.CategoryScope.MEHANIZACIJA,
        display_order=99,
    )

    url = "/sr/mehanizacija/prikljucna/"
    response = client.get(url)
    assert response.status_code == 200, (
        f"GET {url} treba HTTP 200 pre HTML parse-a, dobio {response.status_code}. "
        "Test bi pao vacuously na 404 page-u."
    )
    html = response.content.decode("utf-8")

    # TAČNO 3 kartice (whitelist)
    card_pattern = re.compile(
        r'<article[^>]*\bcoric-category-card\b[^>]*>',
        re.IGNORECASE,
    )
    card_matches = card_pattern.findall(html)
    assert len(card_matches) == 3, (
        f"Render MORA imati TAČNO 3 .coric-category-card kartice (whitelist filter "
        f"u view-u prevents non-whitelisted slug-ove). Pronađeno {len(card_matches)}."
    )

    # Non-whitelisted kategorija NE SME biti u render-u
    assert 'data-testid="category-card-random-slug"' not in html, (
        "Non-whitelisted category sa slug='random-slug' NE SME biti renderovan "
        "(view queryset MORA imati `slug__in=_PRIKLJUCNA_CATEGORY_SLUGS` filter)."
    )
    assert "Random Kategorija" not in html, (
        "Non-whitelisted category name 'Random Kategorija' NE SME biti u render-u."
    )


# =============================================================================
# AC8 — i18n + a11y
# =============================================================================


def test_html_lang_attribute_set_correctly(client):
    """AC8: <html lang="sr"> na /sr/; <html lang="hu"> na /hu/.

    base.html provider linija 6: <html lang="{{ LANGUAGE_CODE }}">.
    """
    activate("sr")
    response_sr = client.get("/sr/mehanizacija/prikljucna/")
    html_sr = response_sr.content.decode("utf-8")
    assert '<html lang="sr">' in html_sr or 'lang="sr"' in html_sr.split(">")[0], (
        "HTML root MORA imati lang='sr' atribut na /sr/ URL-u."
    )

    activate("hu")
    response_hu = client.get("/hu/mehanizacija/prikljucna/")
    html_hu = response_hu.content.decode("utf-8")
    assert '<html lang="hu">' in html_hu or 'lang="hu"' in html_hu.split(">")[0], (
        "HTML root MORA imati lang='hu' atribut na /hu/ URL-u."
    )


def test_no_cirillic_characters_in_rendered_html(client):
    """AC8: NEMA ćirilice u render-u (project-context.md anti-pattern linija 486-495).

    Sve user-facing string-ove kroz latinicu (sa punim dijakritikama).
    """
    activate("sr")
    url = "/sr/mehanizacija/prikljucna/"

    response = client.get(url)
    assert response.status_code == 200, (
        f"GET {url} treba HTTP 200 pre HTML parse-a, dobio {response.status_code}. "
        "Test bi pao vacuously na 404 page-u (404 strana NEMA ćirilice)."
    )
    html = response.content.decode("utf-8")

    cirillic_pattern = re.compile(r"[А-Яа-яЁё]")
    cirillic_matches = cirillic_pattern.findall(html)

    assert not cirillic_matches, (
        f"Render NE SME sadržati ćirilične karaktere (project-context.md striktno). "
        f"Pronađeno: {set(cirillic_matches)!r}. Sve user-facing string-ove MORAJU "
        f"biti u latinici sa punim dijakritikama (č/ć/ž/š/đ)."
    )


def test_vary_header_not_required_for_static_page(client):
    """AC8: Story 2-10 je statička strana — NEMA HTMX, NEMA Vary: HX-Request header.

    Razlika vs Story 2-9 (UsedMachineryListView) koja ima
    @vary_on_headers('HX-Request') dekorator. Story 2-10 NEMA HTMX branching pa Vary
    header nije potreban — sprečava cache poisoning analysis paranoia.
    """
    activate("sr")
    url = "/sr/mehanizacija/prikljucna/"

    response = client.get(url)
    assert response.status_code == 200

    vary_header = response.headers.get("Vary", "")
    # Vary header MAY biti present zbog default Django middleware-a (npr. Accept-Language
    # iz LocaleMiddleware), ali ne treba sadržati HX-Request (Story 2-10 NEMA HTMX).
    assert "HX-Request" not in vary_header, (
        f"Story 2-10 (statička strana) NE SME emit-ovati 'Vary: HX-Request' header "
        f"(razlika vs Story 2-9 HTMX listing). View NE SME imati "
        f"@vary_on_headers('HX-Request') dekorator. Dobijen Vary: {vary_header!r}."
    )
