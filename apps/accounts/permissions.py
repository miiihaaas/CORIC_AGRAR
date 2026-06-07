"""apps.accounts.permissions — RBAC core (Story 8.2).

Sav RBAC u jednom modulu (SM-D14 — YAGNI zaseban signals.py):
- GROUP_SUPERADMIN / GROUP_EDITOR konstante (single-source naziva — SM-D5).
- EDITOR_CONTENT_MODELS — eksplicitan default-deny allowlist od 15 content modela
  (4 brands + 7 products + 3 blog + 1 pages; SM-D3 / G-13).
- IsSuperadminMixin / IsEditorMixin — LoginRequiredMixin + UserPassesTestMixin,
  raise_exception=True (anon → 302 login; autentifikovan-neovlašćen → 403; SM-D8).
- sync_rbac_groups(sender, **kwargs) — post_migrate handler koji kreira obe grupe
  (get_or_create) i dodeljuje Editor-u CRUD permisije TAČNO za 15 modela
  (permissions.set — idempotentno; G-2). Superadmin grupa ostaje prazna jer
  is_superuser implicitno pokriva sve (SM-D6). NIKAD auth/admin/infra perms (G-3).

Mixini su KREIRANI ovde ali PRIMENJENI na CRUD view-ove tek u 8.3..8.9 (forward-dep).

Collection-safe top-level import: Group/Permission (RBAC modeli, NE swappable User)
su OK na module-level; SAMO `from django.contrib.auth.models import User` je
ZABRANJEN (project-context:112 / G-12).
"""

from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import redirect_to_login

# ─────────────────────────────────────────────────────────────────────────────
# Group-name konstante (single-source-of-truth — SM-D5)
# ─────────────────────────────────────────────────────────────────────────────
GROUP_SUPERADMIN: str = "Superadmin"
GROUP_EDITOR: str = "Editor"


# ─────────────────────────────────────────────────────────────────────────────
# EDITOR_CONTENT_MODELS — eksplicitan default-deny allowlist (SM-D3 / G-13)
#
# DRIFT INVARIJANTA (G-13): SVAKI BUDUĆI content model MORA biti EKSPLICITNO dodat
# ovde ili Editor nečujno NEMA pristup. Ne oslanjaj se na auto-discovery.
# IZOSTAVLJENO (Superadmin-only): pages.sitesettings (SM-D15), gdpr.cookiepolicy
# (SM-D16); sve auth/admin/contenttypes/sessions/axes/search (infra/auth — G-3).
# ─────────────────────────────────────────────────────────────────────────────
EDITOR_CONTENT_MODELS: list[tuple[str, str]] = [
    # brands (4)
    ("brands", "brand"),
    ("brands", "series"),
    ("brands", "category"),
    ("brands", "subcategory"),
    # products (7 — _ProductIndex je models.Index, NIJE Model → izostavljen)
    ("products", "product"),
    ("products", "productimage"),
    ("products", "productvariant"),
    ("products", "productspecification"),
    ("products", "productbrochure"),
    ("products", "producttestimonial"),
    ("products", "productsimilar"),
    # blog (3)
    ("blog", "post"),
    ("blog", "category"),
    ("blog", "tag"),
    # pages (1 — SAMO Page; SiteSettings IZOSTAVLJEN, SM-D15)
    ("pages", "page"),
]


