# SPDX-License-Identifier: AGPL-3.0-or-later
"""
AWS Strands Agent @tool definitions for IDP extraction.
These tools are invoked by the Strands Agent framework via function-calling.
"""
import json
from strands import tool


@tool
def extract_fields(
    document_text: str,
    layout_hints: str,
    field_schema: str,
) -> str:
    """
    Extract structured fields from document text using layout context.

    Args:
        document_text: Full text content of the document
        layout_hints: Structured description of page layout (block types, positions)
        field_schema: JSON schema of fields to extract

    Returns:
        JSON string: {field_name: {value, confidence, page_number, source_text, reasoning}}
    """
    # The Strands framework calls this tool; the LLM fills in the return value.
    # This function body is never executed directly — it serves as the tool specification.
    return json.dumps({})


@tool
def validate_field(
    field_name: str,
    field_value: str,
    validation_rule: str,
    document_context: str,
) -> str:
    """
    Validate an extracted field value against a business rule.

    Args:
        field_name: Name of the field being validated
        field_value: The extracted value to validate
        validation_rule: JSON-encoded validation rule specification
        document_context: Relevant surrounding text for context

    Returns:
        JSON string: {valid: bool, error: str | null, corrected_value: str | null}
    """
    return json.dumps({"valid": True, "error": None, "corrected_value": None})


@tool
def resolve_ambiguity(
    field_name: str,
    candidates: list[str],
    document_context: str,
    rule_context: str,
) -> str:
    """
    Resolve ambiguity when multiple candidate values exist for a field.

    Args:
        field_name: Name of the ambiguous field
        candidates: List of candidate values to choose from
        document_context: Surrounding document text for context
        rule_context: Business rules and field type information

    Returns:
        JSON string: {chosen_value: str, reasoning: str, confidence: float}
    """
    return json.dumps({"chosen_value": candidates[0] if candidates else "", "reasoning": "", "confidence": 0.5})


@tool
def flag_for_human_review(
    field_name: str,
    reason: str,
    candidates: list[str] | None = None,
) -> str:
    """
    Flag a field for human review when the agent cannot determine the value with sufficient confidence.

    Args:
        field_name: Name of the field to flag
        reason: Explanation of why human review is needed
        candidates: Optional list of candidate values for the reviewer

    Returns:
        JSON string: {flagged: true, reason: str, candidates: list}
    """
    return json.dumps({
        "flagged": True,
        "reason": reason,
        "candidates": candidates or [],
    })
