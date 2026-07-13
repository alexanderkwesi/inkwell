import hmac
import hashlib
import httpx
from typing import Dict, Any, List
from app.config import GC_ACCESS_TOKEN, GC_WEBHOOK_SECRET, GC_API_BASE

class GoCardlessService:
    @staticmethod
    async def _request(method: str, path: str, body: Dict[str, Any] = None, idempotency_key: str = "") -> Dict[str, Any]:
        url = f"{GC_API_BASE}{path}"
        headers = {
            "Authorization": f"Bearer {GC_ACCESS_TOKEN}",
            "GoCardless-Version": "2015-07-06",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers)
                elif method.upper() == "POST":
                    response = await client.post(url, json=body, headers=headers)
                elif method.upper() == "PUT":
                    response = await client.put(url, json=body, headers=headers)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    raise ValueError(f"Invalid HTTP method: {method}")

                data = response.json()
                if response.status_code >= 400:
                    msg = data.get("error", {}).get("message", response.text)
                    raise Exception(f"GoCardless API error ({response.status_code}): {msg}")
                return data
            except httpx.RequestError as exc:
                raise Exception(f"GoCardless connection error: {exc}")

    @classmethod
    async def create_customer(cls, user_id: str, email: str, name: str) -> Dict[str, Any]:
        names = name.split(" ", 1)
        given_name = names[0]
        family_name = names[1] if len(names) > 1 else ""

        body = {
            "customers": {
                "email": email,
                "given_name": given_name,
                "family_name": family_name,
                "country_code": "GB",  # UK by default
                "metadata": {"inkwell_user_id": user_id}
            }
        }
        res = await cls._request("POST", "/customers", body, idempotency_key=f"cust_{user_id}")
        return res["customers"]

    @classmethod
    async def create_billing_request(
        cls,
        plan_name: str,
        amount_gbp: float,
        gc_customer_id: str = "",
        inkwell_user_id: str = "",
        inkwell_sub_id: str = ""
    ) -> Dict[str, Any]:
        amount_pence = int(round(amount_gbp * 100))
        body = {
            "billing_requests": {
                "payment_request": {
                    "description": f"Inkwell AI — {plan_name} plan",
                    "amount": amount_pence,
                    "currency": "GBP",
                    "app_fee": 0
                },
                "mandate_request": {
                    "scheme": "bacs",  # UK Direct Debit
                    "description": f"Inkwell AI {plan_name} monthly subscription"
                },
                "metadata": {
                    "inkwell_user_id": inkwell_user_id,
                    "inkwell_sub_id": inkwell_sub_id,
                    "plan": plan_name
                }
            }
        }
        if gc_customer_id:
            body["billing_requests"]["links"] = {"customer": gc_customer_id}

        res = await cls._request(
            "POST",
            "/billing_requests",
            body,
            idempotency_key=f"br_{inkwell_sub_id}"
        )
        return res["billing_requests"]

    @classmethod
    async def create_billing_request_flow(
        cls,
        billing_request_id: str,
        success_redirect_uri: str,
        exit_uri: str = ""
    ) -> Dict[str, Any]:
        body = {
            "billing_request_flows": {
                "redirect_uri": success_redirect_uri,
                "exit_uri": exit_uri or success_redirect_uri,
                "show_redirect_buttons": True,
                "links": {
                    "billing_request": billing_request_id
                },
                "prefilled_bank_account": {},
                "lock_currency": True
            }
        }
        res = await cls._request("POST", "/billing_request_flows", body)
        return res["billing_request_flows"]

    @classmethod
    async def create_subscription(
        cls,
        mandate_id: str,
        amount_pence: int,
        plan_name: str,
        inkwell_user_id: str
    ) -> Dict[str, Any]:
        body = {
            "subscriptions": {
                "amount": amount_pence,
                "currency": "GBP",
                "interval_unit": "monthly",
                "interval": 1,
                "name": f"Inkwell AI — {plan_name} plan",
                "metadata": {
                    "plan": plan_name,
                    "inkwell_user_id": inkwell_user_id
                },
                "links": {"mandate": mandate_id}
            }
        }
        res = await cls._request("POST", "/subscriptions", body, idempotency_key=f"sub_new_{mandate_id}")
        return res["subscriptions"]

    @classmethod
    async def create_payment(
        cls,
        mandate_id: str,
        amount_pence: int,
        description: str,
        idempotency_key: str = ""
    ) -> Dict[str, Any]:
        import uuid
        key = idempotency_key or f"pay_{uuid.uuid4()}"
        body = {
            "payments": {
                "amount": amount_pence,
                "currency": "GBP",
                "description": description,
                "links": {"mandate": mandate_id}
            }
        }
        res = await cls._request("POST", "/payments", body, idempotency_key=key)
        return res["payments"]

    @classmethod
    async def cancel_subscription(cls, gc_sub_id: str) -> Dict[str, Any]:
        res = await cls._request("POST", f"/subscriptions/{gc_sub_id}/actions/cancel")
        return res["subscriptions"]

    @classmethod
    async def get_billing_request(cls, br_id: str) -> Dict[str, Any]:
        res = await cls._request("GET", f"/billing_requests/{br_id}")
        return res["billing_requests"]

    @staticmethod
    def verify_webhook(raw_body: bytes, signature_header: str) -> None:
        """
        Verify the signature of the webhook body.
        Raises ValueError if signature doesn't match.
        """
        key = GC_WEBHOOK_SECRET.encode("utf-8")
        expected_sig = hmac.new(key, raw_body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected_sig, signature_header):
            raise ValueError("Invalid GoCardless webhook signature")

    @classmethod
    async def list_mandates(cls, gc_customer_id: str) -> List[Dict[str, Any]]:
        import urllib.parse
        encoded_cust = urllib.parse.quote(gc_customer_id)
        res = await cls._request("GET", f"/mandates?customer={encoded_cust}")
        return res.get("mandates", [])

    @classmethod
    async def refund_payment(cls, gc_payment_id: str, amount_pence: int, reason: str = "requested_by_customer") -> Dict[str, Any]:
        body = {
            "refunds": {
                "amount": amount_pence,
                "total_amount_confirmation": amount_pence,
                "metadata": {"reason": reason},
                "links": {"payment": gc_payment_id}
            }
        }
        res = await cls._request("POST", "/refunds", body)
        return res["refunds"]
