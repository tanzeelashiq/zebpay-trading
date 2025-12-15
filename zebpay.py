import time
import hmac
import hashlib
import requests
import os

ZEBPAY_BASE_URL = "https://www.zebpay.com/api/v1"

API_KEY = os.getenv("ZEBPAY_API_KEY")
API_SECRET = os.getenv("ZEBPAY_API_SECRET")

if not API_KEY or not API_SECRET:
    raise RuntimeError("ZEBPAY API key or secret not set in environment")

def _sign(payload: str):
    return hmac.new(
        API_SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()


def place_market_order(symbol: str, side: str, amount_inr: int):
    """
    side: BUY or SELL
    amount_inr: fixed INR amount (₹200)
    """

    endpoint = "/orders"
    url = ZEBPAY_BASE_URL + endpoint

    timestamp = str(int(time.time() * 1000))

    body = {
        "market": symbol,
        "side": side.lower(),   # buy / sell
        "order_type": "market",
        "price": 0,
        "quantity": 0,
        "amount": amount_inr
    }

    payload = timestamp + "POST" + endpoint

    headers = {
        "X-Zebpay-ApiKey": API_KEY,
        "X-Zebpay-Timestamp": timestamp,
        "X-Zebpay-Signature": _sign(payload),
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=body, headers=headers, timeout=10)

    try:
        data = response.json()
    except Exception:
        data = response.text
    return response.status_code, data

