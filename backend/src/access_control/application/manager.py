from typing import Optional

from fastapi import Depends, Request
from fastapi_users import UUIDIDMixin, BaseUserManager
from loguru import logger

from src.access_control.domain.models import User
from src.access_control.infrastructure.dependencies import get_user_db
from src.core.config import settings


class UserManager(UUIDIDMixin, BaseUserManager):
    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY

    async def on_after_register(self, user: User, request: Optional = None):
        logger.info(f"User {user.id} has registered.")

        await self.request_verify(user, request)

    async def on_after_request_verify(self, user: User, token: str, request: Optional[Request] = None):
        logger.info(f"Verification requested for user {user.id}.")
        # TODO: add email code send
        logger.info(f"--- [EMAIL SIMULATION: VERIFICATION] ---")
        logger.info(f"To: {user.email}")
        logger.info(f"Token: {token}")
        logger.info(f"----------------------------------------")

    async def on_after_forgot_password(self, user: User, token: str, request: Optional = None):
        logger.warning(f"User {user.id} has forgotten their password. Reset token generated.")

        logger.info(f"--- [EMAIL SIMULATION: PASSWORD RESET] ---")
        logger.info(f"To: {user.email}")
        logger.info(f"Token: {token}")
        logger.info(f"----------------------------------------")


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)
