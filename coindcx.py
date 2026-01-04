import time
import hmac
import hashlib
import json
import requests
import os
from decimal import Decimal

COINDCX_BASE_URL = "https://api.coindcx.com"
API_KEY = os.getenv("COINDCX_API_KEY")
API_SECRET = os.getenv("COINDCX_API_SECRET")  # Don't encode here

if not API_KEY or not API_SECRET:
    raise RuntimeError("CoinDCX API credentials not set")

def _sign(payload: str) -> str:
    """Generate HMAC signature for API request"""
    return hmac.new(
        API_SECRET.encode(),  # Encode only when signing
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

def _make_request(endpoint: str, body: dict):
    """Common request handler with better error handling"""
    body["timestamp"] = int(time.time() * 1000)
    
    # Custom JSON serializer to handle floats without scientific notation
    class DecimalEncoder(json.JSONEncoder):
        def encode(self, obj):
            if isinstance(obj, float):
                # Format float without scientific notation
                return format(obj, 'f')
            return super().encode(obj)
        
        def iterencode(self, obj, _one_shot=False):
            """Encode while avoiding scientific notation for floats"""
            for chunk in super().iterencode(obj, _one_shot):
                # Replace any scientific notation that might have slipped through
                chunk = chunk.replace('e-0', 'E-0')  # Make it easier to find
                if 'E-' in chunk or 'e-' in chunk:
                    # This shouldn't happen with our formatting, but just in case
                    pass
                yield chunk
    
    # Manually build JSON to ensure no scientific notation
    json_parts = []
    json_parts.append('{')
    items = []
    for key, value in body.items():
        if isinstance(value, float):
            # Format float with enough precision, strip trailing zeros
            formatted = format(value, '.10f').rstrip('0').rstrip('.')
            items.append(f'"{key}":{formatted}')
        elif isinstance(value, str):
            items.append(f'"{key}":"{value}"')
        elif isinstance(value, int):
            items.append(f'"{key}":{value}')
        else:
            items.append(f'"{key}":{json.dumps(value)}')
    json_parts.append(','.join(items))
    json_parts.append('}')
    
    body_json = ''.join(json_parts)
    signature = _sign(body_json)
    
    headers = {
        "X-AUTH-APIKEY": API_KEY,
        "X-AUTH-SIGNATURE": signature,
        "Content-Type": "application/json"
    }
    
    print(f"📤 COINDCX REQUEST to {endpoint}:", body_json)
    
    try:
        response = requests.post(
            COINDCX_BASE_URL + endpoint,
            data=body_json,
            headers=headers,
            timeout=15
        )
        
        # Log raw response for debugging
        print(f"📥 COINDCX RAW RESPONSE [{response.status_code}]:")
        print(f"   Headers: {dict(response.headers)}")
        print(f"   Body: {response.text[:500]}")  # First 500 chars
        
        try:
            data = response.json()
        except Exception as e:
            data = {
                "error": "Invalid JSON response", 
                "raw": response.text,
                "status_code": response.status_code,
                "headers": dict(response.headers)
            }
        
        print(f"📥 COINDCX PARSED:", data)
        return response.status_code, data
        
    except requests.exceptions.Timeout:
        return 408, {"error": "Request timeout"}
    except requests.exceptions.ConnectionError:
        return 503, {"error": "Connection failed"}
    except Exception as e:
        return 500, {"error": str(e)}

def get_ticker_price(market: str):
    """Get current market price from ticker"""
    try:
        response = requests.get(
            f"{COINDCX_BASE_URL}/exchange/ticker",
            timeout=10
        )
        data = response.json()
        for ticker in data:
            if ticker.get("market") == market:
                return float(ticker.get("last_price", 0))
        return None
    except Exception as e:
        print(f"Error fetching ticker: {e}")
        return None

def place_market_buy(market: str, amount_inr: int):
    """
    Place a MARKET BUY order (INR-based)
    
    Args:
        market: Trading pair (e.g., "BTCINR", "ETHINR")
        amount_inr: Amount in INR to spend (must be integer)
    """
    # Get current market price
    current_price = get_ticker_price(market)
    if not current_price:
        return 500, {"error": "Could not fetch current market price"}
    
    # Calculate quantity to buy (with small buffer for price fluctuation)
    quantity = (amount_inr * 0.99) / current_price
    
    # Use Decimal to format properly without scientific notation
    quantity_str = format(Decimal(str(quantity)), '.6f')
    quantity_formatted = float(quantity_str)
    
    print(f"💰 Current {market} price: ₹{current_price}")
    print(f"📊 Calculated quantity: {quantity}")
    print(f"📊 Formatted quantity: {quantity_formatted}")
    
    body = {
        "side": "buy",
        "order_type": "market_order",
        "market": market,
        "total_quantity": quantity_formatted,
        "ecode": "I"
    }
    return _make_request("/exchange/v1/orders/create", body)

def place_market_sell(market: str, quantity: float):
    """
    Place a MARKET SELL order (quantity-based)
    
    Args:
        market: Trading pair (e.g., "BTCINR", "ETHINR")
        quantity: Amount of crypto to sell
    """
    body = {
        "side": "sell",
        "order_type": "market_order",
        "market": market,
        "total_quantity": quantity,
        "ecode": "I"  # Required for INR markets
    }
    return _make_request("/exchange/v1/orders/create", body)

def get_balance(currency: str = "INR"):
    """
    Get balance for a specific currency
    
    Args:
        currency: Currency code (e.g., "INR", "BTC", "ETH")
    """
    body = {"timestamp": int(time.time() * 1000)}
    status_code, data = _make_request("/exchange/v1/users/balances", body)
    
    if status_code == 200 and isinstance(data, list):
        for item in data:
            if item.get("currency") == currency:
                return status_code, item
        return 404, {"error": f"Currency {currency} not found"}
    
    return status_code, data

# Backward compatibility
def place_market_buy_btcinr(amount_inr: int):
    """Legacy function for BTC only"""
    return place_market_buy("BTCINR", amount_inr)
