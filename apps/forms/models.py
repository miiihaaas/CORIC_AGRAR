"""Story 4.1 — `Lead` model (jedinstveno DB skladište za sve 4 lead-gen forme).

`Lead(TimestampedModel)` koristi `form_type` discriminator (nested `TextChoices`,
DB vrednosti LOWERCASE — STABILAN cross-story ugovor za 4-2…4-5 + Epic 8.3) i
`data` JSONField za form-specific polja (shape ugovor SM-D13; product context
ide kroz `data["product_slug"]`, NE FK — dep boundary SM-D3a).

NEMA:
- `photo`/attachment polja (= 4-4 `LeadAttachment` child model — SM-D14)
- FK / relacija (product context kroz `data` JSON slug)
- `get_absolute_url` (lead nije content sa javnom stranom — isti izuzetak kao 3-4)
- translatable polja (lead je raw user-submitted, NE site content) → NEMA translation.py
- defensive validacija (project-context.md:358)

Refs: 4-1-lead-model-smtp-setup.md AC1; 4-1-interface-contract.md § 2.
"""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimestampedModel


class Lead(TimestampedModel):
    """Jedinstveno DB skladište za sve 4 lead-gen forme (kontakt/model/servis/delovi)."""

    class FormType(models.TextChoices):
        # DB vrednosti LOWERCASE (LOCKED cross-story ugovor — epics.md:791/802);
        # member imena uppercase (čitljivost); label puni dijakritik kroz gettext_lazy.
        KONTAKT = "contact", _("Opšti kontakt")
        MODEL_INQUIRY = "model_inquiry", _("Upit za model")
        SERVICE_REQUEST = "service_request", _("Servisni zahtev")
        PART_REQUEST = "part_request", _("Upit za rezervni deo")

    form_type = models.CharField(
        max_length=20,  # pokriva najduži DB string "service_request" (15)
        choices=FormType.choices,
        verbose_name=_("Tip forme"),
    )
    name = models.CharField(max_length=200, verbose_name=_("Ime"))  # blank=False — obavezno
    email = models.EmailField(verbose_name=_("Email"))
    phone = models.CharField(max_length=50, blank=True, verbose_name=_("Telefon"))
    message = models.TextField(blank=True, verbose_name=_("Poruka"))
    data = models.JSONField(default=dict, blank=True, verbose_name=_("Dodatni podaci"))
    ip_address = models.GenericIPAddressField(
        null=True, blank=True, verbose_name=_("IP adresa")
    )
    locale = models.CharField(
        max_length=10, default="sr", blank=True, verbose_name=_("Jezik")
    )
    # nasleđeno iz TimestampedModel: created_at, updated_at

    class Meta:
        verbose_name = _("Lead")
        verbose_name_plural = _("Lead-ovi")
        ordering = ["-created_at"]
        indexes = [
            # Epic 8.3 segmentovan count po form_type za current month (filter+count ubrzanje)
            models.Index(fields=["form_type", "created_at"], name="forms_lead_type_created_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.get_form_type_display()}: {self.name}"
