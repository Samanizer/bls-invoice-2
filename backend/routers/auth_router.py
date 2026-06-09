"""
routers/auth_router.py - Authentication endpoints.
  POST /api/auth/login  — returns JWT token for valid credentials
  POST /api/auth/users  — create a new user (admin only)
  GET  /api/auth/me     — return currently authenticated user info
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
import models, schemas, auth as auth_utils

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate with username + password.
    Returns a JWT Bearer token valid for 8 hours.
    """
    user = db.query(models.User).filter(models.User.username == payload.username).first()
    if not user or not auth_utils.verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    token = auth_utils.create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(auth_utils.get_current_user)):
    """Return the currently logged-in user's profile."""
    return current_user


@router.post("/users", response_model=schemas.UserResponse)
def create_user(
    payload: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user)
):
    """
    Create a new application user (requires existing login).
    Returns HTTP 400 if the username is already taken.
    """
    if db.query(models.User).filter(models.User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    user = models.User(
        username=payload.username,
        hashed_password=auth_utils.hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/{user_id}/password")
def change_password(
    user_id: int,
    payload: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user)
):
    """Change a user's password. Any authenticated user may change their own password."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.hashed_password = auth_utils.hash_password(payload.password)
    db.commit()
    return {"message": "Password updated"}
