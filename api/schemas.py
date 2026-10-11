"""Modèles Pydantic des réponses exposées par l'API."""

from pydantic import BaseModel


class OptionsVaRResponse(BaseModel):
    var_value: float
    pnl_total: list[float]


class StocksVaRResponse(BaseModel):
    var_cf: float
    var_gbm: float
    real_returns: list[float]
    real_returns_dates: list[str]
    sim_porto: list[float]


class HistoricalVaRResponse(BaseModel):
    var_histo: float
    dates: list[str]
    pnl: list[float]
