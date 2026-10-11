import numpy as np
from fastapi import APIRouter, Form, UploadFile

from api.schemas import StocksVaRResponse
from pkg.data_processing import parse_price_series_file
from pkg.model import GBM, CF_var

router = APIRouter(prefix="/var/stocks", tags=["stocks"])


@router.post("", response_model=StocksVaRResponse)
async def compute_stocks_var(
    stocks_file: UploadFile,
    confidence_level: float = Form(..., ge=0, le=100),
    n_simulations: int = Form(..., gt=0),
) -> StocksVaRResponse:
    df = parse_price_series_file(await stocks_file.read(), sort_ascending=True)

    returns = np.log(df / df.shift(1)).dropna()
    n_assets = returns.shape[1]
    weights = np.ones(n_assets) / n_assets
    real_returns = returns.dot(weights)

    var_cf = CF_var(returns, 100 - confidence_level, weights)
    var_gbm, sim_porto = GBM(n_simulations, returns, weights, confidence_level)

    return StocksVaRResponse(
        var_cf=float(var_cf),
        var_gbm=float(var_gbm),
        real_returns=real_returns.tolist(),
        real_returns_dates=[d.isoformat() for d in real_returns.index],
        sim_porto=np.asarray(sim_porto).tolist(),
    )
