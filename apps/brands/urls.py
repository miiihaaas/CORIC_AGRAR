"""URL routing za apps.brands — Story 2.6 + Story 2.10 + Story 2.11."""

from django.urls import path

from apps.brands.views import (
    BrandDetailView,
    HzmRadneMasineView,
    JeegeePrikljucnaView,
    SubcategoryListView,
    TulipMixPrikoliceView,
)

app_name = "brands"

urlpatterns = [
    path("traktori/<slug:slug>/", BrandDetailView.as_view(), name="detail"),
    path(
        "mehanizacija/prikljucna/",
        JeegeePrikljucnaView.as_view(),
        name="jeegee_prikljucna",
    ),
    path(
        "mehanizacija/prikljucna/<slug:category_slug>/",
        SubcategoryListView.as_view(),
        name="subcategory_listing_category",
    ),
    path(
        "mehanizacija/prikljucna/<slug:category_slug>/<slug:l1_slug>/",
        SubcategoryListView.as_view(),
        name="subcategory_listing_l1",
    ),
    path(
        "mehanizacija/prikljucna/<slug:category_slug>/<slug:l1_slug>/<slug:l2_slug>/",
        SubcategoryListView.as_view(),
        name="subcategory_listing_l2",
    ),
    path(
        "mehanizacija/prikljucna/<slug:category_slug>/<slug:l1_slug>/"
        "<slug:l2_slug>/<slug:l3_slug>/",
        SubcategoryListView.as_view(),
        name="subcategory_listing_l3",
    ),
    path(
        "mehanizacija/radne-masine/",
        HzmRadneMasineView.as_view(),
        name="hzm_radne_masine",
    ),
    path(
        "mehanizacija/mix-prikolice/",
        TulipMixPrikoliceView.as_view(),
        name="tulip_mix_prikolice",
    ),
]
