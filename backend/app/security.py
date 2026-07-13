import time
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRY_SECONDS
from app.database import get_db
from app.models import User
from app.schemas import TokenData

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer authentication dependency
security_bearer = HTTPBearer()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_jwt_token(user_id: str, email: str, is_admin: bool) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "email": email,
        "is_admin": is_admin,
        "iat": now,
        "exp": now + JWT_EXPIRY_SECONDS
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def get_current_user_data(credentials: HTTPAuthorizationCredentials = Depends(security_bearer)) -> TokenData:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        is_admin: bool = payload.get("is_admin", False)
        
        # Verify exp
        exp = payload.get("exp")
        if exp is None or exp < int(time.time()):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        if user_id is None or email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return TokenData(user_id=user_id, email=email, is_admin=is_admin)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(
    token_data: TokenData = Depends(get_current_user_data),
    db: Session = Depends(get_db)
) -> User:
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def get_current_admin(
    user: User = Depends(get_current_user)
) -> User:
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation forbidden. Admin rights required."
        )
    return user
