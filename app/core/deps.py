from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.auth import decode_token
from app.models.user import User
import uuid

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    DEV_MODE = True  # Enable local development bypass

    # If in local dev mode or if dev token is received, seamlessly authorize
    if DEV_MODE or not token or token == "dev-bypass-token":
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.email == "dev@edusim.com"))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
                name="Developer",
                email="dev@edusim.com",
                hashed_password="",
                class_level="Class 9",
                xp=1240,
                level=1,
                streak=7
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        return user

    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    user = await db.get(User, uuid.UUID(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# alias used in some routes
get_current_user_dep = get_current_user
