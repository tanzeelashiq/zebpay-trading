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

    timestamp = int(time.time() * 1000)

    body = {
        "side": side.lower(),           # buy / sell
        "order_type": "market",
        "market": symbol,               # I-BTC_INR
        "total_quantity": amount_inr,   # INR amount
        "timestamp": timestamp
    }

    body_json = json.dumps(body, separators=(',', ':'), ensure_ascii=False)

    signature = hmac.new(
        API_SECRET.encode("utf-8"),
        body_json.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    headers = {
        "X-AUTH-APIKEY": API_KEY,
        "X-AUTH-SIGNATURE": signature,
        "Content-Type": "application/json"
    }

    response = requests.post(
        url,
        data=body_json,
        headers=headers,
        timeout=15
    )

    try:
        return response.status_code, response.json()
    except Exception:
        return response.status_code, response.text
