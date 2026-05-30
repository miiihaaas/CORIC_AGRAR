"""Story 2.6 — Brand listing templates + partials tests (RED phase TDD).

Pokriva AC3 (page structure) + AC4 (grid) + AC5 (extended akordion) + AC6 (medallions) +
AC7 (testimonials slider) + AC8 (i18n + a11y).

Test scope (~20 tests):
- AC3 page structure: 2 tests (section order + ARIA landmarks)
- AC4 grid: 3 tests (markup + data-testid + aria-label linkable card)
- AC5 extended: 4 tests (Motor-first regroup + Motor open default + empty skip + hu locale)
- AC6 medallions: 3 tests (value+label no icon + data-count-target + slice 4)
- AC7 testimonials: 4 tests (markup + pause/play aria-pressed + keyboard hint + single-testimonial hides controls)
- AC8 i18n + a11y: 4 tests (translate markers + semantic HTML5 + html lang + no bi icons)

Pokrenuti sa:
    docker compose -f compose/local.yml exec django uv run pytest \\
        apps/brands/tests/test_templates_brand_listing.py -v

Refs:
- 2-6-brand-listing-strana-sa-grid-extended-layout-om.md (AC3-AC8)
- 2-6-interface-contract.md (data-testid surface + partials structure)
"""

from __future__ import annotations

import re

import pytest
from django.urls import reverse
from django.utils.translation import activate

from apps.brands.tests.factories import BrandFactory, SeriesFactory
from apps.products.tests.factories import (
    ProductFactory,
    ProductSpecificationFactory,
    ProductTestimonialFactory,
)

pytestmark = pytest.mark.django_db


# =============================================================================
# Helpers
# =============================================================================


def _full_brand_fixture():
    """Helper: kreira brand sa svim sekcijama (statistics + grid + extended + testimonijali)."""
    brand = BrandFactory.create_with_statistics(name="Agri Tracking")
    grid_series = SeriesFactory.create_grid(brand=brand, name="Grid Serija", display_order=1)
    ext_series = SeriesFactory.create_extended(brand=brand, name="Extended Serija", display_order=2)
    p_grid_1 = ProductFactory.create(brand=brand, series=grid_series, name="Grid Model A", horse_power=120)
    p_grid_2 = ProductFactory.create(brand=brand, series=grid_series, name="Grid Model B", horse_power=140)
    p_ext = ProductFactory.create(brand=brand, series=ext_series, name="Extended Model X", horse_power=200)
    # Extended produkt dobija specifications u sve 4 sekcije (test regroup order)
    ProductSpecificationFactory.create(product=p_ext, section="hidraulika", key="Pumpa", value="Bosch")
    ProductSpecificationFactory.create(product=p_ext, section="motor", key="Snaga", value="200 KS")
    ProductSpecificationFactory.create(product=p_ext, section="ostalo", key="Boja", value="Žuta")
    ProductSpecificationFactory.create(product=p_ext, section="transmisija", key="Brzina", value="40 km/h")
    ProductTestimonialFactory.create(product=p_grid_1, author_name="Marko", quote="Sjajna mašina!")
    ProductTestimonialFactory.create(product=p_grid_2, author_name="Stojan", quote="Preporučujem.")
    return brand


# =============================================================================
# AC3 — Page structure (section order + ARIA landmarks)
# =============================================================================


def test_sections_render_in_correct_order(client):
    """AC3: hero → statistike → testimonijali → serije → catalog_cta (TAČAN redosled)."""
    activate("sr")
    brand = _full_brand_fixture()
    # Dodaj catalog_pdf za pun render
    from django.core.files.base import ContentFile

    brand.catalog_pdf.save("stub.pdf", ContentFile(b"%PDF-1.4 stub"), save=True)

    url = f"/sr/traktori/{brand.slug}/"
    response = client.get(url)
    assert response.status_code == 200

    html = response.content.decode("utf-8")

    # Pronalazi index pozicije sekcija u HTML render-u — redosled mora biti monotono rastući
    hero_idx = html.find('id="brand-hero"')
    stats_idx = html.find('id="brand-statistics"')
    test_idx = html.find('id="brand-testimonials"')
    series_idx = html.find('id="brand-series"')
    cta_idx = html.find('id="brand-catalog-cta"')

    # Sve sekcije moraju postojati (-1 znači nije pronađen)
    assert hero_idx >= 0, "id='brand-hero' MORA postojati u render-u (AC3 § 1)."
    assert stats_idx >= 0, "id='brand-statistics' MORA postojati (brand ima statistics)."
    assert test_idx >= 0, "id='brand-testimonials' MORA postojati (brand ima testimonijale)."
    assert series_idx >= 0, "id='brand-series' MORA postojati (uvek render)."
    assert cta_idx >= 0, "id='brand-catalog-cta' MORA postojati (brand ima catalog_pdf)."

    # Redosled: hero < stats < test < series < cta (po AC3 spec)
    assert hero_idx < stats_idx < test_idx < series_idx < cta_idx, (
        f"Section order BROKEN. Pozicije: hero={hero_idx} stats={stats_idx} "
        f"test={test_idx} series={series_idx} cta={cta_idx}. "
        "Očekivan redosled: hero < statistike < testimonijali < serije < catalog_cta."
    )


