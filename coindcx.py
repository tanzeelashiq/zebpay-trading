import time
import hmac
import hashlib
import json
import requests
import os

COINDCX_BASE_URL = "https://api.coindcx.com"

API_KEY = os.getenv("COINDCX_API_KEY")
API_SECRET = os.getenv("COINDCX_API_SECRET")

if not API_KEY or not API_SECRET:
    raise RuntimeError("CoinDCX API credentials missing")


def place_market_buy_inr(symbol: str, amount_inr: int):
    endpoint = "/exchange/v1/orders/create"
    url = COINDCX_BASE_URL + endpoint

    body = {
        "market": symbol,
        "side": "buy",
        "order_type": "market",
        "total_price": amount_inr,
        "timestamp": int(time.time() * 1000)
    }

    # ✅ Canonical JSON (key order preserved)
    body_json = json.dumps(body, separators=(",", ":"), sort_keys=True)

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

    print("📤 COINDCX BODY:", body_json)
    print("📤 COINDCX SIGNATURE:", signature)

    response = requests.post(url, data=body_json, headers=headers, timeout=15)

    try:
        data = response.json()
    except Exception:
        data = response.text

    return response.status_code, data
