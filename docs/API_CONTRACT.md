# RoadIQ API contract

## Base URL
- Local development: `http://localhost:8000`
- Versioned prefix: `/api/v1`

## Health endpoint
### `GET /api/v1/health`
Returns a basic service-status response.

#### Response schema
```json
{
  "status": "ok",
  "service": "RoadIQ API"
}
```

#### Success status
- HTTP 200 OK

#### Error format
The scaffold does not yet implement custom exception handlers beyond FastAPI's default validation errors.

Example validation error shape:
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "quality_score"],
      "msg": "Value error, quality_score must be between 0 and 100",
      "input": 120
    }
  ]
}
```

## Road segment schema
The backend validates sample road-segment payloads using the following structure:

```json
{
  "segment_id": "seg-demo-001",
  "start": {
    "latitude": 40.7128,
    "longitude": -74.0060
  },
  "end": {
    "latitude": 40.7138,
    "longitude": -74.0050
  },
  "quality_score": 72.5,
  "quality_class": "good",
  "scoring_method": "placeholder",
  "observed_at": "2026-10-15T12:00:00+00:00",
  "metadata": {
    "source": "fixture",
    "notes": "Sample data only; not production telemetry."
  }
}
```

### Validation rules
- `segment_id`: string with 1-64 characters; only letters, numbers, underscores, and dashes allowed
- `start.latitude` / `end.latitude`: inclusive range `[-90, 90]`
- `start.longitude` / `end.longitude`: inclusive range `[-180, 180]`
- `quality_score`: inclusive range `[0, 100]`
- `quality_class`: one of `poor`, `fair`, `good`, `excellent`
- `observed_at`: ISO-8601 timestamp if provided

## Planned future endpoints
The API contract is intentionally minimal at this stage. Planned additions include:
- road-segment creation and retrieval,
- scoring result endpoints,
- defect summary endpoints,
- image upload and preprocessing boundaries.