def test_aria_landmarks_present(client):
    """AC3: <main> wrapper + svaka sekcija ima <section aria-labelledby="...">."""
    activate("sr")
    brand = _full_brand_fixture()

    url = f"/sr/traktori/{brand.slug}/"
    response = client.get(url)
    html = response.content.decode("utf-8")

    # base.html već ima <main id="main-content"> wrapper (Story 1.6 deliverable)
    assert "<main" in html.lower(), "Render MORA imati <main> landmark (base.html provides it)."

    # Hero sekcija MORA imati aria-label (B1 fix — uklonjen duplikat <h1>; section landmark
    # ima accessible name kroz aria-label umesto aria-labelledby).
    assert re.search(r'<section[^>]*id="brand-hero"[^>]*aria-label="', html), (
        "Hero sekcija MORA imati aria-label atribut (B1 fix — uklonjen visually-hidden h1; "
        "section landmark dobija accessible name preko aria-label umesto aria-labelledby)."
    )
    # Statistike sekcija
    assert 'aria-labelledby="brand-statistics-title"' in html, (
        "Statistike sekcija MORA imati aria-labelledby='brand-statistics-title'."
    )
    # Testimonijali sekcija
    assert 'aria-labelledby="brand-testimonials-title"' in html, (
        "Testimonijali sekcija MORA imati aria-labelledby='brand-testimonials-title'."
    )
    # Serije sekcija
    assert 'aria-labelledby="brand-series-title"' in html, (
        "Serije sekcija MORA imati aria-labelledby='brand-series-title'."
    )


# =============================================================================
# AC4 — Grid layout (linkable card + data-testid + aria-label)
# =============================================================================


def test_grid_product_card_markup_structure(client):
    """AC4: Grid kartica je <a> wrapper sa coric-product-card BEM klasom."""
    activate("sr")
    brand = BrandFactory.create(name="Agri Tracking")
    series = SeriesFactory.create_grid(brand=brand, name="Grid Serija")
    product = ProductFactory.create(brand=brand, series=series, name="Model A", horse_power=120)

    url = f"/sr/traktori/{brand.slug}/"
    response = client.get(url)
    html = response.content.decode("utf-8")

    # Kartica je <a class="coric-product-card" ...>
    assert 'class="coric-product-card"' in html, (
        "Grid kartica MORA imati klasu 'coric-product-card' (BEM root — AC4 linkable card pattern)."
    )
    # OPŠIRNIJE CTA je <span aria-hidden="true"> (NE <a>/<button> — nested interactive guard)
    cta_pattern = re.compile(
        r'<span[^>]*class="[^"]*coric-product-card__cta[^"]*"[^>]*aria-hidden="true"',
        re.IGNORECASE,
    )
    assert cta_pattern.search(html), (
        "CTA 'OPŠIRNIJE' MORA biti <span> sa aria-hidden='true' (NE <a>/<button>) — "
        "AC4 + I6 fix nested interactive elements guard."
    )


def test_grid_product_card_has_data_testid(client):
    """AC4: <a data-testid='product-card-{slug}'> za Playwright (Story 9.8)."""
    activate("sr")
    brand = BrandFactory.create(name="Agri Tracking")
    series = SeriesFactory.create_grid(brand=brand, name="Grid Serija")
    product = ProductFactory.create(brand=brand, series=series, name="Model A")

    url = f"/sr/traktori/{brand.slug}/"
    response = client.get(url)
    html = response.content.decode("utf-8")

    expected_testid = f'data-testid="product-card-{product.slug}"'
    assert expected_testid in html, (
        f"Grid kartica MORA imati '{expected_testid}' atribut (UX-DR-13 + Story 9.8 Playwright selektor)."
    )


