"""Story 4.2 — `contact_submit` HTMX FBV (Opšta kontakt forma, FR-5).

POST-only (`@require_POST` → GET vraća 405). Ratelimit `5/m` po IP-u sa
**`block=False`** (NE `block=True` → 403): kad je limit pređen, `request.limited`
je True i view na VRHU tela vraća `HttpResponse(status=429)` (SM-D9). Save-before-send:
`Lead.objects.create(...)` PA TEK ONDA `send_lead_email(lead)` (4.1 ugovor; povratak
se NE rollback-uje — AC5). Success/error oba vraćaju PARTIAL (HTTP 200) sa OOB
aria-live najavom (guarded `{% if request.htmx %}`).

Story 4.3 dodaje `model_inquiry_submit` (REUSE strukture): product se rezolvuje
SERVER-SIDE iz trusted hidden `product_slug` (`Product.objects.filter(is_published=True,
slug=...)`) — nepostojeći/unpublished → error partial 200, NE Lead, NE email (SM-D2/SM-D8).
`data["product_name"]` + subject UVEK iz `Product.name` (DB), NIKAD iz POST stringa (spoofing).

Refs: 4-2 AC2-AC7 + Task 6; 4-3 AC2-AC8 + Task 7; interface-contract § 2.
"""

from __future__ import annotations

from django.http import HttpResponse
from django.shortcuts import render
from django.utils.translation import get_language
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from apps.forms.forms import ContactForm, ModelInquiryForm
from apps.forms.models import Lead
from apps.forms.notifications import send_lead_email
from apps.products.models import Product


@require_POST
@ratelimit(key="ip", rate="5/m", block=False)
def contact_submit(request):
    if getattr(request, "limited", False):
        return HttpResponse(status=429)

    form = ContactForm(request.POST)
    if not form.is_valid():
        return render(
            request, "forms/partials/_contact_form_fields.html", {"form": form}
        )

    lead = Lead.objects.create(
        form_type=Lead.FormType.KONTAKT,
        name=form.cleaned_data["name"],
        email=form.cleaned_data["email"],
        phone=form.cleaned_data["phone"],
        message=form.cleaned_data["message"],
        locale=get_language(),
        ip_address=request.META.get("REMOTE_ADDR"),
        data={},
    )
    send_lead_email(lead)
    return render(request, "forms/partials/contact_success.html", {"lead": lead})


@require_POST
@ratelimit(key="ip", rate="5/m", block=False)
def model_inquiry_submit(request):
    if getattr(request, "limited", False):
        return HttpResponse(status=429)

    form = ModelInquiryForm(request.POST)

    # Server-side product re-validacija (SECURITY — NE veruj klijentu, SM-D2).
    # forms→products READ-ONLY izuzetak (SM-D6 — dokumentovan u project-context.md).
    if not form.is_valid():
        # Best-effort raw-POST lookup za readonly model display u error rerender-u
        # (AC5 — forma se ne gubi; cleaned_data nedostupan jer forma nije validna).
        product = Product.objects.filter(
            is_published=True, slug=request.POST.get("product_slug", "")
        ).first()
        return render(
            request,
            "forms/partials/_model_inquiry_form_fields.html",
            {"form": form, "product": product},
        )

    # Validan path: autoritativni lookup iz validovanog cleaned_data (validate-first).
    product = Product.objects.filter(
        is_published=True, slug=form.cleaned_data["product_slug"]
    ).first()

    if product is None:
        return render(
            request,
            "forms/partials/_model_inquiry_form_fields.html",
            {"form": form, "product": None, "product_not_found": True},
        )

    lead = Lead.objects.create(
        form_type=Lead.FormType.MODEL_INQUIRY,
        name=form.cleaned_data["name"],
        email=form.cleaned_data["email"],
        phone=form.cleaned_data["phone"],
        message=form.cleaned_data["message"],
        locale=get_language(),
        ip_address=request.META.get("REMOTE_ADDR"),
        data={"product_slug": product.slug, "product_name": product.name},
    )
    send_lead_email(lead)
    return render(request, "forms/partials/model_inquiry_success.html", {})
