"""AppConfig za apps.accounts — admin auth hardening layer (Story 8.1).

PRVA story Epic 8 (Admin Dashboard & Content Management). Samostalan app za
admin customization (arch:730): forms.py:AdminLoginForm (email-as-username).
NEMA models u v1 (SM-D3 — default auth.User ostaje). `ready()` STVARNO ožičava
AdminLoginForm u admin login flow (SM-D13 / CRITICAL-5).
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"  # KRITIČNO — sa apps. prefiksom
    verbose_name = _("Nalozi i pristup")

    def ready(self):
        # CRITICAL-5 / SM-D13: STVARNO ožičenje forme u admin login flow.
        # Import UNUTAR ready() — circular-import safe (admin/app registry).
        from django.contrib import admin

        from apps.accounts.forms import AdminLoginForm

        admin.site.login_form = AdminLoginForm
