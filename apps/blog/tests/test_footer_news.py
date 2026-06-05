"""Story 5.4 — Footer „Najnovije vesti" kolona render + lazy lock — TEA RED phase.

Pokriva AC5/AC6/AC7/AC8 na RENDER nivou (full-page `client.get` → base.html →
footer iterira `latest_blog_posts`):
  - AC6: svaka objava renderuje `<a href="{post.get_absolute_url}">{post.title}</a>`
    linkujući na `/sr/blog/<slug>/` (locale-prefiksovano).
  - AC5: 0 published → `{% empty %}` placeholder „Uskoro nove priče sa polja"
    (REUSE 5-2 msgid; SM-D5); validan markup, NEMA broken/prazan <li>.
  - AC7 LAZY (SM-D2 LOAD-BEARING): blog Post upit puca TAČNO 1× na full-page
    render (footer iterira), 0× na HTMX partial (`_post_results.html` ne extend-uje
    base.html → footer se ne iterira → lazy se ne razrešava). Lock empirijski kroz
    `CaptureQueriesContext` (filtriran na blog_post SELECT) — robusno na chrome
    upite (SiteSettings/session) koji nisu deo lazy ponašanja.
  - AC8: title u aktivnoj lokali + link locale-prefiksovan (/sr/ vs /hu/).

⚠️ C3/IMP-3 — KRITIČNO: NE koristi `_render_partial`/`render_to_string` za query
lock (bypass-uje context processore → context processor NE radi → LAŽNO 0 upita,
ne dokazuje lazy). 1-upit vehicle = `client.get(reverse("pages:home"))` (pun
RequestContext). 0-upit vehicle = `client.get("/sr/blog/", HX-Request) →
_post_results.html` (ne renderuje footer).

⚠️ GUARD IMPORTS: apps.blog importi UNUTAR funkcija. Pristup processor vrednosti
SAMO kroz `client.get` render (KeyError/markup-assert = čist RED, NE collection abort).

RED razlog: footer još renderuje 3 Lorem `<li>` (statika), context processor NIJE
registrovan → footer NE sadrži post linkove/empty placeholder → markup asercije
FAIL; query lock-ovi FAIL (lazy ponašanje ne postoji dok Dev ne implementira).

Pokrenuti sa:  just test apps/blog/tests/test_footer_news.py

Refs:
- 5-4-...-kolona.md AC5/AC6/AC7/AC8 + SM-D2/SM-D5/SM-D6 + Task 5.6/5.7/5.8/5.9
- 5-4-interface-contract.md § footer.html kolona 3
- apps/blog/tests/test_blog_index_n_plus_1.py (CaptureQueriesContext presedan)
"""

from __future__ import annotations

import re

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import activate

pytestmark = pytest.mark.django_db


# ── Shape filters (anchored LIMIT 3 — TEA F2: NE matchuje LIMIT 30/300) ──────────


def _has_limit_3(sql):
    """ANCHORED LIMIT 3 match (TEA F2): `\\blimit\\s+3\\b` da `limit 30`/`limit 300`
    NE bude false-match (npr. buduća LIMIT 30 query na blog_post bez category-join).
    """
    return re.search(r"\blimit\s+3\b", sql, re.IGNORECASE) is not None


def _is_footer_shaped(sql):
    """Footer `latest_blog_posts` upit shape: blog_post SELECT, BEZ category-join,
    ORDER BY, anchored LIMIT 3 (izoluje footer od bilo kog drugog blog upita).
    """
    low = sql.lower()
    return (
        "blog_category" not in low
        and "order by" in low
        and _has_limit_3(sql)
    )


# ── Helpers ───────────────────────────────────────────────────────────────────


def _published(make_post, *, days_ago=1, **overrides):
    defaults = {
        "status": "published",
        "published_at": timezone.now() - timezone.timedelta(days=days_ago),
    }
    defaults.update(overrides)
    return make_post(**defaults)


def _footer_slice(html):
    """Izvuče SAMO `<footer>...</footer>` isečak (TEA N2/N4: scope-uj asercije na
    footer da buduće home-page sekcije sa blog linkovima ne izazovu false pass/fail).
    """
    match = re.search(r"<footer\b.*?</footer>", html, re.IGNORECASE | re.DOTALL)
    assert match is not None, "Strana MORA renderovati <footer>...</footer> blok."
    return match.group(0)


