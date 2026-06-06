"""Story 6.4 — OPEN-REDIRECT guard (TEA RED phase, AC5 — SECURITY LOCK).

`Redirect.clean()` MORA odbiti svaki bypass-vektor za `new_path` (apsolutni
http(s)://, scheme-relative //, backslash /\\, javascript:, ftp://) kroz
`django.utils.http.url_has_allowed_host_and_scheme(url=new_path, allowed_hosts=None)`
(NE ručni startswith — propušta backslash/encoded). Plus: self-loop (old==new),
old_path bez vodećeg „/" (tiho-mrtvo pravilo). Enforcement NIJE admin-only:
`Redirect.save()` override zove `full_clean()` → programski `.create()`/`.save()`
sa nevalidnim new_path TAKOĐE raise-uje ValidationError.

⚠️ GUARD: apps.seo.models.Redirect import UNUTAR test body-ja (collection-safety).

Refs:
- 6-4-redirect-manager-301.md AC5 + Task 1.4/1.5/6.2 + SM-D2 + Gotcha SEO4-2
- 6-4-interface-contract.md § 1. Model clean()/save()
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


# AC5: svi bypass-vektori za new_path → ValidationError (full_clean direktno)
@pytest.mark.parametrize(
    "bad_new_path",
    [
        "https://evil.com",        # apsolutni eksterni (https)
        "http://x.com",            # apsolutni eksterni (http)
        "//evil.com",              # scheme-relative
        "/\\evil.com",             # backslash bypass (ručni startswith propušta — KLJUČNO)
        "javascript:alert(1)",     # javascript: shema
        "ftp://x",                 # ftp shema
    ],
)
def test_clean_rejects_open_redirect_vectors(bad_new_path):
    from django.core.exceptions import ValidationError

    from apps.seo.models import Redirect

    r = Redirect(old_path="/sr/x/", new_path=bad_new_path)
    with pytest.raises(ValidationError) as exc:
        r.full_clean()
    # greška MORA biti vezana za new_path (SM-D2)
    assert "new_path" in exc.value.message_dict, (
        f"ValidationError za {bad_new_path!r} MORA biti keyed na 'new_path' "
        "(url_has_allowed_host_and_scheme guard — AC5/SM-D2). "
        f"Dobio: {exc.value.message_dict}"
    )


# AC5: validan site-internal new_path PROLAZI clean() (no error)
def test_clean_accepts_internal_path():
    from apps.seo.models import Redirect

    r = Redirect(old_path="/sr/stari/", new_path="/sr/novi/")
    # NE sme raise — site-internal path je dozvoljen (SM-D2/SEO4-2)
    r.full_clean()


# AC5: self-loop (old_path == new_path) → ValidationError (beskonačni 301 guard — SM-D2)
def test_clean_rejects_self_loop():
    from django.core.exceptions import ValidationError

    from apps.seo.models import Redirect

    r = Redirect(old_path="/sr/x/", new_path="/sr/x/")
    with pytest.raises(ValidationError) as exc:
        r.full_clean()
    assert "new_path" in exc.value.message_dict, (
        "self-loop (old_path == new_path) MORA raise ValidationError na new_path "
        "(beskonačni 301 guard — SM-D2). "
        f"Dobio: {exc.value.message_dict}"
    )


# AC5: old_path bez vodećeg „/" → ValidationError na old_path (tiho-mrtvo pravilo guard)
def test_clean_rejects_old_path_without_leading_slash():
    from django.core.exceptions import ValidationError

    from apps.seo.models import Redirect

    r = Redirect(old_path="sr/stara/", new_path="/sr/nova/")
    with pytest.raises(ValidationError) as exc:
        r.full_clean()
    assert "old_path" in exc.value.message_dict, (
        "old_path bez vodeceg slash-a MORA raise ValidationError na old_path "
        "(sprecava tiho-mrtvo pravilo — request.path uvek pocinje sa '/'). "
        f"Dobio: {exc.value.message_dict}"
    )


# AC5: new_path must start with / — bez vodećeg „/" browser resolve-uje
#       relativno na trenutni URL (/sr/stara/ + sr/nova/ → /sr/stara/sr/nova/)
#       → pogrešna destinacija + agresivno keširan 301 (simetrično old_path guard-u)
def test_clean_rejects_new_path_without_leading_slash():
    from django.core.exceptions import ValidationError

    from apps.seo.models import Redirect

    r = Redirect(old_path="/sr/stara/", new_path="sr/nova/")
    with pytest.raises(ValidationError) as exc:
        r.full_clean()
    assert "new_path" in exc.value.message_dict, (
        "new_path bez vodeceg slash-a MORA raise ValidationError na new_path "
        "(sprecava relativni resolve protiv trenutnog URL-a + keširan 301). "
        f"Dobio: {exc.value.message_dict}"
    )


# AC5: ENFORCEMENT NIJE admin-only — save() override zove full_clean()
#       → programski .create() sa nevalidnim new_path raise-uje ValidationError
def test_save_enforces_guard_via_create():
    from django.core.exceptions import ValidationError

    from apps.seo.models import Redirect

    with pytest.raises(ValidationError):
        # .objects.create() poziva save() → save() MORA zvati full_clean() (SM-D2/SEO4-2)
        Redirect.objects.create(old_path="/sr/x/", new_path="//evil.com")


# AC5: ENFORCEMENT NIJE admin-only — direktan instance.save() sa nevalidnim new_path
def test_save_enforces_guard_via_instance_save():
    from django.core.exceptions import ValidationError

    from apps.seo.models import Redirect

    r = Redirect(old_path="/sr/y/", new_path="https://evil.com")
    with pytest.raises(ValidationError):
        r.save()


# AC5: validan rule se ZAISTA perzistira kroz save() (guard ne lomi legitimne write-ove)
def test_save_persists_valid_redirect():
    from apps.seo.models import Redirect

    r = Redirect(old_path="/sr/legit/", new_path="/sr/legit-novi/")
    r.save()
    assert Redirect.objects.filter(old_path="/sr/legit/").exists(), (
        "Validan Redirect MORA biti perzistiran kroz save() (guard ne blokira legitimni write — AC5)."
    )
