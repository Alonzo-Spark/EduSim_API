import uuid
import random
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel, EmailStr, Field, model_validator
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.src.config.database import get_db
from app.src.models.user import User
from app.src.utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)

auth_router = APIRouter(tags=["Authentication"])


def normalize_email(raw_email: str) -> str:
    return raw_email.strip().lower()


# --- Pydantic Schemas ---

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)
    role: str = Field("student", pattern="^(student|teacher)$")
    mobile_number: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_mobile_number(cls, values):
        if isinstance(values, dict) and not values.get("mobile_number"):
            mobile = values.get("mobile")
            if mobile:
                values["mobile_number"] = mobile
        return values


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class VerifyEmailRequest(BaseModel):
    token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class SendOtpRequest(BaseModel):
    country_code: str = Field("+91")
    mobile_number: str = Field(..., min_length=5, max_length=15)


class VerifyOtpRequest(BaseModel):
    mobile_number: str
    otp_code: str = Field(..., min_length=6, max_length=6)


class UserResponse(BaseModel):
    id: UUID
    name: Optional[str]
    email: str
    role: str
    mobile_number: Optional[str] = None
    is_email_verified: bool
    is_mobile_verified: bool

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RegisterResponse(BaseModel):
    success: bool = True
    message: str
    id: UUID


# --- Helper to get current user from token ---

async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication credentials"
        )
    
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is expired or invalid"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_418_IM_A_TEAPOT,
            detail="Token payload contains no user ID"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists"
        )
    
    return user


# --- Routes ---

@auth_router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user, hashes password, and sends virtual email verification."""
    email = normalize_email(request.email)

    # Check if user already exists
    existing_user = db.query(User).filter(func.lower(User.email) == email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )

    if request.mobile_number:
        existing_mobile_user = db.query(User).filter(User.mobile_number == request.mobile_number).first()
        if existing_mobile_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mobile number is already registered"
            )

        if not request.mobile_number.isdigit() or len(request.mobile_number) != 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid mobile number"
            )

    if len(request.password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password cannot exceed 72 bytes"
        )

    print("PASSWORD:", request.password)
    print("PASSWORD LENGTH:", len(request.password.encode("utf-8")))

    # Generate verification token
    verification_token = str(uuid.uuid4())
    
    # Hash password
    hashed_pwd = hash_password(request.password)
    
    new_user = User(
        name=request.name,
        email=email,
        password_hash=hashed_pwd,
        role=request.role,
        mobile_number=request.mobile_number,
        is_email_verified=False,
        is_mobile_verified=False,
        verification_token=verification_token
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Simulated email sending
    print(f"\n[EMAIL SIMULATOR] Sent activation email to {new_user.email}")
    print(f"[EMAIL SIMULATOR] Activation Link: http://localhost:5173/login?verify_token={verification_token}\n")
    
    return RegisterResponse(
        success=True,
        message="Account created successfully",
        id=new_user.id,
    )


@auth_router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Logs in user using email and password, issuing access & refresh tokens."""
    email = normalize_email(request.email)
    
    # Conditional admin login check
    if email == "admin@gmail.com" and request.password == "Admin@123":
        user = db.query(User).filter(func.lower(User.email) == "admin@gmail.com").first()
        if not user:
            user = User(
                name="Administrator",
                email="admin@gmail.com",
                password_hash=hash_password("Admin@123"),
                role="teacher",
                is_email_verified=True,
                is_mobile_verified=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
        access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user
        }

    user = db.query(User).filter(func.lower(User.email) == email).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
        
    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }


@auth_router.post("/refresh", response_model=TokenResponse)
def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refreshes access token using refresh token."""
    payload = decode_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
        
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
        
    # Re-issue both tokens
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user": user
    }


@auth_router.post("/verify-email")
def verify_email(request: VerifyEmailRequest, db: Session = Depends(get_db)):
    """Verifies user email using the verification token."""
    user = db.query(User).filter(User.verification_token == request.token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
        
    user.is_email_verified = True
    user.verification_token = None
    db.commit()
    
    return {"success": True, "message": "Email verified successfully."}


@auth_router.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Sends a mock password reset link."""
    email = normalize_email(request.email)
    user = db.query(User).filter(func.lower(User.email) == email).first()
    if not user:
        # Prevent user enumeration security leak by returning success anyway
        return {"success": True, "message": "Password reset instructions sent."}
        
    reset_token = str(uuid.uuid4())
    user.verification_token = reset_token
    db.commit()
    
    # Simulated email sending
    print(f"\n[EMAIL SIMULATOR] Sent password reset instructions to {user.email}")
    print(f"[EMAIL SIMULATOR] Password Reset Link: http://localhost:5173/login?reset_token={reset_token}\n")
    
    return {"success": True, "message": "Password reset instructions sent."}


@auth_router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Resets user password with a valid reset token."""
    user = db.query(User).filter(User.verification_token == request.token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
        
    user.password_hash = hash_password(request.new_password)
    user.verification_token = None
    db.commit()
    
    return {"success": True, "message": "Password reset completed successfully."}


@auth_router.post("/send-otp")
def send_otp(request: SendOtpRequest, db: Session = Depends(get_db)):
    """Generates and logs a 6-digit OTP code to the mobile number (Simulated)."""
    user = db.query(User).filter(User.mobile_number == request.mobile_number).first()
    
    # For testing, if user doesn't exist, we can register them dynamically or throw an error.
    # To keep things simple and secure, we'll ask them to register first, or create a mock student user.
    if not user:
        # Create a mock user if they select mobile login to make testing super smooth
        mock_email = f"mobile_{request.mobile_number[-4:]}@edusim.local"
        user = db.query(User).filter(User.email == mock_email).first()
        if not user:
            user = User(
                name="Mobile Student",
                email=mock_email,
                password_hash=hash_password("MobilePass123!"),
                role="student",
                mobile_number=request.mobile_number,
                is_email_verified=True,
                is_mobile_verified=False
            )
            db.add(user)
            db.commit()
            db.refresh(user)

    otp = f"{random.randint(100000, 999999)}"
    expires = datetime.now(timezone.utc) + timedelta(minutes=10)
    
    user.otp_code = otp
    user.otp_expires_at = expires
    db.commit()
    
    # Simulated SMS
    print(f"\n[SMS SIMULATOR] Sent OTP '{otp}' to {request.country_code}{request.mobile_number}")
    print(f"[SMS SIMULATOR] Code will expire in 10 minutes.\n")
    
    return {"success": True, "message": "OTP sent successfully."}


@auth_router.post("/verify-otp", response_model=TokenResponse)
def verify_otp(request: VerifyOtpRequest, db: Session = Depends(get_db)):
    """Verifies OTP and logs in user, issuing tokens."""
    user = db.query(User).filter(User.mobile_number == request.mobile_number).first()
    if not user or not user.otp_code or user.otp_code != request.otp_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code"
        )
        
    now = datetime.now(timezone.utc)
    # Ensure expires is timezone-aware for comparison, or normalize both
    otp_expiry = user.otp_expires_at
    if otp_expiry.tzinfo is None:
        otp_expiry = otp_expiry.replace(tzinfo=timezone.utc)
        
    if now > otp_expiry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP code has expired"
        )
        
    user.is_mobile_verified = True
    user.otp_code = None
    user.otp_expires_at = None
    db.commit()
    
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }


@auth_router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Returns profile for currently logged in user."""
    return current_user
