"""apps.accounts.forms — AdminLoginForm (email-as-username admin login).

Story 8.1 / SM-D4 / SM-D13. Subclass `AdminAuthenticationForm` → zadržava
`confirm_login_allowed` is_staff guard. UI label `username` polja prikazuje
„Email". `clean()` rezolvuje uneti email → username (case-insensitive, prvi
match) PRE `super().clean()` → `authenticate()`. NIKAD direktan User import —
get_user_model() (project-context.md).
"""

from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _


class AdminLoginForm(AdminAuthenticationForm):
    """Email-as-username admin login (SM-D4/SM-D13)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = _("Email")

    def clean(self):
        identifier = self.cleaned_data.get("username", "")
        if identifier and "@" in identifier:
            user = get_user_model().objects.filter(email__iexact=identifier).first()
            if user is not None:
                # mapiraj rezolvovani email → username PRE authenticate()
                self.cleaned_data["username"] = user.get_username()
        return super().clean()
