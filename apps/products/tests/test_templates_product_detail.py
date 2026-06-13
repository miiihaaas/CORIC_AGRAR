"""Story 2.7 — Product detail templates + partials tests (RED phase TDD).

Pokriva AC3 (page structure + sections in correct order + single h1 + single main +
testimonials product-specific aria id) + AC4 (gallery carousel + GLightbox auto-pickup) +
AC5 (specs accordion + Motor open + empty section skip + hu locale xfail) + AC6 (similar
products linkable card + nested-interactive guard + max 4 + wave divider) + AC7 (brochure
card + cover thumbnail + size label + PDF download + plural heading + PDF translatable +
cover empty .name guard) + AC8 (variants with/without image + glightbox slug-scoped data-gallery +
no state change markup audit).

Naming: srpska latinica + engleski code identifiers (per project-context.md).
TEA RED phase: SVI testovi MORAJU pasti dok Dev ne implementira ProductDetailView +
sve partials.

Pokrenuti sa:
    docker compose -f compose/local.yml exec django uv run pytest \\
        apps/products/tests/test_templates_product_detail.py -v

Refs:
- 2-7-product-detail-strana.md (AC3-AC8 + Subtask 12.3 + 12.4)
- 2-7-interface-contract.md (template + partial canonical contract)
"""

from __future__ import annotations

import re

import pytest
from django.utils.translation import activate

from apps.brands.tests.factories import BrandFactory, SeriesFactory
from apps.products.tests.factories import (
    ProductBrochureFactory,
    ProductFactory,
    ProductImageFactory,
    ProductSimilarFactory,
    ProductSpecificationFactory,
    ProductTestimonialFactory,
    ProductVariantFactory,
)

pytestmark = pytest.mark.django_db


# =============================================================================
# Helpers
# =============================================================================


def _full_product_fixture(slug_suffix=""):
    """Helper: kreira product sa svim sekcijama (gallery + specs + brochure + similar +
    testimonials + variants) za sektijske testove.
    """
    brand = BrandFactory.create(name=f"Test Brand {slug_suffix}")
    series = SeriesFactory.create_grid(brand=brand, name=f"Test Series {slug_suffix}")
    product = ProductFactory.create(
        brand=brand,
        series=series,
        name=f"Test Product {slug_suffix}",
        description="Test opis proizvoda.\nDrugi paragraf.",
        key_features=["Feature 1", "Feature 2"],
        is_published=True,
    )
    # Gallery (2 images)
    ProductImageFactory.create(product=product, order=0, alt_text="Slika 1")
    ProductImageFactory.create(product=product, order=1, alt_text="Slika 2")
    # Specs (4 sections)
    ProductSpecificationFactory.create(product=product, section="hidraulika", key="Pumpa", value="Bosch")
    ProductSpecificationFactory.create(product=product, section="motor", key="Snaga", value="200 KS")
    ProductSpecificationFactory.create(product=product, section="ostalo", key="Boja", value="Žuta")
    ProductSpecificationFactory.create(product=product, section="transmisija", key="Brzina", value="40 km/h")
    # Brochure (with cover)
    ProductBrochureFactory.create_with_cover(product=product, title="Glavna brošura")
    # Similar (manual override)
    other = ProductFactory.create(brand=brand, name=f"Similar {slug_suffix}", is_published=True)
    ProductSimilarFactory.create(product=product, related_product=other)
    # Testimonials
    ProductTestimonialFactory.create(product=product, author_name="Marko", quote="Odlični traktor.")
    # Variants (1 with image, 1 without)
    ProductVariantFactory.create_with_image(product=product, name="Sa kabinom", code="VAR-001", order=0)
    ProductVariantFactory.create(product=product, name="Bez kabine", code="VAR-002", order=1)
    return product


# =============================================================================
# AC3 — Page structure: section order + article wrapper + single h1 + single main +
# testimonials product-specific aria id
# =============================================================================


