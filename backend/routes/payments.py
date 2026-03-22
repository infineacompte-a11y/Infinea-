"""
InFinea — Payment routes.
Stripe checkout, status, and webhook handling.
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from datetime import datetime, timezone
import os
import logging
import uuid

from database import db
from auth import get_current_user
from config import SUBSCRIPTION_PRICE
from models import CheckoutRequest

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)


@router.post("/payments/checkout")
async def create_checkout(
    checkout_data: CheckoutRequest,
    request: Request,
    user: dict = Depends(get_current_user),
):
    """Create Stripe checkout session for Premium subscription"""
    try:
        from emergentintegrations.payments.stripe.checkout import (
            StripeCheckout,
            CheckoutSessionRequest,
        )
    except ImportError:
        raise HTTPException(status_code=503, detail="Payment service not available")

    stripe_key = os.environ.get("STRIPE_API_KEY")
    if not stripe_key:
        raise HTTPException(status_code=500, detail="Payment service not configured")

    host_url = str(request.base_url).rstrip("/")
    webhook_url = f"{host_url}/api/webhook/stripe"

    stripe_checkout = StripeCheckout(api_key=stripe_key, webhook_url=webhook_url)

    success_url = (
        f"{checkout_data.origin_url}/pricing?session_id={{CHECKOUT_SESSION_ID}}"
    )
    cancel_url = f"{checkout_data.origin_url}/pricing"

    checkout_request = CheckoutSessionRequest(
        amount=SUBSCRIPTION_PRICE,
        currency="eur",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "user_id": user["user_id"],
            "email": user["email"],
            "plan": "premium",
        },
    )

    session = await stripe_checkout.create_checkout_session(checkout_request)

    await db.payment_transactions.insert_one(
        {
            "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
            "session_id": session.session_id,
            "user_id": user["user_id"],
            "email": user["email"],
            "amount": SUBSCRIPTION_PRICE,
            "currency": "eur",
            "plan": "premium",
            "payment_status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    return {"url": session.url, "session_id": session.session_id}


@router.get("/payments/status/{session_id}")
async def get_payment_status(
    session_id: str,
    user: dict = Depends(get_current_user),
):
    """Check payment status and upgrade user if successful"""
    try:
        from emergentintegrations.payments.stripe.checkout import StripeCheckout
    except ImportError:
        raise HTTPException(status_code=503, detail="Payment service not available")

    stripe_key = os.environ.get("STRIPE_API_KEY")
    if not stripe_key:
        raise HTTPException(status_code=500, detail="Payment service not configured")

    stripe_checkout = StripeCheckout(api_key=stripe_key, webhook_url="")

    try:
        status = await stripe_checkout.get_checkout_status(session_id)

        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "payment_status": status.payment_status,
                    "status": status.status,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            },
        )

        if status.payment_status == "paid":
            txn = await db.payment_transactions.find_one(
                {"session_id": session_id, "processed": True}, {"_id": 0}
            )

            if not txn:
                await db.users.update_one(
                    {"user_id": user["user_id"]},
                    {
                        "$set": {
                            "subscription_tier": "premium",
                            "subscription_started_at": datetime.now(
                                timezone.utc
                            ).isoformat(),
                        }
                    },
                )
                await db.payment_transactions.update_one(
                    {"session_id": session_id}, {"$set": {"processed": True}}
                )

        return {
            "status": status.status,
            "payment_status": status.payment_status,
            "amount": status.amount_total / 100,
            "currency": status.currency,
        }
    except Exception as e:
        logger.error(f"Payment status error: {e}")
        raise HTTPException(status_code=400, detail="Failed to get payment status")


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    try:
        from emergentintegrations.payments.stripe.checkout import StripeCheckout
    except ImportError:
        return {"status": "error", "message": "Payment service not available"}

    stripe_key = os.environ.get("STRIPE_API_KEY")
    if not stripe_key:
        return {"status": "error", "message": "Not configured"}

    host_url = str(request.base_url).rstrip("/")
    webhook_url = f"{host_url}/api/webhook/stripe"

    stripe_checkout = StripeCheckout(api_key=stripe_key, webhook_url=webhook_url)

    body = await request.body()
    signature = request.headers.get("Stripe-Signature")

    try:
        event = await stripe_checkout.handle_webhook(body, signature)

        if event.payment_status == "paid":
            user_id = event.metadata.get("user_id")
            if user_id:
                await db.users.update_one(
                    {"user_id": user_id},
                    {"$set": {"subscription_tier": "premium"}},
                )

        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error"}
