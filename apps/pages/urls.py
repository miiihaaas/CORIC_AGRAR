"""URL routing za apps.pages (Story 3.1) — root path `/` → HomeView (pages:home)."""

from django.urls import path

from apps.pages.views import AboutView, ContactView, HomeView, ServiceView

app_name = "pages"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("o-nama/", AboutView.as_view(), name="about"),
    path("kontakt/", ContactView.as_view(), name="contact"),
    path("servis/", ServiceView.as_view(), name="service"),
]
