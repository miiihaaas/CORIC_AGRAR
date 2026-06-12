# Story 9.8 — Page Object pattern paket (AC5).
# Selektori i akcije su enkapsulirani u page objektima; spec-ovi ostaju deklarativni.

from tests.e2e.page_objects.admin_product_page import AdminProductPage
from tests.e2e.page_objects.product_detail_page import ProductDetailPage
from tests.e2e.page_objects.service_page import ServicePage
from tests.e2e.page_objects.traktori_listing_page import TraktoriListingPage

__all__ = [
    "AdminProductPage",
    "ProductDetailPage",
    "ServicePage",
    "TraktoriListingPage",
]
