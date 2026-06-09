"""
auth.py - Authentication utilities for the BLS Invoice application.
Handles password hashing, JWT token creation/verification, and the
FastAPI dependency that protects routes requiring a logged-in user.

Default credentials (created automatically on first run):
  username: admin
  password: admin123
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import get_db
import models

# Secret key — override with env var in production
SECRET_KEY = os.environ.get("SECRET_KEY", "bluelight-invoice-secret-key-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("TOKEN_EXPIRE_MINUTES", "480"))  # 8 hours

# Use bcrypt directly to avoid passlib/bcrypt version compatibility issues
import bcrypt as _bcrypt

# OAuth2 scheme; tokenUrl tells Swagger UI where to post credentials
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(password: str) -> str:
    """Return a bcrypt hash of the given plain-text password."""
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the stored bcrypt hash."""
    return _bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a signed JWT containing `data`.
    Expiry defaults to ACCESS_TOKEN_EXPIRE_MINUTES if not specified.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    """
    FastAPI dependency — validates the Bearer token and returns the User record.
    Raises HTTP 401 if the token is missing, invalid, or the user no longer exists.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def ensure_default_user(db: Session):
    """
    Create the default admin account if no users exist.
    Called once at application startup.
    """
    if db.query(models.User).count() == 0:
        admin = models.User(
            username="admin",
            hashed_password=hash_password("admin123"),
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print("Default admin user created (username: admin, password: admin123)")
