from fastapi import APIRouter

router = APIRouter(tags=['system'])


@router.get('/health')
def health() -> dict[str, str]:
    """Return a basic backend availability signal.

    This endpoint intentionally does not depend on external services or models.
    """
    return {'status': 'ok', 'service': 'RoadIQ API'}
