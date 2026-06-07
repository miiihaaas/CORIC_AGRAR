"""Story 8.3 — TEA RED phase conftest za apps/admin_ext/ test suite.

TREĆA Epic 8 story (Admin Dashboard). NOVI app apps/admin_ext/ koji PINOVANO
override-uje admin index (admin.site.index wrapper + index_template) i isporučuje
read-only agregacionu statistiku (segmentovan lead count + content count + GA stub).

RED phase: apps.admin_ext NE postoji (NIJE u INSTALLED_APPS, nema stats.py/analytics.py,
admin index NIJE override-ovan). Svaki test koji importuje `apps.admin_ext.*` MORA pasti
čisto (ModuleNotFoundError), a render/override testovi padaju jer default admin index
NEMA stats markup.

⚠️ COLLECTION-SAFETY: NIJEDAN test modul NE importuje apps.admin_ext na module-top-level
— importi su UNUTAR test funkcija (lazy). Tako missing apps.admin_ext daje per-test FAIL
(RED), NE collection abort koji bi oborio CELU suite (ostali app-ovi ostaju zeleni).

Test data inline kroz factory helpers (mirror 4-1/5-1 stil — factory_boy NIJE dep).
Pune srpske dijakritike (č/ć/ž/š/đ) u test podacima (project-context anti-šišana-latinica).

Refs:
- 8-3-admin-dashboard-sa-segmentovanim-lead-count-om.md AC1-AC9 + ## Testing
- 8-3-interface-contract.md
- apps/blog/tests/conftest.py + apps/accounts/permissions.py (8.2 RBAC grupe)
"""

from __future__ import annotations

import pytest


# ── Media izolacija (Product.main_image / Post.main_image ImageField stub uploads) ──


@pytest.fixture(autouse=True)
def _isolate_media_root(settings, tmp_path):
    """Per-test MEDIA_ROOT izolacija (established project pattern)."""
    settings.MEDIA_ROOT = str(tmp_path)


# ── Korisnici (admin gate AC7) ────────────────────────────────────────────────


@pytest.fixture
def superuser(django_user_model):
    """Superadmin (is_superuser + is_staff) — AC7 SIMETRIJA gornja granica.

    `django_user_model` = settings.AUTH_USER_MODEL kroz get_user_model() —
    NIKAD direktan `from django.contrib.auth.models import User`.
    """
    return django_user_model.objects.create_superuser(
        username="dash_superadmin_tea",
        email="superadmin-dash@example.com",
        password="tea-pass-12345",
    )


@pytest.fixture
def editor_user(django_user_model):
    """Editor (is_staff=True, član Editor grupe 8.2, NE is_superuser) — AC7 SIMETRIJA.

    Editor prolazi kroz admin `is_staff` gate i VIDI dashboard (agregati, ne PII; SM-D5).
    Grupa „Editor" se kreira ovde (post_migrate sync je možda već kreirao — get_or_create).
    """
    from django.contrib.auth.models import Group

    from apps.accounts.permissions import GROUP_EDITOR

    user = django_user_model.objects.create_user(
        username="dash_editor_tea",
        email="editor-dash@example.com",
        password="tea-pass-12345",
        is_staff=True,  # admin gate (8.2 Editor je staff)
    )
    group, _ = Group.objects.get_or_create(name=GROUP_EDITOR)
    user.groups.add(group)
    return user


# ── Lead factory (segmentovan count AC2/AC3) ──────────────────────────────────


@pytest.fixture
def make_lead():
    """Helper: kreira Lead datog form_type-a sa eksplicitnim created_at.

    `created_at` je auto_now_add (TimestampedModel) → posle create() prepiše se preko
    QuerySet.update() (zaobilazi auto_now_add da test može simulirati prošli mesec).
    PII polja (name/email/phone/message) imaju PREPOZNATLJIVE sentinel vrednosti da
    PII-guard test može da ih traži u dashboard HTML-u (AC9).
    """

    def _make(form_type, *, created_at=None, **overrides):
        from apps.forms.models import Lead

        defaults = {
            "form_type": form_type,
            "name": "Đorđe PII-Sentinel Petrović",
            "email": "pii-sentinel-lead@example.com",
            "phone": "+381641234567",
            "message": "Tajna PII poruka koja NE sme na dashboard.",
        }
        defaults.update(overrides)
        lead = Lead.objects.create(**defaults)
        if created_at is not None:
            # zaobiđi auto_now_add — set created_at na željenu (TZ-aware) vrednost
            Lead.objects.filter(pk=lead.pk).update(created_at=created_at)
            lead.refresh_from_db()
        return lead

    return _make
