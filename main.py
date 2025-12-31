from fastapi import FastAPI, Request
from coindcx import place_market_buy_inr
import uvicorn

TRADE_AMOUNT_INR = 200
ENABLE_TRADING = True

SYMBOL_MAP = {
    "BTCUSDT": "BTCINR",
    "ETHUSDT": "ETHINR",
    "SOLUSDT": "SOLINR",
    "XRPUSDT": "XRPINR",
}

ALLOWED_SYMBOLS = set(SYMBOL_MAP.values())

app = FastAPI()


@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
    except Exception:
        return {"status": "error", "reason": "invalid JSON"}

    print("📩 Received alert:", data)

    tv_symbol = data.get("symbol")
    signal = data.get("signal")

    if not tv_symbol or not signal:
        return {"status": "error", "reason": "invalid payload"}

    if signal != "BUY":
        return {"status": "ignored", "reason": "only BUY supported"}

    exchange_symbol = SYMBOL_MAP.get(tv_symbol)

    if not exchange_symbol:
        return {"status": "ignored", "reason": "symbol not mapped"}

    if exchange_symbol not in ALLOWED_SYMBOLS:
        return {"status": "ignored", "reason": "symbol not allowed"}

    if not ENABLE_TRADING:
        return {"status": "blocked", "reason": "trading disabled"}

    print(f"⚡ Executing BUY for {exchange_symbol} (₹{TRADE_AMOUNT_INR})")

    status_code, response = place_market_buy_inr(
        symbol=exchange_symbol,
        amount_inr=TRADE_AMOUNT_INR
    )

    return {
        "status": "ok",
        "signal": signal,
        "tv_symbol": tv_symbol,
        "exchange_symbol": exchange_symbol,
        "amount_inr": TRADE_AMOUNT_INR,
        "coindcx_status": status_code,
        "coindcx_response": response,
    }


@app.get("/")
def health():
    return {"status": "alive"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080)
