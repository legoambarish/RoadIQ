"""Deterministic, evidence-gated image-feature RSQI scoring.

This module consumes component-level measurements from a future vision pipeline. It does not
extract image features or invent normalization references. Callers must supply a versioned,
surface-type- and capture-profile-specific set of fixed reference ranges.
"""

from __future__ import annotations

import math
from typing import Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.road_segment import DataSource, ModeSuitability, QualityLabel

ComponentName = Literal[
    'visible_defect_burden',
    'aggregate_loss',
    'gap_anomaly',
    'texture_anomaly',
    'aggregate_distribution_anomaly',
]
SurfaceType = Literal['asphalt_bituminous', 'cement_concrete', 'unknown']
MeasurementStatus = Literal['observed', 'estimated', 'unavailable']
DamageDirection = Literal['higher_is_more_damage', 'lower_is_more_damage']
RSQIStatus = Literal['rated', 'low_confidence', 'unrated']

COMPONENTS: tuple[ComponentName, ...] = (
    'visible_defect_burden',
    'aggregate_loss',
    'gap_anomaly',
    'texture_anomaly',
    'aggregate_distribution_anomaly',
)

DEFAULT_WEIGHTS: dict[ComponentName, float] = {
    'visible_defect_burden': 0.35,
    'aggregate_loss': 0.20,
    'gap_anomaly': 0.15,
    'texture_anomaly': 0.15,
    'aggregate_distribution_anomaly': 0.15,
}

BASE_LIMITATIONS = (
    'Candidate weights and label cutoffs are provisional and have not been validated on a labelled RoadIQ dataset.',
    'Confidence is uncalibrated and spatial evidence coverage has no agreed denominator; both are null.',
    'RSQI describes image-based surface condition only; it does not establish safety, travel-mode suitability, structural strength, skid resistance, or physical roughness.',
)


class ScoringModel(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)


class NormalizationReference(ScoringModel):
    """Fixed reference interval for one component within a capture profile."""

    unit: str = Field(min_length=1, max_length=64)
    reference_min: float = Field(allow_inf_nan=False)
    reference_max: float = Field(allow_inf_nan=False)
    damage_direction: DamageDirection = 'higher_is_more_damage'

    @field_validator('reference_min', 'reference_max', mode='before')
    @classmethod
    def validate_numeric_bounds(cls, value: object) -> object:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError('normalization reference bounds must be numeric')
        return value

    @model_validator(mode='after')
    def validate_interval(self) -> NormalizationReference:
        if self.reference_min >= self.reference_max:
            raise ValueError('reference_min must be less than reference_max')
        return self


class NormalizationProfile(ScoringModel):
    """Frozen component references for one material and capture-condition profile."""

    profile_id: str = Field(min_length=1, max_length=64)
    reference_set_id: str = Field(min_length=1, max_length=128)
    surface_type: Literal['asphalt_bituminous', 'cement_concrete']
    capture_profile: str = Field(min_length=1, max_length=64)
    components: dict[ComponentName, NormalizationReference] = Field(default_factory=dict)


