import pandas as pd
import pytest
from VaR.model import find_nearest_date, get_rates


class TestRateCalculations:
    @pytest.fixture
    def mock_market_data(self):
        """Génère un dictionnaire de courbes fictives pour les tests."""
        dates = pd.to_datetime(["2024-01-01", "2024-01-05"])
        # Création d'une courbe MAD simple
        df_mad = pd.DataFrame(
            {"Date": dates, "0.5": [0.03, 0.035], "1.0": [0.04, 0.045]}
        )
        # Création d'une courbe EUR simple
        df_eur = pd.DataFrame(
            {"Date": dates, "0.5": [0.01, 0.012], "1.0": [0.02, 0.022]}
        )
        return {"MAD": df_mad, "EUR": df_eur}

    def test_find_nearest_date_exact(self, mock_market_data):
        """Vérifie que la fonction trouve la date exacte si elle existe."""
        target_date = pd.to_datetime("2024-01-01")
        result = find_nearest_date(target_date, mock_market_data["MAD"])
        # Le premier taux de la courbe MAD au 01/01 est 0.03
        assert result["0.5"] == 0.03

    def test_find_nearest_date_approx(self, mock_market_data):
        """Vérifie qu'elle trouve la date la plus proche (ex: 02/01 -> 01/01)."""
        target_date = pd.to_datetime("2024-01-02")
        result = find_nearest_date(target_date, mock_market_data["MAD"])
        assert result["0.5"] == 0.03

    def test_get_rates_unrecognized_currency(self, mock_market_data):
        """Vérifie que la fonction lève une erreur pour une devise inconnue."""
        with pytest.raises(ValueError, match="Devise non reconnue"):
            get_rates("2024-01-01", 180, "GBPMAD", mock_market_data)
