"""URL routing za apps.products — Story 2.6 placeholder; Story 2.7 zameni."""

from django.urls import path

from apps.products import views

app_name = "products"

urlpatterns = [
    path("proizvod/<slug:slug>/", views.placeholder_view, name="detail"),
]
