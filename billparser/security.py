from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from .config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
api_keys = settings.get("API_KEYS", [])
if isinstance(api_keys, str):
    api_keys = [api_keys]
VALID_API_KEYS = set(api_keys)


async def get_api_key(api_key: str = Security(api_key_header)) -> str:
    """Get the valid API key from the request header.

    Args:
        api_key :str: The API key from the request header.

    Returns:
        str: The valid API key.

    Raises:
        HTTPException: If the API key is missing or invalid.
    """
    if api_key in VALID_API_KEYS:
        return api_key
    else:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
