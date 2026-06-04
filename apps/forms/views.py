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

from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.translation import get_language
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from apps.forms.forms import (
    ContactForm,
    ModelInquiryForm,
    PartRequestForm,
    ServiceRequestForm,
)
from apps.forms.models import Lead, LeadAttachment
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


@require_POST
@ratelimit(key="ip", rate="5/m", block=False)
def service_request_submit(request):
    if getattr(request, "limited", False):
        return HttpResponse(status=429)

    form = ServiceRequestForm(request.POST, request.FILES)
    if not form.is_valid():
        return render(
            request, "forms/partials/_service_request_form_fields.html", {"form": form}
        )

    # Lead + attachment loop su ATOMIČNI: ako attachment create padne na fajlu N
    # (storage OSError), Lead se rollback-uje → NEMA orphan lead-a sa parcijalnim
    # prilozima. send_lead_email JE NAMERNO IZVAN atomic bloka (email failure NE SME
    # da rollback-uje sačuvan lead — C1 ugovor / SM-D5).
    with transaction.atomic():
        lead = Lead.objects.create(
            form_type=Lead.FormType.SERVICE_REQUEST,
            name=form.cleaned_data["name"],
            phone=form.cleaned_data["phone"],
            email=form.cleaned_data["email"],
            message=form.cleaned_data["description"],  # opis kvara → Lead.message (SM-D2)
            locale=get_language(),
            ip_address=request.META.get("REMOTE_ADDR"),
            data={
                "machine_type": form.cleaned_data["machine_type"],
                "brand_model": form.cleaned_data["brand_model"],  # prazan → "" (ključ PRISUTAN)
            },
        )
        for f in form.cleaned_data["photos"]:  # prazna lista ako bez slika
            LeadAttachment.objects.create(lead=lead, file=f)
    send_lead_email(lead)  # save-before-send; povratak se NE rollback-uje
    return render(request, "forms/partials/service_request_success.html", {"lead": lead})


@require_POST
@ratelimit(key="ip", rate="5/m", block=False)
def part_request_submit(request):
    """Story 4.5 — rezervni delovi HTMX submit (REUSE service_request_submit; SM-D7 NEMA
    apps.products import — model/deo su free text). Single-file slika kroz `request.FILES`.
    """
    if getattr(request, "limited", False):
        return HttpResponse(status=429)

    form = PartRequestForm(request.POST, request.FILES)
    if not form.is_valid():
        return render(
            request, "forms/partials/_part_request_form_fields.html", {"form": form}
        )

    # Lead + opciona slika su ATOMIČNI (mirror 4.4); send_lead_email IZVAN atomic
    # bloka (email failure NE rollback-uje sačuvan lead — C1 / SM-D5).
    with transaction.atomic():
        lead = Lead.objects.create(
            form_type=Lead.FormType.PART_REQUEST,
            name=form.cleaned_data["name"],
            phone=form.cleaned_data["phone"],
            email=form.cleaned_data["email"],
            message=form.cleaned_data["note"],  # napomena → Lead.message (SM-D2)
            locale=get_language(),
            ip_address=request.META.get("REMOTE_ADDR"),
            data={
                "tractor_model": form.cleaned_data["tractor_model"],
                "part_name": form.cleaned_data["part_name"],
                "extra_description": form.cleaned_data["extra_description"],  # prazan → ""
                "payment_method": form.cleaned_data["payment_method"],
                "delivery_method": form.cleaned_data["delivery_method"],
            },
        )
        photo = form.cleaned_data.get("photo")
        if photo:
            LeadAttachment.objects.create(lead=lead, file=photo)
    send_lead_email(lead)  # save-before-send; povratak se NE rollback-uje
    return render(request, "forms/partials/part_request_success.html", {"lead": lead})
