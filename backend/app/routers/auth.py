from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request, status

from app.core.security import create_access_token, hash_password, verify_password
from app.core.rate_limit import auth_limiter
from app.schemas import LoginRequest, RegisterRequest, TokenResponse, UserOut
from app.store import save_store, users

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, request: Request) -> dict:
    try:
        allowed = auth_limiter.allow(f"register:{request.client.host if request.client else 'unknown'}")
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail="Authentication rate limiter is unavailable") from error
    if not allowed:
        raise HTTPException(status_code=429, detail="Too many authentication attempts. Try again later.", headers={"Retry-After": "60"})
    if any(user["email"].lower() == payload.email.lower() for user in users.values()):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")
    user = {"id": str(uuid4()), "name": payload.name, "email": str(payload.email), "role": payload.role.value, "password_hash": hash_password(payload.password)}
    users[user["id"]] = user
    save_store()
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request) -> dict:
    try:
        allowed = auth_limiter.allow(f"login:{request.client.host if request.client else 'unknown'}")
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail="Authentication rate limiter is unavailable") from error
    if not allowed:
        raise HTTPException(status_code=429, detail="Too many authentication attempts. Try again later.", headers={"Retry-After": "60"})
    user = next((item for item in users.values() if item["email"].lower() == payload.email.lower()), None)
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    return {"access_token": create_access_token(user["id"], user["role"]), "role": user["role"]}
