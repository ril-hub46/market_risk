from datetime import date as Date

from fastapi import APIRouter, Form, UploadFile

from api.schemas import OptionsVaRResponse
from pkg.data_processing import parse_curve_file, parse_options_file
from pkg.model import compute_var

router = APIRouter(prefix="/var/options", tags=["options"])


@router.post("", response_model=OptionsVaRResponse)
async def compute_options_var(
    options_file: UploadFile,
    usd_curve: UploadFile,
    eur_curve: UploadFile,
    mad_curve: UploadFile,
    pricing_date: Date = Form(...),
    confidence_level: float = Form(..., ge=0, le=100),
    n_simulations: int = Form(..., gt=0),
) -> OptionsVaRResponse:
    df_options = parse_options_file(await options_file.read())
    curve_map = {
        "USD": parse_curve_file(await usd_curve.read()),
        "EUR": parse_curve_file(await eur_curve.read()),
        "MAD": parse_curve_file(await mad_curve.read()),
    }

    var_value, pnl_total = compute_var(
        df_options, pricing_date, confidence_level / 100, n_simulations, curve_map
    )

    return OptionsVaRResponse(var_value=float(var_value), pnl_total=pnl_total)
