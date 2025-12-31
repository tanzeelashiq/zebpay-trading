from fastapi import FastAPI, Request
from coindcx import place_market_buy_min_btc
import uvicorn

ENABLE_TRADING = True

SYMBOL_MAP = {
    "BTCUSDT": "BTCINR"
}

ALLOWED_SYMBOLS = set(SYMBOL_MAP.values())

app = FastAPI()


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    print("📩 Received alert:", data)

    tv_symbol = data.get("symbol")
    signal = data.get("signal")

    if signal != "BUY":
        return {"status": "ignored", "reason": "only BUY supported"}

    exchange_symbol = SYMBOL_MAP.get(tv_symbol)

    if not exchange_symbol:
        return {"status": "ignored", "reason": "symbol not mapped"}

    if not ENABLE_TRADING:
        return {"status": "blocked", "reason": "trading disabled"}

    print(f"⚡ Executing MIN BTC BUY for {exchange_symbol}")

    status_code, response = place_market_buy_min_btc(exchange_symbol)

    return {
        "status": "ok",
        "signal": signal,
        "exchange_symbol": exchange_symbol,
        "min_btc_qty": "0.00001",
        "coindcx_status": status_code,
        "coindcx_response": response
    }


@app.get("/")
def health():
    return {"status": "alive"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080)
