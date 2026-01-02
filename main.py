from fastapi import FastAPI, Request
from symbol_map import SYMBOL_MAP
from coindcx import place_buy_btcinr
import uvicorn
import os

TRADE_AMOUNT_INR = 200
ENABLE_TRADING = True

app = FastAPI()


@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
    except Exception:
        return {"status": "error", "reason": "invalid json"}

    print("📩 Received alert:", data)

    signal = data.get("signal")
    tv_symbol = data.get("symbol")

    if not signal or not tv_symbol:
        return {"status": "error", "reason": "missing signal or symbol"}

    if signal != "BUY":
        return {"status": "ignored", "reason": "only BUY supported for now"}

    exchange_symbol = SYMBOL_MAP.get(tv_symbol)

    if exchange_symbol != "BTCINR":
        return {"status": "ignored", "reason": "symbol not allowed"}

    if not ENABLE_TRADING:
        return {"status": "blocked", "reason": "trading disabled"}

    print(f"⚡ Executing BUY for {exchange_symbol} (₹{TRADE_AMOUNT_INR})")

    try:
        status_code, response = place_buy_btcinr(
            amount_inr=TRADE_AMOUNT_INR
        )
    except Exception as e:
        print("❌ Order execution failed:", str(e))
        return {
            "status": "error",
            "exchange": "coindcx",
            "error": str(e)
        }

    print("📊 CoinDCX response:", response)

    return {
        "status": "ok",
        "signal": signal,
        "exchange_symbol": exchange_symbol,
        "amount_inr": TRADE_AMOUNT_INR,
        "coindcx_status": status_code,
        "coindcx_response": response
    }


@app.get("/")
def health():
    return {"status": "alive"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
