"""Story 4.2 — `contact_submit` HTMX FBV (Opšta kontakt forma, FR-5).

POST-only (`@require_POST` → GET vraća 405). Ratelimit `5/m` po IP-u sa
**`block=False`** (NE `block=True` → 403): kad je limit pređen, `request.limited`
je True i view na VRHU tela vraća `HttpResponse(status=429)` (SM-D9). Save-before-send:
`Lead.objects.create(...)` PA TEK ONDA `send_lead_email(lead)` (4.1 ugovor; povratak
se NE rollback-uje — AC5). Success/error oba vraćaju PARTIAL (HTTP 200) sa OOB
aria-live najavom (guarded `{% if request.htmx %}`).

Refs: 4-2-opsta-kontakt-forma-fr-5.md AC2-AC7 + Task 6; interface-contract § 2.
"""

from __future__ import annotations

from django.http import HttpResponse
from django.shortcuts import render
from django.utils.translation import get_language
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from apps.forms.forms import ContactForm
from apps.forms.models import Lead
from apps.forms.notifications import send_lead_email


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
