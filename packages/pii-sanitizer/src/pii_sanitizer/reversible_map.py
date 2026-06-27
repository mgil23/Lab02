# SPDX-License-Identifier: AGPL-3.0-or-later
"""Deterministic reversible token generation for PII anonymization."""
import hashlib


def generate_token(pii_value: str, entity_type: str, salt: str = "") -> str:
    """
    Generate a deterministic, stable replacement token for a PII value.
    Same PII value + entity_type + salt → always same token within a session.
    """
    digest = hashlib.sha256(f"{salt}:{entity_type}:{pii_value}".encode()).hexdigest()[:8]
    return f"[{entity_type}_{digest}]"
