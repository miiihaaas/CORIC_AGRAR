"""Story 4.1 — SM-D5 no post_save signal (email je view-called) (TEA RED phase).

Pokriva SM-D5: `Lead.objects.create(...)` SAM (BEZ poziva send_lead_email) → mailoutbox
PRAZAN. Dokazuje da NEMA post_save signala koji auto-šalje email (signal bi okinuo na
SVAKI Lead.create — uključujući testove/admin/seed = neželjeno). Email je VIEW-ORCHESTRATED.

TEA RED phase: testovi MORAJU pasti — apps.forms.models ne postoji.
NAPOMENA: kad model bude postojao a service NE bude vezan signalom, OVAJ test će proći
(GREEN) — to je njegova svrha (regresija-lock protiv slučajnog post_save wiring-a).

Refs:
- 4-1-lead-model-smtp-setup.md SM-D5 + Task 8.7
- 4-1-interface-contract.md § 4 (VIEW-CALLED, NE signal)
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


# SM-D5: bare Lead.objects.create(...) NE šalje email (NEMA post_save signal)
def test_create_lead_does_not_send_email(mailoutbox):
    from apps.forms.models import Lead

    Lead.objects.create(
        form_type=Lead.FormType.KONTAKT,
        name="Marko Marković",
        email="marko@example.com",
        locale="sr",
    )

    assert len(mailoutbox) == 0, (
        f"`Lead.objects.create(...)` SAM NE SME slati email (email je view-called, NE "
        f"post_save signal — SM-D5). mailoutbox ima {len(mailoutbox)} email-ova → "
        "verovatno postoji neželjen post_save signal."
    )


# SM-D5: FormsConfig.ready ne registruje signal (nema signals modul wiring)
def test_forms_app_does_not_wire_signals():
    import importlib.util

    from django.conf import settings

    # apps/forms/signals.py NE SME postojati (4-1 nema signal — SM-D5)
    spec = importlib.util.find_spec("apps.forms.signals")
    assert spec is None, (
        "apps/forms/signals.py NE SME postojati u 4-1 (email je view-called, NE signal — SM-D5)."
    )
    assert "apps.forms" in settings.INSTALLED_APPS, "apps.forms MORA biti registrovan (AC3)."
