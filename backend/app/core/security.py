"""
Security - JWT OAuth2, password hashing. GDPR-compliant, no PII in logs.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional

from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import settings

ALGORITHM = "HS256"


class TokenData(BaseModel):
    sub: str
    scopes: list[str] = []
    exp: Optional[datetime] = None


def verify_password(plain: str, hashed: str) -> bool:
    import bcrypt
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def hash_password(plain: str) -> str:
    import bcrypt
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(subject: str, scopes: Optional[list[str]] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": subject, "scopes": scopes or [], "exp": expire}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[TokenData]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return TokenData(sub=payload.get("sub", ""), scopes=payload.get("scopes", []))
    except JWTError:
        return None
