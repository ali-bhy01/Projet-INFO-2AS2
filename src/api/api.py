from fastapi import FastAPI
from src.api.routers.backtest_router import router as backtest_router

app = FastAPI(title="DAX Backtest API", version="1.0.0")

app.include_router(backtest_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
