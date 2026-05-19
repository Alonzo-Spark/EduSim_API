from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse
from app.core.auth import hash_password, verify_password, create_access_token
from app.core.deps import get_current_user_dep
from app.services.gamification_service import update_streak
import uuid

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", response_model=TokenResponse)
async def signup(request: SignupRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == request.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        id=uuid.uuid4(),
        name=request.name,
        email=request.email,
        hashed_password=hash_password(request.password),
        class_level=request.class_level
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token({"sub": str(user.id), "email": user.email})
    return {"access_token": token, "token_type": "bearer", "user": {
        "id": str(user.id), "name": user.name, "email": user.email,
        "class_level": user.class_level, "xp": user.xp, "level": user.level
    }}

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    await update_streak(user.id, db)
    # Refresh to get updated XP, streak, and level
    await db.refresh(user)
    
    token = create_access_token({"sub": str(user.id), "email": user.email})
    return {"access_token": token, "token_type": "bearer", "user": {
        "id": str(user.id), "name": user.name, "email": user.email,
        "class_level": user.class_level, "xp": user.xp, "level": user.level,
        "streak": user.streak
    }}

@router.get("/me")
async def get_me(current_user = Depends(get_current_user_dep)):
    return {
        "id": str(current_user.id), "name": current_user.name,
        "email": current_user.email, "class_level": current_user.class_level,
        "xp": current_user.xp, "level": current_user.level,
        "streak": current_user.streak, "preferred_subjects": current_user.preferred_subjects
    }
