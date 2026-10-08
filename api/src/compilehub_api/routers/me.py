from fastapi import APIRouter, Request, Response

from ..db import Session
from ..deps import CurrentUser, user_out
from ..errors import ApiError
from ..redis import Redis
from ..schemas import DeleteAccountIn, SettingsPatch, UserOut
from ..security import verify_password
from .auth import COOKIE, COOKIE_PATH

router = APIRouter(prefix="/api/me", tags=["me"])


@router.get("", response_model=UserOut)
async def me(user: CurrentUser, session: Session, redis: Redis) -> UserOut:
    return await user_out(session, redis, user)


@router.patch("/settings", response_model=UserOut)
async def patch_settings(body: SettingsPatch, user: CurrentUser, session: Session, redis: Redis) -> UserOut:
    for field, value in body.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(user.settings, field, value)
    await session.commit()
    return await user_out(session, redis, user)


@router.delete("", status_code=204)
async def delete_account(
    body: DeleteAccountIn, request: Request, response: Response, user: CurrentUser, session: Session
) -> None:
    if not await verify_password(user.password_hash, body.password):
        raise ApiError(403, "wrong_password", "Password is wrong")
    await session.delete(user)  # файлы, папки, запуски, токены — ON DELETE CASCADE
    await session.commit()
    response.delete_cookie(COOKIE, path=COOKIE_PATH)
