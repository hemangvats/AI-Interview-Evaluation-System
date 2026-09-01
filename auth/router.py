from fastapi import APIRouter, Depends, status
from auth.schemas import (
    UserRegisterRequest, UserLoginRequest, TokenResponse,
    RefreshTokenRequest, UserProfileResponse
)
from auth.service import AuthService
from auth.deps import get_auth_service, get_current_user

auth_router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

@auth_router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register a new candidate user account"
)
async def register(
    request: UserRegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    user = await auth_service.register(request)
    return {
        "status": "success",
        "message": "User registered successfully",
        "user_id": user["_id"]
    }

@auth_router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate candidate credentials and return JWT bearer tokens"
)
async def login(
    request: UserLoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    tokens = await auth_service.login(request)
    return tokens

@auth_router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Exchange valid refresh token for a new set of JWT tokens"
)
async def refresh(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    tokens = await auth_service.refresh(request.refresh_token)
    return tokens

@auth_router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current logged-in candidate profile"
)
async def me(
    current_user: dict = Depends(get_current_user)
):
    return current_user
