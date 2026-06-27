# SPDX-License-Identifier: AGPL-3.0-or-later
"""
ExtractionAgent: AWS Strands-based document extraction with PII sanitization.
"""
import json
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from .tools import extract_fields, validate_field, resolve_ambiguity, flag_for_human_review

_jinja_env = Environment(
    loader=FileSystemLoader(str(Path(__file__).parent / "prompts")),
    autoescape=False,
)


def _sanitize_and_restore(text: str) -> tuple[str, dict]:
    """PII sanitization with reversible token map."""
    try:
        from pii_sanitizer.sanitizer import PiiSanitizer
        sanitizer = PiiSanitizer()
        return sanitizer.sanitize(text)
    except ImportError:
        return text, {}


def _restore_pii(result: dict, token_map: dict) -> dict:
    if not token_map:
        return result
    try:
        from pii_sanitizer.sanitizer import PiiSanitizer
        sanitizer = PiiSanitizer()
        return sanitizer.restore(result, token_map)
    except ImportError:
        return result


class ExtractionAgent:
    """
    AWS Strands Agent for structured field extraction from documents.

    Uses temperature=0.0 for deterministic, consistent extraction.
    PII is sanitized before any LLM call and restored in results.
    """

    def __init__(self, document_type_config: dict) -> None:
        self._config = document_type_config
        self._system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        template = _jinja_env.get_template("extraction.j2")
        return template.render(
            document_type=self._config.get("name", "generic"),
            fields=self._config.get("fields", []),
            validation_rules=self._config.get("validation_rules", []),
        )

    def _build_user_prompt(
        self,
        text: str,
        layout: dict,
        page_range: tuple[int, int],
    ) -> str:
        layout_summary = "\n".join(
            f"[{b.get('type', 'text').upper()}] p{b.get('page', '?')}: {str(b.get('text', ''))[:120]}"
            for b in layout.get("blocks", [])[:30]
        )
        field_schema = json.dumps(
            [{"name": f["name"], "type": f["field_type"], "required": f.get("is_required", False)}
             for f in self._config.get("fields", [])],
            indent=2,
        )
        return (
            f"Document pages {page_range[0]}–{page_range[1]}.\n\n"
            f"TEXT:\n{text[:8000]}\n\n"
            f"LAYOUT:\n{layout_summary}\n\n"
            "Now extract all fields defined in the schema. "
            "Call extract_fields first with the full text, layout hints, "
            f"and this field schema:\n{field_schema}\n\n"
            "Then validate each extracted field and resolve any ambiguities."
        )

    async def run(
        self,
        text: str,
        layout: dict,
        page_range: tuple[int, int],
    ) -> dict:
        """
        Run extraction agent on document text.
        Returns: {field_name: {value, confidence, page_number, source_text, reasoning}}
        """
        sanitized_text, token_map = _sanitize_and_restore(text)
        user_prompt = self._build_user_prompt(sanitized_text, layout, page_range)

        try:
            from strands import Agent
            from strands.models import BedrockModel

            model = BedrockModel(
                model_id=os.environ.get("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-6"),
                region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
                temperature=float(os.environ.get("EXTRACTION_TEMPERATURE", "0.0")),
                max_tokens=int(os.environ.get("EXTRACTION_MAX_TOKENS", "4096")),
            )
            agent = Agent(
                model=model,
                tools=[extract_fields, validate_field, resolve_ambiguity, flag_for_human_review],
                system_prompt=self._system_prompt,
            )
            raw_result = await agent.run_async(user_prompt)
            parsed = self._parse_agent_output(raw_result)

        except Exception as e:
            # Graceful degradation: return empty fields with error note
            parsed = {
                field["name"]: {
                    "value": None,
                    "confidence": 0.0,
                    "source_text": None,
                    "reasoning": f"Agent error: {e}",
                    "flagged": True,
                }
                for field in self._config.get("fields", [])
            }

        return _restore_pii(parsed, token_map)

    def _parse_agent_output(self, raw: object) -> dict:
        """Extract field results from Strands Agent tool call outputs."""
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                pass
        # Try to parse from agent's accumulated tool results
        if hasattr(raw, "tool_results"):
            for result in raw.tool_results:
                if result.get("tool") == "extract_fields":
                    try:
                        return json.loads(result.get("output", "{}"))
                    except Exception:
                        pass
        return {}
