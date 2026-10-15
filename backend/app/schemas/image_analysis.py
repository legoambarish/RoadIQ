"""Runtime contract for Task C image observations.

This schema follows the planned ``image-analyses`` payload in ``docs/API_CONTRACT.md``.
Task D owns the HTTP request/response integration and may wrap this service payload.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ImageContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())


MeasurementStatus = Literal["observed", "estimated", "unavailable"]
MeasurementSource = Literal["image_inference", "user_input"]


class BinaryRLEMask(ImageContractModel):
    encoding: Literal["row_major_binary_rle_v1"]
    size_px: tuple[int, int] = Field(min_length=2, max_length=2)
    foreground_label: str = Field(min_length=1)
    counts: list[int] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_runs(self) -> BinaryRLEMask:
        height, width = self.size_px
        if height <= 0 or width <= 0 or any(count < 0 for count in self.counts):
            raise ValueError("mask dimensions and RLE counts must be non-negative, with positive dimensions")
        if sum(self.counts) != height * width:
            raise ValueError("binary RLE run lengths must cover exactly height_px * width_px pixels")
        return self


class ImageMeasurement(ImageContractModel):
    value: Any | None = None
    unit: str
    status: MeasurementStatus
    source: MeasurementSource | None = None
    reason: str | None = None

    @model_validator(mode="after")
    def validate_availability(self) -> ImageMeasurement:
        if self.status == "unavailable":
            if self.value is not None or self.source is not None:
                raise ValueError("unavailable image measurements require null value and source")
        elif self.value is None or self.source is None:
            raise ValueError("available image measurements require a value and source")
        return self


class ImageBox(ImageContractModel):
    x_min: float = Field(ge=0)
    y_min: float = Field(ge=0)
    x_max: float = Field(ge=0)
    y_max: float = Field(ge=0)

    @model_validator(mode="after")
    def validate_order(self) -> ImageBox:
        if self.x_max < self.x_min or self.y_max < self.y_min:
            raise ValueError("image box maxima must not precede minima")
        return self


class Detection(ImageContractModel):
    class_name: str = Field(alias="class", min_length=1)
    model_label: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    bbox_xyxy_px: ImageBox
    bbox_xyxy_normalized: ImageBox

    @model_validator(mode="after")
    def validate_normalized_box(self) -> Detection:
        if any(value > 1 for value in self.bbox_xyxy_normalized.model_dump().values()):
            raise ValueError("normalized bounding-box coordinates must be at most 1")
        return self


class DefectObservation(ImageContractModel):
    class_name: str = Field(alias="class", min_length=1)
    count: ImageMeasurement
    visible_area_ratio: ImageMeasurement
    confidence: float | None = Field(default=None, ge=0, le=1)
    annotation: ImageMeasurement
    detections: list[Detection] = Field(default_factory=list)
    mask_rle: BinaryRLEMask | None = None


class ImageAnalysisResponse(ImageContractModel):
    analysis_status: Literal["completed", "low_confidence", "unrated", "failed"]
    image: dict[str, Any]
    image_quality: dict[str, Any]
    pavement_region: dict[str, Any]
    surface_type: dict[str, Any]
    aggregate_analysis: dict[str, Any]
    defects: list[DefectObservation]
    metal_fragments: DefectObservation
    texture_features: dict[str, Any]
    calibration: dict[str, Any]
    processing_errors: list[dict[str, Any]]
    model: dict[str, Any]
    data_provenance: list[dict[str, str]]