# ─────────────────────────────────────────────────────────────────────────────
# Permission mixini (AC2 / AC3 — fail-closed, raise_exception=True / SM-D8)
# ─────────────────────────────────────────────────────────────────────────────
class _RbacGateMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Zajednička baza: raise_exception=True ALI anon → 302 login (G-9 / SM-D8).

    Django-ov AccessMixin.handle_no_permission sa raise_exception=True baca 403
    BEZUSLOVNO (i za anonimne). Story zahteva: anoniman → 302 login redirect,
    autentifikovan-ali-neovlašćen → 403 (G-9). Override handle_no_permission:
    anoniman → redirect_to_login (302) direktno, autentifikovan-neovlašćen →
    super() (403 via raise_exception=True). BEZ mutacije instance state-a
    (čist idiom — kopira se na 8.3..8.9).
    """

    raise_exception = True

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            # anoniman → standardni login redirect (302), NE 403
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )
        # autentifikovan-ali-neovlašćen → 403 (raise_exception=True)
        return super().handle_no_permission()


class IsSuperadminMixin(_RbacGateMixin):
    """Gate: SAMO superadmin (is_superuser ILI član Superadmin grupe — SM-D6).

    Anon → 302 login (G-9); autentifikovan-neovlašćen → 403 (SM-D8).
    PRIMENJUJE se na view-ove tek u 8.3..8.9 (forward-dep).

    SM-D6 NAPOMENA (Security): članstvo u "Superadmin" grupi SAMO (bez
    is_superuser) prolazi OVAJ custom-view gate, ALI NE daje Django-admin
    superuser moći — grupa je PRAZNA (nema perms; vidi sync_rbac_groups). Da
    bi se neko dodao u Superadmin grupu, već mora biti superuser (admin User
    change traži is_superuser). Sprečava buduću zabunu u 8.3..8.9.
    """

    def test_func(self) -> bool:
        u = self.request.user
        return u.is_superuser or u.groups.filter(name=GROUP_SUPERADMIN).exists()


class IsEditorMixin(_RbacGateMixin):
    """Gate: Editor ILI superadmin (superset — superuser prolazi Editor gate; SM-D7).

    Anon → 302 login (G-9); autentifikovan-neovlašćen → 403 (SM-D8).
    PRIMENJUJE se tek u 8.3..8.9 (forward-dep).
    """

    def test_func(self) -> bool:
        u = self.request.user
        return u.is_superuser or u.groups.filter(name=GROUP_EDITOR).exists()


# ─────────────────────────────────────────────────────────────────────────────
# Opcioni helper-i (membership provera bez mixina)
# ─────────────────────────────────────────────────────────────────────────────
def is_superadmin(user) -> bool:
    """True za superuser ILI člana Superadmin grupe (SM-D6)."""
    return bool(user.is_superuser or user.groups.filter(name=GROUP_SUPERADMIN).exists())


def is_editor(user) -> bool:
    """True za superuser (superset — SM-D7) ILI člana Editor grupe."""
    return bool(user.is_superuser or user.groups.filter(name=GROUP_EDITOR).exists())


# ─────────────────────────────────────────────────────────────────────────────
# post_migrate RBAC sync handler (AC4/5/6/7 — SM-D2 / G-1/G-2)
# ─────────────────────────────────────────────────────────────────────────────
def sync_rbac_groups(sender, **kwargs) -> None:
    """Kreiraj Superadmin+Editor grupe i dodeli Editor CRUD perms za 15 modela.

    Idempotentan (G-2): get_or_create + permissions.set(). Re-run NE duplira
    grupe ni permisije. Superadmin grupa ostaje prazna (is_superuser pokriva —
    SM-D6). Editor NIKAD ne dobija auth/admin/infra perms (G-3).

    Import Group/Permission UNUTAR funkcije — post_migrate se emituje tek kad je
    app registry potpuno učitan (izbegava AppRegistryNotReady).
    """
    from django.contrib.auth.models import Group, Permission

    Group.objects.get_or_create(name=GROUP_SUPERADMIN)  # prazna — is_superuser pokriva
    editor, _ = Group.objects.get_or_create(name=GROUP_EDITOR)

    perms: list = []
    for app_label, model in EDITOR_CONTENT_MODELS:
        # filter() je robusno: ne-postojeći model → prazan QS, ne crash (G-5)
        perms.extend(
            Permission.objects.filter(
                content_type__app_label=app_label,
                content_type__model=model,
            )
        )

    editor.permissions.set(perms)  # set (NE add) → deterministički krajnji skup (G-2)
