"""Story 2.13 — URL routing za apps.search (SM-D2).

`app_name = "search"`; 2 statička path-a (bez slug-a) koja se ne kolidiraju sa
postojećim products/brands pattern-ima (SM-D2 deconfliction):
- `htmx/pretraga/` — HTMX dropdown endpoint (search:dropdown)
- `pretraga/` — „Vidi sve" full strana (search:results, SM-D16)
"""

from __future__ import annotations

from django.urls import path

from apps.search import views

app_name = "search"

urlpatterns = [
    path("htmx/pretraga/", views.search_dropdown, name="dropdown"),
    path("pretraga/", views.search_results, name="results"),
]
