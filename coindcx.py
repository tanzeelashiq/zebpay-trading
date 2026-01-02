import time
import hmac
import hashlib
import json
import requests
import os

COINDCX_BASE_URL = "https://api.coindcx.com"

API_KEY = os.getenv("COINDCX_API_KEY")
API_SECRET = os.getenv("COINDCX_API_SECRET")

if not API_KEY or not API_SECRET:
    raise RuntimeError("CoinDCX API credentials not set")

API_SECRET = API_SECRET.encode()


def place_market_buy_btcinr(amount_inr: int):
    """
    Places a MARKET BUY for BTCINR using INR amount (₹)
    CoinDCX handles quantity internally
    """

    body = {
        "side": "buy",
        "order_type": "market",
        "market": "BTCINR",
        "total_price": amount_inr,
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
