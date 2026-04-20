from src.models.candle import Candle
import src.dao.price_candle_dao as _base

insert_candle = _base.insert_candle
exists = _base.exists


def get_all(epic: str) -> list[Candle]:
    return [Candle(**r) for r in _base.get_all(epic)]


def get_by_date_range(epic: str, from_date: str, to_date: str) -> list[Candle]:
    return [Candle(**r) for r in _base.get_by_date_range(epic, from_date, to_date)]
