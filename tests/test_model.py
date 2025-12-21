from datetime import date

import pandas as pd
import pytest

from var.model import find_nearest_date, get_rates


class TestVaREngine:
    """Focuses on date proximity logic and rate interpolation."""

    @pytest.fixture
    def mock_market_data(self):
        """Excel data structure (Date column + maturities)."""
        dates = pd.to_datetime(["2024-12-30", "2025-01-05"])
        df_mad = pd.DataFrame(
            {
                "Date": dates,
                "0.5": [0.030, 0.032],  # 6 months rates
                "1.0": [0.035, 0.037],  # 1 year rates
            }
        )

        df_eur = pd.DataFrame(
            {"Date": dates, "0.5": [0.010, 0.011], "1.0": [0.015, 0.016]}
        )
        return {
            "MAD": df_mad,
            "EUR": df_eur,
            "USD": df_eur,  # Reusing EUR for USD mock
        }

    def test_find_nearest_date_exact_match(self, mock_market_data):
        """Ensures the function picks the exact row when the date exists."""
        target = date(2024, 12, 30)
        result = find_nearest_date(target, mock_market_data["MAD"])
        # Expecting the 6m rate of the first row
        assert result["0.5"] == 0.030

    def test_find_nearest_date_fallback(self, mock_market_data):
        """Ensures the function picks the closest date when exact match is missing."""
        # 2024-12-31 is closer to 2024-12-30 than to 2025-01-05
        target = date(2024, 12, 31)
        result = find_nearest_date(target, mock_market_data["MAD"])
        assert result["0.5"] == 0.030

    # Rate Retrieval & Interpolation Tests ---

    def test_get_rates_unsupported_currency(self, mock_market_data):
        """Verifies that the engine raises a ValueError for unknown currency pairs."""
        with pytest.raises(ValueError, match="Devise non reconnue"):
            get_rates(date(2024, 12, 30), 180, "JPYMAD", mock_market_data)

    def test_get_rates_interpolation_accuracy(self, mock_market_data):
        """
        Verifies that the rates returned are floats and within
        the expected range after interpolation.
        """
        # Testing for 180 days (approx 0.5 year)
        r_d, r_f = get_rates(
            date=date(2024, 12, 30), T=180, currency="EURMAD", dic=mock_market_data
        )

        assert isinstance(r_d, float)
        assert isinstance(r_f, float)
        # Rates should be close to the 0.5 maturity values defined in mock
        assert 0.029 <= r_d <= 0.031
        assert 0.009 <= r_f <= 0.011
