"""Story 8.5 — Category + Subcategory CRUD sa Hierarchy (TEA RED phase).

DEFINES the contract Dev must satisfy. Maps to the 11 ACs + Testing section of
`8-5-category-subcategory-crud-sa-hierarchy.md`. Canonical contract:
`8-5-category-subcategory-crud-sa-hierarchy-interface-contract.md`.

RUN (through Docker for parity; no upload fields here but `just test` keeps env identical):
    just test apps/brands/tests/test_category_subcategory_crud_admin.py -v

RED expectation: `apps/brands/admin.py` still has the minimal 6.1 stubs
(`CategoryAdmin`/`SubcategoryAdmin = SeoWarningAdminMixin + admin.ModelAdmin`, no
`TranslationAdmin`, no `view_on_site`, no `list_display`/`list_editable`/`list_filter`/
`search_fields`/`prepopulated_fields`/`list_select_related`). So nearly every test MUST
fail/error. EXCEPTIONS that MAY PASS today (regression locks — noted inline):
  - SeoMetaInline still present on both admins (6.1 already provides it).
  - hierarchy depth/cycle graceful-reject (the MODEL clean() already enforces it, and the
    stub admin's ModelForm already calls full_clean()) — these may pass even before the
    TranslationAdmin conversion; they lock that the conversion does NOT break delegation.
  - cascade/PROTECT delete render-smoke (Django gives it for free on the stub too).
  - the no-pending-migration check.

────────────────────────────────────────────────────────────────────────────────
COLLECTION-SAFETY: all `apps.brands.admin` / model / factory imports are INSIDE test
bodies (lazy) so a missing symbol fails that test individually (true RED), never aborts
collection of the whole file.

AUTH: authenticate with `force_login` (NEVER `client.login` — django-axes from 8.1
pollutes lockout state through authenticate(); established project lesson).

ADMIN URL: always `reverse("admin:brands_category_*")` / `..._subcategory_*` — admin is
at bare `/admin-coric/` (8.1), never hardcode.

EDITOR USER: `is_staff` + member of the `Editor` group. The `Editor` group is created by
the 8.2 `sync_rbac_groups` post_migrate handler during test-DB setup and already carries
brands.add/change/delete/view (EDITOR_CONTENT_MODELS). 8.5 does NOT re-grant (SM-D8).

DEPENDENCY-ORDER FIXTURES: depth + cascade fixtures are built Category → L1 → L2 → L3 in
order (each `parent` requires the prior level) — otherwise an IntegrityError from the
wrong cause masks the real assert.

Refs: 8-5-category-subcategory-crud-sa-hierarchy.md (AC1-AC11, SM-D1..D8, G-1..G-13,
Testing) + the interface contract.
"""

from __future__ import annotations

import re

import pytest
from django.contrib import admin
from django.urls import reverse

pytestmark = pytest.mark.django_db


# ──────────────────────────────────────────────────────────────────────────────
# Users
# ──────────────────────────────────────────────────────────────────────────────
@pytest.fixture
def superuser(django_user_model):
    """Superuser for admin smoke (django_user_model — NEVER direct User import)."""
    return django_user_model.objects.create_superuser(
        username="cat_admin_tea",
        email="cat-admin@example.com",
        password="tea-pass-12345",
    )


@pytest.fixture
def editor(django_user_model):
    """Editor = is_staff + member of the `Editor` group (8.2 post_migrate created it;
    group already carries brands CRUD via EDITOR_CONTENT_MODELS — SM-D8)."""
    from django.contrib.auth.models import Group

    user = django_user_model.objects.create_user(
        username="cat_editor_tea",
        email="cat-editor@example.com",
        password="tea-pass-12345",
        is_staff=True,
        is_superuser=False,
    )
    user.groups.add(Group.objects.get(name="Editor"))
    return user


# ──────────────────────────────────────────────────────────────────────────────
# Admin registry + change-form scraper helpers
# ──────────────────────────────────────────────────────────────────────────────
def _category_admin():
    from apps.brands.models import Category

    return admin.site._registry[Category]


def _subcategory_admin():
    from apps.brands.models import Subcategory

    return admin.site._registry[Subcategory]


def _scrape_change_form(html):
    """name->value for all input/select/textarea fields in an admin change/add form.

    Re-submits the rendered values so the per-locale + inline management-form payload
    stays valid (mirror apps/seo + 8.4 scraper). Callers override only what they test.
    File/submit/button inputs are skipped.
    """
    data = {}
    for m in re.finditer(r"<input[^>]*>", html):
        tag = m.group(0)
        nm = re.search(r'name="([^"]+)"', tag)
        if not nm:
            continue
        name = nm.group(1)
        typ_m = re.search(r'type="([^"]+)"', tag)
        typ = typ_m.group(1) if typ_m else "text"
        if typ in ("submit", "button", "file"):
            continue
        val_m = re.search(r'value="([^"]*)"', tag)
        val = val_m.group(1) if val_m else ""
        if typ == "checkbox":
            if "checked" in tag:
                data[name] = val or "on"
        else:
            data[name] = val
    for sm in re.finditer(r'<select[^>]*name="([^"]+)"[^>]*>(.*?)</select>', html, re.S):
        name = sm.group(1)
        opt = re.search(r'<option[^>]*value="([^"]*)"[^>]*selected', sm.group(2))
        data[name] = opt.group(1) if opt else ""
    for tm in re.finditer(r'<textarea[^>]*name="([^"]+)"[^>]*>(.*?)</textarea>', html, re.S):
        data[tm.group(1)] = tm.group(2)
    return data


