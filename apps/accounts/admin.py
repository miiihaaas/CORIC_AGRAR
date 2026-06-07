"""apps.accounts.admin — CustomUserAdmin (Story 8.2).

Unregister default auth UserAdmin → re-register CustomUserAdmin (subclass) sa:
- zadržanim default fieldsets / add_form / UserChangeForm (password change link;
  SM-D10/D12).
- SELF-ESCALATION HARDENING (AC13 / SM-D17 / G-14 — HIGH security, defense-in-depth):
  za ne-superusera (request.user.is_superuser=False) polja is_superuser/is_staff/
  groups/user_permissions NISU editabilna (uklonjena iz fieldsets). Superuser
  zadržava pun pristup. Editor ionako nema auth.change_user (AC6 — primarna
  granica), ali ovo štiti od buduće misconfig-a.

NIKAD direktan auth User import — get_user_model() (G-12 / project-context:112).
INSTALLED_APPS redosled (django.contrib.admin pre apps.accounts) garantuje da
naš admin ide POSLE → unregister radi (G-7).
"""

from __future__ import annotations

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

User = get_user_model()

# default auth UserAdmin je registrovan ranije (admin app pre accounts) → unregister.
# try/except: u izolovanim/test scenarijima gde User još NIJE registrovan, import
# modula ne sme da padne (NotRegistered). Standardni flow nepromenjen.
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """UserAdmin ekstenzija sa self-escalation hardening-om (AC13)."""

    # osetljiva polja koja ne-superuser NE sme da menja (SM-D17 / G-14)
    _SENSITIVE_FIELDS = ("is_superuser", "is_staff", "groups", "user_permissions")

    def get_fieldsets(self, request, obj=None):
        """Za ne-superusera ukloni osetljiva polja iz fieldsets (AC13).

        Add-form (obj is None) koristi default add_fieldsets (UserAdmin) — bez
        osetljivih polja po default-u, pa ostaje netaknuta. Superuser → pun
        default fieldsets (osetljiva polja editabilna).
        """
        fieldsets = super().get_fieldsets(request, obj)
        if request.user.is_superuser:
            return fieldsets

        sensitive = set(self._SENSITIVE_FIELDS)
        sanitized = []
        for name, opts in fieldsets:
            opts = dict(opts)
            opts["fields"] = self._strip_fields(opts.get("fields", ()), sensitive)
            # Sekcija koja je sadržala SAMO osetljiva polja postaje prazna (npr.
            # "Permissions") — izostavi je da se ne renderuje prazna titlovana
            # sekcija (BUG, kozmetika). Polja su i dalje uklonjena (security isti).
            if opts["fields"]:
                sanitized.append((name, opts))
        return sanitized

    def get_readonly_fields(self, request, obj=None):
        """Defense-in-depth: za ne-superusera osetljiva polja su i readonly (AC13).

        get_fieldsets ih već sklanja, ali readonly garantuje da ni eksplicitan
        POST/override ne može da ih menja.
        """
        readonly = tuple(super().get_readonly_fields(request, obj))
        if request.user.is_superuser:
            return readonly
        return tuple(set(readonly) | set(self._SENSITIVE_FIELDS))

    @staticmethod
    def _strip_fields(fields, sensitive):
        """Ukloni osetljiva imena iz (ravni ili ugnježdeni) fields tuple-a."""
        out = []
        for f in fields:
            if isinstance(f, (tuple, list)):
                kept = tuple(x for x in f if x not in sensitive)
                if kept:
                    out.append(kept)
            elif f not in sensitive:
                out.append(f)
        return tuple(out)