def test_grid_product_card_has_aria_label_on_link(client):
    """AC4 (I6 fix): <a aria-label="{product.name}"> za screen reader najavu."""
    activate("sr")
    brand = BrandFactory.create(name="Agri Tracking")
    series = SeriesFactory.create_grid(brand=brand, name="Grid Serija")
    product = ProductFactory.create(brand=brand, series=series, name="John Deere 8R")

    url = f"/sr/traktori/{brand.slug}/"
    response = client.get(url)
    html = response.content.decode("utf-8")

    # aria-label na <a> wrap-eru kartice — screen reader najavi link target jasno
    aria_pattern = re.compile(
        r'<a[^>]*class="[^"]*coric-product-card[^"]*"[^>]*aria-label="John Deere 8R"',
        re.IGNORECASE,
    )
    assert aria_pattern.search(html), (
        "Linkable card <a> MORA imati aria-label='{product.name}' (I6 fix — "
        "bez aria-label SR čita konkatenaciju svih labels uključujući 'OPŠIRNIJE'). "
        f"HTML snippet (prva 500 char): {html[:500]!r}"
    )


# =============================================================================
# AC5 — Extended layout (Motor-first regroup + Motor open default + empty skip + hu locale)
# =============================================================================


def test_extended_regroup_orders_sections_motor_first(client):
    """AC5 (C3 fix): regroup section_label sortira Motor→Transmisija→Hidraulika→Ostalo (NE alphabetical)."""
    activate("sr")
    brand = BrandFactory.create(name="Agri Tracking")
    series = SeriesFactory.create_extended(brand=brand, name="Extended Serija")
    product = ProductFactory.create(brand=brand, series=series, name="Model X")
    # Kreirane u SUPROTNOM redosledu (alphabetical hidraulika → motor → ostalo → transmisija)
    # da test pokaže da queryset annotate(section_rank) ispravlja na Motor-first.
    ProductSpecificationFactory.create(product=product, section="hidraulika", key="Pumpa")
    ProductSpecificationFactory.create(product=product, section="motor", key="Snaga")
    ProductSpecificationFactory.create(product=product, section="ostalo", key="Boja")
    ProductSpecificationFactory.create(product=product, section="transmisija", key="Brzina")

    url = f"/sr/traktori/{brand.slug}/"
    response = client.get(url)
    html = response.content.decode("utf-8")

    # Pronalazi <summary> tekstove (regroup grouper rendering)
    # section_label Case/When mapira sr lokal default ("Motor"/"Transmisija"/...)
    motor_idx = html.find(">Motor<")
    trans_idx = html.find(">Transmisija<")
    hidra_idx = html.find(">Hidraulika<")
    ostalo_idx = html.find(">Ostalo<")

    assert motor_idx >= 0, "<summary>Motor</summary> MORA biti render-ovan."
    assert trans_idx >= 0, "<summary>Transmisija</summary> MORA biti render-ovan."
    assert hidra_idx >= 0, "<summary>Hidraulika</summary> MORA biti render-ovan."
    assert ostalo_idx >= 0, "<summary>Ostalo</summary> MORA biti render-ovan."

    assert motor_idx < trans_idx < hidra_idx < ostalo_idx, (
        f"Section order BROKEN. Pozicije: Motor={motor_idx} Transmisija={trans_idx} "
        f"Hidraulika={hidra_idx} Ostalo={ostalo_idx}. "
        "section_rank Case/When annotation u get_queryset() MORA sortirati Motor=1 → "
        "Transmisija=2 → Hidraulika=3 → Ostalo=4."
    )


def test_extended_motor_section_open_by_default(client):
    """AC5: prva accordion sekcija (Motor) MORA imati <details open>."""
    activate("sr")
    brand = BrandFactory.create(name="Agri Tracking")
    series = SeriesFactory.create_extended(brand=brand, name="Extended Serija")
    product = ProductFactory.create(brand=brand, series=series, name="Model X")
    ProductSpecificationFactory.create(product=product, section="motor", key="Snaga")
    ProductSpecificationFactory.create(product=product, section="transmisija", key="Brzina")

    url = f"/sr/traktori/{brand.slug}/"
    response = client.get(url)
    html = response.content.decode("utf-8")

    # Pronalazi prvi <details> u extended layout-u
    # Mora biti `<details ... open>` (na prvoj sekciji = Motor zbog sort order-a)
    first_details = re.search(r"<details[^>]*>", html)
    assert first_details, "Bar jedan <details> mora postojati u extended layout-u."
    assert "open" in first_details.group(0), (
        f"Prva accordion sekcija (Motor) MORA imati 'open' atribut. "
        f"Pronađen: {first_details.group(0)!r}. Koristi `{{% if forloop.first %}}open{{% endif %}}` u template-u."
    )


