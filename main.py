from fastapi import FastAPI, Request
from symbol_map import SYMBOL_MAP
from zebpay import place_market_order
from config import TRADE_AMOUNT_INR, ALLOWED_SYMBOLS, ENABLE_TRADING
import uvicorn

app = FastAPI()


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    print("📩 Received alert:", data)

    tv_symbol = data.get("symbol")          # BTCUSDT
    signal = data.get("signal")             # BUY / SELL

    if not tv_symbol or not signal:
        return {"status": "error", "reason": "invalid alert payload"}

    zebpay_symbol = SYMBOL_MAP.get(tv_symbol)

    if zebpay_symbol is None:
        return {"status": "ignored", "reason": "symbol not mapped"}

    if zebpay_symbol not in ALLOWED_SYMBOLS:
        return {"status": "ignored", "reason": "symbol not allowed"}

    if signal not in ["BUY", "SELL"]:
        return {"status": "ignored", "reason": "invalid signal"}

    if not ENABLE_TRADING:
        print("🚫 Trading disabled by config")
        return {"status": "blocked", "reason": "trading disabled"}

    print(f"⚡ Executing {signal} for {zebpay_symbol} (₹{TRADE_AMOUNT_INR})")

    status_code, response = place_market_order(
        symbol=zebpay_symbol,
        side=signal,
        amount_inr=TRADE_AMOUNT_INR
    )

    print("📊 ZebPay response:", response)

    return {
        "status": "ok",
        "signal": signal,
        "tv_symbol": tv_symbol,
        "zebpay_symbol": zebpay_symbol,
        "amount_inr": TRADE_AMOUNT_INR,
        "zebpay_status": status_code,
        "zebpay_response": response
    }


@app.get("/")
def health():
    return {"status": "alive"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
