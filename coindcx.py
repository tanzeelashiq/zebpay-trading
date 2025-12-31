import time
import hmac
import hashlib
import json
import requests
import os

COINDCX_BASE_URL = "https://api.coindcx.com"

API_SECRET = os.getenv("COINDCX_API_SECRET", "").strip()
API_KEY = os.getenv("COINDCX_API_KEY", "").strip()

if not API_KEY or not API_SECRET:
    raise RuntimeError("CoinDCX API credentials not set")


def place_market_buy_inr(symbol: str, amount_inr: int):
    endpoint = "/exchange/v1/orders/create"
    url = COINDCX_BASE_URL + endpoint

    body = {
        "side": "buy",
        "order_type": "market",
        "market": symbol,
        "total_price": amount_inr,   # 👈 THIS IS THE KEY
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

    print("📤 CoinDCX request:", body_json)

    response = requests.post(url, headers=headers, data=body_json, timeout=15)

    print("🔐 API KEY length:", len(API_KEY))
    print("🔐 API SECRET length:", len(API_SECRET))

    try:
        return response.status_code, response.json()
    except Exception:
        return response.status_code, response.text
