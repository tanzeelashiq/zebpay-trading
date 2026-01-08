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

def _sign(payload: str) -> str:
    """Generate HMAC signature for API request"""
    secret_bytes = bytes(API_SECRET, encoding='utf-8')
    return hmac.new(secret_bytes, payload.encode(), hashlib.sha256).hexdigest()

def place_order(market: str, side: str, order_type: str, total_quantity: float, price_per_unit: float):
    """
    Place a single order on CoinDCX - matches documentation exactly
    
    Args:
        market: Trading pair (e.g., "BTCINR")
        side: "buy" or "sell"
        order_type: "limit_order" or "market_order"
        total_quantity: Quantity of crypto to trade
        price_per_unit: Price per unit
    """
    timeStamp = int(round(time.time() * 1000))
    
    # Build body exactly as shown in documentation
    body = {
        "side": side,
        "order_type": order_type,
        "market": market,
        "price_per_unit": price_per_unit,
        "total_quantity": total_quantity,
        "timestamp": timeStamp,
        "ecode": "I"  # Required for INR markets
    }
    
    json_body = json.dumps(body, separators=(',', ':'))
    signature = _sign(json_body)
    
    headers = {
        'Content-Type': 'application/json',
        'X-AUTH-APIKEY': API_KEY,
        'X-AUTH-SIGNATURE': signature
    }
    
    print(f"📤 REQUEST: {json_body}")
    
    try:
        response = requests.post(
            COINDCX_BASE_URL + "/exchange/v1/orders/create",
            data=json_body,
            headers=headers,
            timeout=15
        )
        
        print(f"📥 RESPONSE [{response.status_code}]: {response.text}")
        
        try:
            data = response.json()
        except:
            data = {"error": "Invalid response", "raw": response.text}
        
        return response.status_code, data
        
    except Exception as e:
        return 500, {"error": str(e)}

def get_ticker_price(market: str):
    """Get current market price"""
    try:
        response = requests.get(f"{COINDCX_BASE_URL}/exchange/ticker", timeout=10)
        data = response.json()
        for ticker in data:
            if ticker.get("market") == market:
                return float(ticker.get("last_price", 0))
        return None
    except:
        return None

def get_market_details(market: str):
    """Get market details including min/max limits"""
    try:
        response = requests.get(
            f"{COINDCX_BASE_URL}/exchange/v1/markets_details",
            timeout=10
        )
        data = response.json()
        for item in data:
            if item.get("coindcx_name") == market:
                return item
        return None
    except Exception as e:
        print(f"Error fetching market details: {e}")
        return None

def place_market_buy_btcinr(amount_inr: int):
    """
    Buy BTC - uses 10x minimum quantity from market details
    Uses limit order at current price to ensure execution
    """
    # Get market details
    market_details = get_market_details("BTCINR")
    if not market_details:
        return 500, {"error": "Could not fetch market details"}
    
    min_quantity = float(market_details.get("min_quantity", 0.00001))
    
    # Get current price
    current_price = get_ticker_price("BTCINR")
    if not current_price:
        return 500, {"error": "Could not fetch price"}
    
    # Buy 10x minimum quantity
    quantity = min_quantity * 2
    
    # Price must be integer for INR (precision = 0)
    price = int(current_price)
    
    order_value = quantity * price
    
    print(f"💰 Price: ₹{price}")
    print(f"📊 Quantity: {quantity} BTC (10x minimum)")
    print(f"💵 Order value: ₹{order_value:.2f}")
    
    return place_order(
        market="BTCINR",
        side="buy",
        order_type="limit_order",
        total_quantity=quantity,
        price_per_unit=price
    )

def get_balance(currency: str = "INR"):
    """Get balance for a currency"""
    timeStamp = int(round(time.time() * 1000))
    
    body = {"timestamp": timeStamp}
    json_body = json.dumps(body, separators=(',', ':'))
    signature = _sign(json_body)
    
    headers = {
        'Content-Type': 'application/json',
        'X-AUTH-APIKEY': API_KEY,
        'X-AUTH-SIGNATURE': signature
    }
    
    try:
        response = requests.post(
            COINDCX_BASE_URL + "/exchange/v1/users/balances",
            data=json_body,
            headers=headers,
            timeout=15
        )
        
        data = response.json()
        
        if response.status_code == 200 and isinstance(data, list):
            for item in data:
                if item.get("currency") == currency:
                    return response.status_code, item
            return 404, {"error": f"Currency {currency} not found"}
        
        return response.status_code, data
        
    except Exception as e:
        return 500, {"error": str(e)}
