"""HTMX lead-gen submit endpoints (kanonski form pattern — Story 4.6 STANDARDIZACIJA).

Kanonski reusable HTMX-form pattern (AC8 — buduće forme ga REUSE-uju, npr.
epics.md:746 kontakt strana „prati HTMX pattern iz Story 4.6"):

1. **`@htmx_form_endpoint`** dekorator (vidi dole) enkapsulira zajednički meta-prefiks:
   `@require_POST` (SPOLJAŠNJI → GET = 405) + `@ratelimit(key="ip",
   rate=FORM_RATELIMIT_RATE, block=False)` (UNUTRAŠNJI) + `request.limited → 429`
   guard. Rate je `FORM_RATELIMIT_RATE = "5/m"` (jedno-mesto konstanta).
2. **`forms/partials/_oob_aria_live.html`** `{% include %}` (parametrizovan `message`)
   renderuje guarded OOB aria-live najavu (regija #2). Tri jednostavne forme +
   4 success partiala koriste ga; `_model_inquiry_form_fields.html` zadržava svoj
   tro-ishodni OOB INLINE (SM-D8 izuzetak — product_not_found + form.errors granjanje).
3. Telo view-a (bind → invalid/valid → `Lead.objects.create` [+ atomic LeadAttachment]
   → `send_lead_email`) divergira po formi (atomic vs ne, FILES vs ne, product
   re-validacija) → NE ekstrahuje se (anti-YAGNI; callback-hell bi smanjio čitljivost).

Save-before-send: `Lead.objects.create(...)` PA TEK ONDA `send_lead_email(lead)`
(4.1 ugovor; email failure se NE rollback-uje — AC5/C1, send_lead_email IZVAN atomic).
Success/error oba vraćaju PARTIAL (HTTP 200) sa OOB aria-live najavom.

`model_inquiry_submit`: product se rezolvuje SERVER-SIDE iz trusted hidden
`product_slug` (`Product.objects.filter(is_published=True, slug=...)`) —
nepostojeći/unpublished → error partial 200, NE Lead, NE email (SM-D2/SM-D8).
`data["product_name"]` + subject UVEK iz `Product.name` (DB), NIKAD iz POST stringa.

Refs: 4-2 AC2-AC7; 4-3 AC2-AC8; 4-6 AC2/AC3/AC4/AC8; interface-contract § 2/§ 3.
"""

from __future__ import annotations

from functools import wraps

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

# AC3 — behavior-preserving (SM-D3/SM-D9): rate ostaje "5/m". Centralizacija u JEDNU
# konstantu čini buduću promenu jedno-mesto izmenom. epics.md:840/NFR-3 traže "10/15m"
# = OQ-1 PRODUKT odluka (odložena follow-up; ova story je NE primenjuje jer bi
# promenila ponašanje + oborila ~8 ratelimit testova).
FORM_RATELIMIT_RATE = "5/m"


def htmx_form_endpoint(view_func):
    """Zajednički HTMX-form meta-prefiks (AC2). Kanonski pattern (AC8) za buduće forme.

    Enkapsulira `@require_POST` + `@ratelimit(key="ip", rate=FORM_RATELIMIT_RATE,
    block=False)` + `request.limited → HttpResponse(status=429)` guard — uklanjajući
    duplirani prefiks iz sva 4 view-a (telo ostaje NETAKNUTO).

    Kompozicija (EKSPLICITNO — redosled je LOCKED testovima, NE menjati):

        require_POST( ratelimit(key="ip", rate=FORM_RATELIMIT_RATE, block=False)( guarded ) )

    → `require_POST` je NAJSPOLJAŠNJIJI; `ratelimit` je UNUTRAŠNJI; `request.limited → 429`
    guard se izvršava UNUTAR (posle) ratelimit wrappera. Razlog (NE menjati redosled):

    1. `require_POST` se izvršava PRVI → GET vraća 405 PRE nego django_ratelimit pozove
       `is_ratelimited(increment=True)` → GET NE troši 5/m budžet i 405 precedira 429.
    2. ratelimit wrapper postavlja `request.limited` PRE nego guard pročita taj flag.

    Pogrešan redosled bi ILI obrnuo 405-vs-429 precedenciju ILI nečujno isključio rate
    limiting (security regresija). Vraća 429 (NE 403 — block=False, SM-D9).
    """

    @ratelimit(key="ip", rate=FORM_RATELIMIT_RATE, block=False)
    @wraps(view_func)
    def _guarded(request, *args, **kwargs):
        if getattr(request, "limited", False):
            return HttpResponse(status=429)  # NE 403 (block=False — SM-D9)
        return view_func(request, *args, **kwargs)

    return require_POST(_guarded)


@htmx_form_endpoint
def contact_submit(request):
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


@htmx_form_endpoint
def model_inquiry_submit(request):
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


@htmx_form_endpoint
def service_request_submit(request):
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


@htmx_form_endpoint
def part_request_submit(request):
    """Story 4.5 — rezervni delovi HTMX submit (REUSE service_request_submit; SM-D7 NEMA
    apps.products import — model/deo su free text). Single-file slika kroz `request.FILES`.
    """
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
