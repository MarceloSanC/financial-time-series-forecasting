from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

from src.entities.tft_inference_record import TFTInferenceRecord


class TFTInferenceEngine(ABC):
    @abstractmethod
    def infer(
        self,
        *,
        model: Any,
        dataset_df: pd.DataFrame,
        asset_id: str,
        model_version: str,
        model_path: str,
        feature_set_name: str,
        features_used_csv: str,
        feature_cols: list[str],
        dataset_parameters: dict[str, Any] | None,
        max_encoder_length: int,
        max_prediction_length: int,
        batch_size: int,
        run_id: str,
    ) -> list[TFTInferenceRecord]:
        """Run TFT inference over a dataset slice and return prediction records."""
        ...
