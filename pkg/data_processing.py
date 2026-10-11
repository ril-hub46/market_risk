"""Parsing et nettoyage des fichiers Excel bruts en DataFrames exploitables.

Fonctions pures : entrée = bytes/chemin de fichier Excel, sortie = pandas
DataFrame/Series nettoyé. Aucune dépendance à un framework web ou UI —
ce module est appelé aussi bien par l'API que par des scripts/tests.
"""

from io import BytesIO
from typing import BinaryIO, Union

import pandas as pd

ExcelSource = Union[str, bytes, BinaryIO]


def _as_buffer(source: ExcelSource) -> Union[str, BinaryIO]:
    """Normalise la source en un objet lisible par pandas.read_excel."""
    return BytesIO(source) if isinstance(source, bytes) else source


def parse_options_file(source: ExcelSource) -> pd.DataFrame:
    """Charge un portefeuille d'options (Spot, Strike, Vol, Maturity, ...)."""
    return pd.read_excel(_as_buffer(source))


def parse_price_series_file(source: ExcelSource, sort_ascending: bool = True) -> pd.DataFrame:
    """Charge une série de prix (actions ou OPCVM) indexée par date.

    La première colonne est traitée comme la date, convertie et utilisée
    comme index. Les autres colonnes sont converties en numérique.
    """
    df = pd.read_excel(_as_buffer(source))
    date_col = df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])
    df = df.sort_values(by=date_col, ascending=sort_ascending)
    df = df.set_index(date_col)
    df = df.apply(pd.to_numeric, errors="coerce")
    return df


def parse_quantities_file(source: ExcelSource) -> pd.Series:
    """Charge les quantités détenues par actif (une ligne de valeurs)."""
    df_qty = pd.read_excel(_as_buffer(source), header=0)
    qty_series = df_qty.iloc[0]
    return pd.to_numeric(qty_series, errors="coerce")


def parse_curve_file(source: ExcelSource) -> pd.DataFrame:
    """Charge une courbe de taux (colonne Date + maturités en colonnes)."""
    df = pd.read_excel(_as_buffer(source))
    df["Date"] = pd.to_datetime(df["Date"])
    return df
