import base64
import random
from typing import Optional, cast

from fastapi import Depends, Request
from fastapi_users import UUIDIDMixin, BaseUserManager
from fastapi_users.exceptions import InvalidVerifyToken, UserAlreadyVerified
from loguru import logger

from src.users.domain.models import User
from src.users.infrastructure.dependencies import get_user_db
from src.core.config import settings


class UserManager(UUIDIDMixin, BaseUserManager):
    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY

    async def verify(self, token: str, request: Optional[Request] = None) -> User:
        try:
            user = await self.validate_verify_token(token)

            if user.is_verified:
                raise UserAlreadyVerified()

            await self.user_db.update(user, {"is_verified": True})
            await self.on_after_verify(user, request)
            
            return user
        except Exception as e:
            raise e

    async def request_verify(self, user: User, request: Optional[Request] = None):
        if user.is_verified:
            raise UserAlreadyVerified()

        code = str(random.randint(100000, 999999))

        await self.user_db.update(user, {"verification_code": code})
        
        await self.on_after_request_verify(user, code, request)

    async def validate_verify_token(self, token: str) -> User:
        try:
            decoded_bytes = base64.b64decode(token)
            decoded_str = decoded_bytes.decode('utf-8')
            email, code = decoded_str.split(':', 1)
        except Exception:
            raise InvalidVerifyToken()

        user = await self.get_by_email(email)
        
        if not user:
            raise InvalidVerifyToken()

        user = cast(User, user)

        if user.verification_code != code:
            raise InvalidVerifyToken()

        return user

    async def on_after_register(self, user: User, request: Optional = None):
        logger.info(f"User {user.id} has registered.")

        await self.request_verify(user, request)

    async def on_after_request_verify(self, user: User, token: str, request: Optional[Request] = None):
        logger.info(f"Verification requested for user {user.id}.")
        # TODO: add email code send
        logger.info(f"--- [EMAIL SIMULATION: VERIFICATION] ---")
        logger.info(f"To: {user.email}")
        logger.info(f"Code: {token}")
        logger.info(f"----------------------------------------")

    async def on_after_verify(self, user: User, request: Optional[Request] = None):
        await self.user_db.update(user, {"verification_code": None})
        logger.info(f"User {user.id} has been verified.")

    async def on_after_forgot_password(self, user: User, token: str, request: Optional = None):
        logger.warning(f"User {user.id} has forgotten their password. Reset token generated.")

        logger.info(f"--- [EMAIL SIMULATION: PASSWORD RESET] ---")
        logger.info(f"To: {user.email}")
        logger.info(f"Token: {token}")
        logger.info(f"----------------------------------------")


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)