def _blog_post_select_queries(captured):
    """Filtrira captured upite na blog_post SELECT (ono što lazy callable okida).

    Robusno na chrome upite (django_session, SiteSettings, contenttype) koji NISU
    deo lazy ponašanja — izoluje SAMO `latest_blog_posts` upit.
    """
    return [
        q
        for q in captured
        if "blog_post" in q["sql"].lower() and q["sql"].lstrip().lower().startswith("select")
    ]


# ── AC6 — svaka objava renderuje link na blog:detail (get_absolute_url) ───────


def test_footer_renders_post_link_with_title_and_href(client, make_post):
    activate("sr")
    post = _published(make_post, title="Žetva pšenice 2026", days_ago=1)

    response = client.get(reverse("pages:home"), HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    expected_href = post.get_absolute_url()  # /sr/blog/<slug>/
    assert expected_href == f"/sr/blog/{post.slug}/", (
        f"get_absolute_url MORA biti /sr/blog/<slug>/ (5-2 blog:detail). "
        f"Dobili: {expected_href!r}."
    )
    assert f'href="{expected_href}"' in html, (
        f"Footer kolona 3 MORA renderovati link href={expected_href!r} "
        f"(<a href='{{{{ post.get_absolute_url }}}}'>). HTML ne sadrži taj href."
    )
    assert "Žetva pšenice 2026" in html, (
        "Footer link tekst MORA biti post.title 'Žetva pšenice 2026' (pun dijakritik)."
    )


def test_footer_renders_at_most_three_post_links(client, make_post):
    """5 published → footer kolona 3 renderuje TAČNO 3 linka na blog:detail."""
    activate("sr")
    for i in range(5):
        _published(make_post, title=f"Priča broj {i}", days_ago=i + 1)

    response = client.get(reverse("pages:home"), HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # TEA N2: scope-uj count na <footer> isečak (NE celu stranu — buduća home
    # sekcija sa blog linkovima ne sme oboriti ovaj footer lock).
    footer = _footer_slice(html)
    blog_detail_links = footer.count('href="/sr/blog/')
    assert blog_detail_links == 3, (
        f"Footer MORA renderovati TAČNO 3 blog:detail linka (LIMIT [:3]). "
        f"Dobili {blog_detail_links} '/sr/blog/' href-ova u <footer> isečku."
    )


# ── AC5 — 0 published → empty placeholder (SM-D5; REUSE msgid) ────────────────


def test_footer_empty_placeholder_when_no_posts(client, make_post):
    """0 PUBLISHED (samo draft/future) → `{% empty %}` placeholder
    „Uskoro nove priče sa polja"; validan <li>; NEMA blog:detail linkova.
    „NAJNOVIJE VESTI" heading OSTAJE.
    """
    activate("sr")
    now = timezone.now()
    make_post(title="Samo nacrt", status="draft", published_at=None)
    make_post(
        title="Samo buduca",
        status="published",
        published_at=now + timezone.timedelta(days=5),
    )

    response = client.get(reverse("pages:home"), HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # TEA N4: scope-uj asercije na <footer> isečak (placeholder string ne sme
    # slučajno matchovati nepovezan include drugde na strani).
    footer = _footer_slice(html)
    assert "Uskoro nove priče sa polja" in footer, (
        "0 published -> footer MORA renderovati empty placeholder "
        "'Uskoro nove price sa polja' (REUSE 5-2 msgid; SM-D5)."
    )
    assert "NAJNOVIJE VESTI" in footer, (
        "'NAJNOVIJE VESTI' section_eyebrow heading MORA OSTATI i kad je 0 objava."
    )
    # NEMA blog:detail linkova u footeru (nijedna objava nije vidljiva)
    assert 'href="/sr/blog/' not in footer, (
        "0 published → footer NE SME imati nijedan blog:detail link "
        "(draft/future ne curi)."
    )


def test_footer_empty_state_has_no_broken_empty_li(client, make_post):
    """Validan markup: empty grana je 1 <li class="coric-footer__news-empty">,
    NE prazan <li></li> / prazan <a></a> (broken markup guard).
    """
    activate("sr")
    # 0 published — prazan blog
    response = client.get(reverse("pages:home"), HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert "coric-footer__news-empty" in html, (
        "Empty placeholder MORA imati <li class='coric-footer__news-empty'> "
        "(stabilan markup hook — SM-D5)."
    )
    # Bez praznog <li></li> u news <ul> (broken markup)
    assert "<li></li>" not in html, (
        "Footer NE SME imati prazan <li></li> (broken markup)."
    )


# ── AC7 — LAZY: 1 upit na full page, 0 na HTMX partial (SM-D2 LOAD-BEARING) ───


def test_full_page_render_fires_exactly_one_blog_query(client, make_post):
    """Full-page render (footer iterira latest_blog_posts) → blog Post SELECT
    puca TAČNO 1× (LIMIT 3 indeksiran). Re-iteracija u template-u (`{% if %}` +
    `{% for %}`) NE re-query (list() materijalizacija u lazy — Gotcha BL4-1).
    """
    activate("sr")
    for i in range(3):
        _published(make_post, title=f"Objava {i}", days_ago=i + 1)

    with CaptureQueriesContext(connection) as ctx:
        response = client.get(reverse("pages:home"), HTTP_HOST="localhost")
        assert response.status_code == 200

    # Footer-shaped upit: Post.published BEZ category-join, ORDER BY published_at
    # LIMIT 3 (isti shape kao u HTMX-0-lock — izoluje footer od bilo kog drugog
    # blog upita na home strani).
    blog_queries = _blog_post_select_queries(ctx.captured_queries)
    footer_shaped = [q for q in blog_queries if _is_footer_shaped(q["sql"])]
    assert len(footer_shaped) == 1, (
        f"Full-page render (footer iterira latest_blog_posts) MORA okinuti TAČNO "
        f"1 footer-shaped blog upit (Post.published, ORDER BY published_at LIMIT 3, "
        f"BEZ category-join; list() materijalizacija → re-iteracija ne re-query — "
        f"SM-D2/BL4-1). Dobili {len(footer_shaped)} footer-shaped (od "
        f"{len(blog_queries)} blog_post) upita:\n"
        + "\n".join(q["sql"] for q in blog_queries)
    )


def test_lazy_reiteration_fires_exactly_one_query(make_post):
    """BL4-1/SM-D2 LOAD-BEARING (TEA F1): `list()` UNUTAR SimpleLazyObject lambda
    → pristup `latest_blog_posts` DVA puta u jednom renderu okida TAČNO 1 upit
    (NE 2). Bare-QuerySet regresija (bez `list()` umotavanja) bi prošla sve ostale
    testove ali bi okinula 2 upita (jednom po iteraciji).

    Mimic-uje template re-iteraciju: `{% if latest_blog_posts %}` (bool) +
    `{% for post in latest_blog_posts %}` (iteracija) — oba pristupaju lazy-ju.

    Direktan `latest_blog_posts(RequestFactory().get("/"))` poziv (BEZ full-page
    render-a) izoluje SAMO footer lazy upit od chrome/view upita.
    """
    activate("sr")
    from django.test import RequestFactory

    from apps.blog.context_processors import latest_blog_posts

    _published(make_post, title="Re-iteracija objava", days_ago=1)

    ctx = latest_blog_posts(RequestFactory().get("/"))
    lazy = ctx["latest_blog_posts"]

    with CaptureQueriesContext(connection) as capture:
        # DVA pristupa u jednom "renderu": bool() + len() + list() — mimic
        # {% if %} + {% for %} re-iteraciju.
        assert bool(lazy) is True
        assert len(list(lazy)) == 1
        _ = list(lazy)

    footer_shaped = [
        q for q in capture.captured_queries if _is_footer_shaped(q["sql"])
    ]
    assert len(footer_shaped) == 1, (
        f"Re-iteracija lazy `latest_blog_posts` (bool + 2× list — mimic "
        f"{{% if %}}+{{% for %}}) MORA okinuti TAČNO 1 footer-shaped upit, NE 2 "
        f"(BL4-1/SM-D2: `list()` UNUTAR lambda → SimpleLazyObject kešira → "
        f"re-iteracija NE re-query). Bare-QuerySet regresija bi okinula 2. "
        f"Dobili {len(footer_shaped)} footer-shaped upita:\n"
        + "\n".join(q["sql"] for q in footer_shaped)
    )


def test_htmx_partial_fires_zero_blog_queries(client, make_post):
    """HTMX partial (`_post_results.html` ne extend-uje base.html → footer se NE
    iterira → lazy se NE razrešava) → 0 blog_post SELECT od footera (SM-D2).

    ⚠️ Context processor SE izvršava (RequestContext postoji), ali lazy callable
    se NE poziva → 0 upita DOKAZUJE lazy ponašanje (NE odsustvo processora).
    BlogIndexView sam radi svoj Post upit (lista objava) — zato lock NIJE
    „0 ukupno blog upita", nego „footer NE dodaje svoj LIMIT-3 latest upit".
    Vehicle bira stranu BEZ blog Post listanja da izoluje footer lazy: home HTMX?
    Ne — home nema HTMX partial. Koristimo blog index HTMX i poredimo sa baseline.
    """
    activate("sr")
    for i in range(3):
        _published(make_post, title=f"HTMX objava {i}", days_ago=i + 1)

    # HTMX partial render — _post_results.html (NE extend-uje base.html → bez footera).
    with CaptureQueriesContext(connection) as ctx:
        response = client.get(
            "/sr/blog/", HTTP_HX_REQUEST="true", HTTP_HOST="localhost"
        )
        assert response.status_code == 200
        # Sanity: HTMX partial NE renderuje footer (nema „NAJNOVIJE VESTI" heading).
        body = response.content.decode("utf-8")
        assert "NAJNOVIJE VESTI" not in body, (
            "HTMX partial (_post_results.html) NE SME renderovati footer "
            "(NE extend-uje base.html). Ako sadrzi footer heading, 0-query lock "
            "ne dokazuje nista."
        )

    # latest_blog_posts footer upit NE sme pucati. BlogIndexView pravi SVOJ Post
    # upit (lista + count) — ALI taj upit ima `select_related("category")` →
    # `JOIN blog_category` (views.py:56). Footer `latest_blog_posts` upit je
    # `Post.published.order_by(...)[:3]` BEZ select_related → NEMA category JOIN.
    # Izolacija footer-upita = blog_post SELECT BEZ `blog_category` joina.
    blog_queries = _blog_post_select_queries(ctx.captured_queries)
    footer_shaped = [q for q in blog_queries if _is_footer_shaped(q["sql"])]
    assert footer_shaped == [], (
        "HTMX partial (footer se NE iterira) NE SME okinuti footer "
        "latest_blog_posts upit (Post.published BEZ category-join, ORDER BY "
        "published_at LIMIT 3 — lazy se NE razrešava; SM-D2). Nađeni footer-shaped "
        "upiti:\n" + "\n".join(q["sql"] for q in footer_shaped)
    )


# ── AC8 — i18n: title aktivna lokala + link locale-prefiksovan ────────────────


def test_footer_link_locale_prefixed_hu(client, make_post):
    """GET /hu/ → footer title_hu + link /hu/blog/<slug>/ (i18n_patterns;
    slug NIJE translatable → isti ASCII slug).
    """
    activate("hu")
    post = make_post(
        title="Žetva pšenice 2026",
        status="published",
        published_at=timezone.now() - timezone.timedelta(days=1),
    )
    post.title_hu = "Búza aratás 2026"
    post.save()

    response = client.get("/hu/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert f'href="/hu/blog/{post.slug}/"' in html, (
        f"hu lokala → footer link MORA biti /hu/blog/{post.slug}/ "
        f"(locale-prefiksovan; slug ASCII nepromenjen)."
    )
    assert "Búza aratás 2026" in html, (
        "hu lokala → footer link tekst MORA biti title_hu 'Búza aratás 2026' "
        "(modeltranslation aktivna lokala)."
    )


def test_footer_link_locale_prefixed_sr(client, make_post):
    activate("sr")
    post = make_post(
        title="Žetva pšenice 2026",
        status="published",
        published_at=timezone.now() - timezone.timedelta(days=1),
    )
    post.title_hu = "Búza aratás 2026"
    post.save()

    response = client.get("/sr/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert f'href="/sr/blog/{post.slug}/"' in html, (
        f"sr lokala → footer link MORA biti /sr/blog/{post.slug}/."
    )
    assert "Žetva pšenice 2026" in html, (
        "sr lokala → footer link tekst MORA biti title_sr 'Žetva pšenice 2026'."
    )
