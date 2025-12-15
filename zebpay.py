import time
import hmac
import hashlib
import requests
import os

ZEBPAY_BASE_URL = "https://api.zebpay.com"
ENDPOINT = "/trade/order"

API_KEY = os.getenv("ZEBPAY_API_KEY")
API_SECRET = os.getenv("ZEBPAY_API_SECRET")

if not API_KEY or not API_SECRET:
    raise RuntimeError("ZEBPAY API key or secret not set")


def sign_payload(payload: str) -> str:
    return hmac.new(
        API_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def place_market_order(symbol: str, side: str, amount_inr: int):
    timestamp = str(int(time.time() * 1000))

    # IMPORTANT: body must be EXACTLY this
    body = (
        f'{{'
        f'"market":"{symbol}",'
        f'"side":"{side.lower()}",'
        f'"order_type":"market",'
        f'"amount":"{amount_inr}"'
        f'}}'
    )

    payload = timestamp + "POST" + ENDPOINT + body
    signature = sign_payload(payload)

    headers = {
        "Content-Type": "application/json",
        "X-Zebpay-ApiKey": API_KEY,
        "X-Zebpay-Timestamp": timestamp,
        "X-Zebpay-Signature": signature
    }

    response = requests.post(
        ZEBPAY_BASE_URL + ENDPOINT,
        data=body,
        headers=headers,
        timeout=15
    )

    try:
        return response.status_code, response.json()
    except Exception:
        return response.status_code, response.text
