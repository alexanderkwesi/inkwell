import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    ForeignKey,
    DateTime,
    Numeric,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(120), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    plan = Column(String(20), nullable=False, default="free")
    books_used = Column(Integer, nullable=False, default=0)
    is_admin = Column(Boolean, nullable=False, default=False)
    email_verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # GoCardless mapping IDs (named stripe for schema compatibility)
    stripe_customer_id = Column(String(120), nullable=True, unique=True)

    # Relationships
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    books = relationship("Book", back_populates="user", cascade="all, delete-orphan")
    files = relationship("UploadedFile", back_populates="user", cascade="all, delete-orphan")
    password_resets = relationship("PasswordReset", back_populates="user", cascade="all, delete-orphan")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_name = Column(String(20), nullable=False)  # free, pro, elite
    status = Column(String(20), nullable=False, default="active")  # active, cancelled, expired, trialing
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    stripe_subscription_id = Column(String(120), nullable=True, unique=True)

    # Relationships
    user = relationship("User", back_populates="subscriptions")
    payments = relationship("Payment", back_populates="subscription")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subscription_id = Column(String(36), ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    card_last4 = Column(String(4), nullable=True)
    card_brand = Column(String(30), nullable=True)
    status = Column(String(20), nullable=False, default="pending")  # pending, succeeded, failed, refunded
    stripe_payment_id = Column(String(120), nullable=True, unique=True)  # maps GC payment/billing request ID
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="payments")
    subscription = relationship("Subscription", back_populates="payments")


class Book(Base):
    __tablename__ = "books"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(300), nullable=False)
    synopsis = Column(Text, nullable=True)
    prompt = Column(Text, nullable=False)
    chapter_count = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="generating")  # generating, complete, failed, draft
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="books")
    chapters = relationship("Chapter", back_populates="book", cascade="all, delete-orphan")
    files = relationship("UploadedFile", back_populates="book")


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    book_id = Column(String(36), ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    chapter_number = Column(Integer, nullable=False)
    title = Column(String(300), nullable=False)
    content = Column(Text, nullable=False)
    image_description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    book = relationship("Book", back_populates="chapters")
    images = relationship("BookImage", back_populates="chapter", cascade="all, delete-orphan")


class BookImage(Base):
    __tablename__ = "book_images"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    chapter_id = Column(String(36), ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False)
    url = Column(String(1000), nullable=True)
    storage_key = Column(String(500), nullable=True)
    provider = Column(String(50), default="dalle")
    status = Column(String(20), nullable=False, default="pending")  # pending, generated, failed
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    chapter = relationship("Chapter", back_populates="images")


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    book_id = Column(String(36), ForeignKey("books.id", ondelete="SET NULL"), nullable=True)
    filename = Column(String(300), nullable=False)
    storage_key = Column(String(500), nullable=False)
    mime_type = Column(String(120), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    file_type = Column(String(20), nullable=False, default="document")  # document, image
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="files")
    book = relationship("Book", back_populates="files")


class PasswordReset(Base):
    __tablename__ = "password_resets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="password_resets")


class AdminLog(Base):
    __tablename__ = "admin_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    admin_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)  # change_plan, delete_user, etc.
    target_type = Column(String(60), nullable=True)
    target_id = Column(String(36), nullable=True)
    metadata_json = Column(JSON, nullable=True)  # stores jsonb
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
