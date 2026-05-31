"""URL routing za apps.core.

Story 3.1 (C1): `home` path je UKLONJEN — root `/` sada mapira `pages:home`
(`apps/pages/urls.py`). `apps/core/urls.py` zadržava `app_name` + prazan
`urlpatterns` za buduće leaf core URL-ove (NIJE uključen u config/urls.py dok
je prazan).
"""

from django.urls import path  # noqa: F401  (zadržan za buduće core URL-ove)

app_name = "core"

urlpatterns: list = []
