from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import os

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hour shift

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def _hash_pw(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


class TokenData(BaseModel):
    sub: str
    name: str
    role: str  # coordinator, director, qa_reviewer, admin
    site: str
    exp: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    name: str
    role: str
    site: str


# Pre-seeded demo users (in production these come from the DB)
DEMO_USERS = {
    "maya@bioflow.io": {
        "name": "Maya R.",
        "role": "coordinator",
        "site": "Rockville Site A",
        "hashed_password": _hash_pw("demo123"),
    },
    "david@bioflow.io": {
        "name": "David M.",
        "role": "director",
        "site": "Rockville Site A",
        "hashed_password": _hash_pw("demo123"),
    },
    "sarah@bioflow.io": {
        "name": "Sarah K.",
        "role": "qa_reviewer",
        "site": "Rockville Site A",
        "hashed_password": _hash_pw("demo123"),
    },
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def authenticate_user(email: str, password: str) -> Optional[dict]:
    user = DEMO_USERS.get(email)
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return {"email": email, **user}


async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[TokenData]:
    """Returns current user from JWT token, or None if no token (allows demo mode)."""
    if token is None:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenData(
            sub=payload["sub"],
            name=payload["name"],
            role=payload["role"],
            site=payload["site"],
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
        )
    except JWTError:
        return None


def require_auth(user: Optional[TokenData] = Depends(get_current_user)) -> TokenData:
    """Strict auth — raises 401 if no valid token."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_role(*roles: str):
    """Dependency that checks user has one of the required roles."""
    def checker(user: TokenData = Depends(require_auth)) -> TokenData:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' not authorized. Required: {', '.join(roles)}",
            )
        return user
    return checker
