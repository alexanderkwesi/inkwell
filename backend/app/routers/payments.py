from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Subscription, Payment
from app.schemas import (
    PaymentInitiate,
    PaymentInitiateResponse,
    PaymentComplete,
    PaymentCompleteResponse,
    PaymentHistoryResponse,
)
from app.security import get_current_user
from app.config import PLAN_PRICES, GC_SUCCESS_REDIRECT_URI
from app.services.gocardless import GoCardlessService

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("/initiate", response_model=PaymentInitiateResponse)
async def initiate_payment(
    data: PaymentInitiate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    plan = data.plan.lower()
    if plan not in ["pro", "elite"]:
        raise HTTPException(status_code=400, detail="Invalid plan choice. Choose 'pro' or 'elite'.")

    # Don't allow downgrade
    plan_rank = {"free": 0, "pro": 1, "elite": 2}
    current_rank = plan_rank.get(current_user.plan, 0)
    target_rank = plan_rank.get(plan, 0)
    
    if current_rank >= target_rank:
        raise HTTPException(
            status_code=400,
            detail=f"You are already on the {current_user.plan} plan or higher."
        )

    amount = PLAN_PRICES.get(plan, 0.0)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid plan price configuration.")

    # 1. Lookup or create GC Customer ID (mapped to stripe_customer_id column)
    gc_customer_id = current_user.stripe_customer_id
    if not gc_customer_id:
        try:
            gc_customer = await GoCardlessService.create_customer(
                current_user.id,
                current_user.email,
                current_user.name
            )
            gc_customer_id = gc_customer["id"]
            current_user.stripe_customer_id = gc_customer_id
            current_user.updated_at = datetime.utcnow()
            db.commit()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"GoCardless customer registration failed: {e}")

    # 2. Insert pending subscription
    sub = Subscription(
        user_id=current_user.id,
        plan_name=plan,
        status="trialing",
        amount=amount,
        currency="GBP",
        started_at=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    db.add(sub)
    db.flush()

    # 3. Create Billing Request & Flow via GoCardless
    try:
        br = await GoCardlessService.create_billing_request(
            plan,
            amount,
            gc_customer_id,
            current_user.id,
            sub.id
        )
        
        success_uri = f"{GC_SUCCESS_REDIRECT_URI}?sub_id={sub.id}&br_id={br['id']}"
        cancel_uri = f"{GC_SUCCESS_REDIRECT_URI}?cancelled=1&sub_id={sub.id}"
        
        flow = await GoCardlessService.create_billing_request_flow(
            br["id"],
            success_uri,
            cancel_uri
        )
    except Exception as e:
        # Roll back DB sub
        db.delete(sub)
        db.commit()
        raise HTTPException(status_code=502, detail=f"GoCardless flow setup failed: {e}")

    # 4. Insert pending Payment record
    payment = Payment(
        user_id=current_user.id,
        subscription_id=sub.id,
        amount=amount,
        currency="GBP",
        status="pending",
        stripe_payment_id=br["id"],  # temp storage of BR ID for verification mapping
        created_at=datetime.utcnow()
    )
    db.add(payment)
    db.commit()

    return {
        "payment_url": flow["authorisation_url"],
        "billing_request_id": br["id"],
        "subscription_id": sub.id
    }


@router.post("/complete", response_model=PaymentCompleteResponse)
async def complete_payment(
    data: PaymentComplete,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sub = db.query(Subscription).filter(
        Subscription.id == data.subscription_id,
        Subscription.user_id == current_user.id
    ).first()
    
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription record not found.")

    # Already active (webhook might have won the race)
    if sub.status == "active":
        return {
            "status": "active",
            "plan": sub.plan_name,
            "user": current_user
        }

    # Query status from GoCardless
    try:
        br = await GoCardlessService.get_billing_request(data.billing_request_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"GoCardless verification failed: {e}")

    br_status = br.get("status", "")
    
    if br_status == "fulfilled":
        # Activate subscription and upgrade user plan
        db.begin_nested() if db.in_nested_transaction() else None
        try:
            # Set subscription active
            sub.status = "active"
            sub.started_at = datetime.utcnow()
            sub.expires_at = datetime.utcnow() + timedelta(days=30)
            
            # Retrieve payment ID linked with this billing request
            payment = db.query(Payment).filter(
                Payment.subscription_id == sub.id,
                Payment.status == "pending"
            ).first()
            if payment:
                payment.status = "succeeded"
                payment.paid_at = datetime.utcnow()
                # If GoCardless created a payment resource, link it
                gc_pay_links = br.get("links", {})
                if gc_pay_links.get("payment"):
                    payment.stripe_payment_id = gc_pay_links["payment"]

            # Upgrade User
            current_user.plan = sub.plan_name
            current_user.updated_at = datetime.utcnow()
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Database update failed: {e}")
            
        return {
            "status": "active",
            "plan": sub.plan_name,
            "user": current_user
        }

    elif br_status == "cancelled":
        sub.status = "cancelled"
        db.commit()
        raise HTTPException(status_code=402, detail="Payment flow was cancelled.")

    # Still processing - tell front end to poll again
    return {
        "status": "pending"
    }


@router.get("/history", response_model=PaymentHistoryResponse)
def get_payment_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Fetch user's payments with plan name left joined
    results = db.query(
        Payment.id,
        Payment.amount,
        Payment.currency,
        Payment.status,
        Payment.card_last4,
        Payment.card_brand,
        Payment.paid_at,
        Payment.created_at,
        Subscription.plan_name
    ).outerjoin(
        Subscription, Subscription.id == Payment.subscription_id
    ).filter(
        Payment.user_id == current_user.id
    ).order_by(
        Payment.created_at.desc()
    ).limit(50).all()

    # Convert query results into dictionary lists matching schemas
    payments_list = []
    for r in results:
        payments_list.append({
            "id": r[0],
            "amount": float(r[1]),
            "currency": r[2],
            "status": r[3],
            "card_last4": r[4],
            "card_brand": r[5],
            "paid_at": r[6],
            "created_at": r[7],
            "plan_name": r[8]
        })
        
    return {"payments": payments_list}


@router.post("/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sub = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == "active"
    ).order_by(Subscription.created_at.desc()).first()

    if not sub:
        raise HTTPException(status_code=404, detail="No active subscription found.")

    # Cancel via GoCardless
    # The stripe_subscription_id column maps to GoCardless subscription ID
    gc_sub_id = sub.stripe_subscription_id
    if gc_sub_id:
        try:
            await GoCardlessService.cancel_subscription(gc_sub_id)
        except Exception as e:
            # Log error but don't crash, still cancel in DB
            pass

    # Cancel in local DB
    sub.status = "cancelled"
    sub.cancelled_at = datetime.utcnow()
    
    # Immediately downgrade user plan to free
    current_user.plan = "free"
    current_user.updated_at = datetime.utcnow()
    
    db.commit()
    return {"message": "Subscription cancelled. You have been moved to the Free plan."}