def test_extended_empty_section_skipped(client):
    """AC5: regroup PRESKAČE sekcije bez specifikacija (no empty <details>)."""
    activate("sr")
    brand = BrandFactory.create(name="Agri Tracking")
    series = SeriesFactory.create_extended(brand=brand, name="Extended Serija")
    product = ProductFactory.create(brand=brand, series=series, name="Model X")
    # SAMO Motor sekcija ima spec — Transmisija/Hidraulika/Ostalo prazni
    ProductSpecificationFactory.create(product=product, section="motor", key="Snaga", value="200 KS")

    url = f"/sr/traktori/{brand.slug}/"
    response = client.get(url)
    html = response.content.decode("utf-8")

    # Motor MORA biti render-ovan
    assert ">Motor<" in html, "Motor sekcija sa spec mora biti render-ovana."
    # Transmisija NE SME biti render-ovana (nema spec)
    assert ">Transmisija<" not in html, (
        "Transmisija sekcija BEZ specifikacija NE SME biti render-ovana ({% regroup %} skip)."
    )
    assert ">Hidraulika<" not in html, "Hidraulika sekcija BEZ specifikacija NE SME biti render-ovana."
    assert ">Ostalo<" not in html, "Ostalo sekcija BEZ specifikacija NE SME biti render-ovana."


@pytest.mark.xfail(
    reason=(
        "hu translations za 'Motor'/'Transmisija'/'Hidraulika'/'Ostalo' su PRAZNE u "
        "locale/hu/LC_MESSAGES/django.po (verifikovano live 2026-05-30 — msgstr ''). "
        "Dev/Mihas mora popuniti hu prevode pre nego ovaj test prođe — TEA blocker za "
        "Subtask 10.4 SM-D20 locale-aware Case/When verifikacija. Kad prevodi budu "
        "popunjeni, ovaj decorator se uklanja i test ima xpass effect (pytest exit 1)."
    ),
    strict=False,
)
def test_extended_section_labels_hu_locale(client):
    """AC5 (SM-D20): section_label Case/When per-request mora vratiti hu prevode kad je locale='hu'.

    Ovaj test verifikuje I-iter2-1 fix: ako se Case/When ekspresije postave na module-level,
    Value(gettext_lazy(...)) "freeze-uje" sr locale za sve buduće requeste. Premestanje
    Case/When unutar get_queryset() per-request je kanonski Django pattern.

    Test mora videti hu prevode (NE 'Motor' sr msgid) u <summary> tekstu.
    """
    activate("hu")
    brand = BrandFactory.create(name="Agri Tracking")
    series = SeriesFactory.create_extended(brand=brand, name="Extended Serija")
    product = ProductFactory.create(brand=brand, series=series, name="Model X")
    ProductSpecificationFactory.create(product=product, section="motor", key="Erő")
    ProductSpecificationFactory.create(product=product, section="transmisija", key="Sebesség")

    url = f"/hu/traktori/{brand.slug}/"
    response = client.get(url)
    assert response.status_code == 200, (
        f"Brand detail strana (hu locale) mora vratiti 200, dobio {response.status_code}."
    )
    html = response.content.decode("utf-8")
    # Pozitivna proba: brand_detail.html stvarno renderovan + Motor sekcija prisutna
    assert 'data-testid="brand-detail-page"' in html, (
        "Brand_detail.html MORA biti renderovan pre nego što asertujemo na sadržaj sekcija."
    )

    # Očekuje da hu prevod ZA "Motor" NIJE jednak srpskoj reči "Motor" —
    # ali pošto je "Motor" identičan u oba jezika (uobičajen termin), umesto pozitivnog
    # assertion-a, asertujemo da je hu msgstr za "Transmisija" različit od sr msgid.
    # Konkretan hu msgstr je TBD — kad Dev/Mihas popuni, test treba updateovati na
    # eksplicitnu reč (npr. "Hajtómű" ako prevodilac to bira).
    #
    # Konzervativno: očekujemo da BAREM JEDAN od 4 termina ima različitu vrednost
    # u render-u kad je locale='hu' vs default sr. Pošto su sva 4 msgstr-a trenutno
    # PRAZNA, Django fallback vraća msgid sam (sr) → svi se renderuju isto kao u sr.
    # → ovaj assert PADA u trenutnom stanju (po dizajnu xfail).
    # Kad hu prevodi budu popunjeni, "Transmisija" (sr msgid) NE SME biti u hu render-u
    # (osim ako prevodilac slučajno koristi istu reč — što je ok za "Motor" ali ne za "Transmisija").
    assert "Transmisija" not in html, (
        "Sa popunjenim hu prevodom, 'Transmisija' (sr msgid) NE SME biti u hu render-u — "
        "očekujemo hu msgstr (npr. 'Hajtómű' ili sličan). Verifikuj da "
        "locale/hu/LC_MESSAGES/django.po ima popunjene msgstr-ove za "
        "'Motor', 'Transmisija', 'Hidraulika', 'Ostalo'."
    )


