import os
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import User
from app.security import hash_password
from app.config import ADMIN_EMAIL

def init_db():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    try:
        # Check if admin already exists
        admin = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if not admin:
            print(f"Seeding default admin user ({ADMIN_EMAIL})...")
            hashed_pass = hash_password("InkwellAdmin2024!")
            admin_user = User(
                name="Admin",
                email=ADMIN_EMAIL,
                password_hash=hashed_pass,
                plan="elite",
                books_used=0,
                is_admin=True
            )
            db.add(admin_user)
            db.commit()
            print("Admin user seeded successfully. Password: InkwellAdmin2024!")
        else:
            print("Admin user already exists.")
            
        # Seed test user
        test_email = "test@inkwell.ai"
        test_user = db.query(User).filter(User.email == test_email).first()
        if not test_user:
            print(f"Seeding test user ({test_email})...")
            test_user = User(
                name="Test Writer",
                email=test_email,
                password_hash=hash_password("password"),
                plan="free",
                books_used=0,
                is_admin=False
            )
            db.add(test_user)
            db.commit()
            print("Test user seeded successfully. Password: password")
        else:
            print("Test user already exists.")
            
    finally:
        db.close()
    print("Database initialization complete.")

if __name__ == "__main__":
    init_db()
