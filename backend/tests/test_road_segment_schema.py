from datetime import datetime, timezone

from app.schemas.road_segment import RoadSegment


def test_road_segment_schema_validates_sample_fixture() -> None:
    payload = {
        'segment_id': 'seg-demo-001',
        'start': {'latitude': 40.7128, 'longitude': -74.0060},
        'end': {'latitude': 40.7138, 'longitude': -74.0050},
        'quality_score': 72.5,
        'quality_class': 'good',
        'scoring_method': 'placeholder',
        'observed_at': datetime(2026, 10, 15, 12, 0, tzinfo=timezone.utc).isoformat(),
    }

    segment = RoadSegment.model_validate(payload)

    assert segment.segment_id == 'seg-demo-001'
    assert 0 <= segment.quality_score <= 100
    assert segment.quality_class == 'good'
    assert segment.observed_at is not None