# =============================================================================
# AC6 — Statistic medallions (value + label, no icon, data-count-target, slice 4)
# =============================================================================


def test_medallion_renders_value_and_label_without_icon(client):
    """AC6 (C7 fix): medallion sadrži value + label, NEMA <i class="bi"> (Bootstrap Icons deferred to 9-10)."""
    activate("sr")
    brand = BrandFactory.create_with_statistics(
        name="Agri Tracking",
        stats=[
            {"value": 5000, "label": "Prodatih traktora"},
            {"value": 25, "label": "Godina"},
        ],
    )

    url = f"/sr/traktori/{brand.slug}/"
    response = client.get(url)
    html = response.content.decode("utf-8")

    # value postoji
    assert 'data-count-target="5000"' in html, (
        "Medallion MORA imati data-count-target='5000' za JS count-up animation."
    )
    assert 'data-count-target="25"' in html, "Medallion MORA imati data-count-target='25'."
    # label postoji
    assert "Prodatih traktora" in html, "Medallion label MORA biti render-ovana."
    assert "Godina" in html, "Medallion label MORA biti render-ovana."
    # NEMA <i class="bi ...">  (SM-D18 C7 fix — Bootstrap Icons NIJE wired u v1)
    bi_pattern = re.compile(r'<i\s+class="[^"]*\bbi[\s-]', re.IGNORECASE)
    assert not bi_pattern.search(html), (
        "C7 fix: NEMA <i class='bi ...'> elemenata u medallion-u — Bootstrap Icons font "
        "NIJE wired u v1 (deferred Story 9-10 polish per SM-D18)."
    )


def test_medallion_slice_caps_at_4(client):
    """AC6: defensive |slice:":4" filter — admin omaške upisivanje > 4 entry-ja je odsečeno."""
    activate("sr")
    # Brand.clean() limit-uje na 4, ali test koristi raw stats list da verifikuje template defensive
    # filter (caller koji bypass-uje admin formu ne sme da prebije medaljon grid).
    # Bypass: kreiramo brand sa 4 (max), zatim sirovo postavimo 6 u JSONField (bez full_clean).
    brand = BrandFactory.create_with_statistics(name="Agri Tracking")
    brand.statistics = [
        {"value": i, "label": f"Label {i}"} for i in range(1, 7)  # 6 items
    ]
    # Bypass full_clean — testiramo template defensive
    type(brand).objects.filter(pk=brand.pk).update(statistics=brand.statistics)

    url = f"/sr/traktori/{brand.slug}/"
    response = client.get(url)
    html = response.content.decode("utf-8")

    # Prvi 4 MORAJU biti render-ovane
    for i in range(1, 5):
        assert f'data-count-target="{i}"' in html, f"Medallion {i} MORA biti render-ovana."
    # 5. i 6. NE SMEJU biti render-ovane (|slice:":4" defensive)
    assert 'data-count-target="5"' not in html, (
        "Medallion 5 NE SME biti render-ovana — template MORA imati |slice:':4' defensive filter."
    )
    assert 'data-count-target="6"' not in html, "Medallion 6 NE SME biti render-ovana."


def test_medallion_section_hidden_when_no_statistics(client):
    """AC6: ako brand.statistics prazan, sekcija medaljona se NE renderuje (no empty container)."""
    activate("sr")
    brand = BrandFactory.create(name="Agri Tracking", statistics=[])
    # Dodaj seriju + produkt da pun template render mora ipak da prođe (200, ne 404)
    series = SeriesFactory.create_grid(brand=brand)
    ProductFactory.create(brand=brand, series=series)

    url = f"/sr/traktori/{brand.slug}/"
    response = client.get(url)
    assert response.status_code == 200, (
        f"Pre testiranja negative assertion-a, brand detail strana mora vratiti 200 "
        f"(dobio {response.status_code}). Verifikuj da BrandDetailView + urls postoje."
    )
    html = response.content.decode("utf-8")

    # Pozitivna proba: brand_detail.html stvarno render-ovan (ne 404)
    assert 'data-testid="brand-detail-page"' in html, (
        "Pre negative assertion-a, brand_detail.html MORA biti renderovan (data-testid markeruje root)."
    )

    assert 'id="brand-statistics"' not in html, (
        "Sekcija statistike (id='brand-statistics') NE SME biti render-ovana kad brand.statistics "
        "je prazan ({% if brand.statistics %} guard u brand_detail.html)."
    )


