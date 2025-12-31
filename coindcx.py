import time
import hmac
import hashlib
import json
import requests
import os
from decimal import Decimal, ROUND_UP

COINDCX_BASE_URL = "https://api.coindcx.com"

API_KEY = os.getenv("COINDCX_API_KEY")
API_SECRET = os.getenv("COINDCX_API_SECRET")

MIN_BTC_QTY = Decimal("0.00001")


def get_btc_price(symbol: str) -> Decimal:
    resp = requests.get(f"{COINDCX_BASE_URL}/exchange/ticker", timeout=10)
    data = resp.json()

    for item in data:
        if item["market"] == symbol:
            return Decimal(item["last_price"])

    raise RuntimeError("Price not found")


def place_market_buy(symbol: str):
    price = get_btc_price(symbol)

    min_inr = (price * MIN_BTC_QTY).quantize(Decimal("1"), rounding=ROUND_UP)

    endpoint = "/exchange/v1/orders/create"
    url = COINDCX_BASE_URL + endpoint

    body = {
        "side": "buy",
        "order_type": "market",
        "market": symbol,
        "total_price": int(min_inr),
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

    print("📤 COINDCX REQUEST:", body_json)

    response = requests.post(url, data=body_json, headers=headers, timeout=15)

    try:
        data = response.json()
    except Exception:
        data = response.text

    return response.status_code, data
