from __future__ import annotations

from collections.abc import Mapping

import pytest
from pydantic import ValidationError

from app.schemas.road_segment import ModeSuitability
from app.services.scoring import (
    COMPONENTS,
    DEFAULT_WEIGHTS,
    FeatureObservation,
    NormalizationProfile,
    NormalizationReference,
    ScoringConfig,
    ScoringEvidence,
    normalize_damage_component,
    quality_label_for_score,
    score_surface_quality,
)


def test_known_inputs_follow_documented_weighted_damage_formula() -> None:
    inputs = {
        'visible_defect_burden': 0.2,
        'aggregate_loss': 0.1,
        'gap_anomaly': 0.4,
        'texture_anomaly': 0.5,
        'aggregate_distribution_anomaly': 0.6,
    }

    result = score_surface_quality(evidence(inputs), scoring_config())

    assert result.rsqi.value == pytest.approx(68.5)
    assert result.rsqi.status == 'rated'
    assert result.quality_label == 'Fair'
    assert result.rsqi.components['visible_defect_burden'].value == pytest.approx(20)
    assert result.rsqi.components['visible_defect_burden'].weighted_contribution == pytest.approx(7)
    assert result.rsqi.components['aggregate_distribution_anomaly'].weighted_contribution == pytest.approx(9)
    assert 'visible_defect_burden 20.00 × 0.35 = 7.00' in result.rsqi.explanation
    assert result.scoring_version == 'test-candidate-v1'


@pytest.mark.parametrize(
    ('value', 'expected_score', 'expected_label'),
    [(0, 100, 'Good'), (1, 0, 'Very Poor')],
)
def test_overall_score_extreme_boundaries(
    value: float,
    expected_score: float,
    expected_label: str,
) -> None:
    result = score_surface_quality(
        evidence({name: value for name in COMPONENTS}),
        scoring_config(),
    )

    assert result.rsqi.value == pytest.approx(expected_score)
    assert result.quality_label == expected_label


@pytest.mark.parametrize(
    ('score', 'label'),
    [
        (100, 'Good'),
        (80, 'Good'),
        (79.999, 'Fair'),
        (60, 'Fair'),
        (59.999, 'Poor'),
        (40, 'Poor'),
        (39.999, 'Very Poor'),
        (0, 'Very Poor'),
    ],
)
def test_provisional_label_threshold_boundaries(score: float, label: str) -> None:
    assert quality_label_for_score(score) == label


def test_configurable_label_thresholds_are_used() -> None:
    config = ScoringConfig(good_min=90, fair_min=70, poor_min=30)

    assert quality_label_for_score(90, config) == 'Good'
    assert quality_label_for_score(70, config) == 'Fair'
    assert quality_label_for_score(30, config) == 'Poor'
    assert quality_label_for_score(29.99, config) == 'Very Poor'


@pytest.mark.parametrize(
    ('value', 'direction', 'expected'),
    [
        (0, 'higher_is_more_damage', 0),
        (1, 'higher_is_more_damage', 0),
        (2, 'higher_is_more_damage', 50),
        (3, 'higher_is_more_damage', 100),
        (4, 'higher_is_more_damage', 100),
        (1, 'lower_is_more_damage', 100),
        (2, 'lower_is_more_damage', 50),
        (3, 'lower_is_more_damage', 0),
    ],
)
def test_normalization_maps_boundaries_and_clamps(
    value: float,
    direction: str,
    expected: float,
) -> None:
    reference = NormalizationReference(
        unit='metric_units',
        reference_min=1,
        reference_max=3,
        damage_direction=direction,
    )

    assert normalize_damage_component(value, reference) == pytest.approx(expected)


def test_normalization_reference_rejects_invalid_interval_and_nonfinite_values() -> None:
    with pytest.raises(ValidationError):
        NormalizationReference(unit='ratio', reference_min=1, reference_max=1)
    with pytest.raises(ValidationError):
        NormalizationReference(unit='ratio', reference_min=2, reference_max=1)
    with pytest.raises(ValidationError):
        NormalizationReference(unit='ratio', reference_min=float('nan'), reference_max=1)
    with pytest.raises(ValidationError, match='must be numeric'):
        NormalizationReference(unit='ratio', reference_min=True, reference_max=2)
    with pytest.raises(ValueError, match='finite number'):
        normalize_damage_component(float('inf'), NormalizationReference(
            unit='ratio', reference_min=0, reference_max=1
        ))
    with pytest.raises(ValueError, match='finite number'):
        normalize_damage_component('1', NormalizationReference(
            unit='ratio', reference_min=0, reference_max=1
        ))  # type: ignore[arg-type]


