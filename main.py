from fastapi import FastAPI, Request
from symbol_map import SYMBOL_MAP
import uvicorn

app = FastAPI()

@app.api_route("/probe", methods=["GET", "POST"])
async def probe(request: Request):
    return {
        "method": request.method
    }
    
@app.get("/")
def health():
    return {"status": "alive"}

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    print("Received alert:", data)

    tv_symbol = data.get("symbol")      # e.g. BTCUSDT
    signal = data.get("signal")         # BUY or SELL

    inr_symbol = SYMBOL_MAP.get(tv_symbol)

    print(f"Mapped {tv_symbol} → {inr_symbol}")

    # If coin not found, do nothing
    if inr_symbol is None:
        return {"status": "error", "reason": "symbol not mapped"}

    # Later: send order to ZebPay here
    return {
        "status": "ok",
        "tv_symbol": tv_symbol,
        "mapped_symbol": inr_symbol,
        "signal": data.get("signal"),
        "price": data.get("price"),
        "order_id": data.get("order_id")
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
