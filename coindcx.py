import time
import hmac
import hashlib
import json
import requests
import os
from decimal import Decimal

COINDCX_BASE_URL = "https://api.coindcx.com"

API_KEY = os.getenv("COINDCX_API_KEY")
API_SECRET = os.getenv("COINDCX_API_SECRET")

if not API_KEY or not API_SECRET:
    raise RuntimeError("CoinDCX API keys not set")

MIN_BTC_QTY = Decimal("0.00001")


def get_ticker_price(symbol: str) -> Decimal:
    """
    Fetch current market price
    """
    url = f"{COINDCX_BASE_URL}/exchange/ticker"
    resp = requests.get(url, timeout=10)
    data = resp.json()

    for item in data:
        if item["market"] == symbol:
            return Decimal(item["last_price"])

    raise RuntimeError("Market price not found")


def place_market_buy_min_btc(symbol: str):
    """
    Buy minimum tradable BTC quantity directly
    """

    endpoint = "/exchange/v1/orders/create"
    url = COINDCX_BASE_URL + endpoint

    quantity = MIN_BTC_QTY

    body = {
        "side": "buy",
        "order_type": "market",
        "market": symbol,
        "quantity": float(quantity),
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

    try:
        response = requests.post(url, data=body_json, headers=headers, timeout=15)
    except Exception as e:
        return 500, {"error": str(e)}

    try:
        data = response.json()
    except Exception:
        data = response.text

    print("📥 COINDCX STATUS:", response.status_code)
    print("📥 COINDCX RESPONSE:", data)

    return response.status_code, data
