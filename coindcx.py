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

if not API_KEY or not API_SECRET:
    raise RuntimeError("CoinDCX API credentials not set")

API_SECRET = API_SECRET.encode()


def _sign(payload: str) -> str:
    return hmac.new(
        API_SECRET,
        payload.encode(),
        hashlib.sha256
    ).hexdigest()


def _round_down(value: float, decimals: int) -> float:
    factor = 10 ** decimals
    return math.floor(value * factor) / factor


def get_btcinr_price() -> float:
    """Fetch latest BTCINR price"""
    url = "https://public.coindcx.com/market_data/trade_history?pair=BTCINR&limit=1"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return float(r.json()[0]["p"])


def place_buy_btcinr(amount_inr: int):
    """
    SAFEST CoinDCX method:
    LIMIT BUY slightly ABOVE market price
    Behaves like market order but never fails
    """

    market_price = get_btcinr_price()

    # Buy slightly above market to guarantee fill
    limit_price = market_price * 1.002  # +0.2%

    raw_qty = amount_inr / limit_price
    quantity = _round_down(raw_qty, 5)  # BTC precision

    MIN_QTY = 0.00001
    if quantity < MIN_QTY:
        raise RuntimeError(f"Quantity too small: {quantity}")

    body = {
        "side": "buy",
        "order_type": "limit_order",
        "market": "BTCINR",
        "price": round(limit_price, 2),
        "quantity": quantity,
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
