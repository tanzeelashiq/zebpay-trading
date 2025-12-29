from fastapi import FastAPI, Request
from symbol_map import SYMBOL_MAP
from coindcx import place_market_buy_inr
from config import TRADE_AMOUNT_INR, ALLOWED_SYMBOLS, ENABLE_TRADING
import uvicorn
import os

app = FastAPI()


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    print("📩 Received alert:", data)

    tv_symbol = data.get("symbol")      # BTCUSDT
    signal = data.get("signal")         # BUY / SELL

    if not tv_symbol or not signal:
        return {"status": "error", "reason": "invalid alert payload"}

    exchange_symbol = SYMBOL_MAP.get(tv_symbol)

    if exchange_symbol is None:
        return {"status": "ignored", "reason": "symbol not mapped"}

    if exchange_symbol not in ALLOWED_SYMBOLS:
        return {"status": "ignored", "reason": "symbol not allowed"}

    if signal != "BUY":
        return {"status": "ignored", "reason": "SELL not supported yet"}

    if not ENABLE_TRADING:
        print("🚫 Trading disabled by config")
        return {"status": "blocked", "reason": "trading disabled"}

    print(f"⚡ Executing BUY for {exchange_symbol} (₹{TRADE_AMOUNT_INR})")

    status_code, response = place_market_buy_inr(
        symbol=exchange_symbol,
        amount_inr=TRADE_AMOUNT_INR
    )

    print("📊 CoinDCX response:", response)

    return {
        "status": "ok",
        "signal": "BUY",
        "tv_symbol": tv_symbol,
        "exchange_symbol": exchange_symbol,
        "amount_inr": TRADE_AMOUNT_INR,
        "coindcx_status": status_code,
        "coindcx_response": response
    }


@app.get("/")
def health():
    return {"status": "alive"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000))
    )
