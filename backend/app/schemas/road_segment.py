from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Coordinate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)


class RoadSegment(BaseModel):
    model_config = ConfigDict(extra='forbid')

    segment_id: str = Field(..., min_length=1, max_length=64, pattern=r'^[A-Za-z0-9_-]+$')
    start: Coordinate
    end: Coordinate
    quality_score: float = Field(..., ge=0.0, le=100.0)
    quality_class: Literal['poor', 'fair', 'good', 'excellent']
    scoring_method: str | None = Field(default=None, max_length=64)
    observed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode='after')
    def validate_quality_class(self) -> 'RoadSegment':
        """Placeholder quality mapping used until the production scoring model is approved.

        The score range is defined as 0-100, with higher scores indicating better road condition.
        """
        thresholds = [
            (0.0, 25.0, 'poor'),
            (25.0, 50.0, 'fair'),
            (50.0, 75.0, 'good'),
            (75.0, 100.1, 'excellent'),
        ]

        label_for_score = next(label for lower, upper, label in thresholds if lower <= self.quality_score < upper)
        if self.quality_score >= 100.0:
            label_for_score = 'excellent'

        if self.quality_class != label_for_score:
            raise ValueError(
                'quality_class does not match the placeholder score range: '
                f'{self.quality_score} -> {label_for_score}'
            )

        return self