# =============================================================================
# AC7 — Testimonials slider (markup + pause/play + keyboard + single-testimonial hides controls)
# =============================================================================


def test_testimonials_slider_markup_renders_with_aria_roles(client):
    """AC7: slider ima role='region' + aria-label + data-testimonials-slider attribute."""
    activate("sr")
    brand = BrandFactory.create(name="Agri Tracking")
    series = SeriesFactory.create_grid(brand=brand)
    product = ProductFactory.create(brand=brand, series=series)
    ProductTestimonialFactory.create(product=product, author_name="Marko", quote="Odlični!")
    ProductTestimonialFactory.create(product=product, author_name="Stojan", quote="Top!")

    url = f"/sr/traktori/{brand.slug}/"
    response = client.get(url)
    html = response.content.decode("utf-8")

    assert "data-testimonials-slider" in html, (
        "Slider root MORA imati 'data-testimonials-slider' attribute za JS init selector."
    )
    assert 'role="region"' in html, "Slider MORA imati role='region' za a11y landmark."
    # aria-roledescription="karusel" (translated)
    assert "aria-roledescription=" in html, (
        "Slider MORA imati aria-roledescription attribute (npr. 'karusel' / 'carousel')."
    )
    # Quote text se renderuje
    assert "Odlični!" in html, "Quote text mora biti render-ovan u slider-u."


def test_testimonials_slider_pause_button_has_aria_pressed(client):
    """AC7: pause button MORA biti <button> sa aria-pressed='false' inicijalno."""
    activate("sr")
    brand = BrandFactory.create(name="Agri Tracking")
    series = SeriesFactory.create_grid(brand=brand)
    product = ProductFactory.create(brand=brand, series=series)
    ProductTestimonialFactory.create(product=product, author_name="Marko")
    ProductTestimonialFactory.create(product=product, author_name="Stojan")

    url = f"/sr/traktori/{brand.slug}/"
    response = client.get(url)
    html = response.content.decode("utf-8")

    # data-slider-pause selektor + aria-pressed='false' (inicijalno auto-advance je aktivan)
    pause_pattern = re.compile(
        r'<button[^>]*data-slider-pause[^>]*aria-pressed="false"',
        re.IGNORECASE,
    )
    # Atributi mogu biti u bilo kom redosledu — fallback pattern
    pause_pattern2 = re.compile(
        r'<button[^>]*aria-pressed="false"[^>]*data-slider-pause',
        re.IGNORECASE,
    )
    assert pause_pattern.search(html) or pause_pattern2.search(html), (
        "Pause button MORA biti <button> sa atributima data-slider-pause + aria-pressed='false' "
        f"(inicijalno auto-advance aktivan). HTML snippet: {html[html.find('coric-testimonials'):html.find('coric-testimonials')+1500]!r}"
    )


def test_testimonials_slider_has_prev_next_data_testid(client):
    """AC7: prev/next/pause buttons imaju data-testid atribute za Playwright."""
    activate("sr")
    brand = BrandFactory.create(name="Agri Tracking")
    series = SeriesFactory.create_grid(brand=brand)
    product = ProductFactory.create(brand=brand, series=series)
    ProductTestimonialFactory.create(product=product, author_name="Marko")
    ProductTestimonialFactory.create(product=product, author_name="Stojan")

    url = f"/sr/traktori/{brand.slug}/"
    response = client.get(url)
    html = response.content.decode("utf-8")

    assert 'data-testid="prev-testimonial"' in html, (
        "Prev button MORA imati data-testid='prev-testimonial'."
    )
    assert 'data-testid="next-testimonial"' in html, (
        "Next button MORA imati data-testid='next-testimonial'."
    )
    assert 'data-testid="pause-testimonial"' in html, (
        "Pause button MORA imati data-testid='pause-testimonial'."
    )


def test_testimonials_section_hidden_when_no_testimonials(client):
    """AC7: ako testimonials queryset prazan, sekcija slider-a se NE renderuje."""
    activate("sr")
    brand = BrandFactory.create(name="Agri Tracking")
    series = SeriesFactory.create_grid(brand=brand)
    ProductFactory.create(brand=brand, series=series)
    # NEMA testimonijala

    url = f"/sr/traktori/{brand.slug}/"
    response = client.get(url)
    assert response.status_code == 200, (
        f"Brand detail strana mora vratiti 200 (dobio {response.status_code})."
    )
    html = response.content.decode("utf-8")
    # Pozitivna proba: brand_detail.html render-ovan
    assert 'data-testid="brand-detail-page"' in html, (
        "Pre negative assertion-a, brand_detail.html MORA biti renderovan."
    )

    assert 'id="brand-testimonials"' not in html, (
        "Sekcija testimonijala NE SME biti render-ovana kad testimonials queryset je prazan "
        "({% if testimonials %} guard)."
    )
    assert "data-testimonials-slider" not in html, (
        "Slider markup NE SME biti render-ovan kad nema testimonijala."
    )


