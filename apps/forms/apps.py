"""Story 4.1 — AppConfig za dedikovani lead-gen forms app (SM-D1).

`apps/forms/` je samostalan top-level app (dep boundary forms → core only;
NIKAD products/brands/search/catalog/blog — architecture.md:739, SM-D3a).
Drži `Lead` model (jedinstveno DB skladište za sve 4 forme), `send_lead_email`
service (sync, view-called) i read-mostly `LeadAdmin`. NEMA signal wiring
(email je view-orchestrated, NE post_save — SM-D5). Mirror `apps/search/apps.py`.
"""

from __future__ import annotations

from django.apps import AppConfig


class FormsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.forms"
