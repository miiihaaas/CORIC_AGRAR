"""Story 8.7 — Deljivi admin ModelForm helperi (SM-D6 promocija iz 8.6).

8.6 (`apps/products/admin.py`) je uveo `_relax_base_translation_fields` +
`_relax_fields_with_model_default` lokalno. Architect forward-watch (HARD): „ako
8-7 mirror → promoviši u core helper; shim NE sme proliferirati copy-paste".

8.7 direct-bind-uje `PostAdminForm` (TEA `_make_post_form` šalje `title_sr`-only
payload) → potreban je relaks baznog `title` (NIKAD `title_sr`). Da se izbegne
copy-paste, helperi su izvučeni ovde i 8.6 ih sada importuje (konzistentan swap).

NAPOMENA (modul-ime): `apps/core/forms.py` i `apps/core/admin.py` su EKSPLICITNO
zabranjeni u apps.core (Story 1.4/2.1 scope-guard — `test_ac1_core_does_not_have_admin_or_forms_yet`:
apps.core je infrastructure namespace, NE domain CRUD app). Zato je modul nazvan
`admin_forms.py` (admin-form util, NIJE `forms.py`/`admin.py`) — poštuje lock dok
zadržava SM-D6 nameru (deljiv helper u core, NE copy-paste).

`isinstance(models.Field)` guard (8.6) zadržan — `get_fields()` vraća i reverse
relacije čije `.name` može slučajno da se poklopi sa form-poljem.
"""

from __future__ import annotations

from django.db import models


def relax_base_translation_fields(form):
    """Relaksira `required` na BAZNIM translatable poljima kad raw ModelForm vidi i `_sr`.

    modeltranslation u adminu (formfield_for_dbfield) promoviše default-lang polje (`_sr`)
    u required i skida required sa baznog polja. Taj swap se dešava kroz admin sloj, NE
    kroz raw ModelForm — pa kad se ModelForm bind-uje DIREKTNO (testovi), bazno `title`/`name`
    ostaje required i blokira validan `_sr`-only payload. Ovde repliciramo admin ponašanje:
    bazno polje postaje opciono (vrednost se sinhronizuje iz `_sr` kroz modeltranslation
    descriptor), `*_sr` ostaje BEZUSLOVNO obavezan (NE relaksiramo ga — AC9/M1).
    """
    for field in form._meta.model._meta.get_fields():
        # Restrict to concrete model fields — get_fields() also yields reverse
        # relations (ManyToOneRel etc.) whose `.name` == related_name; a reverse-rel
        # name could otherwise accidentally match a form field and relax it. Concrete
        # `models.Field` instances are the only ones with a translatable `_sr` twin.
        if not isinstance(field, models.Field):
            continue
        name = field.name
        sr_name = f"{name}_sr"
        if name in form.fields and sr_name in form.fields:
            form.fields[name].required = False


def relax_fields_with_model_default(form):
    """Relaksira `required` na poljima koja imaju model-level default (npr. status).

    Django ModelForm drži takva polja required kad je `blank=False` na modelu, iako default
    popunjava vrednost pri save-u. U adminu se renderuju sa initial-om (default izabran), pa
    submit uvek nosi vrednost; u raw direct-bind testu izostaju → relaksacija je bezbedna jer
    model default popunjava prazno polje.
    """
    for field in form._meta.model._meta.fields:
        if field.has_default() and field.name in form.fields:
            form.fields[field.name].required = False
