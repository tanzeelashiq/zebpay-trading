from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from symbol_map import SYMBOL_MAP
from coindcx import place_market_buy_btcinr, get_balance
from config import TRADE_AMOUNT_INR, ALLOWED_SYMBOLS, ENABLE_TRADING
import uvicorn
import os
from datetime import datetime

app = FastAPI(title="TradingView to CoinDCX Bot")

def log(message: str):
    """Simple logger with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

@app.post("/webhook")
async def webhook(request: Request):
    """
    Receives TradingView webhook alerts and executes trades on CoinDCX
    
    Expected JSON format:
    {
        "signal": "BUY" or "SELL",
        "symbol": "BTCUSDT" (TradingView symbol)
    }
    """
    try:
        data = await request.json()
    except Exception as e:
        log(f"❌ Invalid JSON received: {e}")
        return JSONResponse(
            status_code=400,
            content={"status": "error", "reason": "invalid json"}
        )
    
    log(f"📩 Received alert: {data}")
    
    # Extract signal and symbol
    signal = data.get("signal", "").upper()
    tv_symbol = data.get("symbol", "")
    
    if not signal or not tv_symbol:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "reason": "missing signal or symbol"}
        )
    
    # Validate signal type
    if signal not in ["BUY", "SELL"]:
        return {
            "status": "ignored",
            "reason": f"unsupported signal: {signal}"
        }
    
    # Map TradingView symbol to CoinDCX symbol
    exchange_symbol = SYMBOL_MAP.get(tv_symbol)
    if not exchange_symbol:
        return {
            "status": "ignored",
            "reason": f"symbol {tv_symbol} not in mapping"
        }
    
    # Check if symbol is allowed
    if exchange_symbol not in ALLOWED_SYMBOLS:
        return {
            "status": "ignored",
            "reason": f"symbol {exchange_symbol} not in allowed list"
        }
    
    # Check trading kill switch
    if not ENABLE_TRADING:
        log(f"⚠️  Trading disabled - would have executed {signal} for {exchange_symbol}")
        return {
            "status": "blocked",
            "reason": "trading disabled",
            "would_execute": {
                "signal": signal,
                "symbol": exchange_symbol
            }
        }
    
    # Execute the trade
    log(f"⚡ Executing {signal} for {exchange_symbol}")
    
    try:
        if signal == "BUY":
            status_code, response = place_market_buy_btcinr(
                amount_inr=TRADE_AMOUNT_INR
            )
            
        elif signal == "SELL":
            # For SELL, we need the available BTC balance
            bal_status, bal_data = get_balance("BTC")
            if bal_status != 200:
                raise Exception(f"Failed to get balance: {bal_data}")
            
            available_qty = float(bal_data.get("balance", 0))
            if available_qty <= 0:
                return {
                    "status": "error",
                    "reason": "no BTC balance to sell"
                }
            
            # Use generic place_order for sell
            from coindcx import place_order, get_ticker_price
            
            current_price = get_ticker_price(exchange_symbol)
            if not current_price:
                return {"status": "error", "reason": "Could not fetch price"}
            
            status_code, response = place_order(
                market=exchange_symbol,
                side="sell",
                order_type="limit_order",
                total_quantity=available_qty,
                price_per_unit=int(current_price)
            )
        
    except Exception as e:
        log(f"❌ Order execution failed: {str(e)}")
        return {
            "status": "error",
            "exchange": "coindcx",
            "signal": signal,
            "symbol": exchange_symbol,
            "error": str(e)
        }
    
    # Check if order was successful
    success = status_code == 200 and not response.get("error")
    
    if success:
        log(f"✅ {signal} order executed successfully for {exchange_symbol}")
    else:
        log(f"❌ {signal} order failed: {response}")
    
    return {
        "status": "success" if success else "failed",
        "signal": signal,
        "exchange_symbol": exchange_symbol,
        "amount_inr": TRADE_AMOUNT_INR if signal == "BUY" else None,
        "coindcx_status": status_code,
        "coindcx_response": response,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
def health():
    """Health check endpoint"""
    return {
        "status": "alive",
        "service": "tradingview-coindcx-bot",
        "trading_enabled": ENABLE_TRADING,
        "allowed_symbols": ALLOWED_SYMBOLS
    }

@app.get("/balance/{currency}")
async def check_balance(currency: str):
    """Check balance for a specific currency"""
    status_code, data = get_balance(currency.upper())
    return JSONResponse(
        status_code=status_code,
        content=data
    )

if __name__ == "__main__":
    log("🚀 Starting TradingView to CoinDCX Bot")
    log(f"💰 Trade amount: ₹{TRADE_AMOUNT_INR}")
    log(f"📊 Allowed symbols: {ALLOWED_SYMBOLS}")
    log(f"⚡ Trading enabled: {ENABLE_TRADING}")
    
    # Railway provides PORT env variable
    port = int(os.getenv("PORT", 8080))
    log(f"🌐 Server starting on port {port}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )
