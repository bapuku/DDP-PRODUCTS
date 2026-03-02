"""
Auth API - OAuth2 token for protected endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

from app.core.security import create_access_token, decode_token, verify_password, hash_password

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Demo user (in production use DB)
_DEMO_USER = "operator@example.com"
_DEMO_HASH = hash_password("demo-password")


@router.post("/token", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 password flow - exchange username/password for JWT."""
    if form_data.username != _DEMO_USER or not verify_password(form_data.password, _DEMO_HASH):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(subject=form_data.username, scopes=["dpp:write"])
    return TokenResponse(access_token=token)


async def get_current_user_optional(token: str = Depends(oauth2_scheme)):
    """Optional auth - returns token data or None."""
    if not token:
        return None
    return decode_token(token)
