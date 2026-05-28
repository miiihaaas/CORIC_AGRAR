"""Views za apps.core. Story 1.4 sadrži samo `home` smoke view.

Story 1.6+ će overrid-ovati ili proširiti home sa Hero sekcijom, vestima,
itd. — vidi epics.md § Story 3.1 (Home strana sa svim sekcijama).
"""

from django.shortcuts import render


def home(request):
    return render(request, "base.html", {})
