#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# Download PaddleOCR ONNX models for the OCR engine.
# Usage: ./scripts/download_models.sh [output_dir]

set -euo pipefail

OUTPUT_DIR="${1:-packages/ocr-engine/models}"
mkdir -p "${OUTPUT_DIR}/det" "${OUTPUT_DIR}/rec" "${OUTPUT_DIR}/cls"

echo "Downloading PaddleOCR ONNX models to ${OUTPUT_DIR}..."

BASE_URL="https://paddleocr.bj.bcebos.com/PP-OCRv4/english"

# Detection model
if [ ! -f "${OUTPUT_DIR}/det/model.onnx" ]; then
    echo "  → Detection model..."
    curl -fsSL "${BASE_URL}/en_PP-OCRv4_det_infer.tar" | tar -xz -C "${OUTPUT_DIR}/det/" --strip-components=1
fi

# Recognition model
if [ ! -f "${OUTPUT_DIR}/rec/model.onnx" ]; then
    echo "  → Recognition model..."
    curl -fsSL "${BASE_URL}/en_PP-OCRv4_rec_infer.tar" | tar -xz -C "${OUTPUT_DIR}/rec/" --strip-components=1
fi

# Classification model
if [ ! -f "${OUTPUT_DIR}/cls/model.onnx" ]; then
    echo "  → Classification model..."
    curl -fsSL "https://paddleocr.bj.bcebos.com/dygraph_v2.0/ch/ch_ppocr_mobile_v2.0_cls_infer.tar" \
        | tar -xz -C "${OUTPUT_DIR}/cls/" --strip-components=1
fi

echo "Models downloaded successfully."
ls -la "${OUTPUT_DIR}/det/" "${OUTPUT_DIR}/rec/" "${OUTPUT_DIR}/cls/"
