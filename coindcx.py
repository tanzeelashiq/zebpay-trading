import time
import hmac
import hashlib
import json
import requests
import os

COINDCX_BASE_URL = "https://api.coindcx.com"

API_KEY = os.getenv("COINDCX_API_KEY")
API_SECRET = os.getenv("COINDCX_API_SECRET")

def place_market_order(symbol: str, side: str, amount_inr: int):

    endpoint = "/exchange/v1/orders/create"
    url = COINDCX_BASE_URL + endpoint

    body = {
        "side": side.lower(),           # buy / sell
        "order_type": "market",
        "market": symbol,               # I-BTC_INR
        "total_quantity": amount_inr,   # INR amount
        "timestamp": int(time.time() * 1000)
    }

    body_json = json.dumps(body, separators=(',', ':'))

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

    response = requests.post(url, data=body_json, headers=headers, timeout=10)

    try:
        return response.status_code, response.json()
    except Exception:
        return response.status_code, response.text
