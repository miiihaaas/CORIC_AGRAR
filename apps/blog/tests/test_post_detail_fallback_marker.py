"""Story 6.5 — Blog post_detail H1 i18n fallback marker integration (TEA RED).

Cross-app integration: renderuje CELU blog post detail stranu preko i18n URL routing-a
(`/hu/blog/<slug>/`) sa LocaleMiddleware → verifikuje da H1 (`coric-blog-detail__title`)
koristi `{% translated_field post 'title' %}` → sadrži `coric-fallback-marker` kad je
`title_hu` prazan, NE sadrži kad je `title_hu` popunjen (AC6/#14).

Wiring koji ovaj test zaključava (Dev mora implementirati):
- templates/blog/post_detail.html: `{% load i18n_fallback %}` + H1 →
  `{% translated_field post 'title' %}`

HTML parsing: regex (NIKAD BeautifulSoup). Post reachable preko status="published" +
published_at. URL = `/hu/blog/<slug>/` (potvrđeno test_blog_post_detail.py).

Refs:
- 6-5-i18n-fallback-marker-tooltip.md AC6 + Testing #14 + Task 5.1
- apps/blog/tests/test_blog_post_detail.py (URL/render precedent)
- apps/blog/tests/conftest.py (make_post fixture)
"""

from __future__ import annotations

import re

import pytest
from django.utils import timezone
from django.utils.translation import activate

pytestmark = pytest.mark.django_db


def _published(make_post, **overrides):
    defaults = {
        "status": "published",
        "published_at": timezone.now() - timezone.timedelta(days=1),
    }
    defaults.update(overrides)
    return make_post(**defaults)


def _detail_html(client, post, locale: str) -> str:
    activate(locale)
    try:
        resp = client.get(f"/{locale}/blog/{post.slug}/", HTTP_HOST="localhost")
        assert resp.status_code == 200, (
            f"Blog detail /{locale}/blog/{post.slug}/ MORA vratiti 200 — dobio "
            f"{resp.status_code}."
        )
        return resp.content.decode("utf-8")
    finally:
        activate("sr")


def _h1_inner(html: str) -> str | None:
    m = re.search(
        r'<h1[^>]*class="[^"]*coric-blog-detail__title[^"]*"[^>]*>(.*?)</h1>',
        html,
        re.DOTALL,
    )
    return m.group(1) if m else None


# AC6 / Testing #14 — prazan title_hu → H1 sadrži marker
def test_post_detail_h1_fallback_marker_when_title_hu_empty(client, make_post):
    """#14 — /hu/blog/<slug>/ sa title_hu="" → H1 sadrži coric-fallback-marker."""
    activate("sr")
    post = _published(make_post, title="Žetva pšenice na vreme")
    post.title_sr = "Žetva pšenice na vreme"
    post.title_hu = ""
    post.save()

    html = _detail_html(client, post, "hu")
    h1_inner = _h1_inner(html)
    assert h1_inner is not None, (
        "Blog detail strana MORA imati H1 sa klasom coric-blog-detail__title."
    )
    assert "coric-fallback-marker" in h1_inner, (
        "H1 MORA sadržati coric-fallback-marker kad je title_hu prazan "
        f"({{% translated_field post 'title' %}}; AC6/#14). H1: {h1_inner!r}"
    )
    assert "Žetva pšenice na vreme" in h1_inner, (
        "Marker MORA nositi sr naslov (title_sr; AC6)."
    )
    assert 'lang="sr"' in h1_inner, 'Fallback tekst MORA imati lang="sr" (AC2/AC6).'


# AC6 / Testing #14 — popunjen title_hu → H1 BEZ markera
def test_post_detail_h1_no_marker_when_title_hu_populated(client, make_post):
    """#14 (negativ) — /hu/ sa popunjenim title_hu → H1 BEZ markera."""
    activate("sr")
    post = _published(make_post, title="Žetva pšenice na vreme")
    post.title_sr = "Žetva pšenice na vreme"
    post.title_hu = "Búzaaratás időben"
    post.save()

    html = _detail_html(client, post, "hu")
    h1_inner = _h1_inner(html)
    assert h1_inner is not None, "H1 mora postojati."
    assert "coric-fallback-marker" not in h1_inner, (
        "Sa popunjenim title_hu → H1 NE sme imati marker (NEMA fallback-a; AC6/#14)."
    )
    assert "Búzaaratás időben" in h1_inner, (
        "H1 MORA prikazati hu naslov kad je title_hu popunjen (AC6)."
    )


# AC6 / Testing #14 — /sr/ → NIKAD marker (sr je izvor)
def test_post_detail_h1_no_marker_on_sr(client, make_post):
    """#14 (sr) — /sr/blog/<slug>/ → H1 BEZ markera (sr je izvor; AC1/AC6)."""
    activate("sr")
    post = _published(make_post, title="Žetva pšenice na vreme")
    post.title_sr = "Žetva pšenice na vreme"
    post.title_hu = ""
    post.save()

    html = _detail_html(client, post, "sr")
    h1_inner = _h1_inner(html)
    assert h1_inner is not None, "H1 mora postojati."
    assert "coric-fallback-marker" not in h1_inner, (
        "Na /sr/ H1 NIKAD ne sme imati marker (sr je izvorni jezik; AC1/AC6)."
    )
    assert "Žetva pšenice na vreme" in h1_inner, (
        "Na /sr/ H1 MORA prikazati plain sr naslov (AC1)."
    )