def test_missing_component_makes_result_unrated_without_weight_renormalization() -> None:
    values = {
        'visible_defect_burden': 0.2,
        'aggregate_loss': 0.1,
        'gap_anomaly': 0.4,
        'texture_anomaly': 0.5,
    }

    result = score_surface_quality(evidence(values), scoring_config())

    assert result.rsqi.status == 'unrated'
    assert result.rsqi.value is None
    assert result.quality_label is None
    missing = result.rsqi.components['aggregate_distribution_anomaly']
    assert missing.value is None
    assert missing.source is None
    assert missing.status == 'unavailable'
    assert missing.weight == DEFAULT_WEIGHTS['aggregate_distribution_anomaly']
    assert missing.weighted_contribution is None
    assert result.rsqi.components['visible_defect_burden'].weighted_contribution == pytest.approx(7)
    assert 'aggregate_distribution_anomaly: measurement is missing' in result.rsqi.explanation
    assert 'weights were not renormalized' in result.rsqi.explanation


def test_explicitly_unavailable_measurement_stays_null() -> None:
    inputs = evidence({name: 0.25 for name in COMPONENTS})
    components = dict(inputs['components'])
    components['gap_anomaly'] = {
        'value': None,
        'unit': 'ratio',
        'status': 'unavailable',
        'source': None,
    }
    inputs['components'] = components

    result = score_surface_quality(inputs, scoring_config())

    assert result.rsqi.status == 'unrated'
    assert result.rsqi.value is None
    assert result.rsqi.components['gap_anomaly'].value is None
    assert result.rsqi.components['gap_anomaly'].weighted_contribution is None
    assert 'gap_anomaly: measurement is explicitly unavailable' in result.rsqi.explanation


@pytest.mark.parametrize(
    ('change', 'reason'),
    [
        ({'image_quality_usable': False}, 'image-quality gate did not pass'),
        ({'image_quality_usable': None}, 'image-quality gate did not pass or is unavailable'),
        ({'surface_type': 'unknown'}, 'surface type is unknown'),
        ({'usable_region_adequate': False}, 'usable pavement-region gate did not pass'),
        ({'resolution_adequate': None}, 'effective-resolution gate did not pass or is unavailable'),
        ({'capture_profile': None}, 'capture-condition profile is unavailable'),
        ({'capture_profile': 'other-camera'}, 'no fixed normalization profile exists'),
    ],
)
def test_failed_or_unknown_evidence_gates_return_unrated(
    change: dict[str, object],
    reason: str,
) -> None:
    result = score_surface_quality(evidence({name: 0.25 for name in COMPONENTS}, **change), scoring_config())

    assert result.rsqi.status == 'unrated'
    assert result.rsqi.value is None
    assert result.rsqi.confidence is None
    assert result.rsqi.confidence_band == 'unrated'
    assert reason in result.rsqi.explanation


def test_default_config_does_not_invent_normalization_references() -> None:
    result = score_surface_quality(evidence({name: 0.25 for name in COMPONENTS}))

    assert result.rsqi.status == 'unrated'
    assert result.rsqi.value is None
    assert all(component.status == 'unavailable' for component in result.rsqi.components.values())
    assert 'no fixed normalization profile exists' in result.rsqi.explanation


def test_surface_and_capture_profile_references_are_not_shared_implicitly() -> None:
    result = score_surface_quality(
        evidence({name: 0.25 for name in COMPONENTS}, surface_type='cement_concrete'),
        scoring_config(),
    )

    assert result.rsqi.status == 'unrated'
    assert result.rsqi.value is None
    assert 'no fixed normalization profile exists' in result.rsqi.explanation


def test_invalid_component_unit_is_rejected_instead_of_guessed() -> None:
    inputs = evidence({name: 0.25 for name in COMPONENTS})
    components = dict(inputs['components'])
    components['visible_defect_burden'] = {
        'value': 0.25,
        'unit': 'pixels',
        'status': 'observed',
        'source': 'image_inference',
    }
    inputs['components'] = components

    with pytest.raises(ValueError, match='configured reference requires'):
        score_surface_quality(inputs, scoring_config())


