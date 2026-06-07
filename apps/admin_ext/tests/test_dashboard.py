"""Story 8.3 — Admin Dashboard sa Segmentovanim Lead Count-om (TEA RED phase).

Pokriva svih 9 AC-ova:
- AC1  dashboard zamenjuje admin index (override aktivan; app_list zadržan)
- AC2  segmentovan lead count za TEKUĆI mesec; total = zbir 4; TZ-aware month boundary
- AC3  segmenti koriste STABILNE Lead.FormType vrednosti; svi 4 ključa uvek prisutni (0)
- AC4  broj objavljenih proizvoda (is_published) + objavljenih objava (Post.published)
- AC5  GA stub graceful (None-ovi; placeholder; except Exception path)
- AC6  brze-akcije linkuju admin add view-ove (reverse rezolvuje)
- AC7  RBAC gate: anon→302, Editor(is_staff)→200, Superadmin→200; oba VIDE dashboard
- AC8  efikasna agregacija — assertNumQueries(1) na IZOLOVAN get_lead_stats()
- AC9  bez sirovog PII na dashboard-u (samo count-ovi)
+ 0 migracija (makemigrations --check admin_ext → none)

⚠️ COLLECTION-SAFETY (KRITIČNO): SVI importi apps.admin_ext.* su UNUTAR test funkcija
(lazy). U RED fazi apps.admin_ext NE postoji → svaki test pada per-test (ModuleNotFoundError
za stats/analytics; default admin index nema stats markup za render testove), NE collection
abort koji bi oborio celu suite.

⛔ reverse() PRAVILO: admin na bare /admin-coric/ (8.1, VAN i18n_patterns). Koristi
reverse("admin:index") / reverse("admin:products_product_add") — NIKAD hardkodovan put.

OČEKIVANO U RED FAZI: SVI testovi padaju —
- get_lead_stats/get_content_stats/get_ga_visits → ModuleNotFoundError (apps.admin_ext)
- override/render → default admin index NEMA stats markup (segmenti/total/placeholder/brze-akcije)
- makemigrations --check → app admin_ext ne postoji (AppRegistryNotReady / unknown app)

Refs:
- 8-3-...-lead-count-om.md AC1-AC9 + ## Testing + SM-D1..D8 + G-1..G-12
- 8-3-interface-contract.md
- apps/blog/tests/test_admin.py + apps/gdpr/tests/test_admin.py (admin smoke precedent)
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils import timezone

pytestmark = pytest.mark.django_db


# ══════════════════════════════════════════════════════════════════════════════
# Helpers (lazy — collection-safe)
# ══════════════════════════════════════════════════════════════════════════════
def _form_type_values():
    """4 STABILNE DB vrednosti iz Lead.FormType (single-source — AC3/SM-D8)."""
    from apps.forms.models import Lead

    return {
        "contact": Lead.FormType.KONTAKT.value,
        "model_inquiry": Lead.FormType.MODEL_INQUIRY.value,
        "service_request": Lead.FormType.SERVICE_REQUEST.value,
        "part_request": Lead.FormType.PART_REQUEST.value,
    }


def _warm_contenttype_cache():
    """Warm ContentType keš da se eliminiše order-dependent query drift u view testovima
    (Epic 6 query-budget lekcija; pominje se u AC8/## Testing)."""
    list(ContentType.objects.all())


# Dashboard-specifičan sentinel: GA placeholder „uskoro / Epic 9" (AC5/SM-D6/OQ-1).
# Default Django admin index NIKAD ne sadrži ovaj string → koristi se kao DISKRIMINATOR
# da render-zavisni testovi padaju u RED (default index ih inače trivijalno zadovolji
# preko app_list-a / admin chrome-a). Match je case-insensitive na „uskoro" radi
# robusnosti na tačnu interpunkciju Dev-ovog placeholdera.
_DASHBOARD_SENTINEL = "uskoro"


def _assert_is_dashboard(html):
    """Potvrdi da je render PRILAGOĐEN dashboard (override aktivan), NE default admin index.

    Diskriminator = GA placeholder sentinel koji default index nema. U RED fazi override
    NIJE ožičen → sentinel odsutan → AssertionError (korektan RED).
    """
    assert _DASHBOARD_SENTINEL in html.lower(), (
        "Render MORA biti prilagođen 8.3 dashboard (GA placeholder "
        "'Posete: N/D - uskoro / Epic 9'; AC5/SM-D6) - default admin index nema ovaj "
        "marker (override nije ožičen)."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC2/AC3/AC8 — get_lead_stats()
# ══════════════════════════════════════════════════════════════════════════════
def test_get_lead_stats_returns_exact_four_keys_plus_total():
    """AC2/AC3: dict ima TAČNO ključeve {contact, model_inquiry, service_request,
    part_request, total} — ni više ni manje."""
    from apps.admin_ext.stats import get_lead_stats

    stats = get_lead_stats()
    assert set(stats.keys()) == {
        "contact",
        "model_inquiry",
        "service_request",
        "part_request",
        "total",
    }, f"get_lead_stats() MORA imati TAČNO 4 segmenta + total — dobio {set(stats.keys())}."


def test_get_lead_stats_zero_when_no_leads():
    """AC3: svi 4 ključa UVEK prisutni i = 0 kad nema lead-ova; total = 0."""
    from apps.admin_ext.stats import get_lead_stats

    stats = get_lead_stats()
    for key in ("contact", "model_inquiry", "service_request", "part_request", "total"):
        assert stats[key] == 0, f"{key} MORA biti 0 kad nema lead-ova, dobio {stats[key]}."


def test_get_lead_stats_segment_counts_current_month(make_lead):
    """AC2/AC3: tačan broj po segmentu za TEKUĆI mesec (kreiraj raznorodne form_type-ove)."""
    from apps.admin_ext.stats import get_lead_stats

    ft = _form_type_values()
    now = timezone.now()
    # contact x3, model_inquiry x2, service_request x1, part_request x0
    for _ in range(3):
        make_lead(ft["contact"], created_at=now)
    for _ in range(2):
        make_lead(ft["model_inquiry"], created_at=now)
    make_lead(ft["service_request"], created_at=now)

    stats = get_lead_stats()
    assert stats["contact"] == 3, f"contact MORA biti 3, dobio {stats['contact']}."
    assert stats["model_inquiry"] == 2, f"model_inquiry MORA biti 2, dobio {stats['model_inquiry']}."
    assert stats["service_request"] == 1, (
        f"service_request MORA biti 1, dobio {stats['service_request']}."
    )
    assert stats["part_request"] == 0, (
        f"part_request MORA biti 0 (nijedan kreiran), dobio {stats['part_request']}."
    )


def test_get_lead_stats_total_is_sum_of_four_segments(make_lead):
    """AC2 (total-semantika): total == ZBIR 4 segmenta (single-source, NE zaseban count())."""
    from apps.admin_ext.stats import get_lead_stats

    ft = _form_type_values()
    now = timezone.now()
    make_lead(ft["contact"], created_at=now)
    make_lead(ft["contact"], created_at=now)
    make_lead(ft["model_inquiry"], created_at=now)
    make_lead(ft["part_request"], created_at=now)

    stats = get_lead_stats()
    expected = (
        stats["contact"]
        + stats["model_inquiry"]
        + stats["service_request"]
        + stats["part_request"]
    )
    assert stats["total"] == expected, (
        f"total MORA biti zbir 4 segmenta ({expected}), dobio {stats['total']}."
    )
    assert stats["total"] == 4, f"total MORA biti 4 za 4 kreirana lead-a, dobio {stats['total']}."


def test_get_lead_stats_excludes_previous_month(make_lead):
    """AC2/G-4/G-5/SM-D7: lead-ovi iz PROŠLOG meseca se NE broje (TZ-aware month_start
    boundary). Kreira lead pre početka tekućeg meseca → mora biti isključen."""
    from apps.admin_ext.stats import get_lead_stats

    ft = _form_type_values()
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # 1 sekund PRE početka tekućeg meseca = prošli mesec
    previous_month_dt = month_start - timedelta(seconds=1)

    make_lead(ft["contact"], created_at=now)  # tekući mesec — broji se
    make_lead(ft["contact"], created_at=previous_month_dt)  # prošli mesec — NE broji se

    stats = get_lead_stats()
    assert stats["contact"] == 1, (
        f"SAMO tekući-mesec lead se broji (TZ-aware month_start granica; G-4/G-5/SM-D7) — "
        f"prošlomesečni mora biti isključen; očekivano 1, dobio {stats['contact']}."
    )
    assert stats["total"] == 1, (
        f"total MORA biti 1 (prošlomesečni isključen), dobio {stats['total']}."
    )


def test_get_lead_stats_isolated_single_query(django_assert_num_queries, make_lead):
    """AC8/G-6: IZOLOVAN get_lead_stats() poziv = TAČNO 1 upit (jedan .values().annotate()
    agregat) — NE per-segment petlja sa 4 .count(). Opseg lock-a = SAMO ova izolovana
    funkcija (NE ceo view; vidi view budget test)."""
    from apps.admin_ext.stats import get_lead_stats

    ft = _form_type_values()
    now = timezone.now()
    make_lead(ft["contact"], created_at=now)
    make_lead(ft["model_inquiry"], created_at=now)
    make_lead(ft["service_request"], created_at=now)
    make_lead(ft["part_request"], created_at=now)

    with django_assert_num_queries(1):
        get_lead_stats()


def test_get_lead_stats_keys_match_formtype_values():
    """AC3/SM-D8: ključevi su STABILNE Lead.FormType .value vrednosti (NE proizvoljni hardkod)."""
    from apps.admin_ext.stats import get_lead_stats

    ft = _form_type_values()
    stats = get_lead_stats()
    for value in ft.values():
        assert value in stats, (
            f"get_lead_stats() ključ MORA biti Lead.FormType.<X>.value ('{value}') — "
            f"single-source iz enum-a (SM-D8); dobijeni ključevi: {set(stats.keys())}."
        )


# ══════════════════════════════════════════════════════════════════════════════
# AC4/AC8 — get_content_stats()
# ══════════════════════════════════════════════════════════════════════════════
def test_get_content_stats_counts_only_published_products():
    """AC4/G-7: SAMO is_published=True proizvodi se broje; draft/unpublished izostavljeni."""
    from apps.products.tests.factories import ProductFactory

    from apps.admin_ext.stats import get_content_stats

    # TEST_MODIFICATION (8.3 Dev): meri DELTU umesto hardkodovanog ==2.
    # Test-DB već sadrži 2 seed-ovana objavljena proizvoda (brands migracija
    # 0004_seed_hzm_tulip_brands → „Tulip MIX 6/8 m³", is_published=True), pa
    # apsolutni ==2 nije validan na realnom test-DB-u. Delta (+2 published, +1
    # unpublished isključen) i dalje TAČNO verifikuje AC4/G-7 invariantu.
    baseline = get_content_stats()["published_products"]

    ProductFactory.create(is_published=True)
    ProductFactory.create(is_published=True)
    ProductFactory.create_unpublished()  # is_published=False — NE broji se

    stats = get_content_stats()
    assert stats["published_products"] == baseline + 2, (
        f"published_products MORA brojati SAMO is_published=True (+2 nad baseline "
        f"{baseline}; unpublished isključen), dobio {stats['published_products']}."
    )


def test_get_content_stats_counts_only_published_posts():
    """AC4/G-7: SAMO Post.published (status=published AND published_at<=now) se broji;
    draft i future-dated izostavljeni (NE Post.objects)."""
    from apps.blog.models import Post

    from apps.admin_ext.stats import get_content_stats

    now = timezone.now()
    # TEST_MODIFICATION (8.3 batch-fix): meri DELTU umesto hardkodovanog ==1 (mirror
    # published_products) — budući blog-seed migracija ne sme oboriti AC4 invariantu.
    baseline = get_content_stats()["published_posts"]

    # objavljen (status=published, published_at u prošlosti) — broji se (+1)
    Post.objects.create(
        title="Žetva pšenice — objavljeno",
        status=Post.Status.PUBLISHED,
        published_at=now - timedelta(hours=1),
    )
    # draft — NE broji se
    Post.objects.create(title="Nacrt o đubrenju", status=Post.Status.DRAFT)
    # future-dated published — NE broji se (published_at > now)
    Post.objects.create(
        title="Buduća objava",
        status=Post.Status.PUBLISHED,
        published_at=now + timedelta(days=3),
    )

    stats = get_content_stats()
    assert stats["published_posts"] == baseline + 1, (
        f"published_posts MORA brojati SAMO Post.published (status=published AND "
        f"published_at<=now) → +1 nad baseline {baseline}; draft/future-dated "
        f"izostavljeni (G-7); dobio {stats['published_posts']}."
    )


def test_get_content_stats_returns_expected_keys():
    """AC4: dict ima ključeve published_products + published_posts."""
    from apps.admin_ext.stats import get_content_stats

    stats = get_content_stats()
    assert "published_products" in stats and "published_posts" in stats, (
        f"get_content_stats() MORA imati 'published_products' i 'published_posts' — "
        f"dobio {set(stats.keys())}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC1 — get_dashboard_stats() agregator API kontrakt
# ══════════════════════════════════════════════════════════════════════════════
def test_get_dashboard_stats_returns_expected_top_level_keys(make_lead):
    """AC1: agregator vraća TAČNO {lead_stats, lead_segments, content_stats, ga_visits}
    — zaključava API kontrakt koji view-wrapper injektuje u extra_context."""
    from apps.admin_ext.stats import get_dashboard_stats

    make_lead(_form_type_values()["contact"], created_at=timezone.now())

    stats = get_dashboard_stats()
    assert set(stats.keys()) == {
        "lead_stats",
        "lead_segments",
        "content_stats",
        "ga_visits",
    }, f"get_dashboard_stats() MORA imati TAČNO 4 top-level ključa — dobio {set(stats.keys())}."
    # lead_segments = lista {label, count} parova (svi 4 FormType-a; SM-D8)
    assert isinstance(stats["lead_segments"], list) and len(stats["lead_segments"]) == 4, (
        f"lead_segments MORA biti lista od 4 segmenta, dobio {stats['lead_segments']!r}."
    )
    for segment in stats["lead_segments"]:
        assert set(segment.keys()) == {"label", "count"}, (
            f"svaki lead_segment MORA imati {{label, count}}, dobio {set(segment.keys())}."
        )
    assert set(stats["ga_visits"].keys()) == {"last_7", "last_30"}, (
        f"ga_visits MORA imati {{last_7, last_30}}, dobio {set(stats['ga_visits'].keys())}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC5/AC9 — get_ga_visits() graceful stub
# ══════════════════════════════════════════════════════════════════════════════
def test_get_ga_visits_returns_none_in_v1():
    """AC5/SM-D6: v1 (GA Reporting API nekonfigurisan) → {last_7: None, last_30: None}
    BEZ izuzetka i BEZ mrežnog poziva."""
    from apps.admin_ext.analytics import get_ga_visits

    visits = get_ga_visits()
    assert visits == {"last_7": None, "last_30": None}, (
        f"get_ga_visits() v1 MORA vratiti {{last_7: None, last_30: None}} (graceful stub; "
        f"SM-D6), dobio {visits!r}."
    )


def test_get_ga_visits_no_exception_raised():
    """AC5: get_ga_visits() NIKAD ne podiže izuzetak u v1 (fail-safe granica)."""
    from apps.admin_ext.analytics import get_ga_visits

    try:
        get_ga_visits()
    except Exception as exc:  # noqa: BLE001 — test eksplicitno proverava da NEMA izuzetka
        pytest.fail(f"get_ga_visits() NE SME podići izuzetak u v1, podigao: {exc!r}.")


def test_dashboard_loads_when_ga_raises(client, superuser, monkeypatch):
    """AC5/G-9 (except Exception path): čak i ako get_ga_visits() baci izuzetak, dashboard
    se UVEK učita (HTTP 200) — poziv obavijen try/except Exception (NE bare except)."""
    import apps.admin_ext.analytics as analytics

    def _boom():
        raise RuntimeError("GA timeout — simulirani izuzetak")

    monkeypatch.setattr(analytics, "get_ga_visits", _boom)
    # patch-uj i referencu u stats agregatoru ako je import-by-name (defensivno)
    try:
        import apps.admin_ext.stats as stats_mod

        if hasattr(stats_mod, "get_ga_visits"):
            monkeypatch.setattr(stats_mod, "get_ga_visits", _boom)
    except ModuleNotFoundError:
        pass

    _warm_contenttype_cache()
    client.force_login(superuser)
    response = client.get(reverse("admin:index"))
    assert response.status_code == 200, (
        f"Dashboard MORA biti 200 čak i kad get_ga_visits() baci (fail-safe try/except "
        f"Exception; AC5/G-9), dobio {response.status_code}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC1 — override aktivan (admin.site.index zamenjen + index_template)
# ══════════════════════════════════════════════════════════════════════════════
def test_admin_index_template_overridden():
    """AC1/SM-D1: admin.site.index_template pokazuje na admin_ext/dashboard.html."""
    from django.contrib import admin

    assert admin.site.index_template == "admin_ext/dashboard.html", (
        f"admin.site.index_template MORA biti 'admin_ext/dashboard.html' (PINOVAN override; "
        f"SM-D1/G-1), dobio {admin.site.index_template!r}."
    )


def test_dashboard_renders_stats_markup(client, superuser, make_lead):
    """AC1/AC2: /admin-coric/ index renderuje dashboard statistiku (segmenti + total)."""
    ft = _form_type_values()
    make_lead(ft["contact"], created_at=timezone.now())

    _warm_contenttype_cache()
    client.force_login(superuser)
    response = client.get(reverse("admin:index"))
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    # override aktivan (GA placeholder sentinel) + lead total/ukupno marker prisutan
    _assert_is_dashboard(html)
    assert "total" in html.lower() or "ukupno" in html.lower(), (
        "Dashboard HTML MORA prikazati lead 'total'/'Ukupno' (AC2 total istaknut) — "
        "default admin index nema ovaj marker (override nije ožičen)."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC1/SM-D2 — app_list zadržan ispod dashboard-a
# ══════════════════════════════════════════════════════════════════════════════
def test_app_list_preserved_below_dashboard(client, superuser):
    """AC1/SM-D2/G-2: default admin app_list i dalje renderuje ispod dashboard sekcije
    (wrapper delegira na _original_index koji gradi app_list)."""
    _warm_contenttype_cache()
    client.force_login(superuser)
    response = client.get(reverse("admin:index"))
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    # prvo potvrdi da je render PRILAGOĐEN dashboard (override aktivan), pa da app_list KOEGZISTIRA
    _assert_is_dashboard(html)
    # app_list context var prisutan + bar jedan poznat admin model link (products changelist)
    assert "app_list" in response.context, (
        "Dashboard MORA zadržati 'app_list' u context-u (delegira na _original_index; SM-D2/G-2)."
    )
    products_changelist = reverse("admin:products_product_changelist")
    assert products_changelist in html, (
        f"app_list MORA renderovati postojeće admin sekcije (npr. {products_changelist}) "
        f"ISPOD dashboard-a (SM-D2) — navigacija ne sme nestati (G-2)."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC6 — brze-akcije linkovi
# ══════════════════════════════════════════════════════════════════════════════
def test_quick_action_urls_resolve():
    """AC6/G-8: admin add URL-ovi za Product i Post rezolvuju (reverse ne baca)."""
    product_add = reverse("admin:products_product_add")
    post_add = reverse("admin:blog_post_add")
    assert product_add and post_add, "Quick-action admin add URL-ovi MORAJU rezolvovati (G-8)."


def test_dashboard_contains_quick_action_links(client, superuser):
    """AC6/G-8: dashboard HTML sadrži href-ove ka admin:products_product_add i
    admin:blog_post_add (brze akcije „Dodaj proizvod"/„Dodaj blog objavu")."""
    _warm_contenttype_cache()
    client.force_login(superuser)
    response = client.get(reverse("admin:index"))
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    # potvrdi prvo da je override aktivan (dashboard render), pa da brze-akcije postoje
    _assert_is_dashboard(html)
    product_add = reverse("admin:products_product_add")
    post_add = reverse("admin:blog_post_add")
    assert product_add in html, (
        f"Dashboard MORA sadržati brzu-akciju link na {product_add!r} (AC6/G-8)."
    )
    assert post_add in html, (
        f"Dashboard MORA sadržati brzu-akciju link na {post_add!r} (AC6/G-8)."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC7 — RBAC gate (anon / Editor / Superadmin)
# ══════════════════════════════════════════════════════════════════════════════
def test_dashboard_anonymous_redirects_to_login(client):
    """AC7: anoniman pristup /admin-coric/ index → 302 admin login redirect."""
    response = client.get(reverse("admin:index"))
    assert response.status_code == 302, (
        f"Anoniman pristup dashboard-u MORA biti 302 (admin login redirect; AC7), "
        f"dobio {response.status_code}."
    )


def test_dashboard_superadmin_sees_dashboard(client, superuser, make_lead):
    """AC7 SIMETRIJA: Superadmin (is_superuser + is_staff) → 200 vidi dashboard statistiku."""
    make_lead(_form_type_values()["contact"], created_at=timezone.now())
    _warm_contenttype_cache()
    client.force_login(superuser)
    response = client.get(reverse("admin:index"))
    assert response.status_code == 200, (
        f"Superadmin MORA videti dashboard (200; AC7), dobio {response.status_code}."
    )
    html = response.content.decode("utf-8")
    _assert_is_dashboard(html)
    assert reverse("admin:products_product_add") in html, (
        "Superadmin dashboard MORA prikazati brze-akcije (AC6/AC7)."
    )


def test_dashboard_editor_sees_dashboard(client, editor_user, make_lead):
    """AC7 SIMETRIJA/SM-D5: Editor (is_staff, Editor grupa, NE superuser) → 200 vidi
    dashboard (agregat, ne PII — dostupno obema admin ulogama)."""
    make_lead(_form_type_values()["model_inquiry"], created_at=timezone.now())
    _warm_contenttype_cache()
    client.force_login(editor_user)
    response = client.get(reverse("admin:index"))
    assert response.status_code == 200, (
        f"Editor (is_staff) MORA videti dashboard (200; AC7/SM-D5), dobio {response.status_code}."
    )
    html = response.content.decode("utf-8")
    _assert_is_dashboard(html)
    assert reverse("admin:blog_post_add") in html, (
        "Editor dashboard MORA prikazati brze-akcije (AC6/AC7/SM-D5)."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC9 — bez sirovog PII na dashboard-u
# ══════════════════════════════════════════════════════════════════════════════
def test_dashboard_does_not_leak_lead_pii(client, superuser, make_lead):
    """AC9: dashboard prikazuje ISKLJUČIVO agregate — NIJEDNO ime/email/telefon/poruka
    iz Lead-a se NE renderuje (sentinel PII vrednosti iz make_lead ne smeju biti u HTML-u)."""
    make_lead(
        _form_type_values()["contact"],
        created_at=timezone.now(),
        name="Đorđe TAJNI Petrović",
        email="leak-detektor@example.com",
        phone="+381699998877",
        message="POVERLJIVA poruka koja ne sme da procuri.",
    )
    _warm_contenttype_cache()
    client.force_login(superuser)
    response = client.get(reverse("admin:index"))
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    # potvrdi da je override aktivan (inače test trivijalno prolazi na default indexu)
    _assert_is_dashboard(html)
    for pii in (
        "Đorđe TAJNI Petrović",
        "leak-detektor@example.com",
        "+381699998877",
        "POVERLJIVA poruka koja ne sme da procuri.",
    ):
        assert pii not in html, (
            f"Dashboard NE SME sadržati sirovi Lead PII ({pii!r}) — samo agregati/count-ovi (AC9)."
        )


# ══════════════════════════════════════════════════════════════════════════════
# AC8 (view budget — labaviji, zaseban od izolovanog stats lock-a)
# ══════════════════════════════════════════════════════════════════════════════
def test_dashboard_view_query_budget_bounded(
    client, superuser, make_lead, django_assert_max_num_queries
):
    """AC8: pun /admin-coric/ GET ima OGRANIČEN (labaviji, gornja granica) integracioni
    budžet — NE 1 (view pokreće admin get_app_list permission/ContentType upite). Warm
    ContentType keš da se izbegne order-dependent drift (Epic 6 lekcija). Eksplicitno
    razdvojeno od izolovanog get_lead_stats() lock-a (=1)."""
    ft = _form_type_values()
    now = timezone.now()
    for key in ("contact", "model_inquiry", "service_request", "part_request"):
        make_lead(ft[key], created_at=now)

    _warm_contenttype_cache()
    client.force_login(superuser)
    # gornja granica — generozna; stvarna cena su admin chrome upiti + 3 stat upita
    with django_assert_max_num_queries(40):
        response = client.get(reverse("admin:index"))
    assert response.status_code == 200
    # potvrdi da budžet važi za STVARNI dashboard render (override aktivan), NE default index
    _assert_is_dashboard(response.content.decode("utf-8"))


# ══════════════════════════════════════════════════════════════════════════════
# 0 migracija (SM-D3)
# ══════════════════════════════════════════════════════════════════════════════
def test_admin_ext_has_no_pending_migrations():
    """SM-D3: admin_ext nema modela → makemigrations --check admin_ext = No changes."""
    from io import StringIO

    from django.core.management import call_command

    out = StringIO()
    try:
        call_command(
            "makemigrations", "admin_ext", "--check", "--dry-run", stdout=out, stderr=out
        )
    except SystemExit as exc:
        # --check exit-uje 1 ako BI generisao migracije → fail (admin_ext mora biti 0-model)
        assert exc.code == 0, (
            f"makemigrations --check admin_ext MORA biti 0 (No changes; SM-D3) — "
            f"admin_ext je 0-model app. Izlaz: {out.getvalue()}"
        )