def _changelist_reorder_payload(html, row_id, new_order):
    """Build a changelist `list_editable` bulk-save POST dict from a rendered changelist.

    Scrapes the formset management-form counts (`form-TOTAL_FORMS`/`form-INITIAL_FORMS`/…)
    out of the GET HTML rather than hardcoding them, so the payload stays valid no matter
    how many rows the changelist renders. Sets `form-0-id` + `form-0-display_order`.
    """
    data = _scrape_change_form(html)
    data["_save"] = "Save"
    # The scraper already lifts the four `form-*_FORMS` management hidden inputs; assert they
    # are present so a markup change surfaces loudly instead of a silent management-form error.
    for mgmt in ("form-TOTAL_FORMS", "form-INITIAL_FORMS", "form-MIN_NUM_FORMS", "form-MAX_NUM_FORMS"):
        assert mgmt in data, f"changelist GET MORA renderovati `{mgmt}` management-form input."
    data["form-0-id"] = str(row_id)
    data["form-0-display_order"] = str(new_order)
    return data


def _add_payload(client, add_url, extra=None):
    """Scrape the add-view (per-locale + SeoMeta inline management forms) → POST dict.

    `slug` is a REQUIRED admin field; in a browser prepopulated_fields JS fills it from
    name. The no-JS scraper leaves it empty, so callers expecting a SUCCESSFUL save MUST
    pass `slug` explicitly. Callers testing graceful rejection leave it empty.
    """
    data = _scrape_change_form(client.get(add_url).content.decode())
    if extra:
        data.update(extra)
    return data


# ══════════════════════════════════════════════════════════════════════════════
# AC1 — both admins are TranslationAdmin + render 200 + search_fields=name_sr + check
# ══════════════════════════════════════════════════════════════════════════════
# AC-1
def test_ac1_category_admin_is_translationadmin():
    from modeltranslation.admin import TranslationAdmin

    assert isinstance(_category_admin(), TranslationAdmin), (
        "CategoryAdmin MORA biti TranslationAdmin instanca (NE plain ModelAdmin — AC1)."
    )


# AC-1
def test_ac1_subcategory_admin_is_translationadmin():
    from modeltranslation.admin import TranslationAdmin

    assert isinstance(_subcategory_admin(), TranslationAdmin), (
        "SubcategoryAdmin MORA biti TranslationAdmin instanca (NE plain ModelAdmin — AC1)."
    )


# AC-1
def test_ac1_both_admins_keep_seowarning_mixin_in_mro():
    from apps.seo.admin import SeoWarningAdminMixin

    assert isinstance(_category_admin(), SeoWarningAdminMixin), (
        "CategoryAdmin MORA zadržati SeoWarningAdminMixin u MRO (mixin PRVI — G-2/AC1)."
    )
    assert isinstance(_subcategory_admin(), SeoWarningAdminMixin), (
        "SubcategoryAdmin MORA zadržati SeoWarningAdminMixin u MRO (mixin PRVI — G-2/AC1)."
    )


# AC-1 (G-1)
def test_ac1_category_search_fields_uses_name_sr():
    model_admin = _category_admin()
    assert tuple(model_admin.search_fields) == ("name_sr",), (
        "CategoryAdmin.search_fields MORA biti ('name_sr',) — realna DB kolona, NE virtuelni "
        f"`name` (baca FieldError na changelist search — G-1); dobio {model_admin.search_fields!r}."
    )


# AC-1 (G-1)
def test_ac1_subcategory_search_fields_uses_name_sr():
    model_admin = _subcategory_admin()
    assert tuple(model_admin.search_fields) == ("name_sr",), (
        "SubcategoryAdmin.search_fields MORA biti ('name_sr',) — realna DB kolona (G-1); "
        f"dobio {model_admin.search_fields!r}."
    )


# AC-1
def test_ac1_category_changelist_add_change_200_superuser(client, superuser):
    from apps.brands.tests.factories import CategoryFactory

    cat = CategoryFactory.create(name="Plugovi")
    client.force_login(superuser)
    cl = client.get(reverse("admin:brands_category_changelist"))
    assert cl.status_code == 200, f"Category changelist MORA biti 200; dobio {cl.status_code}."
    add = client.get(reverse("admin:brands_category_add"))
    assert add.status_code == 200, f"Category add-view MORA biti 200; dobio {add.status_code}."
    ch = client.get(reverse("admin:brands_category_change", args=[cat.pk]))
    assert ch.status_code == 200, f"Category change-view MORA biti 200; dobio {ch.status_code}."


# AC-1
def test_ac1_subcategory_changelist_add_change_200_superuser(client, superuser):
    from apps.brands.tests.factories import SubcategoryFactory

    sub = SubcategoryFactory.create(name="Jednobrazni")
    client.force_login(superuser)
    cl = client.get(reverse("admin:brands_subcategory_changelist"))
    assert cl.status_code == 200, f"Subcategory changelist MORA biti 200; dobio {cl.status_code}."
    add = client.get(reverse("admin:brands_subcategory_add"))
    assert add.status_code == 200, f"Subcategory add-view MORA biti 200; dobio {add.status_code}."
    ch = client.get(reverse("admin:brands_subcategory_change", args=[sub.pk]))
    assert ch.status_code == 200, f"Subcategory change-view MORA biti 200; dobio {ch.status_code}."


# AC-1 — per-locale fields render on change-view (render-smoke; type lock is the isinstance test)
def test_ac1_category_change_renders_per_locale_fields(client, superuser):
    from apps.brands.tests.factories import CategoryFactory

    cat = CategoryFactory.create(name="Đubriva")
    client.force_login(superuser)
    html = client.get(reverse("admin:brands_category_change", args=[cat.pk])).content.decode()
    for fld in ("name_sr", "name_hu", "name_en", "description_sr"):
        assert f'name="{fld}"' in html, (
            f"Category change-view MORA renderovati per-locale polje '{fld}' (render-smoke — AC1)."
        )


