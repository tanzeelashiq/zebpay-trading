import time
import hmac
import hashlib
import json
import requests
import os
from decimal import Decimal, ROUND_DOWN

COINDCX_BASE_URL = "https://api.coindcx.com"

API_KEY = os.getenv("COINDCX_API_KEY")
API_SECRET = os.getenv("COINDCX_API_SECRET")

if not API_KEY or not API_SECRET:
    raise RuntimeError("CoinDCX API keys not set")


def _round_quantity(qty: Decimal) -> Decimal:
    """
    CoinDCX BTC minimum precision is 0.00001
    """
    return qty.quantize(Decimal("0.00001"), rounding=ROUND_DOWN)


def place_market_buy_inr(symbol: str, amount_inr: int):
    """
    Places a market BUY using INR amount.
    CoinDCX internally computes quantity.
    """

    endpoint = "/exchange/v1/orders/create"
    url = COINDCX_BASE_URL + endpoint

    body = {
        "side": "buy",
        "order_type": "market",
        "market": symbol,
        "total_price": amount_inr,
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
        response = requests.post(
            url,
            data=body_json,
            headers=headers,
            timeout=15
        )
    except Exception as e:
        return 500, {"status": "error", "message": str(e)}

    try:
        data = response.json()
    except Exception:
        data = response.text

    print("📥 COINDCX STATUS:", response.status_code)
    print("📥 COINDCX RESPONSE:", data)

    return response.status_code, data
