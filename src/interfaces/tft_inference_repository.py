from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from src.entities.tft_inference_record import TFTInferenceRecord


class TFTInferenceRepository(ABC):
    @abstractmethod
    def get_latest_timestamp(self, asset_id: str) -> datetime | None:
        """Return the latest inferred timestamp for the asset."""
        ...

    @abstractmethod
    def list_inference_timestamps(
        self,
        asset_id: str,
        start_date: datetime,
        end_date: datetime,
        *,
        model_version: str | None = None,
        feature_set_name: str | None = None,
    ) -> set[datetime]:
        """List persisted inference timestamps inside the given interval."""
        ...

    @abstractmethod
    def upsert_records(self, asset_id: str, records: list[TFTInferenceRecord]) -> int:
        """Persist inference rows and return attempted upserts in this call."""
        ...
