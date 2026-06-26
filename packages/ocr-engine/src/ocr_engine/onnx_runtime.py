# SPDX-License-Identifier: AGPL-3.0-or-later
"""ONNX Runtime session management with CPU/GPU auto-detect."""
import os
from pathlib import Path

_USE_GPU = os.environ.get("USE_GPU", "false").lower() == "true"


def get_execution_providers() -> list[str]:
    """Return ordered list of ONNX execution providers."""
    if _USE_GPU:
        try:
            import onnxruntime as ort
            available = ort.get_available_providers()
            if "CUDAExecutionProvider" in available:
                return ["CUDAExecutionProvider", "CPUExecutionProvider"]
            if "TensorrtExecutionProvider" in available:
                return ["TensorrtExecutionProvider", "CPUExecutionProvider"]
        except Exception:
            pass
    return ["CPUExecutionProvider"]


def create_onnx_session(model_path: str | Path) -> object:
    """Create an ONNX Runtime InferenceSession with appropriate providers."""
    import onnxruntime as ort

    providers = get_execution_providers()
    session_options = ort.SessionOptions()

    intra_threads = int(os.environ.get("ORT_INTRA_THREADS", "4"))
    inter_threads = int(os.environ.get("ORT_INTER_THREADS", "2"))
    session_options.intra_op_num_threads = intra_threads
    session_options.inter_op_num_threads = inter_threads
    session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    session_options.enable_mem_pattern = True
    session_options.enable_cpu_mem_arena = True

    return ort.InferenceSession(str(model_path), session_options, providers=providers)