class ScoringConfig(ScoringModel):
    """Versioned weights, provisional labels, and caller-supplied frozen references."""

    version: str = Field(default='image-rsqi-candidate-v1', min_length=1, max_length=64)
    weights: dict[ComponentName, float] = Field(
        default_factory=lambda: DEFAULT_WEIGHTS.copy()
    )
    good_min: float = Field(default=80.0, ge=0, le=100, allow_inf_nan=False)
    fair_min: float = Field(default=60.0, ge=0, le=100, allow_inf_nan=False)
    poor_min: float = Field(default=40.0, ge=0, le=100, allow_inf_nan=False)
    normalization_profiles: tuple[NormalizationProfile, ...] = ()

    @field_validator('weights', mode='before')
    @classmethod
    def validate_numeric_weights(cls, value: object) -> object:
        if isinstance(value, Mapping):
            if any(
                isinstance(weight, bool) or not isinstance(weight, (int, float))
                for weight in value.values()
            ):
                raise ValueError('weights must be numeric values')
        return value

    @field_validator('good_min', 'fair_min', 'poor_min', mode='before')
    @classmethod
    def validate_numeric_thresholds(cls, value: object) -> object:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError('label thresholds must be numeric values')
        return value

    @model_validator(mode='after')
    def validate_config(self) -> ScoringConfig:
        if set(self.weights) != set(COMPONENTS):
            raise ValueError('weights must configure every RSQI component exactly once')
        if any(not math.isfinite(weight) or weight < 0 for weight in self.weights.values()):
            raise ValueError('weights must be finite and non-negative')
        if not math.isclose(math.fsum(self.weights.values()), 1.0, abs_tol=1e-9):
            raise ValueError('RSQI weights must sum to 1; weights are never renormalized')
        if not self.poor_min < self.fair_min < self.good_min:
            raise ValueError('label thresholds must satisfy poor_min < fair_min < good_min')

        profile_ids = [profile.profile_id for profile in self.normalization_profiles]
        profile_keys = [
            (profile.surface_type, profile.capture_profile)
            for profile in self.normalization_profiles
        ]
        if len(profile_ids) != len(set(profile_ids)):
            raise ValueError('normalization profile IDs must be unique')
        if len(profile_keys) != len(set(profile_keys)):
            raise ValueError('surface/capture normalization profiles must be unique')
        return self


class FeatureObservation(ScoringModel):
    """One caller-produced raw component metric with explicit unit and provenance."""

    value: float | None = Field(default=None, allow_inf_nan=False)
    unit: str = Field(min_length=1, max_length=64)
    status: MeasurementStatus = 'unavailable'
    source: DataSource | None = None

    @field_validator('value', mode='before')
    @classmethod
    def reject_boolean_measurements(cls, value: object) -> object:
        if isinstance(value, bool):
            raise ValueError('boolean values are not valid measurements')
        if value is not None and not isinstance(value, (int, float)):
            raise ValueError('measurements must be numeric values')
        return value

    @model_validator(mode='after')
    def validate_availability(self) -> FeatureObservation:
        if self.status == 'unavailable':
            if self.value is not None or self.source is not None:
                raise ValueError('unavailable observations require null value and source')
        elif self.value is None or self.source is None:
            raise ValueError('observed or estimated observations require value and source')
        if self.value is not None and self.unit == 'ratio' and not 0 <= self.value <= 1:
            raise ValueError('ratio measurements must be in [0, 1]')
        if (
            self.value is not None
            and self.unit == 'damage_index_0_100'
            and not 0 <= self.value <= 100
        ):
            raise ValueError('damage_index_0_100 measurements must be in [0, 100]')
        return self


class ScoringEvidence(ScoringModel):
    """Evidence and upstream gate decisions supplied by the vision/API boundary."""

    surface_type: SurfaceType = 'unknown'
    capture_profile: str | None = Field(default=None, min_length=1, max_length=64)
    image_quality_usable: bool | None = None
    usable_region_adequate: bool | None = None
    resolution_adequate: bool | None = None
    components: dict[ComponentName, FeatureObservation] = Field(default_factory=dict)

    @field_validator(
        'image_quality_usable', 'usable_region_adequate', 'resolution_adequate', mode='before'
    )
    @classmethod
    def validate_boolean_gates(cls, value: object) -> object:
        if value is not None and not isinstance(value, bool):
            raise ValueError('image quality, usable-region, and resolution gates must be booleans')
        return value


class ComponentScore(ScoringModel):
    value: float | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)
    unit: Literal['damage_index_0_100'] = 'damage_index_0_100'
    status: MeasurementStatus = 'unavailable'
    source: DataSource | None = None
    weight: float = Field(ge=0, le=1, allow_inf_nan=False)
    weighted_contribution: float | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)

    @model_validator(mode='after')
    def validate_availability(self) -> ComponentScore:
        if self.status == 'unavailable':
            if any(
                item is not None
                for item in (self.value, self.source, self.weighted_contribution)
            ):
                raise ValueError('unavailable normalized components require null value, source, and contribution')
        elif any(
            item is None for item in (self.value, self.source, self.weighted_contribution)
        ):
            raise ValueError('available normalized components require value, source, and contribution')
        return self


