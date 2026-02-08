from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
import httpx
import secrets
import string

from src.users.api.schemas import GoogleLogin
from src.core.config import settings

from src.users.application.manager import get_user_manager
from src.users.application.services import AuthService
from src.users.infrastructure.security import auth_backend
from src.users.api.dependencies import get_auth_service
from src.users.api import schemas
from src.users.api.schemas import GoogleLogin

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


@router.post("/google", tags=["Auth"])
async def google_login(
        login_data: GoogleLogin,
        user_manager=Depends(get_user_manager),
        auth_service: AuthService = Depends(get_auth_service),
        strategy=Depends(auth_backend.get_strategy)
):
    # 1. Verify ID Token with Google
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": login_data.token}
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="INVALID_GOOGLE_TOKEN"
        )

    google_data = response.json()
    
    # Security: Verify that the token was issued for OUR app
    # We check against the Web Client ID (because that's what mobile app sends as 'audience')
    audience = google_data.get("aud")
    if audience != settings.GOOGLE_CLIENT_ID:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="INVALID_GOOGLE_TOKEN_AUDIENCE"
        )
    
    email = google_data.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GOOGLE_ACCOUNT_NO_EMAIL"
        )
    
    # 2. Check if user exists
    try:
        user = await user_manager.get_by_email(email)
    except Exception:
        user = None

    # 3. If not, register new user
    if not user:
        # Generate random secure password for social login users
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for i in range(20))
        
        try:
            user_create = schemas.UserCreate(
                email=email,
                password=password,
                is_active=True,
                is_verified=True,  # Google accounts are verified
                is_onboarded=False
            )
            user = await user_manager.create(user_create)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="REGISTER_FAILED"
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