# =============================================================================
# AC8 — i18n + a11y (translate markers + semantic HTML5 + html lang + no bi icons)
# =============================================================================


def test_html_lang_attribute_present(client):
    """AC8: <html lang="sr"> postavljen iz base.html (Story 1.4 deliverable)."""
    activate("sr")
    brand = BrandFactory.create(name="Agri Tracking")

    url = f"/sr/traktori/{brand.slug}/"
    response = client.get(url)
    html = response.content.decode("utf-8")

    assert re.search(r'<html\s+lang="sr"', html), (
        "Render MORA imati <html lang='sr'> za sr locale (base.html line 6 — {{ LANGUAGE_CODE }})."
    )


def test_no_bootstrap_icons_in_brand_listing_render(client):
    """AC8 (SM-D18 C7 fix): NEMA <i class="bi ..."> elemenata u brand listing render-u."""
    activate("sr")
    brand = _full_brand_fixture()

    url = f"/sr/traktori/{brand.slug}/"
    response = client.get(url)
    assert response.status_code == 200, (
        f"Brand detail strana mora vratiti 200 (dobio {response.status_code})."
    )
    html = response.content.decode("utf-8")
    # Pozitivna proba: brand_detail.html render-ovan
    assert 'data-testid="brand-detail-page"' in html, (
        "Pre negative assertion-a, brand_detail.html MORA biti renderovan."
    )

    bi_pattern = re.compile(r'<i\s+class="[^"]*\bbi[\s-]', re.IGNORECASE)
    matches = bi_pattern.findall(html)
    assert not matches, (
        f"C7 fix: NEMA <i class='bi-...'> elemenata u brand listing — Bootstrap Icons font "
        f"NIJE wired u v1 (deferred Story 9-10 per SM-D18). Pronađen: {matches!r}."
    )


def test_no_hardcoded_serbian_in_template_only_translatable(client):
    """AC8: sve user-facing string-ove kroz {% translate %} — minimalna pozitivna proba.

    Test renderuje brand listing pod sr lokalom i verifikuje da su sve ključne user-facing
    fraze ("Preuzmi katalog", "OPŠIRNIJE", "Pauziraj", "Prethodni", "Sledeći") prisutne
    u render-u. To garantuje da su ove fraze prošle kroz template render path (ne mrtav
    kod), ali sam test NE razlikuje hardcoded vs {% translate %} marker.

    Strožiji test (rendering pod hu lokalom + assertEquals different string) traži
    popunjene hu prevode (locale/hu/LC_MESSAGES/django.po trenutno prazno za većinu
    Story 2.6 fraza); fallback na msgid daje isti render kao sr, pa pozitivna proba
    pod hu ne bi razlikovala properly translated od hardcoded sr.

    PROŠIRENI assertion (kad hu prevodi budu populated): videti xfail-ovan
    `test_extended_section_labels_hu_locale` za pattern.
    """
    activate("sr")
    brand = _full_brand_fixture()
    from django.core.files.base import ContentFile

    brand.catalog_pdf.save("stub.pdf", ContentFile(b"%PDF-1.4 stub"), save=True)

    url = f"/sr/traktori/{brand.slug}/"
    response = client.get(url)
    html = response.content.decode("utf-8")

    # Pozitivna proba: brand_detail.html stvarno render-ovan (jasna failure poruka ako 404)
    assert 'data-testid="brand-detail-page"' in html, (
        "Pre asertacije fraza, brand_detail.html MORA biti renderovan (data-testid markeruje root)."
    )

    # Ključne user-facing fraze koje moraju biti render-ovane kroz {% translate %}.
    # Story spec eksplicitno propisuje TAČAN srpski tekst za svaku — ako Dev hardcode-uje
    # ili omaške parafrazira, test pada (regression guard za "no hardcoded English/parafraza").
    required_translations = {
        "Preuzmi katalog": "AC3 § Catalog CTA banner",
        "OPŠIRNIJE": "AC4 § Grid kartica CTA + AC5 § Extended row CTA",
        "Pauziraj": "AC7 § Testimonials slider pause button aria-label",
        "Prethodni": "AC7 § Testimonials slider prev button aria-label",
        "Sledeći": "AC7 § Testimonials slider next button aria-label",
    }
    for phrase, location in required_translations.items():
        assert phrase in html, (
            f"Fraza '{phrase}' MORA biti render-ovana ({location}). "
            f"Verifikuj da template koristi {{% translate \"{phrase}\" %}} (NE hardcoded "
            "ili parafraziran tekst). Ako fraza ne postoji u render-u, sekcija je možda "
            "uslovno-skrivena — proveri fixture data."
        )


