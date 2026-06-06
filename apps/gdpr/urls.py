"""Story 7.1 — URL routing za apps.gdpr.

`gdpr:cookie_policy` mount-ovan u config/urls.py i18n_patterns → locale-prefiksovan
(/sr/, /hu/, /en/politika-kolacica/). Slug `politika-kolacica` je ASCII (G-6).
"""

from django.urls import path

from apps.gdpr.views import CookiePolicyView

app_name = "gdpr"

urlpatterns = [
    path("politika-kolacica/", CookiePolicyView.as_view(), name="cookie_policy"),
]
