"""Story 2.13 — AppConfig za dedikovani site-wide search app (SM-D1).

Global search je cross-domain feature (Product danas, Post u Epic 5) — živi u
zasebnom `apps/search/` app-u sa jednosmernom zavisnošću search → products
(+ brands za empty-state CTA). Vidi SM-D1.
"""

from __future__ import annotations

from django.apps import AppConfig


class SearchConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.search"
