from fastapi import FastAPI, Request
from coindcx import place_market_buy_inr

app = FastAPI()

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    print("📩 Received alert:", data)

    if data.get("signal") != "BUY":
        return {"status": "ignored", "reason": "only BUY supported"}

    print("⚡ Executing BUY for BTCINR (₹200)")

    status_code, response = place_market_buy_inr(
        symbol="BTCINR",
        amount_inr=200
    )

    print("📊 CoinDCX response:", response)

    return {
        "status": "ok",
        "signal": "BUY",
        "exchange_symbol": "BTCINR",
        "amount_inr": 200,
        "coindcx_status": status_code,
        "coindcx_response": response
    }

@app.get("/")
def health():
    return {"status": "alive"}
