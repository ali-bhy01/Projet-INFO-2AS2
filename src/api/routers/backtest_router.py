from fastapi import APIRouter, HTTPException
from src.utils.enumeration import Strategy
from src.service.backtest_service import run_backtest
from src.dto.backtest_dto import BacktestDTO

router = APIRouter(prefix="/backtest", tags=["backtest"])


@router.get("", response_model=BacktestDTO)
def backtest(strategy: Strategy) -> BacktestDTO:
    try:
        return run_backtest(strategy)
    except NotImplementedError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
