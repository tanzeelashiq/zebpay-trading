import time
import hmac
import hashlib
import json
import requests
import os
import math

COINDCX_BASE_URL = "https://api.coindcx.com"

API_KEY = os.getenv("COINDCX_API_KEY").strip()
API_SECRET = os.getenv("COINDCX_API_SECRET").strip().encode()

MIN_BTC_QTY = 0.00001

def get_btc_price_inr():
    url = "https://api.coindcx.com/exchange/ticker"
    data = requests.get(url, timeout=10).json()
    for item in data:
        if item["market"] == "BTCINR":
            return float(item["last_price"])
    raise RuntimeError("BTCINR price not found")

def place_market_buy_inr(symbol: str, amount_inr: int):
    price = get_btc_price_inr()

    raw_qty = amount_inr / price
    quantity = math.floor(raw_qty / MIN_BTC_QTY) * MIN_BTC_QTY

    if quantity < MIN_BTC_QTY:
        raise RuntimeError(f"Quantity too small: {quantity}")

    endpoint = "/exchange/v1/orders/create"
    url = COINDCX_BASE_URL + endpoint

    body = {
        "side": "buy",
        "order_type": "market",
        "market": symbol,
        "quantity": quantity,
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

    response = requests.post(url, data=body_json, headers=headers, timeout=15)

    try:
        data = response.json()
    except Exception:
        data = response.text

    return response.status_code, data
