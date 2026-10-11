"""Client HTTP vers l'API Value-at-Risk. Seul point de contact entre web/ et api/."""

import os

import requests

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")


def _file_tuple(uploaded_file):
    return (uploaded_file.name, uploaded_file.getvalue())


def compute_options_var(
    options_file,
    usd_curve_file,
    eur_curve_file,
    mad_curve_file,
    pricing_date,
    confidence_level: float,
    n_simulations: int,
) -> dict:
    files = {
        "options_file": _file_tuple(options_file),
        "usd_curve": _file_tuple(usd_curve_file),
        "eur_curve": _file_tuple(eur_curve_file),
        "mad_curve": _file_tuple(mad_curve_file),
    }
    data = {
        "pricing_date": pricing_date.isoformat(),
        "confidence_level": confidence_level,
        "n_simulations": n_simulations,
    }
    response = requests.post(f"{API_BASE_URL}/var/options", files=files, data=data)
    response.raise_for_status()
    return response.json()


def compute_stocks_var(stocks_file, confidence_level: float, n_simulations: int) -> dict:
    files = {"stocks_file": _file_tuple(stocks_file)}
    data = {"confidence_level": confidence_level, "n_simulations": n_simulations}
    response = requests.post(f"{API_BASE_URL}/var/stocks", files=files, data=data)
    response.raise_for_status()
    return response.json()


def compute_historical_var(
    portfolio_file, quantities_file, confidence_level: float, nb_returns: int
) -> dict:
    files = {
        "portfolio_file": _file_tuple(portfolio_file),
        "quantities_file": _file_tuple(quantities_file),
    }
    data = {"confidence_level": confidence_level, "nb_returns": nb_returns}
    response = requests.post(f"{API_BASE_URL}/var/historical", files=files, data=data)
    response.raise_for_status()
    return response.json()
