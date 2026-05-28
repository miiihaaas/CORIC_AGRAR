"""URL routing za apps.core. Story 1.4 mapira samo root path (home view)."""

from django.urls import path

from apps.core.views import home

app_name = "core"

urlpatterns = [
    path("", home, name="home"),
]
