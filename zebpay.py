import time
import hmac
import hashlib
import requests
import os
import json

ZEBPAY_BASE_URL = "https://api.zebpay.com"

API_KEY = os.getenv("ZEBPAY_API_KEY")
API_SECRET = os.getenv("ZEBPAY_API_SECRET")

if not API_KEY or not API_SECRET:
    raise RuntimeError("ZEBPAY API key or secret not set in environment")


def _sign(payload: str) -> str:
    return hmac.new(
        API_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def place_market_order(symbol: str, side: str, amount_inr: int):
    """
    side: BUY or SELL
    amount_inr: fixed INR amount (₹200)
    """

    endpoint = "/trade/order"
    url = ZEBPAY_BASE_URL + endpoint

    timestamp = str(int(time.time() * 1000))

    body = {
        "market": symbol,              # BTCINR
        "side": side.lower(),           # buy / sell
        "order_type": "market",
        "amount": str(amount_inr)       # IMPORTANT: must be string
    }

    body_json = json.dumps(body, separators=(",", ":"))

    # SIGNATURE FORMAT (CRITICAL)
    payload = timestamp + "POST" + endpoint + body_json

    headers = {
        "X-Zebpay-ApiKey": API_KEY,
        "X-Zebpay-Timestamp": timestamp,
        "X-Zebpay-Signature": _sign(payload),
        "Content-Type": "application/json"
    }

    response = requests.post(
        url,
        data=body_json,
        headers=headers,
        timeout=15
    )

    try:
        data = response.json()
    except Exception:
        data = response.text

    return response.status_code, data
