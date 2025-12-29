import time
import hmac
import hashlib
import json
import requests
import os
import uuid

COINDCX_BASE_URL = "https://api.coindcx.com"

API_KEY = os.getenv("COINDCX_API_KEY")
API_SECRET = os.getenv("COINDCX_API_SECRET")

if not API_KEY or not API_SECRET:
    raise RuntimeError("CoinDCX API credentials not set")

def place_market_buy_inr(symbol: str, amount_inr: int):
    endpoint = "/exchange/v1/orders/create"
    url = COINDCX_BASE_URL + endpoint

    body = {
        "side": "buy",
        "order_type": "market_order",      # ✅ FIXED
        "market": symbol,                  # e.g. BTCINR
        "total_price": amount_inr,          # ₹200
        "client_order_id": f"tv-{uuid.uuid4().hex[:12]}",
        "timestamp": int(time.time() * 1000)
    }

    body_json = json.dumps(body, separators=(",", ":"))

    signature = hmac.new(
        API_SECRET.encode(),
        body_json.encode(),
        hashlib.sha256
    ).hexdigest()

    headers = {
        "X-AUTH-APIKEY": API_KEY,
        "X-AUTH-SIGNATURE": signature,
        "Content-Type": "application/json"
    }

    print("📤 COINDCX REQUEST BODY:", body_json)
    print("📤 COINDCX HEADERS:", headers)

    response = requests.post(
        url,
        headers=headers,
        json=body,            # ✅ FIXED (NOT data=)
        timeout=15
    )

    try:
        data = response.json()
    except Exception:
        data = response.text

    print("📥 COINDCX STATUS:", response.status_code)
    print("📥 COINDCX RESPONSE:", data)

    return response.status_code, data
