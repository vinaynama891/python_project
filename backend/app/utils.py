"""Utility functions for the backend application.
Currently provides a simple UUID generator used by PDT models.
"""

import uuid

def generate_uuid() -> str:
    """Return a new random UUID v4 as a string.
    Used as the default primary‑key factory for PDT tables.
    """
    return str(uuid.uuid4())
