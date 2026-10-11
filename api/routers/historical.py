from fastapi import APIRouter, Form, UploadFile

from api.schemas import HistoricalVaRResponse
from pkg.data_processing import parse_price_series_file, parse_quantities_file
from pkg.model import compute_historical_var

router = APIRouter(prefix="/var/historical", tags=["historical"])


@router.post("", response_model=HistoricalVaRResponse)
async def compute_historical_var_route(
    portfolio_file: UploadFile,
    quantities_file: UploadFile,
    confidence_level: float = Form(..., ge=0, le=100),
    nb_returns: int = Form(..., gt=0),
) -> HistoricalVaRResponse:
    df_prices = parse_price_series_file(await portfolio_file.read(), sort_ascending=False)
    quantities = parse_quantities_file(await quantities_file.read())

    var_histo, portfolio_returns = compute_historical_var(
        df_prices, quantities, confidence_level / 100, nb_returns
    )

    return HistoricalVaRResponse(
        var_histo=float(var_histo),
        dates=[d.isoformat() for d in portfolio_returns.index],
        pnl=portfolio_returns.tolist(),
    )