class RSQIResponse(ScoringModel):
    """The `rsqi` object from the proposed image-analysis API response."""

    value: float | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)
    unit: Literal['index_0_100'] = 'index_0_100'
    status: RSQIStatus
    confidence: None = None
    confidence_band: Literal['unrated'] | None
    components: dict[ComponentName, ComponentScore]
    explanation: str = Field(min_length=1)
    limitations: list[str]

    @model_validator(mode='after')
    def validate_result(self) -> RSQIResponse:
        if set(self.components) != set(COMPONENTS):
            raise ValueError('RSQI response must include every component exactly once')
        if self.status == 'unrated':
            if self.value is not None or self.confidence_band != 'unrated':
                raise ValueError('unrated RSQI requires null value and confidence_band="unrated"')
        else:
            if self.value is None or self.confidence_band is not None:
                raise ValueError('rated RSQI requires a score and an uncalibrated null confidence band')
            if any(component.status == 'unavailable' for component in self.components.values()):
                raise ValueError('rated RSQI requires every normalized component')
        return self


class ScoringResult(ScoringModel):
    """Scorer result plus metadata not yet represented in the proposed image API schema.

    `rsqi` serializes to the documented API object. `quality_label`, `scoring_version`, and
    `mode_suitability` are exposed separately for segment-contract consumers. Confidence and
    evidence coverage remain null until a calibration policy and denominator are agreed.
    """

    rsqi: RSQIResponse
    quality_label: QualityLabel | None
    scoring_version: str
    mode_suitability: ModeSuitability = Field(default_factory=ModeSuitability)
    evidence_coverage: float | None = None
    suitability_explanation: str


DEFAULT_SCORING_CONFIG = ScoringConfig()


