"""URL routing za apps.pages (Story 3.1) — root path `/` → HomeView (pages:home)."""

from django.urls import path

from apps.pages.views import HomeView

app_name = "pages"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
]
