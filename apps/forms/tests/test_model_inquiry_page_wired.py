"""Story 4.3 — AC9: wire model-inquiry forme u product detail stranu — TEA RED.

Pokriva AC9 / Task 5.1 + 5.2 (plain `client.get(product_url)` — ProductDetailView NETAKNUT,
NE prosleđuje `form`; partial se renderuje kroz {{ product.slug }}/{{ product.name }} fallback-e
sirov-`<input>` idiom, SM-D5):
- GET /sr/proizvod/<slug>/ (published) → 200; strana sadrži model-inquiry formu (NEMA disabled);
- forma ima `hx-post` ka forms:model_inquiry_submit;
- hidden product_slug value == product.slug;
- readonly model display sadrži product.name;
- anchor/sekcija id="product-inquiry" postoji (skroluj-do-forme);
- vidljiv CTA dugme sa href="#product-inquiry";
- CSRF token prisutan u renderovanoj formi (relociran iz Task 4.3);
- Regression: POST na products:detail i dalje 405 (ProductDetailView NETAKNUT);
- unpublished product GET → 404 (forma nedostupna).

RED razlog: {% block product_detail_inquiry %} je PRAZAN + forms:model_inquiry_submit URL ne
postoji → asercije za renderovanu formu / NoReverseMatch u template-u padaju.

Pokrenuti:
    just test apps/forms/tests/test_model_inquiry_page_wired.py -v

Refs: 4-3 AC9 + Task 5.1/5.2 + SM-D5; interface-contract § 7/8.
"""

from __future__ import annotations

import re

import pytest
from django.urls import reverse
from django.utils.translation import activate

from apps.products.tests.factories import ProductFactory

pytestmark = pytest.mark.django_db


def _product_html(client, product) -> str:
    activate("sr")
    url = reverse("products:detail", kwargs={"slug": product.slug})
    response = client.get(url)
    assert response.status_code == 200, (
        f"GET {url} (published) MORA biti 200, dobio {response.status_code}."
    )
    return response.content.decode("utf-8")


def _inquiry_section(html: str) -> str:
    """Izvuci SAMO sadržaj <section id="product-inquiry">...</section> (do prvog </section>).

    Asercije moraju biti scope-ovane na model-inquiry sekciju — inače H1/title (product.name)
    ILI header/language-switcher CSRF token daju FALSE-GREEN bez forme (block je još prazan u RED).
    """
    m = re.search(
        r'<section[^>]*id=["\']product-inquiry["\'][^>]*>(.*?)</section>',
        html,
        re.IGNORECASE | re.DOTALL,
    )
    return m.group(1) if m else ""


# AC-9: product detail (published) prikazuje model-inquiry formu sa hx-post ka endpoint-u
def test_page_has_model_inquiry_form_hx_post(client):
    product = ProductFactory.create(name="Agri Tracking TB804")
    html = _product_html(client, product)
    submit_url = reverse("forms:model_inquiry_submit")
    assert submit_url in html, (
        f"Product strana MORA imati hx-post ka forms:model_inquiry_submit ({submit_url}), AC9. "
        f"Sadržaj nije pronašao URL."
    )
    assert re.search(r"hx-post=", html, re.IGNORECASE), (
        "Model-inquiry forma na product strani MORA imati `hx-post` (AC9)."
    )


# AC-9: hidden product_slug value == product.slug
def test_page_has_hidden_product_slug(client):
    product = ProductFactory.create(name="Agri Tracking TB804")
    html = _product_html(client, product)
    hidden = re.search(
        r'<input[^>]*type=["\']hidden["\'][^>]*name=["\']product_slug["\'][^>]*>'
        r'|<input[^>]*name=["\']product_slug["\'][^>]*type=["\']hidden["\'][^>]*>',
        html,
        re.IGNORECASE,
    )
    assert hidden, "Forma MORA imati hidden <input name=\"product_slug\"> (AC9/SM-D5)."
    assert product.slug in hidden.group(0), (
        f"Hidden product_slug value MORA biti product.slug={product.slug!r}, dobio {hidden.group(0)!r}."
    )


