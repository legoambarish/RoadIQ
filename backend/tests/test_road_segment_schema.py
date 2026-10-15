from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.fixtures.sample_road_segments import get_sample_road_segment
from app.schemas.road_segment import RoadSegment


def test_sample_segment_uses_explicit_unknown_values() -> None:
    segment = get_sample_road_segment()

    assert segment.segment_id == 'seg-demo-001'
    assert segment.geometry.type == 'LineString'
    assert segment.measurements.roughness_iri.value is None
    assert segment.measurements.roughness_iri.status == 'unavailable'
    assert segment.surface_quality_score is None
    assert segment.assessment_status == 'unrated'


def test_validated_segment_preserves_geojson_order_and_units() -> None:
    payload = unrated_payload()
    payload['measurements'] = {
        'defect_count': {
            'value': 3,
            'unit': 'defects',
            'status': 'observed',
            'source': 'sensor',
        }
    }

    segment = RoadSegment.model_validate(payload)

    assert segment.geometry.coordinates[0] == (-74.006, 40.7128)
    assert segment.measurements.defect_count.value == 3
    assert segment.measurements.defect_count.unit == 'defects'


@pytest.mark.parametrize(
    'measurement',
    [
        {'value': 0, 'unit': 'defects', 'status': 'unavailable', 'source': None},
        {'value': 3, 'unit': 'defects', 'status': 'observed', 'source': None},
    ],
)
def test_measurement_rejects_silent_zero_and_missing_provenance(
    measurement: dict[str, object],
) -> None:
    payload = unrated_payload()
    payload['measurements'] = {'defect_count': measurement}

    with pytest.raises(ValidationError):
        RoadSegment.model_validate(payload)


def test_measurement_rejects_wrong_units_and_out_of_range_values() -> None:
    payload = unrated_payload()
    payload['measurements'] = {
        'damaged_area_ratio': {
            'value': 1.2,
            'unit': 'ratio',
            'status': 'estimated',
            'source': 'image_inference',
        }
    }

    with pytest.raises(ValidationError):
        RoadSegment.model_validate(payload)

    payload['measurements'] = {
        'roughness_iri': {
            'value': 2,
            'unit': 'percent',
            'status': 'observed',
            'source': 'sensor',
        }
    }
    with pytest.raises(ValidationError):
        RoadSegment.model_validate(payload)


def test_geometry_requires_valid_geojson_linestring_positions() -> None:
    payload = unrated_payload()
    payload['geometry'] = {'type': 'LineString', 'coordinates': [[181, 40], [0, 0]]}
    with pytest.raises(ValidationError):
        RoadSegment.model_validate(payload)

    payload['geometry'] = {'type': 'LineString', 'coordinates': [[0, 0]]}
    with pytest.raises(ValidationError):
        RoadSegment.model_validate(payload)


def test_rated_segment_requires_all_normalized_components() -> None:
    payload = unrated_payload()
    payload.update(
        {
            'assessment_status': 'rated',
            'surface_quality_score': 85,
            'quality_label': 'Good',
        }
    )

    with pytest.raises(ValidationError):
        RoadSegment.model_validate(payload)


def test_rated_segment_accepts_provisional_label_and_timezone() -> None:
    payload = unrated_payload()
    payload.update(
        {
            'damage_components': {
                'damaged_area': 10,
                'defect_density': 20,
                'severity': 20,
                'roughness': 30,
            },
            'surface_quality_score': 85,
            'quality_label': 'Good',
            'assessment_status': 'rated',
        }
    )

    segment = RoadSegment.model_validate(payload)
    assert segment.quality_label == 'Good'

    payload['surveyed_at'] = datetime(2026, 10, 15, 12, 0).isoformat()
    with pytest.raises(ValidationError):
        RoadSegment.model_validate(payload)


def unrated_payload() -> dict[str, object]:
    return {
        'segment_id': 'seg-demo-001',
        'geometry': {
            'type': 'LineString',
            'coordinates': [[-74.006, 40.7128], [-74.005, 40.7138]],
        },
        'survey_source': 'demo fixture',
        'surveyed_at': datetime(2026, 10, 15, 12, 0, tzinfo=timezone.utc).isoformat(),
        'assessment_status': 'unrated',
        'explanation': 'Fixture only; no quality rating is inferred from missing evidence.',
        'data_provenance': [{'field_path': 'geometry', 'source': 'demo_fixture'}],
    }
