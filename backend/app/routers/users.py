from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import User, Book, Subscription, Payment, AdminLog
from app.schemas import (
    UserUpdate,
    UserPasswordUpdate,
    UserResponse,
    AdminStats,
    AdminUserListResponse,
    AdminSetPlan,
)
from app.security import (
    get_current_user,
    get_current_admin,
    hash_password,
)

router = APIRouter(prefix="/users", tags=["Users"])

# ── Self-service routes ───────────────────────────────────────

@router.put("/profile", response_model=UserResponse)
def update_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    email_clean = data.email.strip().lower()
    
    # Check if email is taken by another account
    taken = db.query(User).filter(User.email == email_clean, User.id != current_user.id).first()
    if taken:
        raise HTTPException(status_code=400, detail="Email already in use by another account.")

    current_user.name = data.name.strip()
    current_user.email = email_clean
    current_user.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/password")
def change_password(
    data: UserPasswordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    hashed = hash_password(data.password)
    current_user.password_hash = hashed
    current_user.updated_at = datetime.utcnow()
    
    db.commit()
    return {"message": "Password updated."}


@router.delete("/account")
def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Perform transaction delete
    db.begin_nested() if db.in_nested_transaction() else None
    try:
        # DB relationships have cascade=delete-orphan configured, but double check SQLite constraints
        db.query(Book).filter(Book.user_id == current_user.id).delete()
        db.query(Subscription).filter(Subscription.user_id == current_user.id).delete()
        db.query(Payment).filter(Payment.user_id == current_user.id).delete()
        db.delete(current_user)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {e}"
        )
    return {"message": "Account deleted."}


# ── Admin routes ──────────────────────────────────────────────

@router.get("/admin/list", response_model=AdminUserListResponse)
def admin_list_users(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return {"users": users}


@router.get("/admin/stats", response_model=AdminStats)
def admin_get_stats(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    total_users = db.query(func.count(User.id)).scalar() or 0
    pro_users = db.query(func.count(User.id)).filter(User.plan == "pro").scalar() or 0
    elite_users = db.query(func.count(User.id)).filter(User.plan == "elite").scalar() or 0
    total_books = db.query(func.sum(User.books_used)).scalar() or 0
    
    # Calculate revenue from successful payments
    total_rev = db.query(func.sum(Payment.amount)).filter(Payment.status == "succeeded").scalar() or 0.0

    return {
        "total_users": int(total_users),
        "pro_users": int(pro_users),
        "elite_users": int(elite_users),
        "total_books": int(total_books),
        "total_revenue": float(total_rev)
    }


@router.post("/admin/reset-books")
def admin_reset_book_counts(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    db.query(User).update({User.books_used: 0, User.updated_at: datetime.utcnow()})
    
    # Create log entry
    log = AdminLog(
        admin_id=admin.id,
        action="reset_books",
        created_at=datetime.utcnow()
    )
    db.add(log)
    db.commit()
    
    return {"message": "All book counts reset to 0."}


@router.put("/admin/{user_id}/plan")
def admin_update_user_plan(
    user_id: str,
    data: AdminSetPlan,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    plan = data.plan.lower()
    if plan not in ["free", "pro", "elite"]:
        raise HTTPException(status_code=400, detail="Invalid plan choice.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    old_plan = user.plan
    user.plan = plan
    user.updated_at = datetime.utcnow()

    # Log action
    log = AdminLog(
        admin_id=admin.id,
        action="change_plan",
        target_type="user",
        target_id=user.id,
        metadata_json={"old_plan": old_plan, "new_plan": plan},
        created_at=datetime.utcnow()
    )
    db.add(log)
    db.commit()

    return {"message": f"Plan updated to {plan}."}


@router.delete("/admin/{user_id}")
def admin_delete_user(
    user_id: str,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="You cannot delete yourself.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    db.begin_nested() if db.in_nested_transaction() else None
    try:
        # Delete related tables
        db.query(Book).filter(Book.user_id == user.id).delete()
        db.query(Subscription).filter(Subscription.user_id == user.id).delete()
        db.query(Payment).filter(Payment.user_id == user.id).delete()
        db.delete(user)
        
        # Log action
        log = AdminLog(
            admin_id=admin.id,
            action="delete_user",
            target_type="user",
            target_id=user_id,
            created_at=datetime.utcnow()
        )
        db.add(log)
        
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {e}")

    return {"message": "User deleted."}