def test_sections_render_in_correct_order(client):
    """AC3: hero → opis → galerija → specs → brošura → slični → testimonijali → variants
    TAČNIM redosledom (verifikuje monotono rastuće position indices u HTML render-u).
    """
    activate("sr")
    product = _full_product_fixture("AC3-order")
    url = f"/sr/proizvod/{product.slug}/"

    response = client.get(url, HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    hero_idx = html.find('id="product-hero"')
    desc_idx = html.find('id="product-description"')
    gallery_idx = html.find('id="product-gallery"')
    specs_idx = html.find('id="product-specs"')
    brochure_idx = html.find('aria-labelledby="product-brochure-title"')
    similar_idx = html.find('id="product-similar"')
    testimonials_idx = html.find('id="product-testimonials"')
    variants_idx = html.find('id="product-variants"')

    assert hero_idx >= 0, "Hero sekcija (#product-hero) MORA postojati."
    assert desc_idx >= 0, "Opis sekcija (#product-description) MORA postojati (product ima description)."
    assert gallery_idx >= 0, "Galerija sekcija (#product-gallery) MORA postojati (product ima images)."
    assert specs_idx >= 0, "Specs sekcija (#product-specs) MORA postojati (product ima specifications)."
    assert brochure_idx >= 0, "Brošure sekcija MORA postojati (product ima brochures_list)."
    assert similar_idx >= 0, "Slični modeli sekcija (#product-similar) MORA postojati."
    assert testimonials_idx >= 0, "Testimonijali sekcija (#product-testimonials) MORA postojati."
    assert variants_idx >= 0, "Variants sekcija (#product-variants) MORA postojati."

    assert (
        hero_idx < desc_idx < gallery_idx < specs_idx < brochure_idx
        < similar_idx < testimonials_idx < variants_idx
    ), (
        f"Section order BROKEN. Pozicije: hero={hero_idx} desc={desc_idx} gallery={gallery_idx} "
        f"specs={specs_idx} brochure={brochure_idx} similar={similar_idx} test={testimonials_idx} "
        f"variants={variants_idx}. "
        "Očekivan: hero < opis < galerija < specs < brošura < slični < testimonijali < variants."
    )


def test_article_outer_wrapper_with_testid(client):
    """AC3: outer wrapper je <article class="coric-product-detail" data-testid="product-detail-page">."""
    activate("sr")
    product = ProductFactory.create(name="Wrapper Test", is_published=True)
    url = f"/sr/proizvod/{product.slug}/"

    response = client.get(url, HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # Article wrapper sa coric-product-detail klasom i data-testid atributom
    article_pattern = re.compile(
        r'<article[^>]*class="[^"]*coric-product-detail[^"]*"[^>]*data-testid="product-detail-page"',
        re.IGNORECASE,
    )
    article_pattern_alt = re.compile(
        r'<article[^>]*data-testid="product-detail-page"[^>]*class="[^"]*coric-product-detail',
        re.IGNORECASE,
    )
    assert article_pattern.search(html) or article_pattern_alt.search(html), (
        "Outer wrapper MORA biti <article class='coric-product-detail' "
        "data-testid='product-detail-page'> (SM-D9 + I7 regression guard)."
    )


def test_exactly_one_h1_on_page(client):
    """AC3 (SM-D8 / Story 2.6 B1 fix mirror): TAČNO 1 <h1> na strani.

    Hero card delegate `<h1>` kroz hero_overlay_card.html partial (product.name).
    Sve podsekcije koriste <h2> (visible ili visually-hidden).
    """
    activate("sr")
    product = _full_product_fixture("AC3-h1")
    url = f"/sr/proizvod/{product.slug}/"

    response = client.get(url, HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    h1_pattern = re.compile(r"<h1\b[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)
    h1_matches = h1_pattern.findall(html)
    assert len(h1_matches) == 1, (
        f"Product detail strana MORA imati TAČNO 1 <h1> element (SM-D8 single-h1 rule). "
        f"Pronađeno {len(h1_matches)}. H1 contents: {h1_matches!r}. "
        "Hero card delegate <h1> kroz hero_overlay_card.html — nijedna druga sekcija ne sme h1."
    )
    # Optional: verify h1 contains product.name (case-insensitive substring)
    h1_text = h1_matches[0]
    assert product.name in h1_text, (
        f"Jedini <h1> MORA sadržati product.name='{product.name}'; dobio: {h1_text!r}."
    )


def test_product_detail_has_single_main_element(client):
    """AC3 (SM Fix iter 1 I7 — mirror Story 2.6 B1 nested-main guard):
    TAČNO 1 <main> element u render-u (base.html provider).

    Outer <article> wrapper MORA sedeti INSIDE <main id="main-content">, NE replace
    ili wrap u sopstveni <main>. HTML5 spec: jedan <main> per dokument.
    """
    activate("sr")
    product = ProductFactory.create(name="Single Main Test", is_published=True)
    url = f"/sr/proizvod/{product.slug}/"

    response = client.get(url, HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    main_pattern = re.compile(r"<main\b[^>]*>", re.IGNORECASE)
    main_matches = main_pattern.findall(html)
    assert main_matches, "Render MORA imati bar 1 <main> element (base.html provider)."
    assert len(main_matches) == 1, (
        f"Product detail render MORA imati TAČNO 1 <main> element (HTML5 spec — "
        f"nested <main> je invalid). Pronađeno {len(main_matches)}: {main_matches!r}. "
        "product_detail.html outer wrapper MORA biti <article>, NE drugi <main>."
    )


def test_testimonials_section_uses_product_specific_aria_id(client):
    """AC3 (SM-D27 / I-iter2-2 — future-collision guard):
    Testimonijali sekcija aria-labelledby='product-testimonials-title' (story-specific ID),
    NE generic 'testimonials-title' ni brand-specific 'brand-testimonials-title'.

    Shared partial `templates/partials/_testimonials_slider.html` prima `slider_id` kwarg;
    product konzument prosleđuje `slider_id="product-testimonials-title"` per SM-D27.
    """
    activate("sr")
    product = ProductFactory.create(name="Testimonial Product", is_published=True)
    ProductTestimonialFactory.create(product=product, author_name="Stojan", quote="Sjajno!")
    url = f"/sr/proizvod/{product.slug}/"

    response = client.get(url, HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # Pozitivna proba: section i h2 koriste 'product-testimonials-title'
    assert 'aria-labelledby="product-testimonials-title"' in html, (
        "Testimonijali sekcija MORA imati aria-labelledby='product-testimonials-title' "
        "(SM-D27 story-specific ID future-collision guard)."
    )
    assert 'id="product-testimonials-title"' in html, (
        "Shared testimonials partial MORA renderovati <h2 id='product-testimonials-title'> "
        "kad product konzument prosleđuje slider_id='product-testimonials-title' kwarg."
    )
    # Negativna proba: NE SME postojati brand-testimonials-title na product page-u
    # (taj ID je rezervisan za brand listing strana per SM-D27)
    assert 'id="brand-testimonials-title"' not in html, (
        "Product detail strana NE SME imati id='brand-testimonials-title' "
        "(SM-D27 — brand ID je rezervisan za brand listing; cross-pollution guard)."
    )


# =============================================================================
# AC4 — Galerija karusel (responsive_picture + GLightbox auto-pickup + alt fallback)
# =============================================================================


def test_gallery_renders_all_images(client):
    """AC4: galerija renderuje SVE ProductImage entries (2 fixture entries → 2 gallery items).
    """
    activate("sr")
    product = ProductFactory.create(name="Gallery Product", is_published=True)
    ProductImageFactory.create(product=product, order=0)
    ProductImageFactory.create(product=product, order=1)
    ProductImageFactory.create(product=product, order=2)
    url = f"/sr/proizvod/{product.slug}/"

    response = client.get(url, HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # 3 gallery-item-N data-testid atributa
    assert 'data-testid="gallery-item-1"' in html, "Galerija MORA renderovati 1. sliku."
    assert 'data-testid="gallery-item-2"' in html, "Galerija MORA renderovati 2. sliku."
    assert 'data-testid="gallery-item-3"' in html, "Galerija MORA renderovati 3. sliku."


def test_gallery_glightbox_data_attributes(client):
    """AC4: svaka slika je <a class="glightbox" data-gallery="product-{{ slug }}">
    (Story 2.5 GLightbox auto-pickup; slug-scoped data-gallery per SM-D10/D15).
    """
    activate("sr")
    product = ProductFactory.create(name="Lightbox Product", is_published=True)
    ProductImageFactory.create(product=product, order=0)
    url = f"/sr/proizvod/{product.slug}/"

    response = client.get(url, HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # data-gallery=product-<slug> mora postojati (slug-scoped)
    expected_data_gallery = f'data-gallery="product-{product.slug}"'
    assert expected_data_gallery in html, (
        f"Galerija slike MORAJU imati {expected_data_gallery!r} (slug-scoped per SM-D10/D15). "
        f"HTML snippet: {html[:1000]!r}"
    )
    # class="glightbox" mora biti na gallery item-u
    glightbox_pattern = re.compile(
        r'<a[^>]*class="[^"]*glightbox[^"]*"[^>]*data-gallery="product-'
        + re.escape(product.slug) + r'"',
        re.IGNORECASE,
    )
    glightbox_pattern_alt = re.compile(
        r'<a[^>]*data-gallery="product-' + re.escape(product.slug)
        + r'"[^>]*class="[^"]*glightbox[^"]*"',
        re.IGNORECASE,
    )
    assert glightbox_pattern.search(html) or glightbox_pattern_alt.search(html), (
        "Galerija slike MORAJU imati class='glightbox' + data-gallery='product-{slug}' "
        "(Story 2.5 auto-pickup pattern)."
    )


def test_gallery_responsive_picture_alt_text(client):
    """AC4: <picture> ima alt atribut (fallback iz image.alt_text ili product.name).
    a11y must-have per project-context.md § A11y."""
    activate("sr")
    product = ProductFactory.create(name="Alt Test Product", is_published=True)
    ProductImageFactory.create(product=product, order=0, alt_text="Konkretni alt tekst")
    url = f"/sr/proizvod/{product.slug}/"

    response = client.get(url, HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # alt='Konkretni alt tekst' mora postojati u render-u
    assert 'alt="Konkretni alt tekst"' in html, (
        "Galerija <img>/<picture> MORA imati alt atribut iz image.alt_text. "
        "responsive_picture tag MORA prosleđivati alt kwarg per AC4 + a11y must-have."
    )


# =============================================================================
# AC5 — Specs akordion (regroup + Motor open default + empty skip + native details/summary)
# =============================================================================


def test_specs_grouped_by_section_label(client):
    """AC5: specs grupisani po section_label TAČNIM redosledom Motor → Transmisija →
    Hidraulika → Ostalo (NE alphabetical)."""
    activate("sr")
    product = ProductFactory.create(name="Specs Order Product", is_published=True)
    # Kreiraj u SUPROTNOM redosledu (alphabetical: hidraulika, motor, ostalo, transmisija)
    ProductSpecificationFactory.create(product=product, section="hidraulika", key="Pumpa")
    ProductSpecificationFactory.create(product=product, section="motor", key="Snaga")
    ProductSpecificationFactory.create(product=product, section="ostalo", key="Boja")
    ProductSpecificationFactory.create(product=product, section="transmisija", key="Brzina")
    url = f"/sr/proizvod/{product.slug}/"

    response = client.get(url, HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    motor_idx = html.find(">Motor<")
    trans_idx = html.find(">Transmisija<")
    hidra_idx = html.find(">Hidraulika<")
    ostalo_idx = html.find(">Ostalo<")

    assert motor_idx >= 0, "Motor sekcija MORA biti render-ovana."
    assert trans_idx >= 0, "Transmisija sekcija MORA biti render-ovana."
    assert hidra_idx >= 0, "Hidraulika sekcija MORA biti render-ovana."
    assert ostalo_idx >= 0, "Ostalo sekcija MORA biti render-ovana."

    assert motor_idx < trans_idx < hidra_idx < ostalo_idx, (
        f"Section order BROKEN. Motor={motor_idx} Transmisija={trans_idx} "
        f"Hidraulika={hidra_idx} Ostalo={ostalo_idx}. "
        "section_rank Case/When annotation u get_queryset() MORA sortirati Motor=1 → "
        "Transmisija=2 → Hidraulika=3 → Ostalo=4."
    )


def test_motor_section_open_by_default(client):
    """AC5: prva accordion sekcija (Motor) MORA imati `<details open>`."""
    activate("sr")
    product = ProductFactory.create(name="Motor Open Test", is_published=True)
    ProductSpecificationFactory.create(product=product, section="motor", key="Snaga")
    ProductSpecificationFactory.create(product=product, section="transmisija", key="Brzina")
    url = f"/sr/proizvod/{product.slug}/"

    response = client.get(url, HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # Pronalazi PRVI <details> u render-u
    first_details = re.search(r"<details[^>]*>", html)
    assert first_details, "Bar jedan <details> mora postojati u accordion render-u."
    assert "open" in first_details.group(0), (
        f"Prva accordion sekcija (Motor — section_rank=1) MORA imati `open` atribut. "
        f"Pronađen: {first_details.group(0)!r}. Koristi `{{% if forloop.first %}}open{{% endif %}}`."
    )


def test_empty_section_skipped(client):
    """AC5: prazne sekcije se automatski preskaču kroz {% regroup %} (no empty <details>)."""
    activate("sr")
    product = ProductFactory.create(name="Empty Section Test", is_published=True)
    # SAMO Motor + Ostalo imaju spec — Transmisija + Hidraulika prazni
    ProductSpecificationFactory.create(product=product, section="motor", key="Snaga", value="200 KS")
    ProductSpecificationFactory.create(product=product, section="ostalo", key="Boja", value="Žuta")
    url = f"/sr/proizvod/{product.slug}/"

    response = client.get(url, HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert ">Motor<" in html, "Motor sekcija (sa spec) MORA biti render-ovana."
    assert ">Ostalo<" in html, "Ostalo sekcija (sa spec) MORA biti render-ovana."
    assert ">Transmisija<" not in html, (
        "Transmisija sekcija BEZ spec NE SME biti render-ovana ({% regroup %} skip)."
    )
    assert ">Hidraulika<" not in html, (
        "Hidraulika sekcija BEZ spec NE SME biti render-ovana ({% regroup %} skip)."
    )


def test_accordion_uses_native_details_summary(client):
    """AC5: akordion koristi native <details>/<summary> (keyboard-accessible besplatno)."""
    activate("sr")
    product = ProductFactory.create(name="Details Test", is_published=True)
    ProductSpecificationFactory.create(product=product, section="motor", key="Snaga")
    url = f"/sr/proizvod/{product.slug}/"

    response = client.get(url, HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert "<details" in html, (
        "Akordion MORA koristiti native <details> element (keyboard-accessible per HTML5 spec). "
        "Custom JS-based accordion NIJE acceptable — native daje Enter/Space toggle besplatno."
    )
    assert "<summary" in html, (
        "Akordion MORA koristiti <summary> element unutar <details> (HTML5 spec)."
    )


@pytest.mark.xfail(
    reason=(
        "hu translations za 'Motor'/'Transmisija'/'Hidraulika'/'Ostalo' su PRAZNE u "
        "locale/hu/LC_MESSAGES/django.po linije 309-323 (verifikovano live 2026-05-30 — "
        "msgstr ''). Dev/Mihas mora popuniti hu prevode pre nego ovaj test prođe — "
        "TEA blocker za Subtask 12.4 SM-D20 locale-aware Case/When verifikacija. "
        "Mirror Story 2.6 § AC5 hu locale xfail handling."
    ),
    strict=False,
)
def test_specs_section_labels_hu_locale(client):
    """AC5 (SM-D20 mirror): section_label Case/When per-request mora vratiti hu prevode
    kad je locale='hu'.

    Verifikuje da Case/When ekspresije UNUTAR get_queryset() (per-request) ispravno
    re-evaluat-uju gettext_lazy proxy za aktivnu lokalu. Module-level konstante bi
    "zamrznule" sr locale za sve buduće requeste.
    """
    activate("hu")
    product = ProductFactory.create(name="Hu Specs Product", is_published=True)
    ProductSpecificationFactory.create(product=product, section="motor", key="Erő")
    ProductSpecificationFactory.create(product=product, section="transmisija", key="Sebesség")
    url = f"/hu/proizvod/{product.slug}/"

    response = client.get(url, HTTP_HOST="localhost")
    assert response.status_code == 200, (
        f"Product detail strana (hu locale) MORA vratiti 200, dobio {response.status_code}."
    )
    html = response.content.decode("utf-8")
    assert 'data-testid="product-detail-page"' in html, (
        "Product detail MORA biti renderovan pre nego što asertujemo na sadržaj sekcija."
    )
    # Kad su hu prevodi popunjeni, 'Transmisija' (sr msgid) NE SME biti u hu render-u
    assert "Transmisija" not in html, (
        "Sa popunjenim hu prevodom, 'Transmisija' (sr msgid) NE SME biti u hu render-u — "
        "očekujemo hu msgstr (npr. 'Hajtómű'). Popuni `locale/hu/LC_MESSAGES/django.po` linije 309-323."
    )


# =============================================================================
# AC6 — Slični modeli (linkable card + nested-interactive guard + max 4 + wave divider)
# =============================================================================


def test_similar_cards_render_with_aria_label(client):
    """AC6: similar kartice su <a> wrapper sa aria-label='{product.name}'
    (a11y must-have — screen reader najavi link target)."""
    activate("sr")
    brand = BrandFactory.create(name="Similar Brand")
    product = ProductFactory.create(brand=brand, name="Source", is_published=True)
    similar = ProductFactory.create(brand=brand, name="John Deere 8R", is_published=True)
    ProductSimilarFactory.create(product=product, related_product=similar)
    url = f"/sr/proizvod/{product.slug}/"

    response = client.get(url, HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    aria_pattern = re.compile(
        r'<a[^>]*class="[^"]*coric-product-card[^"]*"[^>]*aria-label="John Deere 8R"',
        re.IGNORECASE,
    )
    aria_pattern_alt = re.compile(
        r'<a[^>]*aria-label="John Deere 8R"[^>]*class="[^"]*coric-product-card',
        re.IGNORECASE,
    )
    assert aria_pattern.search(html) or aria_pattern_alt.search(html), (
        "Similar kartica <a> MORA imati class='coric-product-card' + aria-label='{sim.name}' "
        "(reuse Story 2.6 linkable card pattern + AC6 nested-interactive guard)."
    )


def test_similar_cta_is_span_not_link(client):
    """AC6: CTA u similar kartici je <span aria-hidden="true"> (NE <a>/<button>) —
    nested-interactive guard per WCAG 2.1 SC 4.1.2 (mirror Story 2.6 I6 fix)."""
    activate("sr")
    brand = BrandFactory.create(name="CTA Brand")
    product = ProductFactory.create(brand=brand, name="Source", is_published=True)
    similar = ProductFactory.create(brand=brand, name="Similar Model", is_published=True)
    ProductSimilarFactory.create(product=product, related_product=similar)
    url = f"/sr/proizvod/{product.slug}/"

    response = client.get(url, HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    cta_pattern = re.compile(
        r'<span[^>]*class="[^"]*coric-product-card__cta[^"]*"[^>]*aria-hidden="true"',
        re.IGNORECASE,
    )
    cta_pattern_alt = re.compile(
        r'<span[^>]*aria-hidden="true"[^>]*class="[^"]*coric-product-card__cta',
        re.IGNORECASE,
    )
    assert cta_pattern.search(html) or cta_pattern_alt.search(html), (
        "Similar CTA 'OPŠIRNIJE' MORA biti <span aria-hidden='true'> (NE <a> ni <button>) — "
        "nested-interactive WCAG SC 4.1.2 guard."
    )


def test_max_4_similar_products(client):
    """AC6: similar grid renderuje MAXIMALNO 4 kartice (view limituje na 4).

    Setup: kreiraj 6 manual ProductSimilar entries — verifikuj samo 4 renderovane.
    """
    activate("sr")
    brand = BrandFactory.create(name="Max Test Brand")
    product = ProductFactory.create(brand=brand, name="Source", is_published=True)
    for i in range(6):
        sim = ProductFactory.create(brand=brand, name=f"Similar {i}", is_published=True)
        ProductSimilarFactory.create(product=product, related_product=sim, order=i)
    url = f"/sr/proizvod/{product.slug}/"

    response = client.get(url, HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # Count similar-product-card-* data-testid attributes
    similar_cards_pattern = re.compile(r'data-testid="similar-product-card-[^"]+"')
    matches = similar_cards_pattern.findall(html)
    assert len(matches) == 4, (
        f"Similar grid MORA renderovati TAČNO 4 kartice (view-layer limit per AC6). "
        f"Dobio {len(matches)}: {matches!r}."
    )


def test_wave_divider_rendered_above_similar_section(client):
    """AC6: Wave Divider partial je render-ovan iznad slični-modeli sekcije."""
    activate("sr")
    brand = BrandFactory.create(name="Wave Brand")
    product = ProductFactory.create(brand=brand, name="Source", is_published=True)
    other = ProductFactory.create(brand=brand, name="Other", is_published=True)
    ProductSimilarFactory.create(product=product, related_product=other)
    url = f"/sr/proizvod/{product.slug}/"

    response = client.get(url, HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # Wave divider markup mora biti pre product-similar sekcije
    # (assume wave_divider.html partial renderuje element sa "wave-divider" ili "coric-wave-divider"
    # u class name-u; verify by string presence + position)
    wave_pattern = re.compile(r"wave[-_]divider", re.IGNORECASE)
    wave_match = wave_pattern.search(html)
    similar_idx = html.find('id="product-similar"')
    assert wave_match is not None, (
        "Wave Divider partial MORA biti render-ovan na strani (uključuje keyword "
        "'wave-divider' u markup-u). Story 1.7 partial."
    )
    assert wave_match.start() < similar_idx, (
        f"Wave Divider ({wave_match.start()}) MORA biti PRE slični-modeli sekcije "
        f"(id='product-similar', pozicija {similar_idx}) — included sa position='top'."
    )


# =============================================================================
# AC7 — Brošure card (cover thumbnail + size label + PDF download + plural + PDF translatable +
# empty cover.name guard)
# =============================================================================


def test_brochure_renders_with_cover_thumbnail(client):
    """AC7: brošure card sa cover_thumbnail_image renderuje responsive_picture."""
    activate("sr")
    product = ProductFactory.create(name="Cover Brochure Product", is_published=True)
    ProductBrochureFactory.create_with_cover(product=product, title="Brošura sa cover-om")
    url = f"/sr/proizvod/{product.slug}/"

    response = client.get(url, HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # Brochure card mora biti renderovana sa <img> ili <picture> za cover
    # (responsive_picture renderuje <picture> sa nested <img>)
    assert "coric-product-brochure__cover" in html, (
        "Brošure sa cover_thumbnail_image MORAJU renderovati <div class='coric-product-brochure__cover'> "
        "(per AC7 partial spec)."
    )


def test_brochure_size_label_uses_filesizeformat(client):
    """AC7 (SM-D26/I8): brošure size label koristi {{ entry.size_bytes|filesizeformat }}
    (Django built-in filter — vraća 'X.X MB', 'YYY KB', itd.)."""
    activate("sr")
    product = ProductFactory.create(name="Size Brochure Product", is_published=True)
    ProductBrochureFactory.create(product=product, title="Test Brošura")
    url = f"/sr/proizvod/{product.slug}/"

    response = client.get(url, HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # filesizeformat output: "X bytes" / "Y KB" / "Z MB" — mora biti u render-u
    size_pattern = re.compile(r"\d+(?:[.,]\d+)?\s*(bytes|byte|KB|MB|GB)", re.IGNORECASE)
    assert size_pattern.search(html), (
        f"Brošure card MORA renderovati size label kroz filesizeformat filter "
        f"(očekivani format 'X.X MB' / 'Y KB' / 'Z bytes'). HTML snippet: {html[:2000]!r}"
    )


def test_brochure_download_anchor_target_blank_rel_noopener_download(client):
    """AC7: PDF download CTA je direktan <a> sa target='_blank' rel='noopener noreferrer' download
    atributima (NE pill_button.html partial — SM-D22 mirror Story 2.6)."""
    activate("sr")
    product = ProductFactory.create(name="Download Test", is_published=True)
    ProductBrochureFactory.create(product=product, title="DL Brošura")
    url = f"/sr/proizvod/{product.slug}/"

    response = client.get(url, HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # Anchor mora imati target='_blank' + rel='noopener noreferrer' + download.
    # Atributi mogu biti u bilo kom redosledu — permutacije kroz jedan regex bi bile
    # preglomazne; koristimo individual checks ispod.
    has_target_blank = re.search(
        r'<a[^>]*\bclass="[^"]*coric-button[^"]*"[^>]*target="_blank"', html
    ) or re.search(r'<a[^>]*target="_blank"[^>]*\bclass="[^"]*coric-button', html)
    has_rel_noopener = "rel=\"noopener noreferrer\"" in html or "rel='noopener noreferrer'" in html
    has_download = re.search(r'<a[^>]*\bdownload\b', html, re.IGNORECASE) is not None

    assert has_target_blank, (
        "Brošure download CTA MORA biti <a class='coric-button' target='_blank'> "
        "(otvara PDF u novom tabu). SM-D22 mirror Story 2.6 direct anchor pattern."
    )
    assert has_rel_noopener, (
        "Brošure download CTA MORA imati rel='noopener noreferrer' "
        "(security: target='_blank' bez rel je tabnabbing vuln)."
    )
    assert has_download, (
        "Brošure download CTA MORA imati `download` atribut (browser triggers download "
        "umesto navigacije)."
    )


def test_multiple_brochures_render_all(client):
    """AC7: ako product ima više brochures, sve renderuju kao odvojene karte."""
    activate("sr")
    product = ProductFactory.create(name="Multi Brochure", is_published=True)
    b1 = ProductBrochureFactory.create(product=product, title="Brošura 1")
    b2 = ProductBrochureFactory.create(product=product, title="Brošura 2")
    b3 = ProductBrochureFactory.create(product=product, title="Brošura 3")
    url = f"/sr/proizvod/{product.slug}/"

    response = client.get(url, HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    for b in (b1, b2, b3):
        assert f'data-testid="brochure-card-{b.id}"' in html, (
            f"Brochure {b.id} ({b.title}) MORA biti render-ovana sa data-testid='brochure-card-{b.id}'."
        )


def test_brochure_heading_pluralized_singular_vs_plural(client):
    """AC7 (SM-D24/I1): brošure heading koristi {% blocktranslate count %}{% plural %}{% endblocktranslate %}
    — N=1 daje 'Preuzmite brošuru' (singular), N≥2 daje 'Preuzmite brošure' (plural).
    """
    activate("sr")
    # N=1 test
    p1 = ProductFactory.create(name="Single Brochure Product", is_published=True)
    ProductBrochureFactory.create(product=p1, title="Brošura")
    response1 = client.get(f"/sr/proizvod/{p1.slug}/", HTTP_HOST="localhost")
    html1 = response1.content.decode("utf-8")
    assert "Preuzmite brošuru" in html1, (
        "N=1: heading MORA biti 'Preuzmite brošuru' (singular akuzativ). "
        "Koristi {% blocktranslate count counter=brochures_list|length %}Preuzmite brošuru{% plural %}"
        "Preuzmite brošure{% endblocktranslate %}."
    )

    # N=2 test (paucal: brošure)
    p2 = ProductFactory.create(name="Two Brochure Product", is_published=True)
    ProductBrochureFactory.create(product=p2, title="B1")
    ProductBrochureFactory.create(product=p2, title="B2")
    response2 = client.get(f"/sr/proizvod/{p2.slug}/", HTTP_HOST="localhost")
    html2 = response2.content.decode("utf-8")
    assert "Preuzmite brošure" in html2, (
        "N=2: heading MORA biti 'Preuzmite brošure' (paucal plural akuzativ). "
        "Singular 'brošuru' je gramatički netačno za N>1."
    )


def test_brochure_pdf_acronym_is_translatable(client):
    """AC7 (SM-D25/I3): 'PDF' acronym je wrapped kroz {% translate %} (policy compliance —
    sve user-facing strings kroz gettext, čak i acronyms koji su identični u sve lokale).
    """
    import pathlib

    template_path = pathlib.Path(__file__).resolve().parents[3] / "templates/products/partials/_brochure_card.html"
    assert template_path.exists(), (
        f"Template {template_path} MORA postojati (Story 2.7 Task 7). "
        "Test može asertirati sadržaj tek nakon Dev kreira partial."
    )
    content = template_path.read_text(encoding="utf-8")
    # Mora postojati {% translate "PDF" %} ili {% trans "PDF" %} u partial-u
    translate_pdf_pattern = re.compile(r'\{%\s*(translate|trans)\s+["\']PDF["\']\s*%\}', re.IGNORECASE)
    assert translate_pdf_pattern.search(content), (
        f"_brochure_card.html MORA wrap 'PDF' acronym kroz {{% translate 'PDF' %}} ili "
        f"{{% trans 'PDF' %}} per SM-D25/I3 policy compliance. Partial sadržaj: {content!r}"
    )


def test_brochure_cover_thumbnail_guard_handles_empty_name(client):
    """AC7 (SM-D26/I9): {% if brochure.cover_thumbnail_image and brochure.cover_thumbnail_image.name %}
    double guard — partial-state ImageField sa praznim .name NE SME renderovati <img>."""
    import pathlib

    template_path = pathlib.Path(__file__).resolve().parents[3] / "templates/products/partials/_brochure_card.html"
    assert template_path.exists(), (
        f"Template {template_path} MORA postojati (Story 2.7 Task 7)."
    )
    content = template_path.read_text(encoding="utf-8")
    # Mora postojati double guard `and .name` (ili equivalent)
    double_guard_pattern = re.compile(
        r'\{%\s*if\s+[^%]*cover_thumbnail_image[^%]*\.name[^%]*%\}',
        re.IGNORECASE,
    )
    assert double_guard_pattern.search(content), (
        f"_brochure_card.html MORA imati double guard `{{% if entry.brochure.cover_thumbnail_image "
        f"and entry.brochure.cover_thumbnail_image.name %}}` per SM-D26/I9 partial-state defense. "
        f"Sadržaj: {content!r}"
    )


# =============================================================================
# AC8 — Variants selektor (with/without image + glightbox slug-scoped + no state change)
# =============================================================================


def test_variant_card_with_image_renders_glightbox_anchor(client):
    """AC8: variant sa image renderuje <a class='glightbox' data-gallery='product-{slug}-variants'>."""
    activate("sr")
    product = ProductFactory.create(name="Variant Product", is_published=True)
    variant = ProductVariantFactory.create_with_image(product=product, name="Sa kabinom", code="VAR-001")
    url = f"/sr/proizvod/{product.slug}/"

    response = client.get(url, HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # data-gallery=product-{slug}-variants (RAZLIČIT od main gallery)
    expected_dg = f'data-gallery="product-{product.slug}-variants"'
    assert expected_dg in html, (
        f"Variant kartice sa image MORAJU imati {expected_dg!r} (slug-scoped per SM-D10/D15)."
    )
    # class='glightbox' na variant card-u
    variant_lightbox_pattern = re.compile(
        r'<a[^>]*class="[^"]*glightbox[^"]*coric-product-variants__card',
        re.IGNORECASE,
    )
    variant_lightbox_pattern_alt = re.compile(
        r'<a[^>]*class="[^"]*coric-product-variants__card[^"]*glightbox',
        re.IGNORECASE,
    )
    assert variant_lightbox_pattern.search(html) or variant_lightbox_pattern_alt.search(html), (
        "Variant kartica MORA biti <a class='glightbox coric-product-variants__card'> "
        "(Story 2.5 auto-pickup pattern)."
    )
    # data-testid sa variant.id
    assert f'data-testid="variant-card-{variant.id}"' in html, (
        f"Variant kartica MORA imati data-testid='variant-card-{variant.id}'."
    )


def test_variant_card_no_image_renders_plain_div(client):
    """AC8: variant bez image renderuje plain <div> (NE GLightbox link — defensive)."""
    activate("sr")
    product = ProductFactory.create(name="No Image Variant Product", is_published=True)
    variant = ProductVariantFactory.create(product=product, name="Bez slike", code="VAR-NO-IMG")
    url = f"/sr/proizvod/{product.slug}/"

    response = client.get(url, HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # Variant bez slike mora biti <div data-testid='variant-card-{id}'>, NE <a>
    div_pattern = re.compile(
        r'<div[^>]*class="[^"]*coric-product-variants__card[^"]*"[^>]*data-testid="variant-card-'
        + str(variant.id) + r'"',
        re.IGNORECASE,
    )
    div_pattern_alt = re.compile(
        r'<div[^>]*data-testid="variant-card-' + str(variant.id)
        + r'"[^>]*class="[^"]*coric-product-variants__card',
        re.IGNORECASE,
    )
    assert div_pattern.search(html) or div_pattern_alt.search(html), (
        f"Variant bez slike MORA biti <div class='coric-product-variants__card' "
        f"data-testid='variant-card-{variant.id}'>, NE <a> (defensive — no broken GLightbox link)."
    )
    # Provjeri da NE postoji <a> sa istim variant-id testid-jem
    invalid_anchor = re.search(
        r'<a[^>]*data-testid="variant-card-' + str(variant.id) + r'"', html, re.IGNORECASE
    )
    assert invalid_anchor is None, (
        f"Variant bez slike NE SME biti <a> element — pronađen: {invalid_anchor.group(0)!r}."
    )


def test_variant_no_state_change_no_form(client):
    """AC8 (PRD FR-48): variants partial MORA implementirati 'no state change' UX —
    NEMA <form>, NEMA data-variant-id JS hook, NEMA URL fragment-a.

    Klik na variant = TAČNO GLightbox zoom + ničega više.
    """
    import pathlib

    template_path = pathlib.Path(__file__).resolve().parents[3] / "templates/products/partials/_variants_selector.html"
    assert template_path.exists(), (
        f"Template {template_path} MORA postojati (Story 2.7 Task 9)."
    )
    content = template_path.read_text(encoding="utf-8")

    assert "<form" not in content, (
        f"_variants_selector.html NE SME imati <form> element (PRD FR-48 — no state change). "
        f"Sadržaj: {content!r}"
    )
    assert "data-variant-id" not in content, (
        f"_variants_selector.html NE SME imati `data-variant-id` JS hook (PRD FR-48 — no state change). "
        f"Sadržaj: {content!r}"
    )
    # NEMA URL fragment (#variant-X) — variant.id se koristi SAMO u data-testid, NE u href
    fragment_pattern = re.compile(r'href="#variant', re.IGNORECASE)
    assert not fragment_pattern.search(content), (
        f"_variants_selector.html NE SME imati `href='#variant-X'` URL fragment "
        f"(PRD FR-48 — no URL change). Sadržaj: {content!r}"
    )


def test_variant_data_gallery_distinct_from_main_gallery(client):
    """AC8 (SM-D10/D15): variant data-gallery 'product-{slug}-variants' MORA biti
    RAZLIČIT od main gallery 'product-{slug}' (sprečava prev/next preklapanje u GLightbox-u).
    """
    activate("sr")
    product = ProductFactory.create(name="Distinct Gallery Product", is_published=True)
    ProductImageFactory.create(product=product, order=0)  # main gallery
    ProductVariantFactory.create_with_image(product=product, name="Var 1")  # variant
    url = f"/sr/proizvod/{product.slug}/"

    response = client.get(url, HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    main_dg = f'data-gallery="product-{product.slug}"'
    variant_dg = f'data-gallery="product-{product.slug}-variants"'

    assert main_dg in html, f"Main gallery MORA imati {main_dg!r}."
    assert variant_dg in html, f"Variants MORA imati {variant_dg!r}."
    assert main_dg != variant_dg, (
        f"Main + variants data-gallery moraju biti RAZLIČITI. "
        f"Main={main_dg!r}, variants={variant_dg!r}."
    )
