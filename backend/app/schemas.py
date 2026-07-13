from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Any
from datetime import datetime

# ── Auth schemas ──────────────────────────────────────────────
class UserCreate(BaseModel):
    name: str = Field(..., max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: str
    password: str

class UserUpdate(BaseModel):
    name: str = Field(..., max_length=120)
    email: EmailStr

class UserPasswordUpdate(BaseModel):
    password: str = Field(..., min_length=6)

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    plan: str
    books_used: int
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    token: str
    user: UserResponse

class TokenData(BaseModel):
    user_id: str
    email: str
    is_admin: bool

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(..., min_length=6)


# ── Book schemas ──────────────────────────────────────────────
class BookCreate(BaseModel):
    prompt: str = Field(..., max_length=5000)

class ChapterResponse(BaseModel):
    id: str
    chapter_number: int
    title: str
    content: str
    image_description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class BookResponse(BaseModel):
    id: str
    title: str
    synopsis: Optional[str] = None
    chapter_count: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BookDetailsResponse(BookResponse):
    prompt: str
    chapters: List[ChapterResponse] = []

class BookListResponse(BaseModel):
    books: List[BookResponse]

# ── Payment schemas ───────────────────────────────────────────
class PaymentInitiate(BaseModel):
    plan: str  # pro or elite

class PaymentInitiateResponse(BaseModel):
    payment_url: str
    billing_request_id: str
    subscription_id: str

class PaymentComplete(BaseModel):
    billing_request_id: str
    subscription_id: str

class PaymentCompleteResponse(BaseModel):
    status: str  # active, pending, etc.
    plan: Optional[str] = None
    user: Optional[UserResponse] = None

class PaymentHistoryItem(BaseModel):
    id: str
    amount: float
    currency: str
    status: str
    card_last4: Optional[str] = None
    card_brand: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: datetime
    plan_name: Optional[str] = None

    class Config:
        from_attributes = True

class PaymentHistoryResponse(BaseModel):
    payments: List[PaymentHistoryItem]


# ── Uploaded File schemas ─────────────────────────────────────
class FileResponse(BaseModel):
    id: str
    filename: str
    mime_type: str
    file_size_bytes: int
    file_type: str
    created_at: datetime

    class Config:
        from_attributes = True

class FileListResponse(BaseModel):
    files: List[FileResponse]


# ── Admin schemas ─────────────────────────────────────────────
class AdminStats(BaseModel):
    total_users: int
    pro_users: int
    elite_users: int
    total_books: int
    total_revenue: float

class AdminUserListResponse(BaseModel):
    users: List[UserResponse]

class AdminSetPlan(BaseModel):
    plan: str
