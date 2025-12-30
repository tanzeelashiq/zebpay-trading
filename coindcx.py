import time
import hmac
import hashlib
import json
import requests
import os

COINDCX_PUBLIC_URL = "https://api.coindcx.com"
COINDCX_TRADE_URL = "https://api.coindcx.com/exchange"

API_KEY = os.getenv("COINDCX_API_KEY")
API_SECRET_RAW = os.getenv("COINDCX_API_SECRET")

if not API_KEY or not API_SECRET_RAW:
    raise RuntimeError("CoinDCX API credentials not set")

API_SECRET = API_SECRET_RAW.encode()

def get_last_price(symbol: str) -> float:
    url = f"{COINDCX_PUBLIC_URL}/exchange/ticker"
    r = requests.get(url, timeout=10)
    data = r.json()

    for item in data:
        if item["market"] == symbol:
            return float(item["last_price"])

    raise RuntimeError(f"Price not found for {symbol}")



def place_market_buy_inr(symbol: str, amount_inr: int):
    last_price = get_last_price(symbol)

    quantity = round(amount_inr / last_price, 5)

    if quantity < 0.0001:
        raise RuntimeError(f"Quantity too small: {quantity}")

    endpoint = "/v1/orders/create"
    url = COINDCX_TRADE_URL + "/v1/orders/create"

    body = {
        "market": symbol,
        "side": "buy",
        "order_type": "market",
        "quantity": quantity,
        "timestamp": int(time.time() * 1000)
    }

    body_json = json.dumps(body, separators=(",", ":"), sort_keys=True)

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

    print("🧪 FINAL DEBUG")
    print("SYMBOL:", symbol)
    print("PRICE:", last_price)
    print("QTY:", quantity)
    print("BODY:", body_json)

    response = requests.post(url, data=body_json, headers=headers, timeout=15)

    try:
        data = response.json()
    except Exception:
        data = response.text

    return response.status_code, data
