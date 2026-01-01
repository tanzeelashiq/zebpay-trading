import time
import hmac
import hashlib
import json
import requests
import os

COINDCX_BASE_URL = "https://api.coindcx.com"

API_KEY = os.getenv("COINDCX_API_KEY").strip()
API_SECRET = os.getenv("COINDCX_API_SECRET").strip().encode()

def place_market_buy_inr(symbol: str, amount_inr: int):
    endpoint = "/exchange/v1/orders/create_market_order"
    url = COINDCX_BASE_URL + endpoint

    body = {
        "side": "buy",
        "market": symbol,          # BTCINR
        "total_price": amount_inr, # ₹200
        "timestamp": int(time.time() * 1000)
    }

    body_json = json.dumps(body, separators=(",", ":"))

    signature = hmac.new(
        API_SECRET,
        body_json.encode(),
        hashlib.sha256
    ).hexdigest()

    headers = {
        "X-AUTH-APIKEY": API_KEY,
        "X-AUTH-SIGNATURE": signature,
        "Content-Type": "application/json"
    }

    print("📤 COINDCX REQUEST BODY:", body_json)

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
