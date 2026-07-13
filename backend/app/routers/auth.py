import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, PasswordReset
from app.schemas import (
    UserCreate,
    UserLogin,
    Token,
    UserResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.security import (
    hash_password,
    verify_password,
    create_jwt_token,
    get_current_user,
)
from app.config import ADMIN_EMAIL

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: Session = Depends(get_db)):
    email_clean = data.email.strip().lower()
    
    # Check if duplicate email
    existing = db.query(User).filter(User.email == email_clean).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists."
        )

    # Create new user
    hashed = hash_password(data.password)
    user = User(
        name=data.name.strip(),
        email=email_clean,
        password_hash=hashed,
        plan="free",
        books_used=0,
        is_admin=False
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)

    # Issue JWT Token
    token = create_jwt_token(user_id=user.id, email=user.email, is_admin=user.is_admin)
    return {"token": token, "user": user}


@router.post("/login", response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_db)):
    email_clean = data.email.strip().lower()
    
    # Handle Admin credentials checking
    if email_clean == ADMIN_EMAIL:
        admin_user = db.query(User).filter(User.email == email_clean, User.is_admin == True).first()
        if not admin_user or not verify_password(data.password, admin_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials."
            )
        token = create_jwt_token(user_id=admin_user.id, email=admin_user.email, is_admin=True)
        return {"token": token, "user": admin_user}

    # Standard User auth
    user = db.query(User).filter(User.email == email_clean).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    # Update updated_at timestamp
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    token = create_jwt_token(user_id=user.id, email=user.email, is_admin=user.is_admin)
    return {"token": token, "user": user}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    email_clean = data.email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()
    
    # Always return standard message for security (don't leak user existence)
    if user:
        reset_token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        reset_record = PasswordReset(
            user_id=user.id,
            token=reset_token,
            expires_at=expires_at,
            used=False
        )
        db.add(reset_record)
        db.commit()
        
        # In a real app, send email here:
        # print(f"Reset Link: http://localhost:5173/reset-password?token={reset_token}")
        
    return {"message": "If that email exists, a reset link has been sent."}


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    reset_record = db.query(PasswordReset).filter(
        PasswordReset.token == data.token,
        PasswordReset.used == False
    ).first()
    
    if not reset_record or reset_record.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token."
        )

    hashed = hash_password(data.password)
    user = db.query(User).filter(User.id == reset_record.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found."
        )

    user.password_hash = hashed
    user.updated_at = datetime.utcnow()
    reset_record.used = True
    
    db.commit()
    return {"message": "Password reset successfully. Please log in."}
