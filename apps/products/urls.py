"""URL routing za apps.products — Story 2.7 ProductDetailView."""

from django.urls import path

from apps.products import views

app_name = "products"

urlpatterns = [
    path("proizvod/<slug:slug>/", views.ProductDetailView.as_view(), name="detail"),
]
