import time
import hmac
import hashlib
import json
import requests
import os
import math

COINDCX_BASE_URL = "https://api.coindcx.com"

API_KEY = os.getenv("COINDCX_API_KEY")
API_SECRET = os.getenv("COINDCX_API_SECRET").encode()

if not API_KEY or not API_SECRET:
    raise RuntimeError("CoinDCX API credentials not set")


def _sign(payload: str) -> str:
    return hmac.new(API_SECRET, payload.encode(), hashlib.sha256).hexdigest()


def get_btcinr_price() -> float:
    url = "https://public.coindcx.com/market_data/trade_history?pair=I-BTC_INR&limit=1"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return float(r.json()[0]["p"])


def place_market_buy_btcinr(amount_inr: int):
    market_price = get_btcinr_price()

    # CoinDCX requires integer INR price
    price_inr = int(market_price)

    # Compute BTC qty from integer price
    qty = amount_inr / price_inr

    # BTC precision = 5 decimals
    qty = math.floor(qty * 1e5) / 1e5

    if qty < 0.00001:
        raise RuntimeError(f"BTC quantity too small: {qty}")

    body = {
        "side": "buy",
        "order_type": "limit_order",
        "market": "BTCINR",
        "price": price_inr,
        "quantity": qty,
        "timestamp": int(time.time() * 1000)
    }

    body_json = json.dumps(body, separators=(",", ":"))
    signature = _sign(body_json)

    headers = {
        "X-AUTH-APIKEY": API_KEY,
        "X-AUTH-SIGNATURE": signature,
        "Content-Type": "application/json"
    }

    print("📤 COINDCX REQUEST BODY:", body_json)

    response = requests.post(
        COINDCX_BASE_URL + "/exchange/v1/orders/create",
        data=body_json,
        headers=headers,
        timeout=15
    )

    try:
        data = response.json()
    except Exception:
        data = response.text

    return response.status_code, data
