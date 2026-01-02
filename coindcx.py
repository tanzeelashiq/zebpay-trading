import time
import hmac
import hashlib
import json
import requests
import os

COINDCX_BASE_URL = "https://api.coindcx.com"

API_KEY = os.getenv("COINDCX_API_KEY")
API_SECRET = os.getenv("COINDCX_API_SECRET").encode()

if not API_KEY or not API_SECRET:
    raise RuntimeError("CoinDCX API credentials not set")


def _sign(payload: str) -> str:
    return hmac.new(API_SECRET, payload.encode(), hashlib.sha256).hexdigest()


def place_market_buy_btcinr(amount_inr: int):
    """
    INR-based MARKET BUY (official CoinDCX way)
    """

    body = {
        "side": "buy",
        "order_type": "market",
        "market": "BTCINR",
        "total_price": int(amount_inr),  # INR must be integer
        "timestamp": int(time.time() * 1000)
    }

    body_json = json.dumps(body, separators=(",", ":"))
    signature = _sign(body_json)

    headers = {
        "X-AUTH-APIKEY": API_KEY,
        "X-AUTH-SIGNATURE": signature,
        "Content-Type": "application/json"
    }

    print("📤 COINDCX REQUEST BODY:", body_json)

    response = requests.post(
        COINDCX_BASE_URL + "/exchange/v1/orders/create",
        data=body_json,
        headers=headers,
        timeout=15
    )

    try:
        data = response.json()
    except Exception:
        data = response.text

    return response.status_code, data
