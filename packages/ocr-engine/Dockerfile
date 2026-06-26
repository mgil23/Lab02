# SPDX-License-Identifier: AGPL-3.0-or-later
FROM python:3.12-slim AS base

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ORT_INTRA_THREADS=4 \
    ORT_INTER_THREADS=2

RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install uv && uv pip install --system .

# CPU target
FROM base AS cpu
ENV USE_GPU=false
COPY src ./src
EXPOSE 8001
CMD ["uvicorn", "src.ocr_engine.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "2"]

# GPU target (CUDA 12.1)
FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04 AS gpu-base
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    USE_GPU=true \
    ORT_INTRA_THREADS=8 \
    ORT_INTER_THREADS=4

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.12 \
    python3-pip \
    libglib2.0-0 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install uv && uv pip install --system ".[gpu]"

FROM gpu-base AS gpu
COPY src ./src
EXPOSE 8001
CMD ["uvicorn", "src.ocr_engine.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]
