from datetime import datetime, timezone

from app.schemas.road_segment import RoadSegment


def get_sample_road_segment() -> RoadSegment:
    """Return a deterministic, clearly placeholder road segment for validation examples."""
    return RoadSegment(
        segment_id='seg-demo-001',
        start={'latitude': 40.7128, 'longitude': -74.0060},
        end={'latitude': 40.7138, 'longitude': -74.0050},
        quality_score=72.5,
        quality_class='good',
        scoring_method='placeholder',
        observed_at=datetime(2026, 10, 15, 12, 0, tzinfo=timezone.utc),
        metadata={'source': 'fixture', 'notes': 'Sample data only; not production telemetry.'},
    )
