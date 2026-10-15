from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

DataSource = Literal['sensor', 'image_inference', 'user_input', 'demo_fixture']
MeasurementStatus = Literal['observed', 'estimated', 'unavailable']
MeasurementUnit = Literal[
    'defects',
    'defects_per_km',
    'ratio',
    'severity_index_0_100',
    'm_per_km',
    'percent',
]
QualityLabel = Literal['Good', 'Fair', 'Poor', 'Very Poor']
TravelMode = Literal['walking', 'cycling', 'two_wheeler', 'car', 'bus']


class ContractModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class GeoJSONLineString(ContractModel):
    type: Literal['LineString']
    coordinates: list[tuple[float, float]] = Field(min_length=2)

    @model_validator(mode='after')
    def validate_coordinates(self) -> GeoJSONLineString:
        for longitude, latitude in self.coordinates:
            if not -180 <= longitude <= 180:
                raise ValueError('GeoJSON longitude must be between -180 and 180')
            if not -90 <= latitude <= 90:
                raise ValueError('GeoJSON latitude must be between -90 and 90')
        return self


class Measurement(ContractModel):
    value: float | None = Field(default=None, allow_inf_nan=False)
    unit: MeasurementUnit
    status: MeasurementStatus = 'unavailable'
    source: DataSource | None = None

    @model_validator(mode='after')
    def validate_availability(self) -> Measurement:
        if self.status == 'unavailable':
            if self.value is not None or self.source is not None:
                raise ValueError('unavailable measurements must have null value and source')
        elif self.value is None or self.source is None:
            raise ValueError('observed and estimated measurements require a value and source')
        return self


class RoadMeasurements(ContractModel):
    defect_count: Measurement = Field(
        default_factory=lambda: Measurement(unit='defects')
    )
    defect_density: Measurement = Field(
        default_factory=lambda: Measurement(unit='defects_per_km')
    )
    damaged_area_ratio: Measurement = Field(default_factory=lambda: Measurement(unit='ratio'))
    severity: Measurement = Field(default_factory=lambda: Measurement(unit='severity_index_0_100'))
    roughness_iri: Measurement = Field(default_factory=lambda: Measurement(unit='m_per_km'))
    longitudinal_grade: Measurement = Field(default_factory=lambda: Measurement(unit='percent'))
    crossfall: Measurement = Field(default_factory=lambda: Measurement(unit='percent'))

    @model_validator(mode='after')
    def validate_units_and_ranges(self) -> RoadMeasurements:
        expected_units: dict[str, MeasurementUnit] = {
            'defect_count': 'defects',
            'defect_density': 'defects_per_km',
            'damaged_area_ratio': 'ratio',
            'severity': 'severity_index_0_100',
            'roughness_iri': 'm_per_km',
            'longitudinal_grade': 'percent',
            'crossfall': 'percent',
        }
        for field_name, expected_unit in expected_units.items():
            measurement = getattr(self, field_name)
            if measurement.unit != expected_unit:
                raise ValueError(f'{field_name} must use unit {expected_unit}')
            if measurement.value is None:
                continue
            if field_name == 'defect_count' and not measurement.value.is_integer():
                raise ValueError('defect_count must be a whole number')
            if field_name in {'defect_count', 'defect_density', 'roughness_iri'} and measurement.value < 0:
                raise ValueError(f'{field_name} cannot be negative')
            if field_name == 'damaged_area_ratio' and not 0 <= measurement.value <= 1:
                raise ValueError('damaged_area_ratio must be between 0 and 1')
            if field_name == 'severity' and not 0 <= measurement.value <= 100:
                raise ValueError('severity must be between 0 and 100')
        return self


class DamageComponents(ContractModel):
    damaged_area: float | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)
    defect_density: float | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)
    severity: float | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)
    roughness: float | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)


class ModeSuitability(ContractModel):
    walking: float | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)
    cycling: float | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)
    two_wheeler: float | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)
    car: float | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)
    bus: float | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)


class PedestrianContext(ContractModel):
    footpath_present: bool | None = None
    crossings_observed: bool | None = None
    comfort_score: float | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)


class ProvenanceEntry(ContractModel):
    field_path: str = Field(min_length=1, max_length=128)
    source: DataSource


class RoadSegment(ContractModel):
    segment_id: str = Field(min_length=1, max_length=64, pattern=r'^[A-Za-z0-9_-]+$')
    geometry: GeoJSONLineString
    survey_source: str = Field(min_length=1, max_length=128)
    surveyed_at: datetime
    measurements: RoadMeasurements = Field(default_factory=RoadMeasurements)
    damage_components: DamageComponents = Field(default_factory=DamageComponents)
    surface_quality_score: float | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)
    quality_label: QualityLabel | None = None
    mode_suitability: ModeSuitability = Field(default_factory=ModeSuitability)
    pedestrian_context: PedestrianContext = Field(default_factory=PedestrianContext)
    confidence: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    evidence_coverage: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    assessment_status: Literal['rated', 'unrated']
    explanation: str = Field(min_length=1, max_length=2000)
    data_provenance: list[ProvenanceEntry] = Field(default_factory=list)

    @model_validator(mode='after')
    def validate_assessment(self) -> RoadSegment:
        if self.surveyed_at.utcoffset() is None:
            raise ValueError('surveyed_at must include a timezone')

        if self.assessment_status == 'unrated':
            if self.surface_quality_score is not None or self.quality_label is not None:
                raise ValueError('unrated segments must have null surface score and quality label')
            return self

        if self.surface_quality_score is None or self.quality_label is None:
            raise ValueError('rated segments require a surface score and quality label')
        components = self.damage_components
        if any(
            value is None
            for value in (
                components.damaged_area,
                components.defect_density,
                components.severity,
                components.roughness,
            )
        ):
            raise ValueError('rated segments require all four normalized damage components')

        score = self.surface_quality_score
        expected_label: QualityLabel
        if score >= 80:
            expected_label = 'Good'
        elif score >= 60:
            expected_label = 'Fair'
        elif score >= 40:
            expected_label = 'Poor'
        else:
            expected_label = 'Very Poor'
        if self.quality_label != expected_label:
            raise ValueError('quality_label does not match the provisional score thresholds')
        return self
