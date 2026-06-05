---
story-id: "5.4"
story-key: 5-4-footer-dynamic-najnovije-vesti-kolona
artifact: interface-contract
created: 2026-06-05
author: TEA / Murat (autonomous RED phase)
purpose: Canonical contract za ČETVRTU i POSLEDNJU story Epic 5 — dinamizacija footer
         kolone „Najnovije vesti" (Story 1.8 Lorem placeholder × 3). NOVI
         `apps/blog/context_processors.py:latest_blog_posts(request)` exposes ≤3
         NAJNOVIJE PUBLISHED objave (kroz `Post.published` — draft-not-leaked;
         EKSPLICITAN `.order_by("-published_at","-created_at")`) svim template-ima,
         umotano u `SimpleLazyObject` (upit puca SAMO kad footer iterira — every-request
         perf; 0 upita na HTMX partial, 1 na full page). Registrovan u
         `config/settings/base.py` context_processors listi. Footer kolona 3 renderuje
         svaku objavu kao `<a href="{post.get_absolute_url}">{post.title}</a>`; 0 objava
         → `{% empty %}` placeholder „Uskoro nove priče sa polja" (REUSE 5-2 msgid).
         NEMA model promene / migracije / novog view/url/dep. Dev MORA satisfy svaku
         klauzulu u GREEN.
---

# Interface Contract — Story 5.4 „Footer Dynamic Najnovije vesti Kolona"

Story 5.4 dodaje JEDAN nov modul + JEDNU settings liniju + dinamizuje JEDNU footer kolonu:

- `apps/blog/context_processors.py` (NOVO) — `latest_blog_posts(request)`.
- `config/settings/base.py` (EDIT) — registruj processor u context_processors listi.
- `templates/partials/footer.html` (EDIT) — kolona 3 `<ul class="coric-footer__news">` dinamizacija.

NEMA model promene / migracije / novog view/url/dep. `makemigrations --check --dry-run` MORA „No changes detected".

---

## 1. `apps/blog/context_processors.py` (NOVO)

```python
from django.utils.functional import SimpleLazyObject

from apps.blog.models import Post


def latest_blog_posts(request) -> dict:
    """Exposes ≤3 NAJNOVIJE PUBLISHED objave svim template-ima (footer kolona 3).

    SM-D2 (lazy): SimpleLazyObject → DB upit puca SAMO kad template iterira
    `latest_blog_posts` (full-page render sa footerom). HTMX partial koji NE
    renderuje footer → lazy se NE razrešava → 0 upita (every-request granica —
    footer je u base.html → ovaj processor radi na SVAKOM renderu).

    SM-D2 (list): `list(...)` UNUTAR lambda → SimpleLazyObject kešira listu posle
    prvog poziva → template `{% if %}` + `{% for %}` re-iteracija NE re-query
    (1 upit ukupno; Gotcha BL4-1).

    SM-D1 (ordering): EKSPLICITAN `.order_by("-published_at", "-created_at")` —
    published_at je user-facing recency (kada je objava postala javno vidljiva),
    NE created_at (kada je draft red kreiran). NE oslanja se na Meta.ordering
    (buduća Meta promena ne sme tiho preurediti footer; intent zaključan).

    SM-D3 (draft-not-leaked): `Post.published` (NIKAD `Post.objects`) — status=
    "published" AND published_at__lte=now. Footer je svuda → Post.objects bi
    procurio nacrt/zakazanu objavu na CEO sajt.

    SM-D4 (query shape): BEZ `.only()` — `title` je modeltranslation (realne
    kolone title_sr/_hu/_en); .only("title") bi deferovalo → per-row deferred
    N+1. Plain [:3] queryset je već minimalan (3 reda).

    OQ-2 (no cache): NEMA template-fragment cache / Redis. SimpleLazyObject +
    indeksiran LIMIT-3 upit (blog_post_status_pub_idx) je right-sized.
    """
    return {
        "latest_blog_posts": SimpleLazyObject(
            lambda: list(
                Post.published.order_by("-published_at", "-created_at")[:3]
            )
        )
    }
```

**OBAVEZNE klauzule (testovi asertuju):**

