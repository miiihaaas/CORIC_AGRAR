"""URL routing za apps.pages (Story 3.1) — root path `/` → HomeView (pages:home)."""

from django.urls import path

from apps.pages.views import (
    AboutView,
    ContactView,
    HomeView,
    PageDetailView,
    PartRequestView,
    ServiceView,
)

app_name = "pages"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("o-nama/", AboutView.as_view(), name="about"),
    path("kontakt/", ContactView.as_view(), name="contact"),
    path("servis/", ServiceView.as_view(), name="service"),
    path(
        "servis/rezervni-delovi/",
        PartRequestView.as_view(),
        name="part_request",
    ),
    # Story 7.4 — catch-all slug ruta MORA biti POSLEDNJA u pages.urls (G-3) da ne
    # shadow-uje statičke rute iznad; pages include je TAKOĐE poslednji u
    # config/urls.py i18n_patterns (CRITICAL-1) da ne shadow-uje blog/gdpr.
    path("<slug:slug>/", PageDetailView.as_view(), name="page_detail"),
]
