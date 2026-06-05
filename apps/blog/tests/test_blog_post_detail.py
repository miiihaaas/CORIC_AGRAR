"""Story 5.3 — Obogaćen BlogPostDetailView (AC1/AC2/AC6/AC7) — TEA RED phase.

Pokriva (5-3 OBOGAĆUJE 5-2 placeholder — ADITIVNO):
  - AC1: naslovna slika (`{% if post.main_image %}` guard) + meta (datum + autor
    NULL-guard SM-D5 + kategorija link `blog:category`) + naslov + telo `|linebreaks`
    (plain auto-escape — NIKAD `|safe`; XSS lock) + tag linkovi `blog:tag`
  - AC2: „Slične objave" — 2-4 published iz ISTE kategorije, exclude-self,
    draft-not-leaked, bounded, category=None → prazna
  - AC6: social share FB/Viber/WhatsApp/Copy-link + `share_url` view-context (IMP-2)
    + egzaktni href-ovi (IMP-3)
  - AC7: meta title + meta_description `post.perex|default:post.title` (IMP-4)

⚠️ RED-faza: 5-3 obogaćenje JOŠ NE postoji → ovi testovi padaju na FEATURE odsustvu
(context key `similar_posts`/`share_url` nedostaje; `blog:category`/`blog:tag`
NoReverseMatch UNUTAR template/test; social href/`data-testid` odsutni). NE collection
errori — apps.blog importi su UNUTAR funkcija; `reverse()` je UNUTAR test tela.

⚠️ GUARD: apps.blog importi UNUTAR funkcija. REUSE conftest
make_post/make_category/make_tag/author_user.

Refs:
- 5-3-blog-post-detail-strana.md AC1/AC2/AC6/AC7 + Task 9.2/9.3/9.4/9.5/9.9/9.10
  + SM-D1/D2/D5/D6/D7/D8 + Gotcha BL3-1/BL3-2/BL3-3
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import activate, override

pytestmark = pytest.mark.django_db


def _published(make_post, **overrides):
    defaults = {
        "status": "published",
        "published_at": timezone.now() - timezone.timedelta(days=1),
    }
    defaults.update(overrides)
    return make_post(**defaults)


def _get_detail(client, post):
    return client.get(f"/sr/blog/{post.slug}/", HTTP_HOST="localhost")


# ─────────────────────────────────────────────────────────────────────────────
# AC1 — obogaćen detail: slika + meta + kategorija-link + naslov + telo + tagovi
# ─────────────────────────────────────────────────────────────────────────────


# AC1 (9.2): kategorija ime kao link na blog:category arhivu
def test_detail_renders_category_link(client, make_post, make_category):
    activate("sr")
    cat = make_category(name="Ratarstvo")
    post = _published(make_post, title="Priča sa kategorijom", category=cat)

    response = _get_detail(client, post)

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    # blog:category link mora biti renderovan u meta liniji (reverse UNUTAR testa)
    with override("sr"):
        cat_url = reverse("blog:category", kwargs={"slug": cat.slug})
    assert cat_url in html, (
        f"Detail meta MORA imati kategorija link na arhivu {cat_url!r} "
        f"(`{{% url 'blog:category' slug=post.category.slug %}}` — AC1/SM-D2). "
        f"NoReverseMatch/odsutan link = 5-3 arhiva nije implementirana (RED)."
    )
    assert cat.name in html, "Detail MORA prikazati ime kategorije."


# AC1 (9.2): svaki tag renderuje link na blog:tag arhivu
def test_detail_renders_tag_links(client, make_post, make_category, make_tag):
    activate("sr")
    tag_psenica = make_tag(name="Pšenica")
    tag_zetva = make_tag(name="Žetva")
    post = _published(
        make_post, title="Priča sa tagovima", tags=[tag_psenica, tag_zetva]
    )

    response = _get_detail(client, post)

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    with override("sr"):
        url_a = reverse("blog:tag", kwargs={"slug": tag_psenica.slug})
        url_b = reverse("blog:tag", kwargs={"slug": tag_zetva.slug})
    assert url_a in html and url_b in html, (
        f"Detail MORA renderovati blog:tag link za SVAKI tag ({url_a!r}, {url_b!r}) "
        f"(`{{% url 'blog:tag' slug=tag.slug %}}` — AC1). Odsutan = 5-3 RED."
    )


# AC1 (9.2): naslovna slika guard — bez main_image NEMA <img> craša, naslov i dalje 200
def test_detail_no_main_image_renders_without_crash(client, make_post):
    activate("sr")
    # make_post default NE postavlja main_image → {% if post.main_image %} guard
    post = _published(make_post, title="Priča bez slike")

    response = _get_detail(client, post)

    assert response.status_code == 200, (
        "Detail bez main_image MORA biti 200 (`{% if post.main_image %}` guard)."
    )


# ─────────────────────────────────────────────────────────────────────────────
# AC1 (9.3) — autor display (SM-D5 / IMP-6b)
# ─────────────────────────────────────────────────────────────────────────────


# AC1 (9.3a): author=None → meta linija render-uje BEZ autora (NE „None", NE crash)
def test_detail_author_none_omits_author_line(client, make_post):
    activate("sr")
    post = _published(make_post, title="Priča bez autora", author=None)

    response = _get_detail(client, post)

    assert response.status_code == 200, (
        "Detail sa author=None MORA biti 200 (`{% if post.author %}` guard — SM-D5)."
    )
    html = response.content.decode("utf-8")
    # „None" string NE SME biti renderovan kao autor (guard mora izostaviti liniju)
    assert ">None<" not in html and "Autor: None" not in html, (
        "author=None - autor linija MORA biti IZOSTAVLJENA (NE renderovati None)."
    )


# AC1 (9.3b): autor sa first/last → puno ime
def test_detail_author_full_name(client, make_post, author_user):
    activate("sr")
    author_user.first_name = "Đorđe"
    author_user.last_name = "Petrović"
    author_user.save()
    post = _published(make_post, title="Priča sa autorom", author=author_user)

    response = _get_detail(client, post)

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "Đorđe Petrović" in html, (
        "Detail MORA prikazati puno ime autora (get_full_name) kad postoji."
    )


# AC1 (9.3c): autor sa praznim first/last → username (get_full_name|default:username)
def test_detail_author_empty_name_falls_back_to_username(
    client, make_post, author_user
):
    activate("sr")
    # author_user default: first_name="" last_name="" → get_full_name() == ""
    post = _published(make_post, title="Priča autor bez imena", author=author_user)

    response = _get_detail(client, post)

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert author_user.username in html, (
        f"Autor sa praznim first/last → MORA prikazati username "
        f"({author_user.username!r}) preko `get_full_name|default:username` (IMP-6b). "
        f"get_full_name() vraca prazan string -> `default` hvata -> username."
    )


# ─────────────────────────────────────────────────────────────────────────────
# AC1 (9.4) — XSS body escape (SM-D1 / Gotcha BL3-1 — SECURITY LOCK)
# ─────────────────────────────────────────────────────────────────────────────


# AC1 (9.4): body sa <script> MORA biti ESCAPE-ovan (|linebreaks auto-escape; NE |safe)
def test_detail_body_escapes_script_no_safe_filter(client, make_post):
    activate("sr")
    post = _published(
        make_post,
        title="XSS test priča",
        body="<script>alert(1)</script>",
    )

    response = _get_detail(client, post)

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "&lt;script&gt;" in html, (
        "body MORA biti auto-escape-ovan (`&lt;script&gt;`) — `|linebreaks` "
        "auto-escape (SM-D1/Gotcha BL3-1). Odsustvo = potencijalni `|safe` (stored-XSS)."
    )
    assert "<script>alert(1)</script>" not in html, (
        "SIROV `<script>` NE SME biti u response-u (stored-XSS). "
        "body NIKAD `|safe` bez sanitizacije — rich-text=8.7."
    )


# ─────────────────────────────────────────────────────────────────────────────
# AC2 (9.5) — „Slične objave" (SM-D8 / Gotcha BL3-3)
# ─────────────────────────────────────────────────────────────────────────────


# AC2: similar_posts = same-category published, exclude-self, draft-not-leaked, bounded
def test_similar_posts_same_category_exclude_self_draft_excluded(
    client, make_post, make_category
):
    activate("sr")
    k = make_category(name="Ratarstvo")
    other = make_category(name="Stočarstvo")

    p = _published(make_post, title="Glavna priča P", category=k)
    sim1 = _published(make_post, title="Slična 1", category=k)
    sim2 = _published(make_post, title="Slična 2", category=k)
    sim3 = _published(make_post, title="Slična 3", category=k)
    draft_in_k = make_post(
        title="Draft u K", status="draft", published_at=None, category=k
    )
    pub_other = _published(make_post, title="Druga kategorija", category=other)

    response = _get_detail(client, p)

    assert response.status_code == 200
    assert "similar_posts" in response.context, (
        "get_context_data MORA postaviti `similar_posts` (AC2 — 5-3 obogaćenje; RED)."
    )
    similar_pks = {sp.pk for sp in response.context["similar_posts"]}

    assert {sim1.pk, sim2.pk, sim3.pk} <= similar_pks, (
        "similar_posts MORA sadržati published objave ISTE kategorije."
    )
    assert p.pk not in similar_pks, (
        "current post (P) NE SME biti u svojim slicnim (.exclude(pk=post.pk))."
    )
    assert draft_in_k.pk not in similar_pks, (
        "DRAFT u istoj kategoriji NE SME procuriti (Post.published — draft-not-leaked)."
    )
    assert pub_other.pk not in similar_pks, (
        "published objava DRUGE kategorije NE SME biti u similar_posts."
    )


# AC2: bounded ≤ _SIMILAR_POSTS_LIMIT (4)
def test_similar_posts_bounded_to_limit(client, make_post, make_category):
    activate("sr")
    k = make_category(name="Ratarstvo")
    p = _published(make_post, title="Glavna priča za bound", category=k)
    # 6 dodatnih published u K → similar mora biti CAP-ovan na 4
    for i in range(6):
        _published(make_post, title=f"Slična bound {i}", category=k)

    response = _get_detail(client, p)

    assert response.status_code == 200
    similar = response.context["similar_posts"]
    assert len(similar) <= 4, (
        f"similar_posts MORA biti bounded `[:_SIMILAR_POSTS_LIMIT]` (≤4 — epics.md:889). "
        f"Dobili {len(similar)}."
    )


# AC2: post.category is None (SET_NULL) → similar_posts prazna (NE crash, NE „sve")
def test_similar_posts_empty_when_category_none(client, make_post):
    activate("sr")
    # druge published objave bez kategorije postoje → ne smeju procuriti kao „slične"
    _published(make_post, title="Bez kategorije A", category=None)
    p = _published(make_post, title="Glavna bez kategorije", category=None)

    response = _get_detail(client, p)

    assert response.status_code == 200, (
        "Detail sa post.category=None MORA biti 200 (NE crash — SM-D8 guard)."
    )
    assert list(response.context["similar_posts"]) == [], (
        "post.category=None -> similar_posts MORA biti prazna (NE sve objave; SM-D8)."
    )


# AC2: kategorija sa SAMO current-post → similar prazna → sekcija se NE renderuje
def test_similar_posts_empty_when_only_self_in_category(
    client, make_post, make_category
):
    activate("sr")
    k = make_category(name="Usamljena")
    p = _published(make_post, title="Jedina u kategoriji", category=k)

    response = _get_detail(client, p)

    assert response.status_code == 200
    assert list(response.context["similar_posts"]) == [], (
        "Kategorija sa samo-current-post → similar_posts prazna (graceful)."
    )


# AC2 / AC9 / SM-D2: future-dated (scheduled) sibling NE SME procuriti u similar_posts
# (Post.published filtrira published_at__lte=now — draft-not-leaked druga polovina).
def test_similar_posts_future_published_excluded(client, make_post, make_category):
    activate("sr")
    k = make_category(name="Ratarstvo")
    p = _published(make_post, title="Glavna priča P", category=k)
    past = _published(make_post, title="Prošla slična u K", category=k)
    future = make_post(
        title="Zakazana slična u K",
        status="published",
        published_at=timezone.now() + timezone.timedelta(days=7),
        category=k,
    )

    response = _get_detail(client, p)

    assert response.status_code == 200
    similar_pks = {sp.pk for sp in response.context["similar_posts"]}
    assert past.pk in similar_pks, (
        "Prošla published sibling MORA biti u similar_posts."
    )
    assert future.pk not in similar_pks, (
        "FUTURE-dated (scheduled) sibling NE SME procuriti u similar_posts "
        "(Post.published filtrira published_at__lte=now — AC2/AC9/SM-D2)."
    )


# ─────────────────────────────────────────────────────────────────────────────
# AC6 (9.9) — social share (SM-D6 / IMP-2 / IMP-3)
# ─────────────────────────────────────────────────────────────────────────────


# AC6: share_url u kontekstu == apsolutni post URL (IMP-2)
def test_share_url_is_absolute_post_url(client, make_post):
    activate("sr")
    post = _published(make_post, title="Share URL priča")

    response = _get_detail(client, post)

    assert response.status_code == 200
    assert "share_url" in response.context, (
        "get_context_data MORA postaviti `share_url` "
        "(request.build_absolute_uri(post.get_absolute_url()) — IMP-2; RED)."
    )
    share_url = response.context["share_url"]
    assert share_url.startswith("http://") or share_url.startswith("https://"), (
        f"share_url MORA biti APSOLUTNI URL (scheme + host). Dobili {share_url!r}."
    )
    assert post.get_absolute_url() in share_url, (
        f"share_url MORA sadržati post apsolutnu putanju {post.get_absolute_url()!r}."
    )


# AC6: 4 share dugmeta (FB/Viber/WhatsApp/Copy-link) sa egzaktnim href-ovima (IMP-3)
def test_social_share_buttons_present_with_exact_hrefs(client, make_post):
    activate("sr")
    post = _published(make_post, title="Social share priča")

    response = _get_detail(client, post)

    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert "facebook.com/sharer/sharer.php?u=" in html, (
        "Facebook share href MORA biti `facebook.com/sharer/sharer.php?u=...` (IMP-3)."
    )
    assert "wa.me/?text=" in html or "api.whatsapp.com/send?text=" in html, (
        "WhatsApp share href MORA biti `wa.me/?text=` (ili api.whatsapp.com/send) (IMP-3)."
    )
    assert "viber://forward?text=" in html, (
        "Viber share href MORA biti `viber://forward?text=` (IMP-3)."
    )
    assert "data-share-copy" in html, (
        "Copy-link dugme MORA imati `[data-share-copy]` (vanilla JS clipboard — SM-D6)."
    )


# AC6: Copy-link data-copy-url == share_url
def test_copy_link_carries_share_url(client, make_post):
    activate("sr")
    post = _published(make_post, title="Copy link priča")

    response = _get_detail(client, post)

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    share_url = response.context["share_url"]
    assert f'data-copy-url="{share_url}"' in html, (
        "Copy-link dugme MORA nositi `data-copy-url=\"{{ share_url }}\"` (SM-D6)."
    )


# ─────────────────────────────────────────────────────────────────────────────
# AC7 (9.10) — meta title / description (SM-D7 / IMP-4)
# ─────────────────────────────────────────────────────────────────────────────


# AC7: <title> sadrži post.title; <meta description> sadrži post.perex
def test_meta_title_and_description_from_post(client, make_post):
    activate("sr")
    post = _published(
        make_post,
        title="Žetva pšenice na vreme",
        perex="Kako pravilno isplanirati žetvu.",
    )

    response = _get_detail(client, post)

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "Žetva pšenice na vreme" in html, "<title> MORA sadržati post.title."
    assert 'name="description"' in html
    assert "Kako pravilno isplanirati žetvu." in html, (
        "<meta name=\"description\"> MORA sadržati post.perex (SM-D7)."
    )


# AC7 (IMP-4): prazan perex → meta description == post.title (|default:post.title)
def test_meta_description_falls_back_to_title_when_perex_empty(client, make_post):
    activate("sr")
    post = _published(make_post, title="Naslov bez perexa", perex="")

    response = _get_detail(client, post)

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    import re

    m = re.search(
        r'<meta\s+name="description"\s+content="([^"]*)"', html, re.IGNORECASE
    )
    assert m, "Mora postojati <meta name=\"description\" content=...> tag."
    content = m.group(1)
    assert content.strip() != "", (
        "meta description NE SME biti prazan kad je perex=\"\" "
        "(`|default:post.title` fallback — IMP-4)."
    )
    assert "Naslov bez perexa" in content, (
        "Prazan perex → meta description == post.title (`|default:post.title`; IMP-4)."
    )


# AC7: NEMA OG/twitter (Epic 6)
def test_meta_no_open_graph_yet(client, make_post):
    activate("sr")
    post = _published(make_post, title="Bez OG priča", perex="Perex.")

    response = _get_detail(client, post)

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert 'property="og:' not in html, (
        "5-3 NEMA OG meta (Epic 6 — 6.1 SeoMeta; epics.md:893)."
    )
