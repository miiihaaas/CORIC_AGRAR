"""AppConfig za apps.admin_ext — admin dashboard override sloj (Story 8.3).

TREĆA Epic 8 story. NOVI top-level admin-customization app koji PINOVANO override-uje
admin index (`admin.site.index` wrapper + `index_template`) da prikaže segmentovan
lead count + content count + GA placeholder + brze akcije. Nema modela (SM-D3 → 0
migracija). `ready()` ožičava override (mirror accounts/apps.py 8.1/8.2 pattern).
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AdminExtConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.admin_ext"  # KRITIČNO — sa apps. prefiksom
    verbose_name = _("Admin proširenja")

    def ready(self):
        # Import UNUTAR ready() — circular-safe (mirror accounts/apps.py 8.1/8.2).
        from django.contrib import admin

        from apps.admin_ext.dashboard import make_dashboard_index

        # Uhvati ORIGINAL `admin.site.index` PRE reassignment-a (recursion guard, G-12;
        # SM-D1/Task6 — capture u ready(), ne na import-u modula).
        original_index = admin.site.index

        # PINOVAN override (SM-D1): wrapper injektuje stats + delegira na original
        # (app_list zadržan), template extenduje Django ugrađeni index (G-1).
        admin.site.index = make_dashboard_index(original_index)
        admin.site.index_template = "admin_ext/dashboard.html"
