"""Security utilities for API authentication"""

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings

security = HTTPBearer()


async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> str:
    """
    Verify API key from Bearer token

    Args:
        credentials: HTTP authorization credentials

    Returns:
        str: The API key if valid

    Raises:
        HTTPException: If API key is invalid
    """
    if credentials.credentials != settings.mcp_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


def get_api_key_header(api_key: str = Security(verify_api_key)) -> str:
    """
    Dependency to get verified API key

    Args:
        api_key: Verified API key from verify_api_key

    Returns:
        str: The verified API key
    """
    return api_key