@pytest.mark.parametrize(
    'observation',
    [
        {'value': None, 'unit': 'ratio', 'status': 'observed', 'source': 'image_inference'},
        {'value': 0.25, 'unit': 'ratio', 'status': 'unavailable', 'source': None},
        {'value': 1.1, 'unit': 'ratio', 'status': 'observed', 'source': 'image_inference'},
        {'value': True, 'unit': 'ratio', 'status': 'observed', 'source': 'image_inference'},
        {'value': 0.25, 'unit': 'ratio', 'status': 'observed', 'source': None},
        {'value': 0.25, 'unit': 'ratio', 'status': 'observed', 'source': 'unknown_source'},
        {'value': '0.25', 'unit': 'ratio', 'status': 'observed', 'source': 'image_inference'},
    ],
)
def test_invalid_measurements_availability_units_and_sources_are_rejected(
    observation: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        FeatureObservation.model_validate(observation)


def test_weights_must_cover_all_components_and_sum_to_one() -> None:
    with pytest.raises(ValidationError, match='must sum to 1'):
        ScoringConfig(weights={name: weight * 0.9 for name, weight in DEFAULT_WEIGHTS.items()})
    with pytest.raises(ValidationError, match='exactly once'):
        ScoringConfig(weights={'visible_defect_burden': 1})
    invalid_weights = DEFAULT_WEIGHTS.copy()
    invalid_weights['visible_defect_burden'] = True
    with pytest.raises(ValidationError, match='must be numeric'):
        ScoringConfig(weights=invalid_weights)


def test_invalid_gates_and_score_labels_are_rejected() -> None:
    with pytest.raises(ValidationError):
        ScoringEvidence.model_validate({'image_quality_usable': 1})
    with pytest.raises(ValueError):
        quality_label_for_score(float('nan'))
    with pytest.raises(ValueError):
        quality_label_for_score(100.1)
    with pytest.raises(ValueError, match='finite number'):
        quality_label_for_score('85')  # type: ignore[arg-type]


def test_confidence_coverage_and_each_travel_mode_remain_unknown() -> None:
    result = score_surface_quality(
        evidence({name: 0.25 for name in COMPONENTS}),
        scoring_config(),
    )

    assert result.rsqi.confidence is None
    assert result.evidence_coverage is None
    assert 'Confidence is uncalibrated' in result.rsqi.limitations[1]
    assert 'spatial evidence coverage has no agreed denominator' in result.rsqi.limitations[1]
    assert isinstance(result.mode_suitability, ModeSuitability)
    assert result.mode_suitability.model_dump() == {
        'walking': None,
        'cycling': None,
        'two_wheeler': None,
        'car': None,
        'bus': None,
    }
    assert 'No mode-specific formula' in result.suitability_explanation


@pytest.mark.parametrize('mode', ['walking', 'cycling', 'two_wheeler', 'car', 'bus'])
def test_each_supported_mode_is_present_and_unscored(mode: str) -> None:
    result = score_surface_quality(
        evidence({name: 0.25 for name in COMPONENTS}),
        scoring_config(),
    )

    assert getattr(result.mode_suitability, mode) is None


def test_repeated_scoring_is_deterministic() -> None:
    inputs = evidence({name: 0.25 for name in COMPONENTS})
    config = scoring_config()

    first = score_surface_quality(inputs, config)
    second = score_surface_quality(inputs, config)

    assert first.model_dump(mode='json') == second.model_dump(mode='json')


def test_rsqi_serialization_matches_proposed_api_contract_shape() -> None:
    result = score_surface_quality(
        evidence({name: 0.25 for name in COMPONENTS}),
        scoring_config(),
    )
    rsqi_payload = result.rsqi.model_dump(mode='json')

    assert set(rsqi_payload) == {
        'value',
        'unit',
        'status',
        'confidence',
        'confidence_band',
        'components',
        'explanation',
        'limitations',
    }
    assert set(rsqi_payload['components']) == set(COMPONENTS)
    for component in rsqi_payload['components'].values():
        assert set(component) == {
            'value',
            'unit',
            'status',
            'source',
            'weight',
            'weighted_contribution',
        }
    assert set(result.mode_suitability.model_dump()) == set(ModeSuitability.model_fields)


def test_non_mapping_inputs_are_rejected() -> None:
    with pytest.raises(ValidationError):
        score_surface_quality('not evidence')  # type: ignore[arg-type]


def evidence(
    values: Mapping[str, float],
    **overrides: object,
) -> dict[str, object]:
    payload: dict[str, object] = {
        'surface_type': 'asphalt_bituminous',
        'capture_profile': 'close-daylight-v1',
        'image_quality_usable': True,
        'usable_region_adequate': True,
        'resolution_adequate': True,
        'components': {
            name: {
                'value': value,
                'unit': 'ratio',
                'status': 'observed',
                'source': 'image_inference',
            }
            for name, value in values.items()
        },
    }
    payload.update(overrides)
    return payload


def scoring_config() -> ScoringConfig:
    return ScoringConfig(
        version='test-candidate-v1',
        normalization_profiles=(
            NormalizationProfile(
                profile_id='synthetic-asphalt-profile',
                reference_set_id='synthetic-test-values-only',
                surface_type='asphalt_bituminous',
                capture_profile='close-daylight-v1',
                components={
                    name: NormalizationReference(
                        unit='ratio',
                        reference_min=0,
                        reference_max=1,
                    )
                    for name in COMPONENTS
                },
            ),
        ),
    )
