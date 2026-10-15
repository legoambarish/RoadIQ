import os
from functools import lru_cache


@lru_cache(maxsize=1)
def get_settings() -> dict[str, object]:
    """Load simple configuration values from environment variables."""
    return {
        'api_prefix': os.getenv('API_PREFIX', '/api/v1'),
        'cors_origins': [origin.strip() for origin in os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',') if origin.strip()],
        'environment': os.getenv('FASTAPI_ENV', 'development'),
    }
