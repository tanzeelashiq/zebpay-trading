import time
import hmac
import hashlib
import json
import requests
import os
import math

COINDCX_BASE_URL = "https://api.coindcx.com"

API_KEY = os.getenv("COINDCX_API_KEY")
API_SECRET = os.getenv("COINDCX_API_SECRET")

MIN_BTC_QTY = 0.00001  # <-- this is why 3e-05 fails


def get_btcinr_price():
    url = "https://api.coindcx.com/exchange/ticker"
    res = requests.get(url, timeout=10)
    data = res.json()

    for item in data:
        if item["market"] == "BTCINR":
            return float(item["last_price"])

    raise RuntimeError("BTCINR price not found")


def place_market_buy_inr(symbol: str, amount_inr: float):
    price = get_btcinr_price()

    quantity = amount_inr / price
    quantity = math.floor(quantity * 1e8) / 1e8  # truncate

    if quantity < MIN_BTC_QTY:
        raise RuntimeError(f"Quantity too small: {quantity}")

    endpoint = "/exchange/v1/orders/create"
    url = COINDCX_BASE_URL + endpoint

    body = {
        "side": "buy",
        "order_type": "market",
        "market": symbol,
        "quantity": f"{quantity:.8f}",
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

    response = requests.post(url, data=body_json, headers=headers, timeout=10)

    try:
        return response.status_code, response.json()
    except Exception:
        return response.status_code, response.text
