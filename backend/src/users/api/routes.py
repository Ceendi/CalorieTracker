from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_users import FastAPIUsers
from httpx_oauth.clients.google import GoogleOAuth2
from httpx_oauth.oauth2 import BaseOAuth2

from src.users.api.schemas import UserRead, UserCreate, UserUpdate, ChangePassword
from src.users.application.manager import get_user_manager
from src.users.domain.models import User
from src.users.infrastructure.security import auth_backend
from src.core.config import settings

fastapi_users = FastAPIUsers(
    get_user_manager,
    [auth_backend]
)

router = APIRouter()

router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["Auth"]
)

router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["Auth"]
)

router.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["Auth"]
)

router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["Auth"]
)

google_oauth_client: BaseOAuth2 = GoogleOAuth2(
    settings.GOOGLE_CLIENT_ID,
    settings.GOOGLE_CLIENT_SECRET,
)

router.include_router(
    fastapi_users.get_oauth_router(
        google_oauth_client,
        auth_backend,
        settings.SECRET_KEY,
        associate_by_email=True,
    ),
    prefix="/oauth/google",
    tags=["Auth"]
)

router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["Users"]
)

current_active_user = fastapi_users.current_user(active=True)


@router.post("/users/change-password", tags=["Users"])
async def change_password(
        data: ChangePassword,
        user: User = Depends(current_active_user),
        user_manager=Depends(get_user_manager)
):
    if not user.hashed_password:
        raise HTTPException(status_code=400, detail="User has no password set")

    verified, _ = user_manager.password_helper.verify_and_update(
        data.old_password, user.hashed_password
    )

    if not verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid old password")

    hashed_password = user_manager.password_helper.hash(data.new_password)
    await user_manager.user_db.update(user, {"hashed_password": hashed_password})

    return {"message": "Password updated successfully"}
