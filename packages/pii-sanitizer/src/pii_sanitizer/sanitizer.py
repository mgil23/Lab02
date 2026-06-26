# SPDX-License-Identifier: AGPL-3.0-or-later
"""
PII Sanitizer using Microsoft Presidio.
Provides reversible anonymization: sanitize() → (anonymized_text, token_map)
Calling restore() recovers the original PII values in extracted results.
"""
import re
import secrets
from typing import Any
from .reversible_map import generate_token

_PII_ENTITIES = [
    "PERSON",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "US_SSN",
    "CREDIT_CARD",
    "IBAN_CODE",
    "MEDICAL_LICENSE",
    "DATE_TIME",
    "IP_ADDRESS",
    "URL",
    "NRP",
]


class PiiSanitizer:
    def __init__(self) -> None:
        self._session_salt = secrets.token_hex(8)
        self._analyzer = None
        self._anonymizer = None

    def _get_analyzer(self) -> Any:
        if self._analyzer is None:
            from presidio_analyzer import AnalyzerEngine
            self._analyzer = AnalyzerEngine()
        return self._analyzer

    def _get_anonymizer(self) -> Any:
        if self._anonymizer is None:
            from presidio_anonymizer import AnonymizerEngine
            self._anonymizer = AnonymizerEngine()
        return self._anonymizer

    def sanitize(self, text: str) -> tuple[str, dict[str, str]]:
        """
        Anonymize PII in text. Returns (sanitized_text, token_map).
        token_map: {token: original_value}
        """
        if not text or not text.strip():
            return text, {}

        try:
            analyzer = self._get_analyzer()
            results = analyzer.analyze(text=text, entities=_PII_ENTITIES, language="en")
        except Exception:
            return text, {}

        if not results:
            return text, {}

        # Sort by start position descending so replacements don't shift offsets
        results.sort(key=lambda r: r.start, reverse=True)

        token_map: dict[str, str] = {}
        sanitized = text

        for result in results:
            original = text[result.start:result.end]
            token = generate_token(original, result.entity_type, self._session_salt)
            token_map[token] = original
            sanitized = sanitized[: result.start] + token + sanitized[result.end :]

        return sanitized, token_map

    def restore(self, data: dict | str | list, token_map: dict[str, str]) -> Any:
        """
        Restore PII tokens in extracted results back to original values.
        Recursively processes dicts, lists, and strings.
        """
        if not token_map:
            return data

        if isinstance(data, str):
            return self._restore_string(data, token_map)
        if isinstance(data, dict):
            return {k: self.restore(v, token_map) for k, v in data.items()}
        if isinstance(data, list):
            return [self.restore(item, token_map) for item in data]
        return data

    def _restore_string(self, text: str, token_map: dict[str, str]) -> str:
        for token, original in token_map.items():
            text = text.replace(token, original)
        return text
