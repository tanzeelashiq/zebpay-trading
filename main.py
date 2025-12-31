from fastapi import FastAPI, Request
from coindcx import place_market_buy_inr

app = FastAPI()

TRADE_AMOUNT_INR = 200
EXCHANGE_SYMBOL = "BTCINR"


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    print("📩 Received alert:", data)

    if data.get("signal") != "BUY":
        return {"status": "ignored"}

    print(f"⚡ Executing BUY for {EXCHANGE_SYMBOL} (₹{TRADE_AMOUNT_INR})")

    status_code, response = place_market_buy_inr(
        symbol=EXCHANGE_SYMBOL,
        amount_inr=TRADE_AMOUNT_INR
    )

    return {
        "status": "ok",
        "signal": "BUY",
        "exchange_symbol": EXCHANGE_SYMBOL,
        "amount_inr": TRADE_AMOUNT_INR,
        "coindcx_status": status_code,
        "coindcx_response": response
    }