| Klauzula | WHY | Test |
|---|---|---|
| Vraća `dict` sa ključem `"latest_blog_posts"` | context processor ugovor | `test_latest_blog_posts_callable_returns_dict_shape`, `test_*_is_simple_lazy_object` |
| Vrednost je `SimpleLazyObject` | SM-D2 lazy (upit SAMO na iteraciji) | `test_latest_blog_posts_is_simple_lazy_object` |
| `list(...)` UNUTAR lambda | SM-D2 — re-iteracija NE re-query (1 upit) | `test_full_page_render_fires_exactly_one_blog_query` |
| `Post.published` (NE `Post.objects`) | SM-D3 draft-not-leaked (sajt-wide leak guard) | `test_draft_and_future_excluded` |
| EKSPLICITAN `.order_by("-published_at", "-created_at")` | SM-D1 — published_at primarni, NE Meta.ordering | `test_ordering_is_published_at_first_not_created_at` (LOAD-BEARING) |
| `[:3]` LIMIT | epics „3 najnovije"; <3 → koliko ima | `test_latest_blog_posts_caps_at_three`, `test_two_published_yields_two`, `test_one_published_yields_one` |
| BEZ `.only()` | SM-D4 — modeltranslation deferred N+1 hazard | (negativan — Dev NE dodaje) |
| `Post` import na vrhu modula | context_processors se importuje POSLE app registry (startup) — bezbedno | `manage.py check` exit 0 |
| Prost callable BEZ try/except | C2/BL4-6 — sitewide-500 blast radius svesno prihvaćen; defensive bi sakrio realne greške | — |

---

## 2. `config/settings/base.py` (EDIT)

Append U `TEMPLATES[0]["OPTIONS"]["context_processors"]` listu (posle
`"django.contrib.messages.context_processors.messages"`, linija ~81):

```python
            "context_processors": [
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.blog.context_processors.latest_blog_posts",  # NOVO Story 5.4 — footer Najnovije vesti
            ],
```

**WHY:** bez registracije ključ `latest_blog_posts` NIJE u `response.context` → footer for-loop renderuje prazno / KeyError. Svi render testovi (`test_footer_news.py`, `test_context_processors.py` `_home_context_posts`) asertuju `"latest_blog_posts" in response.context`.

---

## 3. `templates/partials/footer.html` (EDIT — SAMO kolona 3)

Zameni 3 Lorem `<li>` (linije 34-38) + ukloni TODO komentar (linija 33). Tačan markup:

```django
        {# Kolona 3 — Najnovije vesti (dinamičke — Story 5.4 latest_blog_posts context processor). #}
        <div class="col-md-3 coric-footer__col">
          {% include "partials/section_eyebrow.html" with text="NAJNOVIJE VESTI" tag="h2" variant="on-dark" %}
          <ul class="coric-footer__news">
            {% for post in latest_blog_posts %}
            <li><a href="{{ post.get_absolute_url }}">{{ post.title }}</a></li>
            {% empty %}
            <li class="coric-footer__news-empty">{% translate "Uskoro nove priče sa polja" %}</li>
            {% endfor %}
          </ul>
        </div>
```

**OBAVEZNO:**

| Klauzula | WHY | Test |
|---|---|---|
| `{% for post in latest_blog_posts %}` (NE `{% if %}`+`{% for %}`) | single evaluacija; `{% empty %}` pokriva 0-slučaj | `test_ac6_footer_renders_dynamic_news_loop` (nav source-lock) |
| `<a href="{{ post.get_absolute_url }}">{{ post.title }}</a>` | AC6 — link na blog:detail + title (modeltranslation aktivna lokala) | `test_footer_renders_post_link_with_title_and_href`, `test_footer_link_locale_prefixed_{sr,hu}` |
| `{% empty %}` → `<li class="coric-footer__news-empty">{% translate "Uskoro nove priče sa polja" %}</li>` | AC5/SM-D5 — REUSE postojeći msgid; stabilan markup hook | `test_footer_empty_placeholder_when_no_posts`, `test_footer_empty_state_has_no_broken_empty_li` |
| Ukloni „Lorem ipsum" × 3 | 5-4 dinamizuje | `test_ac6_footer_renders_dynamic_news_loop` (asertuje NEMA „Lorem ipsum") |
| Ukloni „Story 5.4" / `latest_posts` TODO komentar | IMP-1 — nijedna `latest_posts` varijabla ne preživljava (kanonski ključ je `latest_blog_posts`) | `test_ac6_footer_renders_dynamic_news_loop` (asertuje NEMA „Story 5.4") |
| `section_eyebrow` „NAJNOVIJE VESTI" + `<ul class="coric-footer__news">` wrapper OSTAJU | SM-D5 — heading uvek; kolone 1/2/4 NETAKNUTE | `test_ac6_footer_renders_4_columns_with_3_section_eyebrows` (:701 — netaknut, OSTAJE zelen) |

