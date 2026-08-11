import os
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from db import UserRecord, get_db

ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
_INSECURE_DEFAULT_SECRET = "dev-only-insecure-secret-change-before-deploy"
JWT_SECRET = os.environ.get("JWT_SECRET", _INSECURE_DEFAULT_SECRET)
JWT_ALGORITHM = "HS256"
JWT_EXPIRES_MINUTES = 60 * 24

if ENVIRONMENT == "production" and JWT_SECRET == _INSECURE_DEFAULT_SECRET:
    raise RuntimeError(
        "JWT_SECRET must be set to a real secret when ENVIRONMENT=production. "
        "Refusing to start with the insecure development default."
    )

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)
        

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_access_token(user: UserRecord) -> str:
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRES_MINUTES)
    payload = {"sub": user.id, "email": user.email, "role": user.role, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> UserRecord:
    credentials_error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    if not token:
        raise credentials_error
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise credentials_error
    except JWTError:
        raise credentials_error

    user = db.query(UserRecord).filter(UserRecord.id == user_id).first()
    if not user:
        raise credentials_error
    return user


def require_roles(*roles: str):
    def dependency(user: UserRecord = Depends(get_current_user)) -> UserRecord:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to do this")
        return user
    return dependency
