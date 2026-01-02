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
    return hmac.new(
        API_SECRET,
        payload.encode(),
        hashlib.sha256
    ).hexdigest()


def _round_down(value: float, decimals: int) -> float:
    factor = 10 ** decimals
    return math.floor(value * factor) / factor


def get_btcinr_price() -> float:
    """Fetch latest BTCINR price from CoinDCX"""
    url = "https://public.coindcx.com/market_data/trade_history?pair=BTCINR&limit=1"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return float(r.json()[0]["p"])


def place_market_buy_btcinr(amount_inr: int):
    """
    Converts ₹amount_inr → BTC quantity
    Places market BUY using quantity (CoinDCX-safe)
    """

    price = get_btcinr_price()
    raw_qty = amount_inr / price

    # CoinDCX BTC precision = 5 decimals
    quantity = _round_down(raw_qty, 5)

    MIN_QTY = 0.00001
    if quantity < MIN_QTY:
        raise RuntimeError(f"Quantity too small after rounding: {quantity}")

    body = {
        "side": "buy",
        "order_type": "market",
        "market": "BTCINR",
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