---

## 4. Context keys / URL-ovi / klase / msgid-i koje testovi asertuju

| Naziv | Tip | Asertovano u |
|---|---|---|
| `latest_blog_posts` | context key (SimpleLazyObject → list[Post] ≤3) | oba test fajla |
| `pages:home` | URL (full-page render vehicle — footer iterira) | sve render asercije |
| `/sr/blog/<slug>/`, `/hu/blog/<slug>/` | `post.get_absolute_url()` (blog:detail, locale-prefiksovano) | AC6/AC8 link testovi |
| `/sr/blog/` + `HTTP_HX_REQUEST="true"` | HTMX partial vehicle (`_post_results.html`, BEZ footera) | AC7 0-query lock |
| `coric-footer__news` | `<ul>` klasa (wrapper OSTAJE) | footer markup |
| `coric-footer__news-empty` | `<li>` empty placeholder klasa (markup hook) | AC5 |
| `"Uskoro nove priče sa polja"` | msgid (REUSE 5-2 `_blog_empty_state.html:15`; sr/hu/en) | AC5 |
| `"NAJNOVIJE VESTI"` | section_eyebrow heading (OSTAJE) | AC5, :701 nav test |

---

## 5. Production signatures (1-paragraf — šta Dev implementira)

Dev kreira `apps/blog/context_processors.py` sa jednom funkcijom
`latest_blog_posts(request) -> dict` koja vraća
`{"latest_blog_posts": SimpleLazyObject(lambda: list(Post.published.order_by("-published_at", "-created_at")[:3]))}`
(import `from django.utils.functional import SimpleLazyObject` + `from apps.blog.models import Post`);
append-uje `"apps.blog.context_processors.latest_blog_posts"` u
`TEMPLATES[0]["OPTIONS"]["context_processors"]` u `config/settings/base.py`;
i menja `templates/partials/footer.html` kolonu 3 da zameni 3 Lorem `<li>` + TODO
komentar sa `{% for post in latest_blog_posts %}<li><a href="{{ post.get_absolute_url }}">{{ post.title }}</a></li>{% empty %}<li class="coric-footer__news-empty">{% translate "Uskoro nove priče sa polja" %}</li>{% endfor %}`,
čuvajući `section_eyebrow` „NAJNOVIJE VESTI" heading i `<ul class="coric-footer__news">` wrapper.
NEMA migracije, model promene, novog view/url, ili novog dep-a. Dev NE piše/ne menja testove.

---

## 6. Test inventory (RED phase — TEA OWNS)

| Fajl | Testovi |
|---|---|
| `apps/blog/tests/test_context_processors.py` (NEW) | AC1 (cap≤3, SimpleLazyObject, dict-shape), AC2 (published_at-first LOAD-BEARING + newest-first), AC3 (draft+future excluded), AC4 (2→2, 1→1, 0→[]), AC8 (title aktivna lokala) |
| `apps/blog/tests/test_footer_news.py` (NEW) | AC6 (link href+title, ≤3 links), AC5 (empty placeholder, no broken `<li>`), AC7 (1-query full-page, 0-query HTMX partial — LAZY LOAD-BEARING), AC8 (link locale-prefiksovan sr/hu) |
| `tests/test_navigation_chrome.py` (REWRITE) | `test_ac6_footer_renders_dynamic_news_loop` (bivši `..._lorem_ipsum_news_placeholder_with_todo`) — source-lock: for-loop PRISUTAN, „Lorem ipsum" ODSUTAN, „Story 5.4" ODSUTAN. `test_ac6_footer_renders_4_columns_with_3_section_eyebrows` (:701) NETAKNUT — OSTAJE zelen. |
