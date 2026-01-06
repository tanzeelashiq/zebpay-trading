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
    return hmac.new(
        API_SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

def place_order(market: str, side: str, order_type: str, total_quantity: float, price_per_unit: int = None):
    """
    Place an order on CoinDCX
    
    Args:
        market: Trading pair (e.g., "BTCINR")
        side: "buy" or "sell"
        order_type: "limit_order" or "market_order"
        total_quantity: Quantity of crypto to trade
        price_per_unit: Price per unit (required for limit_order, optional for market_order)
    """
    timeStamp = int(time.time() * 1000)
    
    # Build body with required parameters in exact order from docs
    body = {
        "side": side,
        "order_type": order_type,
        "market": market,
        "total_quantity": total_quantity,
        "timestamp": timeStamp
    }
    
    # Add price_per_unit if provided (required for limit orders)
    if price_per_unit is not None:
        body["price_per_unit"] = price_per_unit
    
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

def place_market_buy_btcinr(amount_inr: int):
    """
    Buy BTC - uses 2x minimum quantity
    Uses limit order at current price to ensure execution
    """
    # Get current price
    current_price = get_ticker_price("BTCINR")
    if not current_price:
        return 500, {"error": "Could not fetch price"}
    
    # BTCINR minimum quantity is 0.00001 BTC
    # We'll buy exactly 2x minimum = 0.00002 BTC
    MIN_QUANTITY = 0.00001
    quantity = MIN_QUANTITY * 2  # 0.00002 BTC
    
    # Use current price as limit (will execute immediately like market order)
    price = int(current_price)  # INR must be integer (precision = 0)
    
    order_value = quantity * price
    
    print(f"💰 Price: ₹{price}")
    print(f"📊 Quantity: {quantity} BTC (2x minimum)")
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
    timeStamp = int(time.time() * 1000)
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
