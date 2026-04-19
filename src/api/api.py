from fastapi import FastAPI
from src.api.routers.backtest_router import router as backtest_router
from src.api.core.config import add_cors

app = FastAPI(title="DAX Backtest API", version="1.0.0")

add_cors(app)
app.include_router(backtest_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
