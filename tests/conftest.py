"""Pytest config za CORIC_AGRAR test suite.

Dodaje project root u sys.path tako da testovi mogu da import-uju moduli iz
root-a (npr. `manage.py`, `config/`) bez potrebe za instalacijom paketa.

Takođe definiše zajedničke fixture-e koji se koriste kroz testove.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Project root = parent direktorijum od tests/ folder-a
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Dodaj root u sys.path ako nije već (idempotent)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
