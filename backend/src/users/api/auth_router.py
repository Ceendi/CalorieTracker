from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm

from src.users.application.manager import get_user_manager
from src.users.application.services import AuthService
from src.users.infrastructure.security import auth_backend
from src.users.api.dependencies import get_auth_service

router = APIRouter()


@router.post("/login", tags=["Auth"])
async def login(
        credentials: OAuth2PasswordRequestForm = Depends(),
        user_manager=Depends(get_user_manager),
        auth_service: AuthService = Depends(get_auth_service),
        strategy=Depends(auth_backend.get_strategy)
):
    user = await user_manager.authenticate(credentials)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LOGIN_BAD_CREDENTIALS"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    return await auth_service.create_tokens(user, strategy)


@router.post("/refresh", tags=["Auth"])
async def refresh_token(
        refresh_token: str = Body(..., embed=True),
        auth_service: AuthService = Depends(get_auth_service),
        user_manager=Depends(get_user_manager),
        strategy=Depends(auth_backend.get_strategy)
):
    return await auth_service.refresh_session(refresh_token, strategy, user_manager)


@router.post("/logout", tags=["Auth"])
async def logout(
        refresh_token: str = Body(..., embed=True),
        auth_service: AuthService = Depends(get_auth_service)
):
    await auth_service.logout(refresh_token)
    return {"message": "Logged out successfully"}
