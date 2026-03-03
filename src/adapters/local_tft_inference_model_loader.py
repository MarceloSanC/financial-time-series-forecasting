from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Any

from src.interfaces.tft_inference_model_loader import (
    LoadedTFTInferenceModel,
    TFTInferenceModelLoader,
)


class LocalTFTInferenceModelLoader(TFTInferenceModelLoader):
    """
    Loads a TFT model artifact directory produced by LocalTFTModelRepository.
    """

    @staticmethod
    def _load_json(path: Path, required: bool = True) -> dict[str, Any]:
        if not path.exists():
            if required:
                raise FileNotFoundError(f"Required model artifact not found: {path.resolve()}")
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"Expected JSON object in {path.resolve()}")
        return data

    def load(self, model_dir: str | Path) -> LoadedTFTInferenceModel:
        model_path = Path(model_dir)
        if not model_path.exists() or not model_path.is_dir():
            raise FileNotFoundError(f"Model directory not found: {model_path}")

        metadata = self._load_json(model_path / "metadata.json", required=True)
        config = self._load_json(model_path / "config.json", required=True)
        features_cfg = self._load_json(model_path / "features.json", required=True)

        features_used = features_cfg.get("features_used")
        if not isinstance(features_used, list) or not all(
            isinstance(c, str) and c.strip() for c in features_used
        ):
            raise ValueError(
                "Invalid features.json: expected non-empty list in `features_used`."
            )

        checkpoint_path = model_path / "checkpoints" / "best.ckpt"
        if not checkpoint_path.exists():
            raise FileNotFoundError(
                "Best checkpoint not found. Expected file: "
                f"{checkpoint_path.resolve()}"
            )

        try:
            from pytorch_forecasting import TemporalFusionTransformer
        except Exception as exc:
            raise RuntimeError(
                "pytorch-forecasting is required for TFT inference."
            ) from exc

        model = TemporalFusionTransformer.load_from_checkpoint(str(checkpoint_path))
        model.eval()

        scalers: dict[str, Any] = {}
        scalers_path = model_path / "scalers.pkl"
        if scalers_path.exists():
            with scalers_path.open("rb") as fp:
                loaded = pickle.load(fp)
            if isinstance(loaded, dict):
                scalers = loaded

        asset_id = str(metadata.get("asset_id") or "").strip().upper()
        version = str(metadata.get("version") or "").strip()
        if not asset_id:
            raise ValueError("metadata.json missing `asset_id`.")
        if not version:
            raise ValueError("metadata.json missing `version`.")

        training_config = config.get("training_config")
        if not isinstance(training_config, dict):
            training_config = config

        raw_tokens = config.get("feature_tokens")
        feature_tokens: list[str] = []
        if isinstance(raw_tokens, list):
            feature_tokens = [str(t).strip() for t in raw_tokens if str(t).strip()]
        elif isinstance(raw_tokens, str) and raw_tokens.strip():
            feature_tokens = [t.strip() for t in raw_tokens.split(",") if t.strip()]

        if feature_tokens:
            feature_set_name = "+".join(feature_tokens)
        else:
            feature_set_name = ",".join([c.strip() for c in features_used if c.strip()])

        return LoadedTFTInferenceModel(
            asset_id=asset_id,
            version=version,
            model_dir=model_path.resolve(),
            model=model,
            feature_cols=[c.strip() for c in features_used if c.strip()],
            feature_set_name=feature_set_name,
            feature_tokens=feature_tokens,
            training_config=training_config,
            scalers=scalers,
        )