# AC-1 — per-locale fields render on Subcategory change-view (mirror Category render-smoke)
def test_ac1_subcategory_change_renders_per_locale_fields(client, superuser):
    from apps.brands.tests.factories import SubcategoryFactory

    sub = SubcategoryFactory.create(name="Prikljucna Mašina", slug="prikljucna-masina", parent=None)
    client.force_login(superuser)
    html = client.get(
        reverse("admin:brands_subcategory_change", args=[sub.pk])
    ).content.decode()
    for fld in ("name_sr", "name_hu", "name_en", "description_sr"):
        assert f'name="{fld}"' in html, (
            f"Subcategory change-view MORA renderovati per-locale polje '{fld}' (render-smoke — AC1)."
        )


# AC-1 (G-1) — changelist search by name_sr does NOT raise FieldError
def test_ac1_category_changelist_search_no_field_error(client, superuser):
    from apps.brands.tests.factories import CategoryFactory

    CategoryFactory.create(name="Tražna Kategorija")
    client.force_login(superuser)
    resp = client.get(reverse("admin:brands_category_changelist"), {"q": "Tražna"})
    assert resp.status_code == 200, (
        f"Category changelist search (q=) MORA biti 200 — search_fields=('name_sr',) NE sme "
        f"baciti FieldError (G-1/AC1); dobio {resp.status_code}."
    )


