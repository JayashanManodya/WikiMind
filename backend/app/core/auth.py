"""Authentication module for Google OAuth 2.0 and JWT Token Management in WikiLLM."""

import time
import jwt
import httpx
from typing import Optional, Dict, Any
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from .config import get_settings

security = HTTPBearer(auto_error=False)


def create_access_token(user_data: Dict[str, Any], expires_in_seconds: Optional[int] = None) -> str:
    """Create a signed JWT access token containing user identity."""
    settings = get_settings()
    now = int(time.time())
    if expires_in_seconds is None:
        expires_in_seconds = settings.jwt_access_token_expire_minutes * 60

    payload = {
        "sub": user_data["user_id"],
        "email": user_data.get("email", ""),
        "name": user_data.get("name", "User"),
        "picture": user_data.get("picture", ""),
        "iat": now,
        "exp": now + expires_in_seconds,
    }
    
    encoded = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a signed JWT access token."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return {
            "user_id": payload["sub"],
            "email": payload.get("email", ""),
            "name": payload.get("name", "User"),
            "picture": payload.get("picture", ""),
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication token.")


async def verify_google_token(credential: str) -> Dict[str, Any]:
    """Verify Google OAuth 2.0 ID Token / Credential from Google Identity Services.

    Returns dict with user details: user_id (google sub), email, name, picture.
    """
    settings = get_settings()

    # Attempt standard google-auth verification
    try:
        request_adapter = google_requests.Request()
        client_id = settings.google_client_id if settings.google_client_id else None
        
        # Verify token
        id_info = id_token.verify_oauth2_token(credential, request_adapter, client_id=client_id)
        
        user_id = id_info.get("sub")
        email = id_info.get("email", "")
        name = id_info.get("name", email.split("@")[0] if email else "Google User")
        picture = id_info.get("picture", "")

        return {
            "user_id": f"google_{user_id}",
            "raw_sub": user_id,
            "email": email,
            "name": name,
            "picture": picture,
        }
    except Exception as primary_e:
        # Fallback to Google tokeninfo HTTP endpoint if library verification fails or client_id is unconstrained
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}")
                if res.status_code == 200:
                    id_info = res.json()
                    user_id = id_info.get("sub")
                    email = id_info.get("email", "")
                    name = id_info.get("name", email.split("@")[0] if email else "Google User")
                    picture = id_info.get("picture", "")
                    return {
                        "user_id": f"google_{user_id}",
                        "raw_sub": user_id,
                        "email": email,
                        "name": name,
                        "picture": picture,
                    }
        except Exception:
            pass

        # If it's a dev token or mock credential (e.g. "mock_token_123")
        if credential.startswith("mock_token_"):
            parts = credential.split("_")
            mock_id = parts[-1] if len(parts) > 2 else "demo"
            return {
                "user_id": f"google_user_{mock_id}",
                "raw_sub": mock_id,
                "email": f"user_{mock_id}@example.com",
                "name": f"Demo User {mock_id}",
                "picture": "",
            }

        raise HTTPException(status_code=401, detail=f"Failed to verify Google credential: {str(primary_e)}")


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> Dict[str, Any]:
    """FastAPI dependency to extract and validate the authenticated current user."""
    if not credentials or not credentials.credentials:
        # Return default guest user for unauthenticated requests
        return {
            "user_id": "guest_user",
            "email": "guest@wikillm.local",
            "name": "Guest User",
            "picture": "",
            "is_guest": True,
        }

    token = credentials.credentials
    user = decode_access_token(token)
    user["is_guest"] = False
    return user


async def require_authenticated_user(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Dependency enforcing that request must be from a logged-in Google user."""
    if user.get("is_guest"):
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please log in with your Google account."
        )
    return user
