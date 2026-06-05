"""Story 6.1 — NO-DUPLICATE-<title> <head> integracija (TEA RED phase, SM-D2 LOCK).

Pokriva AC6 (SM-D2 KRITIČAN): full <head> render kroz base.html + block override
sa seo tagovima → output ima TAČNO 1 <title> + 1 <meta name="description"> + 1
<link rel="canonical">. Ovo je glavni SM-D2 regression-lock.

Render harness: mini-template koji {% extends "base.html" %} i puni
{% block title %}{% seo_title obj %}{% endblock %} + meta_description + extra_head
{% seo_head obj %} — mirror SM-D2 recept koji detail templati primenjuju.

⚠️ {% load seo_meta %} UNUTAR test body-ja (lazy RED — TemplateSyntaxError do Dev impl).

Refs:
- 6-1-...-admin.md AC6 + Task 7.8 + SM-D2/D3 + Gotcha SEO1-3
"""

from __future__ import annotations

import re

import pytest

pytestmark = pytest.mark.django_db

# Mini harness koji mirror-uje SM-D2 detail-template recept (extends base.html).
_HARNESS = (
    "{% extends 'base.html' %}\n"
    "{% load seo_meta %}\n"
    "{% block title %}{% seo_title obj %}{% endblock %}\n"
    "{% block meta_description %}{% seo_meta_description obj %}{% endblock %}\n"
    "{% block extra_head %}{% seo_head obj %}{% endblock %}\n"
)


def _render_full_head(obj) -> str:
    from django.template import Context, Template
    from django.test import RequestFactory

    request = RequestFactory().get("/")
    return Template(_HARNESS).render(Context({"obj": obj, "request": request}))


# AC6/SM-D2: TAČNO 1 <title> u renderovanom <head> (glavni no-dup-title lock)
def test_exactly_one_title_tag(product):
    from apps.seo.models import SeoMeta

    SeoMeta.objects.create(content_object=product, meta_title_sr="SEO naslov za head")
    html = _render_full_head(product)

    titles = re.findall(r"<title[ >]", html, re.IGNORECASE)
    assert len(titles) == 1, (
        f"MORA postojati TAČNO 1 <title> tag (SM-D2 NO-DUPLICATE — seo_title puni "
        f"base-ov block, seo_head NE emituje drugi <title>); pronađeno {len(titles)}."
    )
    assert "SEO naslov za head" in html, (
        "Jedini <title> MORA biti POPUNJEN seo_title vrednošću (SM-D2)."
    )


# AC6/SM-D2: TAČNO 1 <meta name="description">
def test_exactly_one_meta_description_tag(product):
    from apps.seo.models import SeoMeta

    SeoMeta.objects.create(content_object=product, meta_description_sr="Opis u head-u")
    html = _render_full_head(product)

    metas = re.findall(r'<meta\s+name="description"', html, re.IGNORECASE)
    assert len(metas) == 1, (
        f"MORA postojati TAČNO 1 <meta name=\"description\"> (SM-D2); pronađeno {len(metas)}."
    )


# AC6: canonical se pojavljuje u extra_head (full render) tačno jednom
def test_canonical_present_once_in_full_head(product):
    html = _render_full_head(product)
    canonicals = re.findall(r'rel="canonical"', html, re.IGNORECASE)
    assert len(canonicals) == 1, (
        f"MORA postojati TAČNO 1 <link rel=\"canonical\"> u full head render-u; "
        f"pronađeno {len(canonicals)}."
    )