def normalize_damage_component(
    value: float,
    reference: NormalizationReference,
) -> float:
    """Map a raw feature to the configured damage index, clamped to [0, 100]."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError('component value must be a finite number')
    try:
        value = float(value)
    except OverflowError as error:
        raise ValueError('component value must be a finite number') from error
    if not math.isfinite(value):
        raise ValueError('component value must be a finite number')
    scaled = (value - reference.reference_min) / (
        reference.reference_max - reference.reference_min
    )
    if reference.damage_direction == 'lower_is_more_damage':
        scaled = 1 - scaled
    return min(100.0, max(0.0, 100.0 * scaled))


def quality_label_for_score(
    score: float,
    config: ScoringConfig = DEFAULT_SCORING_CONFIG,
) -> QualityLabel:
    """Apply the configured provisional surface-quality thresholds."""

    if isinstance(score, bool) or not isinstance(score, (int, float)):
        raise ValueError('surface-quality score must be a finite number in [0, 100]')
    try:
        score = float(score)
    except OverflowError as error:
        raise ValueError('surface-quality score must be a finite number in [0, 100]') from error
    if not math.isfinite(score) or not 0 <= score <= 100:
        raise ValueError('surface-quality score must be a finite number in [0, 100]')
    if score >= config.good_min:
        return 'Good'
    if score >= config.fair_min:
        return 'Fair'
    if score >= config.poor_min:
        return 'Poor'
    return 'Very Poor'


def score_surface_quality(
    evidence: ScoringEvidence | Mapping[str, object],
    config: ScoringConfig | Mapping[str, object] = DEFAULT_SCORING_CONFIG,
) -> ScoringResult:
    """Score image-feature evidence using fixed caller-provided references and RSQI weights.

    No weights are renormalized when evidence is missing. Any failed or unavailable image gate,
    unknown surface, unresolved capture profile, missing component, or missing reference makes
    the overall result `unrated` with a null score.
    """

    parsed_evidence = (
        evidence
        if isinstance(evidence, ScoringEvidence)
        else ScoringEvidence.model_validate(evidence)
    )
    parsed_config = (
        config if isinstance(config, ScoringConfig) else ScoringConfig.model_validate(config)
    )

    reasons: list[str] = []
    if parsed_evidence.image_quality_usable is not True:
        reasons.append('image-quality gate did not pass or is unavailable')
    if parsed_evidence.surface_type == 'unknown':
        reasons.append('surface type is unknown')
    if parsed_evidence.usable_region_adequate is not True:
        reasons.append('usable pavement-region gate did not pass or is unavailable')
    if parsed_evidence.resolution_adequate is not True:
        reasons.append('effective-resolution gate did not pass or is unavailable')

    profile = _find_profile(parsed_evidence, parsed_config)
    if profile is None:
        if parsed_evidence.capture_profile is None:
            reasons.append('capture-condition profile is unavailable')
        elif parsed_evidence.surface_type != 'unknown':
            reasons.append(
                'no fixed normalization profile exists for this surface type and capture profile'
            )

    output_components: dict[ComponentName, ComponentScore] = {}
    for component_name in COMPONENTS:
        observation = parsed_evidence.components.get(component_name)
        reference = profile.components.get(component_name) if profile is not None else None
        weight = parsed_config.weights[component_name]

        if observation is None:
            reasons.append(f'{component_name}: measurement is missing')
            output_components[component_name] = _unavailable_component(weight)
            continue
        if observation.status == 'unavailable':
            reasons.append(f'{component_name}: measurement is explicitly unavailable')
            output_components[component_name] = _unavailable_component(weight)
            continue
        if reference is None:
            reasons.append(f'{component_name}: no fixed normalization reference is configured')
            output_components[component_name] = _unavailable_component(weight)
            continue
        if observation.unit != reference.unit:
            raise ValueError(
                f'{component_name} uses unit {observation.unit!r}; '
                f'configured reference requires {reference.unit!r}'
            )

        assert observation.value is not None and observation.source is not None
        normalized = normalize_damage_component(observation.value, reference)
        output_components[component_name] = ComponentScore(
            value=normalized,
            status=observation.status,
            source=observation.source,
            weight=weight,
            weighted_contribution=normalized * weight,
        )

    has_all_components = all(
        output_components[name].status != 'unavailable' for name in COMPONENTS
    )
    is_rated = not reasons and has_all_components
    score: float | None = None
    label: QualityLabel | None = None
    if is_rated:
        damage = math.fsum(
            output_components[name].weighted_contribution or 0.0 for name in COMPONENTS
        )
        score = min(100.0, max(0.0, 100.0 - damage))
        label = quality_label_for_score(score, parsed_config)

    limitations = list(BASE_LIMITATIONS)
    if reasons:
        limitations.extend(reasons)
        explanation = (
            f'Unrated under scoring configuration {parsed_config.version}; no numeric score was '
            'assigned. ' + '; '.join(reasons) + '. Missing evidence was not treated as zero, '
            'and weights were not renormalized.'
        )
    else:
        contributions = '; '.join(
            f'{name} {output_components[name].value:.2f} × '
            f'{output_components[name].weight:.2f} = '
            f'{output_components[name].weighted_contribution:.2f}'
            for name in COMPONENTS
        )
        explanation = (
            f'Provisional RSQI {score:.2f}/100 ({label}) using scoring configuration '
            f'{parsed_config.version}. Weighted damage contributions: {contributions}. '
            'Confidence and spatial evidence coverage are not calibrated.'
        )

    rsqi = RSQIResponse(
        value=score,
        status='rated' if is_rated else 'unrated',
        confidence=None,
        confidence_band=None if is_rated else 'unrated',
        components=output_components,
        explanation=explanation,
        limitations=limitations,
    )
    return ScoringResult(
        rsqi=rsqi,
        quality_label=label,
        scoring_version=parsed_config.version,
        mode_suitability=ModeSuitability(),
        evidence_coverage=None,
        suitability_explanation=(
            'No mode-specific formula or evidence requirements are agreed; all mode scores remain '
            'unknown. Surface quality is not a travel-suitability assessment.'
        ),
    )


def _find_profile(
    evidence: ScoringEvidence,
    config: ScoringConfig,
) -> NormalizationProfile | None:
    if evidence.surface_type == 'unknown' or evidence.capture_profile is None:
        return None
    return next(
        (
            profile
            for profile in config.normalization_profiles
            if profile.surface_type == evidence.surface_type
            and profile.capture_profile == evidence.capture_profile
        ),
        None,
    )


def _unavailable_component(weight: float) -> ComponentScore:
    return ComponentScore(
        value=None,
        status='unavailable',
        source=None,
        weight=weight,
        weighted_contribution=None,
    )
