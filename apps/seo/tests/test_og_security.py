"""Story 6.3 — OG/twitter content autoescape (head injection lock; TEA RED, AC9).

SeoMeta.meta_title/meta_description sa XSS / attribute-breakout payload → rendered
og:title/og:description/twitter:* content je HTML-escaped (`&quot;`/`&lt;`/`&gt;`);
sirov <script> NIJE u head-u; atribut se NE probija. SVE kroz format_html autoescape
(NIKAD |safe na sirovim admin vrednostima — mirror 6-1 SAFE pattern).

⚠️ RED razlog: pre Dev impl og:title/og:description ne postoje uopšte → escaped
vrednost ODSUTNA (assert in head fail-uje). Posle impl, ako bi Dev (pogrešno) koristio
|safe/mark_safe na sirovoj vrednosti → raw <script> bi prošao → ovaj test bi to uhvatio.

Refs:
- 6-3-...-meta.md AC9 + Task 4.3/9.7 + SM-D8 + Gotcha SEO3-6
"""

from __future__ import annotations

import re

import pytest
from django.utils.translation import activate

pytestmark = pytest.mark.django_db

_PAYLOAD = '"><script>alert(1)</script>'


def _product_url(product):
    return f"/sr/proizvod/{product.slug}/"


def _head(html):
    """Izdvoji <head>...</head> (injection lock je head-scoped)."""
    m = re.search(r"<head\b.*?</head>", html, re.IGNORECASE | re.DOTALL)
    return m.group(0) if m else html


def _og_content(html, prop):
    """Izvuci content atribut OG/twitter meta taga po property/name vrednosti."""
    m = re.search(
        rf'<meta\s+(?:property|name)="{re.escape(prop)}"\s+content="([^"]*)"',
        html,
        re.IGNORECASE,
    )
    return m.group(1) if m else None


def test_og_title_payload_is_escaped(client, product):
    """AC9: XSS payload u meta_title → og:title content escaped; NEMA sirovog <script>."""
    from apps.seo.models import SeoMeta

    activate("sr")
    SeoMeta.objects.create(content_object=product, meta_title_sr=_PAYLOAD)

    response = client.get(_product_url(product), HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    head = _head(html)

    # sirov <script> NE SME biti u head-u (autoescape ga pretvara u &lt;script&gt;)
    assert "<script>alert(1)</script>" not in head, (
        "Sirov <script> payload PROBIO atribut u <head> — format_html autoescape "
        "NIJE primenjen (head injection — AC9/SM-D8). NIKAD |safe na sirovim vrednostima."
    )
    # og:title MORA postojati i nositi ESCAPED payload (NE sirov atribut-breakout).
    # Asercija je OG-scoped (NE samo <title>/description) → RED dok 6.3 ne renderuje OG.
    # _og_content izvlači content atribut iz SIROVOG HTML-a → escaped string
    # (`&lt;script&gt;`); sirov `<script>` se nikad ne sme pojaviti unutar atributa.
    og_title = _og_content(html, "og:title")
    assert og_title is not None, (
        "og:title MORA biti renderovan (AC2/AC9) — bez njega security lock je no-op."
    )
    assert "&lt;script&gt;" in og_title, (
        "og:title content atribut MORA biti HTML-escaped (`&lt;script&gt;`) u sirovom "
        "HTML-u (format_html autoescape — AC9/SM-D8)."
    )


def test_og_description_payload_is_escaped(client, product):
    """AC9: XSS payload u meta_description → og:description content escaped."""
    from apps.seo.models import SeoMeta

    activate("sr")
    SeoMeta.objects.create(content_object=product, meta_description_sr=_PAYLOAD)

    response = client.get(_product_url(product), HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    head = _head(html)

    assert "<script>alert(1)</script>" not in head, (
        "Sirov <script> payload PROBIO atribut u <head> kroz meta_description "
        "(head injection — AC9/SM-D8)."
    )
    og_desc = _og_content(html, "og:description")
    assert og_desc is not None, (
        "og:description MORA biti renderovan (AC2/AC9) — bez njega security lock je no-op."
    )
    assert "&lt;script&gt;" in og_desc, (
        "og:description content atribut MORA biti HTML-escaped (`&lt;script&gt;`) "
        "u sirovom HTML-u (format_html autoescape — AC9/SM-D8)."
    )


def test_twitter_title_payload_is_escaped(client, product):
    """NM-4 (twitter direct lock): XSS payload u meta_title → twitter:title content
    escaped nezavisno od og:title. Hvata split-wiring bug gde bi twitter:* dobio
    sirov/unsafe izvor čak i kad og:* ostane ispravan.
    """
    from apps.seo.models import SeoMeta

    activate("sr")
    SeoMeta.objects.create(content_object=product, meta_title_sr=_PAYLOAD)

    response = client.get(_product_url(product), HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    head = _head(html)

    # sirov <script> NE SME biti u head-u (pokriva oba og: i twitter: tagove)
    assert "<script>alert(1)</script>" not in head, (
        "Sirov <script> payload PROBIO atribut u <head> kroz twitter:title "
        "(head injection — AC9/SM-D8/NM-4)."
    )
    twitter_title = _og_content(html, "twitter:title")
    assert twitter_title is not None, (
        "twitter:title MORA biti renderovan (AC3) — bez njega NM-4 lock je no-op."
    )
    assert "&lt;script&gt;" in twitter_title, (
        "twitter:title content atribut MORA biti HTML-escaped (`&lt;script&gt;`) "
        "u sirovom HTML-u — format_html autoescape MORA pokriti twitter:* direktno (NM-4)."
    )


def test_twitter_description_payload_is_escaped(client, product):
    """NM-4 (twitter direct lock): XSS payload u meta_description → twitter:description
    content escaped nezavisno od og:description.
    """
    from apps.seo.models import SeoMeta

    activate("sr")
    SeoMeta.objects.create(content_object=product, meta_description_sr=_PAYLOAD)

    response = client.get(_product_url(product), HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    head = _head(html)

    assert "<script>alert(1)</script>" not in head, (
        "Sirov <script> payload PROBIO atribut u <head> kroz twitter:description "
        "(head injection — AC9/SM-D8/NM-4)."
    )
    twitter_desc = _og_content(html, "twitter:description")
    assert twitter_desc is not None, (
        "twitter:description MORA biti renderovan (AC3) — bez njega NM-4 lock je no-op."
    )
    assert "&lt;script&gt;" in twitter_desc, (
        "twitter:description content atribut MORA biti HTML-escaped (`&lt;script&gt;`) "
        "u sirovom HTML-u — format_html autoescape MORA pokriti twitter:* direktno (NM-4)."
    )
