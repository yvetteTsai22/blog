"""Local embedding (spec §4.3): e5 via fastembed, with `query:` / `passage:` prefixes.

Runs on this machine only; no text leaves it. Vectors are L2-normalised so a dot product
is cosine similarity.
"""
from __future__ import annotations

from typing import Protocol, Sequence

import numpy as np


class Embedder(Protocol):
    def queries(self, texts: Sequence[str]) -> np.ndarray: ...
    def passages(self, texts: Sequence[str]) -> np.ndarray: ...


def _normalise(m: np.ndarray) -> np.ndarray:
    m = np.asarray(m, dtype=np.float32)
    if m.size == 0:
        return m.reshape(0, 0)
    norms = np.linalg.norm(m, axis=1, keepdims=True)
    return m / np.where(norms == 0, 1, norms)


# Models fastembed does not ship but that have an ONNX export on the HF Hub.
CUSTOM_MODELS = {"intfloat/multilingual-e5-small": {"dim": 384, "model_file": "onnx/model.onnx"}}


def _register(model: str) -> None:
    from fastembed import TextEmbedding
    from fastembed.common.model_description import ModelSource, PoolingType

    spec = CUSTOM_MODELS.get(model)
    if not spec or any(m["model"] == model for m in TextEmbedding.list_supported_models()):
        return
    TextEmbedding.add_custom_model(
        model=model, pooling=PoolingType.MEAN, normalization=True,
        sources=ModelSource(hf=model), dim=spec["dim"], model_file=spec["model_file"],
    )


class FastEmbedE5:
    def __init__(self, model: str, cache_dir: str | None = None):
        from fastembed import TextEmbedding  # imported lazily: heavy, and tests use a fake

        _register(model)
        self._model = TextEmbedding(model_name=model, cache_dir=cache_dir)
        self._e5 = "e5" in model.lower()

    def _embed(self, prefix: str, texts: Sequence[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, 0), dtype=np.float32)
        pre = prefix if self._e5 else ""
        return _normalise(np.array(list(self._model.embed([pre + t for t in texts]))))

    def queries(self, texts):
        return self._embed("query: ", texts)

    def passages(self, texts):
        return self._embed("passage: ", texts)
