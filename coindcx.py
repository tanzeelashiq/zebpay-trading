import time
import hmac
import hashlib
import requests
import json
import os

COINDCX_BASE_URL = "https://api.coindcx.com"

API_KEY = os.getenv("COINDCX_API_KEY")
API_SECRET = os.getenv("COINDCX_API_SECRET")

if not API_KEY or not API_SECRET:
    raise RuntimeError("CoinDCX API key or secret not set")


def _sign(payload: str) -> str:
    return hmac.new(
        API_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def place_market_order(symbol: str, side: str, amount_inr: int):
    """
    symbol: BTCINR
    side: BUY or SELL
    amount_inr: fixed INR amount (₹200)
    """

    endpoint = "/exchange/v1/orders/create"
    url = COINDCX_BASE_URL + endpoint

    timestamp = int(time.time() * 1000)

    body = {
        "side": side.lower(),           # buy / sell
        "order_type": "market",
        "market": symbol.lower(),       # btcinr
        "price_per_unit": 0,
        "total_quantity": 0,
        "timestamp": timestamp
    }

    # CoinDCX requires either quantity OR total_price
    if side.upper() == "BUY":
        body["total_price"] = amount_inr
    else:
        # SELL: market sell uses quantity, but we’ll block SELL for now
        return 400, {"error": "SELL disabled until balance tracking is added"}

    body_json = json.dumps(body, separators=(",", ":"))

    signature = _sign(body_json)

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
