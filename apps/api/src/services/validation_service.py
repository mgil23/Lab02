# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Deterministic business rules engine for post-extraction field validation.
Evaluates regex / range / required / cross_field rules and writes
validation_status + validation_errors back to ExtractedField records.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


def _to_float(value: Any) -> float | None:
    try:
        return float(str(value).replace(",", "").replace("$", "").strip())
    except (TypeError, ValueError):
        return None


def _check_regex(value: str | None, pattern: str) -> bool:
    if not value:
        return False
    try:
        return bool(re.fullmatch(pattern, value.strip()))
    except re.error as e:
        logger.warning("Invalid regex pattern %r: %s", pattern, e)
        return True  # skip broken patterns


def _check_range(value: str | None, min_val: Any, max_val: Any) -> bool:
    num = _to_float(value)
    if num is None:
        return False
    if min_val is not None and num < float(min_val):
        return False
    if max_val is not None and num > float(max_val):
        return False
    return True


class ValidationService:
    """Apply deterministic validation rules to a set of extracted fields."""

    def validate(
        self,
        fields: dict[str, str | None],
        rules: list[dict],
    ) -> dict[str, dict]:
        """
        Args:
            fields: {field_name: value_string}
            rules: list of rule dicts from DocumentType.validation_rules

        Returns:
            {field_name: {"status": "valid"|"flagged", "errors": [str]}}
        """
        results: dict[str, dict] = {name: {"status": "valid", "errors": []} for name in fields}

        for rule in rules:
            rule_type: str = rule.get("rule_type", "")
            field_name: str | None = rule.get("field_name")
            config: dict = rule.get("rule_config", {})
            error_msg: str = rule.get("error_message", "Validation failed")

            if rule_type == "required":
                targets = [field_name] if field_name else list(fields.keys())
                for name in targets:
                    val = fields.get(name)
                    if not val or not str(val).strip():
                        results.setdefault(name, {"status": "valid", "errors": []})
                        results[name]["errors"].append(error_msg)
                        results[name]["status"] = "flagged"

            elif rule_type == "regex" and field_name:
                pattern = config.get("pattern", "")
                val = fields.get(field_name)
                if val and not _check_regex(val, pattern):
                    results[field_name]["errors"].append(error_msg)
                    results[field_name]["status"] = "flagged"

            elif rule_type == "range" and field_name:
                val = fields.get(field_name)
                if not _check_range(val, config.get("min"), config.get("max")):
                    results[field_name]["errors"].append(error_msg)
                    results[field_name]["status"] = "flagged"

            elif rule_type == "cross_field":
                op = config.get("operator", "eq")
                lhs_name: str = config.get("lhs_field", "")
                rhs_name: str = config.get("rhs_field", "")
                lhs = _to_float(fields.get(lhs_name))
                rhs = _to_float(fields.get(rhs_name))
                if lhs is not None and rhs is not None:
                    passed = {
                        "eq": lhs == rhs,
                        "ne": lhs != rhs,
                        "lt": lhs < rhs,
                        "lte": lhs <= rhs,
                        "gt": lhs > rhs,
                        "gte": lhs >= rhs,
                    }.get(op, True)
                    if not passed:
                        for name in [lhs_name, rhs_name]:
                            if name in results:
                                results[name]["errors"].append(error_msg)
                                results[name]["status"] = "flagged"

        return results