# AC-9: readonly model display (UNUTAR #product-inquiry sekcije) sadrži product.name
def test_page_shows_readonly_model_name(client):
    product = ProductFactory.create(name="Agri Tracking TB804")
    section = _inquiry_section(_product_html(client, product))
    assert "Agri Tracking TB804" in section, (
        "Readonly model display UNUTAR #product-inquiry sekcije MORA prikazati product.name "
        "'Agri Tracking TB804' (AC9). Scope-ovano na sekciju — H1/title NE računa se."
    )


# AC-9: anchor/sekcija id="product-inquiry" postoji (skroluj-do-forme swap target SM-D5)
def test_page_has_product_inquiry_anchor(client):
    product = ProductFactory.create(name="Agri Tracking TB804")
    html = _product_html(client, product)
    assert re.search(r'id=["\']product-inquiry["\']', html, re.IGNORECASE), (
        "Obuhvatajuća sekcija MORA imati id=\"product-inquiry\" (swap target + skroluj-do-forme, SM-D5)."
    )


# AC-9: vidljiv CTA dugme sa href="#product-inquiry" (Task 10.2 — OBAVEZAN minimalan element)
def test_page_has_visible_cta_to_form(client):
    product = ProductFactory.create(name="Agri Tracking TB804")
    html = _product_html(client, product)
    assert re.search(r'href=["\']#product-inquiry["\']', html, re.IGNORECASE), (
        "Strana MORA imati vidljiv CTA <a href=\"#product-inquiry\"> (skroluj-do-forme, "
        "AC9/Task 10.2 — vidljiv klikabilan element je OBAVEZAN)."
    )


# AC-9: forma NIJE disabled (aktivna na product strani)
def test_form_fields_not_disabled(client):
    product = ProductFactory.create(name="Agri Tracking TB804")
    html = _product_html(client, product)
    # izvuci samo input/textarea unutar product-inquiry sekcije bi bilo idealno; minimalno:
    field_tags = re.findall(r"<(?:input|textarea)\b[^>]*>", html, re.IGNORECASE)
    inquiry_fields = [
        t for t in field_tags
        if any(n in t.lower() for n in ('name="name"', 'name="email"', 'name="phone"', 'name="message"'))
    ]
    assert inquiry_fields, "Model-inquiry forma MORA imati user input/textarea polja (AC9)."
    for t in inquiry_fields:
        assert not re.search(r"\bdisabled\b", t, re.IGNORECASE), (
            f"Model-inquiry polje NE SME imati `disabled` (aktivna forma, AC9): {t!r}"
        )


# AC-9 (relociran iz Task 4.3): CSRF token prisutan u model-inquiry formi (UNUTAR #product-inquiry)
def test_page_form_has_csrf_token(client):
    product = ProductFactory.create(name="Agri Tracking TB804")
    section = _inquiry_section(_product_html(client, product))
    assert re.search(r'name=["\']csrfmiddlewaretoken["\']', section, re.IGNORECASE), (
        "Model-inquiry forma UNUTAR #product-inquiry MORA sadržati {% csrf_token %} "
        "(csrfmiddlewaretoken) — AC8 Security#1. Scope-ovano — header/language-switcher CSRF NE računa se."
    )


# AC-9 (regression): POST na products:detail i dalje 405 (ProductDetailView NETAKNUT GET-only)
def test_productdetailview_post_still_405(client):
    activate("sr")
    product = ProductFactory.create(name="Agri Tracking TB804")
    response = client.post(reverse("products:detail", kwargs={"slug": product.slug}))
    assert response.status_code == 405, (
        "ProductDetailView OSTAJE GET-only (NETAKNUT) — POST MORA biti 405 (AC9 regression). "
        f"Dobio {response.status_code}."
    )


# AC-9 (Task 5.2, low): unpublished product GET → 404 (forma nedostupna)
def test_unpublished_product_get_404(client):
    activate("sr")
    product = ProductFactory.create_unpublished(name="Skriveni Model")
    response = client.get(reverse("products:detail", kwargs={"slug": product.slug}))
    assert response.status_code == 404, (
        "GET unpublished product MORA biti 404 (ProductDetailView filtrira is_published=True) — "
        f"forma nedostupna (AC9/Task 5.2), dobio {response.status_code}."
    )
