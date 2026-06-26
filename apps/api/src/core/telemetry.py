# SPDX-License-Identifier: AGPL-3.0-or-later
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.semconv.resource import ResourceAttributes
from prometheus_client import Counter, Histogram, make_asgi_app

# Prometheus metrics
PIPELINE_STAGE_DURATION = Histogram(
    "openidp_pipeline_stage_duration_seconds",
    "Pipeline stage duration in seconds",
    ["stage", "tenant_id"],
    buckets=[0.5, 1, 2, 5, 10, 15, 20, 30, 60],
)

DOCUMENTS_PROCESSED_TOTAL = Counter(
    "openidp_documents_processed_total",
    "Total documents processed",
    ["tenant_id", "status"],
)

OCR_PAGES_TOTAL = Counter(
    "openidp_ocr_pages_total",
    "Total pages processed by OCR",
    ["tenant_id"],
)

LLM_TOKENS_TOTAL = Counter(
    "openidp_llm_tokens_total",
    "Total LLM tokens used",
    ["tenant_id", "model"],
)

HTTP_REQUEST_DURATION = Histogram(
    "openidp_http_request_duration_seconds",
    "HTTP request duration",
    ["method", "path", "status"],
)


def setup_telemetry(otlp_endpoint: str, service_name: str = "openidp-api") -> None:
    resource = Resource.create({ResourceAttributes.SERVICE_NAME: service_name})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)


def get_tracer(name: str) -> trace.Tracer:
    return trace.get_tracer(name)


def instrument_sqlalchemy(engine: object) -> None:
    SQLAlchemyInstrumentor().instrument(engine=engine)


prometheus_app = make_asgi_app()
