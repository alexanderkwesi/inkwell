import os
import json
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Response, status, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Subscription, Payment
from app.services.gocardless import GoCardlessService

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

# Set up logging for webhooks
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GoCardlessWebhook")

def log_event(event_data: dict):
    # Log event into local webhook storage logs
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "storage")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    log_file = os.path.join(log_dir, "webhook.log")
    log_line = f"{datetime.utcnow().isoformat()} {json.dumps(event_data)}\n"
    try:
        with open(log_file, "a") as f:
            f.write(log_line)
    except Exception as e:
        logger.error(f"Failed to write to webhook log file: {e}")


@router.post("/gocardless")
async def gocardless_webhook(request: Request, db: Session = Depends(get_db)):
    raw_body = await request.body()
    sig_header = request.headers.get("Webhook-Signature", "")

    # 1. Verify signature
    try:
        GoCardlessService.verify_webhook(raw_body, sig_header)
    except ValueError as e:
        logger.warning(f"Signature verification failed: {e}")
        return Response(content="Invalid signature", status_code=status.HTTP_498_INFO_REQUIRED_TO_REPRODUCE) # PHP returns 498

    # 2. Parse body
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception as e:
        logger.error(f"Failed to decode webhook JSON: {e}")
        return Response(content="Invalid JSON body", status_code=status.HTTP_400_BAD_REQUEST)

    events = payload.get("events", [])
    
    for event in events:
        resource_type = event.get("resource_type", "")
        action = event.get("action", "")
        links = event.get("links", {})
        metadata = event.get("metadata", {})

        log_event(event)
        event_key = f"{resource_type}.{action}"
        logger.info(f"Processing event: {event_key}")

        try:
            # ── billing_requests.fulfilled ──
            if event_key == "billing_requests.fulfilled":
                br_id = links.get("billing_request", "")
                payment_id = links.get("payment", "")
                inkwell_sub_id = metadata.get("inkwell_sub_id", "")
                inkwell_user_id = metadata.get("inkwell_user_id", "")
                plan = metadata.get("plan", "")

                if inkwell_sub_id and plan:
                    db.begin_nested() if db.in_nested_transaction() else None
                    try:
                        # Find sub
                        sub = db.query(Subscription).filter(Subscription.id == inkwell_sub_id).first()
                        if sub:
                            sub.status = "active"
                            sub.started_at = datetime.utcnow()
                            sub.expires_at = datetime.utcnow() + timedelta(days=30)

                        # Find payment associated
                        payment = db.query(Payment).filter(
                            Payment.subscription_id == inkwell_sub_id,
                            Payment.status == "pending"
                        ).first()
                        if payment:
                            payment.status = "succeeded"
                            payment.paid_at = datetime.utcnow()
                            if payment_id:
                                payment.stripe_payment_id = payment_id

                        # Upgrade user plan
                        if inkwell_user_id:
                            user = db.query(User).filter(User.id == inkwell_user_id).first()
                            if user:
                                user.plan = plan
                                user.updated_at = datetime.utcnow()

                        db.commit()
                        logger.info(f"Subscription {inkwell_sub_id} activated successfully via webhook.")
                    except Exception as e:
                        db.rollback()
                        logger.error(f"Error executing webhook sub updates: {e}")

            # ── mandates.active ──
            elif event_key == "mandates.active":
                mandate_id = links.get("mandate", "")
                customer_id = links.get("customer", "")
                logger.info(f"Mandate {mandate_id} active for GC customer {customer_id}")

            # ── payments.paid_out / payments.confirmed ──
            elif event_key in ["payments.paid_out", "payments.confirmed"]:
                gc_pay_id = links.get("payment", "")
                if gc_pay_id:
                    payment = db.query(Payment).filter(Payment.stripe_payment_id == gc_pay_id).first()
                    if payment:
                        payment.status = "succeeded"
                        payment.paid_at = datetime.utcnow()
                        db.commit()

            # ── payments.failed ──
            elif event_key == "payments.failed":
                gc_pay_id = links.get("payment", "")
                if gc_pay_id:
                    payment = db.query(Payment).filter(Payment.stripe_payment_id == gc_pay_id).first()
                    if payment:
                        payment.status = "failed"
                        db.commit()

            # ── refunds.created ──
            elif event_key == "refunds.created":
                gc_pay_id = links.get("payment", "")
                if gc_pay_id:
                    payment = db.query(Payment).filter(Payment.stripe_payment_id == gc_pay_id).first()
                    if payment:
                        payment.status = "refunded"
                        db.commit()

            # ── subscriptions.created ──
            elif event_key == "subscriptions.created":
                gc_sub_id = links.get("subscription", "")
                inkwell_sub_id = metadata.get("inkwell_sub_id", "")
                if inkwell_sub_id and gc_sub_id:
                    sub = db.query(Subscription).filter(Subscription.id == inkwell_sub_id).first()
                    if sub:
                        sub.status = "active"
                        sub.stripe_subscription_id = gc_sub_id
                        db.commit()

            # ── subscriptions.cancelled ──
            elif event_key == "subscriptions.cancelled":
                gc_sub_id = links.get("subscription", "")
                if gc_sub_id:
                    sub = db.query(Subscription).filter(
                        Subscription.stripe_subscription_id == gc_sub_id,
                        Subscription.status == "active"
                    ).first()
                    if sub:
                        sub.status = "cancelled"
                        sub.cancelled_at = datetime.utcnow()
                        
                        # Downgrade user
                        user = db.query(User).filter(User.id == sub.user_id).first()
                        if user:
                            user.plan = "free"
                            user.updated_at = datetime.utcnow()
                        db.commit()

            # ── payments.created (renewal charge) ──
            elif event_key == "payments.created":
                gc_pay_id = links.get("payment", "")
                gc_sub_id = links.get("subscription", "")
                if gc_pay_id and gc_sub_id:
                    sub = db.query(Subscription).filter(Subscription.stripe_subscription_id == gc_sub_id).first()
                    if sub:
                        # Insert renewal payment
                        payment = Payment(
                            user_id=sub.user_id,
                            subscription_id=sub.id,
                            amount=sub.amount,
                            currency="GBP",
                            status="pending",
                            stripe_payment_id=gc_pay_id,
                            created_at=datetime.utcnow()
                        )
                        db.add(payment)
                        
                        # Extend subscription expiry by 1 month
                        if sub.expires_at:
                            sub.expires_at += timedelta(days=30)
                        else:
                            sub.expires_at = datetime.utcnow() + timedelta(days=30)
                            
                        db.commit()

        except Exception as e:
            logger.error(f"Error handling event {event_key}: {e}")

    return Response(content="OK", status_code=status.HTTP_200_OK)
