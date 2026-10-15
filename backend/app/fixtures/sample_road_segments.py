from app.schemas.road_segment import RoadSegment


def get_sample_road_segment() -> RoadSegment:
    """Return a deterministic, clearly placeholder road segment for validation examples."""
    return RoadSegment(
        segment_id='seg-demo-001',
        geometry={
            'type': 'LineString',
            'coordinates': [[-74.0060, 40.7128], [-74.0050, 40.7138]],
        },
        survey_source='RoadIQ demo fixture',
        surveyed_at='2026-10-15T12:00:00+00:00',
        assessment_status='unrated',
        explanation='Demo geometry only. No measured evidence or quality rating is provided.',
        data_provenance=[{'field_path': 'geometry', 'source': 'demo_fixture'}],
    )