# AC-1 (G-9) — admin system checks clean (list_editable / list_display_links trap incl.)
def test_ac1_admin_system_checks_clean():
    from django.core.checks import run_checks

    errors = [e for e in run_checks() if e.is_serious()]
    assert errors == [], (
        f"manage.py check MORA biti čist — TranslationAdmin + SeoMetaInline + list_editable "
        f"ne smeju baciti admin.E* (naročito list_editable/list_display_links — G-9/AC1). "
        f"Greške: {errors}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC2 — depth-3 hierarchy editable + validated (model clean delegation)
# ══════════════════════════════════════════════════════════════════════════════
# AC-2 — Category → L1 → L2 → L3 via sequential admin POSTs all succeed (dependency order)
def test_ac2_depth_three_chain_via_admin_posts(client, superuser):
    from apps.brands.models import Category, Subcategory

    client.force_login(superuser)
    sub_add = reverse("admin:brands_subcategory_add")

    # Category root (ORM is fine — focus is the Subcategory chain)
    cat = Category.objects.create(name="Priključna", is_for=Category.CategoryScope.MEHANIZACIJA)

    def _post_subcat(name, slug, parent):
        data = _add_payload(
            client,
            sub_add,
            extra={
                "category": str(cat.pk),
                "parent": str(parent.pk) if parent else "",
                "name_sr": name,
                "slug": slug,
                "display_order": "0",
            },
        )
        resp = client.post(sub_add, data)
        return resp

    r1 = _post_subcat("Nivo 1", "nivo-1", None)
    assert r1.status_code == 302, f"L1 (parent=None) POST MORA uspeti 302; dobio {r1.status_code}."
    l1 = Subcategory.objects.get(category=cat, slug="nivo-1", parent=None)

    r2 = _post_subcat("Nivo 2", "nivo-2", l1)
    assert r2.status_code == 302, f"L2 (parent=L1) POST MORA uspeti 302; dobio {r2.status_code}."
    l2 = Subcategory.objects.get(category=cat, slug="nivo-2", parent=l1)

    r3 = _post_subcat("Nivo 3", "nivo-3", l2)
    assert r3.status_code == 302, f"L3 (parent=L2) POST MORA uspeti 302; dobio {r3.status_code}."
    l3 = Subcategory.objects.get(category=cat, slug="nivo-3", parent=l2)
    assert l3.get_depth() == 3, "L3 MORA biti na dubini 3 (Category → L1 → L2 → L3 — AC2)."


# AC-2 (negative) — L4 (parent chain depth 4) → graceful 200 form error, NO row, NEVER 500
def test_ac2_depth_four_rejected_graceful(client, superuser):
    from apps.brands.models import Category, Subcategory
    from apps.brands.tests.factories import SubcategoryFactory

    cat = Category.objects.create(name="Duboka", is_for=Category.CategoryScope.MEHANIZACIJA)
    l1 = SubcategoryFactory.create(category=cat, slug="d1", parent=None)
    l2 = SubcategoryFactory.create(category=cat, slug="d2", parent=l1)
    l3 = SubcategoryFactory.create(category=cat, slug="d3", parent=l2)

    before = Subcategory.objects.count()
    client.force_login(superuser)
    sub_add = reverse("admin:brands_subcategory_add")
    data = _add_payload(
        client,
        sub_add,
        extra={
            "category": str(cat.pk),
            "parent": str(l3.pk),  # would make depth-4 chain
            "name_sr": "Nivo 4",
            "slug": "d4",
            "display_order": "0",
        },
    )
    resp = client.post(sub_add, data)
    assert resp.status_code == 200, (
        f"L4 POST MORA dati graceful 200 re-render (model clean() depth poruka surfa-uje kao "
        f"non-field greška — AC2/G-5), NIKAD 400/500; dobio {resp.status_code}."
    )
    form = resp.context["adminform"].form
    msg = " ".join(str(e) for e in form.non_field_errors()) + str(form.errors)
    assert "3 nivoa dubine" in msg, (
        f"L4 greška MORA sadržati model clean() poruku '...ne sme prelaziti 3 nivoa dubine.' "
        f"(admin NE duplira proveru — propušta ValidationError); dobio {form.errors!r}."
    )
    assert Subcategory.objects.count() == before, (
        "Nijedan NOV L4 Subcategory red NE SME biti kreiran (graceful odbijanje — AC2)."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC3 — cycle-guard graceful (BOTH paths, change-form POST)
# ══════════════════════════════════════════════════════════════════════════════
# AC-3 (a) self-reference — existing B changed to parent=B → 200 form error, NEVER 500
def test_ac3_self_reference_cycle_rejected_graceful(client, superuser):
    from apps.brands.tests.factories import SubcategoryFactory

    b = SubcategoryFactory.create(name="Samoref", slug="samoref", parent=None)
    client.force_login(superuser)
    change_url = reverse("admin:brands_subcategory_change", args=[b.pk])
    data = _scrape_change_form(client.get(change_url).content.decode())
    data["parent"] = str(b.pk)  # self-reference
    resp = client.post(change_url, data)
    assert resp.status_code == 200, (
        f"Samoreferenca (parent=self) MORA dati graceful 200 re-render (model clean() cycle "
        f"poruka — AC3/G-5), NIKAD 500; dobio {resp.status_code}."
    )
    form = resp.context["adminform"].form
    msg = " ".join(str(e) for e in form.non_field_errors()) + str(form.errors)
    assert "cikličnu referencu" in msg, (
        f"Samoreferenca greška MORA sadržati '...ne sme imati cikličnu referencu.'; "
        f"dobio {form.errors!r}."
    )
    b.refresh_from_db()
    assert b.parent_id is None, "Samoreferentni parent NE SME biti perzistiran (AC3)."


# AC-3 (b) 2-node loop — A(parent=None), B(parent=A), then A→parent=B.
#
# ⚠️ TEA REVIEW (CRITICAL FIX): the original assertion ("graceful 200 form error
# '...cikličnu referencu' + parent NOT persisted") is UNSATISFIABLE through the admin
# without a MODEL change (forbidden — AC11 / 0 migracija). Ground-truth probe
# (apps/brands/models.py:365-396 `Subcategory.clean()`):
#   - The `visited_ids` loop guard only fires when the in-memory object graph is wired
#     (B.parent IS the same Python object as the A being edited). The admin reload path
#     assigns `instance.parent = <fresh B>` whose `.parent` lazily loads a FRESH A from
#     the DB with `parent_id=None` (the cycle is not yet persisted) → the walk terminates
#     at depth 3, no cycle is detected → `full_clean()` passes → the POST SAVES (302).
#   - The DIRECT self-reference case (A→parent=A) IS caught because clean() line 380 does
#     an explicit `current.pk == self.pk` pre-check that survives the DB-reload path —
#     that path is the real cycle discriminator (test above).
# So the achievable 8.5 contract for the 2-node-via-admin path is: handle it GRACEFULLY
# (never 500 — TranslationAdmin form + full_clean must not blow up). The model-clean
# 2-node-via-admin gap is a PRE-EXISTING model limitation (inherited from 2-1, like the
# OQ-5 cross-category gap / G-13 null-parent gap) → flag for a future model-validation
# story; NOT 8.5's job to fix (admin is a thin layer; SM-D4/G-5/G-7). This test locks the
# graceful-no-500 invariant; it does NOT assert persistence (would lock the bug) nor
# rejection (unsatisfiable). The self-ref test carries the real cycle-rejection lock.
def test_ac3_two_node_cycle_via_admin_graceful_no_500(client, superuser):
    from apps.brands.tests.factories import SubcategoryFactory

    cat_a = SubcategoryFactory.create(name="Cvor A", slug="cvor-a", parent=None)
    cat_b = SubcategoryFactory.create(
        category=cat_a.category, name="Cvor B", slug="cvor-b", parent=cat_a
    )
    client.force_login(superuser)
    change_url = reverse("admin:brands_subcategory_change", args=[cat_a.pk])
    data = _scrape_change_form(client.get(change_url).content.decode())
    data["parent"] = str(cat_b.pk)  # A→B→A reassignment
    resp = client.post(change_url, data)
    # Graceful: either rejected (200 re-render) or accepted (302) — NEVER a 500/400 crash.
    # The TranslationAdmin conversion must keep the model full_clean() delegation intact so
    # the form pipeline degrades gracefully on this hierarchy edit.
    assert resp.status_code in (200, 302), (
        f"Dvočvorna petlja (A→B→A) parent-reassignment MORA biti graceful (200 re-render ILI "
        f"302 save — model-clean 2-node-via-admin gap je PRE-POSTOJEĆE ograničenje, NE 8.5 "
        f"posao), NIKAD 400/500; dobio {resp.status_code}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC4 — display_order list_editable (+ G-9 list_display_links guard)
# ══════════════════════════════════════════════════════════════════════════════
# AC-4
def test_ac4_display_order_in_list_editable_both():
    cat = _category_admin()
    sub = _subcategory_admin()
    assert "display_order" in tuple(cat.list_editable), (
        "CategoryAdmin.list_editable MORA sadržati display_order (prerasporedjivanje — AC4)."
    )
    assert "display_order" in tuple(sub.list_editable), (
        "SubcategoryAdmin.list_editable MORA sadržati display_order (AC4)."
    )


# AC-4 (G-9) — name is the change-link, NOT in list_editable; is first in list_display
def test_ac4_name_is_link_not_editable_both():
    for model_admin, label in ((_category_admin(), "Category"), (_subcategory_admin(), "Subcategory")):
        ld = tuple(model_admin.list_display)
        assert ld and ld[0] == "name", (
            f"{label}Admin.list_display[0] MORA biti 'name' (klikabilan link PRE editabilnih — G-9); "
            f"dobio {ld!r}."
        )
        assert "name" not in tuple(model_admin.list_editable), (
            f"{label}Admin.list_editable NE SME sadržati 'name' (mora ostati list_display_link — "
            f"inače admin.E124/E125 — G-9)."
        )


# AC-4 — bulk changelist POST persists display_order
def test_ac4_changelist_bulk_reorder_persists(client, superuser):
    from apps.brands.tests.factories import CategoryFactory

    cat = CategoryFactory.create(name="Redosled", display_order=0)
    client.force_login(superuser)
    cl_url = reverse("admin:brands_category_changelist")
    data = _scrape_change_form(client.get(cl_url).content.decode())
    # changelist list_editable POST requires the management form + action plumbing.
    data.update(
        {
            "_save": "Save",
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "1",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "0",
            "form-0-id": str(cat.pk),
            "form-0-display_order": "7",
        }
    )
    resp = client.post(cl_url, data)
    assert resp.status_code in (200, 302), (
        f"Changelist bulk reorder POST MORA biti 200/302 (list_editable — AC4); dobio {resp.status_code}."
    )
    cat.refresh_from_db()
    assert cat.display_order == 7, (
        f"display_order MORA biti perzistiran kroz changelist bulk save (AC4); dobio {cat.display_order}."
    )


# AC-4 — Subcategory bulk changelist POST persists display_order (robust mgmt-form scrape)
def test_ac4_subcategory_changelist_bulk_reorder_persists(client, superuser):
    from apps.brands.tests.factories import SubcategoryFactory

    sub = SubcategoryFactory.create(name="Sub Redosled", slug="sub-redosled", parent=None, display_order=0)
    client.force_login(superuser)
    cl_url = reverse("admin:brands_subcategory_changelist")
    data = _changelist_reorder_payload(
        client.get(cl_url).content.decode(), row_id=sub.pk, new_order=9
    )
    resp = client.post(cl_url, data)
    assert resp.status_code in (200, 302), (
        f"Subcategory changelist bulk reorder POST MORA biti 200/302 (list_editable — AC4); "
        f"dobio {resp.status_code}."
    )
    sub.refresh_from_db()
    assert sub.display_order == 9, (
        f"Subcategory.display_order MORA biti perzistiran kroz changelist bulk save (AC4); "
        f"dobio {sub.display_order}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC5 — icon editable (plain text), AC7 — list_display / list_filter
# ══════════════════════════════════════════════════════════════════════════════
# AC-5
def test_ac5_icon_field_present_in_category_add_form(client, superuser):
    client.force_login(superuser)
    html = client.get(reverse("admin:brands_category_add")).content.decode()
    assert 'name="icon"' in html, (
        "Category add-view MORA renderovati `icon` polje (Bootstrap Icons CharField — AC5)."
    )


# AC-5
def test_ac5_icon_field_present_in_subcategory_add_form(client, superuser):
    client.force_login(superuser)
    html = client.get(reverse("admin:brands_subcategory_add")).content.decode()
    assert 'name="icon"' in html, (
        "Subcategory add-view MORA renderovati `icon` polje (Bootstrap Icons CharField — AC5)."
    )


# AC-7
def test_ac7_category_list_display_and_filter():
    model_admin = _category_admin()
    ld = tuple(model_admin.list_display)
    for col in ("name", "is_for", "display_order", "slug"):
        assert col in ld, f"CategoryAdmin.list_display MORA sadržati '{col}' (AC7); dobio {ld!r}."
    assert "is_for" in tuple(model_admin.list_filter), (
        "CategoryAdmin.list_filter MORA sadržati 'is_for' (AC7)."
    )


# AC-7
def test_ac7_subcategory_list_display_and_filter():
    model_admin = _subcategory_admin()
    ld = tuple(model_admin.list_display)
    for col in ("name", "category", "parent", "display_order", "slug"):
        assert col in ld, f"SubcategoryAdmin.list_display MORA sadržati '{col}' (AC7); dobio {ld!r}."
    assert "category" in tuple(model_admin.list_filter), (
        "SubcategoryAdmin.list_filter MORA sadržati 'category' (AC7)."
    )


# AC-7 (G-10) — list_select_related avoids N+1 on Subcategory FK columns
def test_ac7_subcategory_list_select_related():
    model_admin = _subcategory_admin()
    lsr = tuple(getattr(model_admin, "list_select_related", ()) or ())
    assert "category" in lsr and "parent" in lsr, (
        f"SubcategoryAdmin.list_select_related MORA biti ('category','parent') — N+1 guard za FK "
        f"kolone u list_display (G-10/AC7); dobio {lsr!r}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC8 — slug auto-gen + per-scope uniqueness + name_sr/is_for required
# ══════════════════════════════════════════════════════════════════════════════
# AC-8 (positive) — Category with only name_sr (+ slug) saves; slug auto-gen path exercised
def test_ac8_category_add_with_name_sr_saves(client, superuser):
    from apps.brands.models import Category

    client.force_login(superuser)
    add_url = reverse("admin:brands_category_add")
    data = _add_payload(
        client,
        add_url,
        extra={
            "name_sr": "Nova Kategorija",
            "slug": "nova-kategorija",  # prepopulated_fields JS-equiv (no-JS scraper)
            "is_for": Category.CategoryScope.MEHANIZACIJA,
            "display_order": "0",
        },
    )
    resp = client.post(add_url, data)
    assert resp.status_code == 302, (
        f"Validan Category (name_sr + slug + is_for) MORA sačuvati i 302 redirect (AC8); "
        f"dobio {resp.status_code}."
    )
    assert Category.objects.filter(name_sr="Nova Kategorija").exists(), (
        "Validan Category sa name_sr MORA biti kreiran (AC8)."
    )


# AC-8 (negative) — empty name_sr → graceful 200 form error, NO row, NEVER 500 (G-11)
def test_ac8_category_empty_name_sr_graceful(client, superuser):
    from apps.brands.models import Category

    before = Category.objects.count()
    client.force_login(superuser)
    add_url = reverse("admin:brands_category_add")
    data = _add_payload(
        client,
        add_url,
        extra={"name_sr": "", "is_for": Category.CategoryScope.MEHANIZACIJA},
    )
    resp = client.post(add_url, data)
    assert resp.status_code == 200, (
        f"Prazan name_sr MORA dati graceful 200 form-error (model name blank=False; NIKAD 400/500 "
        f"iz full_clean escape — AC8/G-11); dobio {resp.status_code}."
    )
    form = resp.context["adminform"].form
    assert "name_sr" in form.errors, (
        f"Prazan name_sr MORA dati field grešku na `name_sr`; dobio {form.errors!r}."
    )
    assert Category.objects.count() == before, "Nijedan nov Category pri praznom name_sr (AC8)."


# AC-8 (negative) — empty is_for → graceful 200 form error (required, no default — SM-D7)
def test_ac8_category_empty_is_for_graceful(client, superuser):
    from apps.brands.models import Category

    before = Category.objects.count()
    client.force_login(superuser)
    add_url = reverse("admin:brands_category_add")
    data = _add_payload(
        client,
        add_url,
        extra={"name_sr": "Bez Tipa", "slug": "bez-tipa", "is_for": ""},
    )
    resp = client.post(add_url, data)
    assert resp.status_code == 200, (
        f"Prazan is_for MORA dati graceful 200 form-error (blank=False bez default → OBAVEZAN — "
        f"SM-D7/AC8); dobio {resp.status_code}."
    )
    form = resp.context["adminform"].form
    assert "is_for" in form.errors, (
        f"Prazan is_for MORA dati field grešku na `is_for`; dobio {form.errors!r}."
    )
    assert Category.objects.count() == before, "Nijedan nov Category pri praznom is_for (SM-D7/AC8)."


# AC-8 (G-6) — duplicate slug under SAME (category, NON-NULL parent) → graceful 200, no 2nd row
def test_ac8_duplicate_slug_same_scope_nonnull_parent_rejected(client, superuser):
    from apps.brands.models import Subcategory
    from apps.brands.tests.factories import CategoryFactory, SubcategoryFactory

    cat = CategoryFactory.create(name="Skop")
    root = SubcategoryFactory.create(category=cat, slug="root", parent=None)
    # first child under (cat, root) with explicit slug
    SubcategoryFactory.create(category=cat, parent=root, slug="dupli", name="Prvi")

    before = Subcategory.objects.filter(category=cat, parent=root, slug="dupli").count()
    client.force_login(superuser)
    sub_add = reverse("admin:brands_subcategory_add")
    data = _add_payload(
        client,
        sub_add,
        extra={
            "category": str(cat.pk),
            "parent": str(root.pk),
            "name_sr": "Drugi",
            "slug": "dupli",  # SAME explicit slug under SAME (category, parent) — no-JS (G-11)
            "display_order": "0",
        },
    )
    resp = client.post(sub_add, data)
    assert resp.status_code == 200, (
        f"Dupli slug pod ISTIM (category, non-null parent) MORA dati graceful 200 form-error "
        f"(UniqueConstraint — G-6/AC8), NIKAD 500; dobio {resp.status_code}."
    )
    assert (
        Subcategory.objects.filter(category=cat, parent=root, slug="dupli").count() == before
    ), "Drugi Subcategory sa duplim slug-om u istom scope-u NE SME biti kreiran (G-6/AC8)."


# AC-8 (G-6) — same slug under DIFFERENT (category, parent) is allowed
def test_ac8_same_slug_different_scope_allowed():
    from apps.brands.models import Subcategory
    from apps.brands.tests.factories import CategoryFactory, SubcategoryFactory

    cat = CategoryFactory.create(name="Razni Skopovi")
    p1 = SubcategoryFactory.create(category=cat, slug="p1", parent=None)
    p2 = SubcategoryFactory.create(category=cat, slug="p2", parent=None)
    # same explicit slug but DIFFERENT parent → both valid (UniqueConstraint is per-scope)
    SubcategoryFactory.create(category=cat, parent=p1, slug="deljen", name="A")
    SubcategoryFactory.create(category=cat, parent=p2, slug="deljen", name="B")
    assert Subcategory.objects.filter(slug="deljen").count() == 2, (
        "Isti slug pod RAZLIČITIM (category, parent) MORA biti dozvoljen (slug NIJE globally "
        "unique — G-6/AC8)."
    )


# AC-8 (G-13) — KNOWN/ACCEPTED v1 GAP behavioral lock.
#
# ⚠️ This test deliberately LOCKS a pre-existing, accepted v1 limitation (G-13), it is NOT
# a bug to fix in 8.5. `Subcategory` has `UniqueConstraint(category, parent, slug)`. On
# PostgreSQL, NULL is DISTINCT (default SQL semantics, no `nulls_distinct=False`), so two
# L1 ROOT Subcategories (parent=None) under the SAME Category with the SAME explicit slug do
# NOT violate the constraint → BOTH rows persist. The matching NON-NULL-parent case IS caught
# (see test_ac8_duplicate_slug_same_scope_nonnull_parent_rejected). Fixing this requires a
# model/migration change (partial constraint for `parent IS NULL`, or `nulls_distinct=False`
# on PG≥15) → out of 8.5's 0-migration scope (AC11); flagged as a future model-validation
# story (sibling of OQ-5 cross-category + the 2-node-cycle-via-admin gaps). This test exists
# so a future constraint hardening can't silently change this behavior unnoticed.
def test_ac8_null_parent_duplicate_slug_accepted_known_gap_g13():
    from apps.brands.models import Subcategory
    from apps.brands.tests.factories import CategoryFactory, SubcategoryFactory

    cat = CategoryFactory.create(name="Null Parent Skop")
    # Two L1 ROOT (parent=None) under SAME category, SAME explicit slug + SAME name_sr.
    SubcategoryFactory.create(category=cat, parent=None, slug="koren", name="Koren")
    SubcategoryFactory.create(category=cat, parent=None, slug="koren", name="Koren")
    assert Subcategory.objects.filter(category=cat, parent=None, slug="koren").count() == 2, (
        "OBA L1 root Subcategory-ja sa istim slug-om pod parent=None MORAJU perzistirati — "
        "PostgreSQL NULL-DISTINCT pa UniqueConstraint(category,parent,slug) NE hvata duplikat "
        "(G-13 PRIHVAĆEN v1 JAZ — NIJE bug u 8.5; ovaj test ZAKLJUČAVA poznato ponašanje da "
        "buduća constraint-popravka ne promeni tiho rezultat)."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC6 — cascade-delete + PROTECT-graceful (render-smoke; Django gives it free)
# ══════════════════════════════════════════════════════════════════════════════
# AC-6 — deleting a Category cascades to its Subcategories (confirm POST removes both)
def test_ac6_category_delete_cascades_subcategories(client, superuser):
    from apps.brands.models import Category, Subcategory
    from apps.brands.tests.factories import CategoryFactory, SubcategoryFactory

    cat = CategoryFactory.create(name="Brisiva")
    SubcategoryFactory.create(category=cat, slug="dete-1", parent=None)
    SubcategoryFactory.create(category=cat, slug="dete-2", parent=None)
    cat_pk = cat.pk
    client.force_login(superuser)
    del_url = reverse("admin:brands_category_delete", args=[cat.pk])
    confirm = client.get(del_url)
    assert confirm.status_code == 200, (
        f"Category delete-confirmation strana MORA biti 200 (cascade lista — AC6); "
        f"dobio {confirm.status_code}."
    )
    resp = client.post(del_url, {"post": "yes"})
    assert resp.status_code == 302, f"Potvrda brisanja MORA biti 302; dobio {resp.status_code}."
    assert not Category.objects.filter(pk=cat_pk).exists(), "Category MORA biti obrisan (AC6)."
    assert not Subcategory.objects.filter(category_id=cat_pk).exists(), (
        "Vezane Subcategory-je MORAJU biti CASCADE-obrisane (AC6)."
    )


# AC-6 — deleting a parent Subcategory CASCADE-deletes its child Subcategories
def test_ac6_subcategory_parent_delete_cascades_children(client, superuser):
    from apps.brands.models import Subcategory
    from apps.brands.tests.factories import CategoryFactory, SubcategoryFactory

    # Dependency order: Category → L1 (parent) → L2 (child of L1). Subcategory.parent=CASCADE.
    cat = CategoryFactory.create(name="Kaskada Sub")
    l1 = SubcategoryFactory.create(category=cat, slug="roditelj", parent=None)
    l2 = SubcategoryFactory.create(category=cat, slug="dete", parent=l1)
    l1_pk, l2_pk = l1.pk, l2.pk

    client.force_login(superuser)
    del_url = reverse("admin:brands_subcategory_delete", args=[l1.pk])
    confirm = client.get(del_url)
    assert confirm.status_code == 200, (
        f"Subcategory parent delete-confirmation strana MORA biti 200 (cascade lista dece — AC6); "
        f"dobio {confirm.status_code}."
    )
    resp = client.post(del_url, {"post": "yes"})
    assert resp.status_code == 302, f"Potvrda brisanja MORA biti 302; dobio {resp.status_code}."
    assert not Subcategory.objects.filter(pk=l1_pk).exists(), (
        "Parent Subcategory MORA biti obrisan (AC6)."
    )
    assert not Subcategory.objects.filter(pk=l2_pk).exists(), (
        "Child Subcategory MORA biti CASCADE-obrisan kad se obriše parent (Subcategory.parent="
        "CASCADE — AC6)."
    )


# AC-6 — deleting a Subcategory with a PROTECTed Product → 200 protected page, blocked, no loss
def test_ac6_subcategory_with_product_protected_delete(client, superuser):
    from apps.brands.models import Subcategory
    from apps.brands.tests.factories import SubcategoryFactory
    from apps.products.models import Product
    from apps.products.tests.factories import ProductFactory

    target = SubcategoryFactory.create(name="Zauzeta", slug="zauzeta", parent=None)
    # PROTECT only triggers when subcategory is EXPLICITLY set (nullable → None = false-green)
    product = ProductFactory.create(subcategory=target)
    client.force_login(superuser)
    del_url = reverse("admin:brands_subcategory_delete", args=[target.pk])
    confirm = client.get(del_url)
    assert confirm.status_code == 200, (
        f"Subcategory-sa-Product delete strana MORA biti 200 'protected' (NE 500 — G-4/AC6); "
        f"dobio {confirm.status_code}."
    )
    # attempt the actual delete → still blocked, nothing lost
    client.post(del_url, {"post": "yes"})
    assert Subcategory.objects.filter(pk=target.pk).exists(), (
        "PROTECTed Subcategory NE SME biti obrisan dok ima vezan Product (G-4/AC6)."
    )
    assert Product.objects.filter(pk=product.pk).exists(), (
        "Vezani Product NE SME biti izgubljen (PROTECT — G-4/AC6)."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC9 — view_on_site=False on BOTH (NoReverseMatch guard)
# ══════════════════════════════════════════════════════════════════════════════
# AC-9
def test_ac9_category_view_on_site_false():
    assert _category_admin().view_on_site is False, (
        "CategoryAdmin.view_on_site MORA biti False — Category.get_absolute_url reverse-uje "
        "neregistrovan brands:category_traktori/mehanizacija → NoReverseMatch zaštita (G-3/AC9)."
    )


# AC-9
def test_ac9_subcategory_view_on_site_false():
    assert _subcategory_admin().view_on_site is False, (
        "SubcategoryAdmin.view_on_site MORA biti False — Subcategory.get_absolute_url reverse-uje "
        "brands:subcategory_listing_l{depth} (registrovan samo za jednu granu) → NoReverseMatch "
        "zaštita (G-3/AC9)."
    )


# AC-9 — change-views render 200 (no NoReverseMatch on the View-on-site affordance)
def test_ac9_change_views_no_noreversematch(client, superuser):
    from apps.brands.tests.factories import CategoryFactory, SubcategoryFactory

    cat = CategoryFactory.create(name="VoS Kat")
    sub = SubcategoryFactory.create(name="VoS Sub", slug="vos-sub", parent=None)
    client.force_login(superuser)
    c = client.get(reverse("admin:brands_category_change", args=[cat.pk]))
    assert c.status_code == 200, (
        f"Category change-view MORA biti 200 (NE pada na View-on-site NoReverseMatch — AC9); "
        f"dobio {c.status_code}."
    )
    s = client.get(reverse("admin:brands_subcategory_change", args=[sub.pk]))
    assert s.status_code == 200, (
        f"Subcategory change-view MORA biti 200 (NE pada na View-on-site NoReverseMatch — AC9); "
        f"dobio {s.status_code}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC6/AC8 regression — SeoMetaInline still present on BOTH (MAY PASS today — 6.1 has it)
# ══════════════════════════════════════════════════════════════════════════════
# AC-11 (regression-lock — MAY PASS today)
def test_seometa_inline_still_on_both_admins():
    from apps.seo.admin import SeoMetaInline

    for model_admin, label in ((_category_admin(), "Category"), (_subcategory_admin(), "Subcategory")):
        inlines = list(model_admin.inlines)
        assert any(ic is SeoMetaInline or issubclass(ic, SeoMetaInline) for ic in inlines), (
            f"SeoMetaInline MORA OSTATI na {label}Admin posle konverzije (6.1 regression — "
            f"G-8/AC11)."
        )


# ══════════════════════════════════════════════════════════════════════════════
# AC10 — RBAC: anon redirect, Editor + superuser CRUD
# ══════════════════════════════════════════════════════════════════════════════
# AC-10 (negative) — anonymous → 302 to admin login (reverse-based matcher)
def test_ac10_anonymous_redirected_to_login(client):
    for view in ("admin:brands_category_changelist", "admin:brands_subcategory_changelist"):
        resp = client.get(reverse(view))
        assert resp.status_code == 302, (
            f"Anoniman na {view} MORA biti 302 (admin login redirect — AC10); dobio {resp.status_code}."
        )
        assert reverse("admin:login") in resp["Location"], (
            f"302 MORA voditi na admin:login (NE hardkodovan put — bare /admin-coric/ iz 8.1); "
            f"Location={resp['Location']!r}."
        )


# AC-10 — Editor changelist/add 200 for both models
def test_ac10_editor_changelist_and_add_200_both(client, editor):
    client.force_login(editor)
    for model in ("category", "subcategory"):
        cl = client.get(reverse(f"admin:brands_{model}_changelist"))
        assert cl.status_code == 200, (
            f"Editor {model} changelist MORA biti 200 (8.2 grant netaknut — AC10/SM-D8); "
            f"dobio {cl.status_code}."
        )
        add = client.get(reverse(f"admin:brands_{model}_add"))
        assert add.status_code == 200, (
            f"Editor {model} add-view MORA biti 200 (forma renderuje bez admin.E* — AC10); "
            f"dobio {add.status_code}."
        )


# AC-10 — Editor can POST-save a valid Category
def test_ac10_editor_can_add_category(client, editor):
    from apps.brands.models import Category

    client.force_login(editor)
    add_url = reverse("admin:brands_category_add")
    data = _add_payload(
        client,
        add_url,
        extra={
            "name_sr": "Editorova Kategorija",
            "slug": "editorova-kategorija",
            "is_for": Category.CategoryScope.MEHANIZACIJA,
            "display_order": "0",
        },
    )
    resp = client.post(add_url, data, follow=True)
    assert resp.status_code == 200, f"Editor Category add POST MORA biti 200; dobio {resp.status_code}."
    assert Category.objects.filter(name_sr="Editorova Kategorija").exists(), (
        "Editor MORA moći da sačuva validnu Category kroz admin (AC10)."
    )


# AC-10 — Editor can POST-save a valid root Subcategory
def test_ac10_editor_can_add_subcategory(client, editor):
    from apps.brands.models import Subcategory
    from apps.brands.tests.factories import CategoryFactory

    cat = CategoryFactory.create(name="Za Editor Sub")
    client.force_login(editor)
    add_url = reverse("admin:brands_subcategory_add")
    data = _add_payload(
        client,
        add_url,
        extra={
            "category": str(cat.pk),
            "parent": "",
            "name_sr": "Editorova Potkategorija",
            "slug": "editorova-potkat",
            "display_order": "0",
        },
    )
    resp = client.post(add_url, data, follow=True)
    assert resp.status_code == 200, f"Editor Subcategory add POST MORA biti 200; dobio {resp.status_code}."
    assert Subcategory.objects.filter(name_sr="Editorova Potkategorija").exists(), (
        "Editor MORA moći da sačuva validnu Subcategory kroz admin (AC10)."
    )


# ══════════════════════════════════════════════════════════════════════════════
# AC11 — no pending migration for brands (admin-only change)
# ══════════════════════════════════════════════════════════════════════════════
# AC-11 (regression-lock — MAY PASS today: 8.5 must NOT introduce schema changes)
def test_ac11_no_pending_migration_for_brands():
    from django.apps import apps as django_apps
    from django.db.migrations.autodetector import MigrationAutodetector
    from django.db.migrations.loader import MigrationLoader
    from django.db.migrations.state import ProjectState

    loader = MigrationLoader(None, ignore_no_migrations=True)
    autodetector = MigrationAutodetector(
        loader.project_state(),
        ProjectState.from_apps(django_apps),
    )
    changes = autodetector.changes(graph=loader.graph)
    assert "brands" not in changes, (
        f"apps.brands NE SME imati pending schema migraciju (8.5 je admin-only — AC11); "
        f"autodetector predlaže: {changes.get('brands')}."
    )


# AC-11 — BrandAdmin/SeriesAdmin untouched (8.4 scope, SM-D1)
def test_ac11_brand_series_admin_untouched():
    from modeltranslation.admin import TranslationAdmin

    from apps.brands.models import Brand, Series

    assert isinstance(admin.site._registry[Brand], TranslationAdmin), (
        "BrandAdmin MORA ostati TranslationAdmin netaknut (8.4 scope — SM-D1/AC11)."
    )
    # SeriesAdmin stays as 8.4 left it (view_on_site guard); just assert it is still registered.
    assert Series in admin.site._registry, "SeriesAdmin MORA ostati registrovan (SM-D1/AC11)."