def test_semantic_html5_section_landmarks_in_render(client):
    """AC8: sve sekcije moraju biti <section> elementi (NE <div>) sa aria-labelledby."""
    activate("sr")
    brand = _full_brand_fixture()

    url = f"/sr/traktori/{brand.slug}/"
    response = client.get(url)
    html = response.content.decode("utf-8")

    # Pronađi sve "id='brand-...'" id-jeve i verifikuj da su unutar <section> tag-a
    # Heuristika: <section ... id="brand-hero"> ili <section ... id="brand-statistics">
    for section_id in ["brand-hero", "brand-series"]:
        section_pattern = re.compile(
            rf'<section[^>]*id="{section_id}"', re.IGNORECASE
        )
        assert section_pattern.search(html), (
            f"id='{section_id}' MORA biti na <section> elementu (a11y semantic landmark), "
            "NE na <div>."
        )


# =============================================================================
# Code review iter-1 — Test gaps (T1/T2/T3)
# =============================================================================


def test_brand_detail_renders_exactly_one_h1(client):
    """T1 (code review iter-1, B1 parallel): brand_detail.html MORA imati TAČNO 1 <h1>.

    Bug B1 fix uklonio je visually-hidden <h1 id="brand-hero-title"> iz
    _hero_section.html jer je hero_overlay_card.html partial već renderovao
    svoj <h1 class="coric-hero-overlay-card__title">. WCAG / Lighthouse traže
    tačno jedan <h1> per stranica.
    """
    activate("sr")
    brand = _full_brand_fixture()

    url = f"/sr/traktori/{brand.slug}/"
    response = client.get(url)
    html = response.content.decode("utf-8")

    h1_count = len(re.findall(r"<h1\b", html, flags=re.IGNORECASE))
    assert h1_count == 1, (
        f"brand_detail.html MORA imati TAČNO 1 <h1>, pronađeno {h1_count}. "
        "Hero_overlay_card partial pruža jedini <h1> (uklonjen duplikat iz "
        "_hero_section.html — B1 fix)."
    )


def test_unpublished_products_excluded_from_brand_listing(client):
    """T2 (code review iter-1): unpublished produkti NE SMEJU biti renderovani.

    BrandDetailView.get_queryset() filtruje Prefetch sa
    Product.objects.filter(is_published=True). Test verifikuje da template
    veruje prefetch filter-u (defensive {% if product.is_published %} guard
    je uklonjen — B3 fix).
    """
    activate("sr")
    brand = BrandFactory.create(name="Agri Tracking")
    series = SeriesFactory.create_grid(brand=brand, name="Grid Serija")
    ProductFactory.create(brand=brand, series=series, name="Published Model Visible")
    ProductFactory.create_unpublished(
        brand=brand, series=series, name="Unpublished Model Hidden"
    )

    url = f"/sr/traktori/{brand.slug}/"
    response = client.get(url)
    html = response.content.decode("utf-8")

    assert "Published Model Visible" in html, (
        "Published produkt MORA biti renderovan u grid-u."
    )
    assert "Unpublished Model Hidden" not in html, (
        "Unpublished produkt NE SME biti renderovan — Prefetch queryset filtruje "
        "is_published=True (apps/brands/views.py get_queryset())."
    )


def test_empty_series_shows_empty_state_message(client):
    """T3 (code review iter-1): serija bez published produkata pokazuje {% empty %} poruku.

    _series_grid.html i _series_extended.html oba imaju {% empty %} branch sa
    porukom 'Modeli ove serije su u pripremi.' kad series.products.all (filtriran
    kroz Prefetch sa is_published=True) vrati praznu listu.
    """
    activate("sr")
    brand = BrandFactory.create(name="Agri Tracking")
    series = SeriesFactory.create_grid(brand=brand, name="Prazna Serija")
    # NEMA published produkata — samo unpublished (isključen iz prefetch-a)
    ProductFactory.create_unpublished(brand=brand, series=series, name="Hidden")

    url = f"/sr/traktori/{brand.slug}/"
    response = client.get(url)
    html = response.content.decode("utf-8")

    assert "Modeli ove serije su u pripremi." in html, (
        "Empty-state poruka 'Modeli ove serije su u pripremi.' MORA biti "
        "renderovana kad serija nema published produkata "
        "({% empty %} branch u _series_grid.html / _series_extended.html)."
    )
