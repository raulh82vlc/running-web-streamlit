# Copyright (c) 2026 Raul Hernandez Lopez
#
# This file is part of the project and is licensed under the
# Creative Commons Attribution-ShareAlike 4.0 International License (CC BY-SA 4.0).
#
# You are free to share and adapt this file under the terms of the CC BY-SA 4.0 license.
# Full license: https://creativecommons.org/licenses/by-sa/4.0/legalcode
#
# @author: Raul Hernandez Lopez

"""
Carga de datos en tiempo real con desencriptado + cacheo (sin geopandas)

Todas las funciones están cacheadas con @st.cache_data
El desencriptado y los filtrados se hacen una sola vez
"""
import sys
import json
from pathlib import Path

import pandas as pd
import streamlit as st

# root del proyecto debe estar en sys.path
# y para importar encrypt_utils.py al hacer debug
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from encrypt_utils import decrypt_csv_file

DATA = ROOT / "data"
CARTO = ROOT / "cartography"

# Metadatos de ámbitos
SCOPES = {
    "Valencia (barrios)": "valencia",
    "Londres (boroughs)": "london",
    "España (provincias)": "spain",
}
GEOJSON = {
    "valencia": "valencia_barrios.geojson",
    "london": "london_boroughs.geojson",
    "spain": "spain_provincias_ES.geojson",
}
YEARS = {
    "valencia": list(range(2019, 2027)),
    "london": list(range(2019, 2022)),
    "spain": list(range(2019, 2027)),
}
METRICS = {
    "valencia": ["km", "n_sessions", "hr", "vo2max"],
    "london": ["km", "n_sessions", "hr", "vo2max"],
    "spain": ["km", "n_sessions", "hr", "vo2max"],
}
METRIC_LABELS = {
    "km": "Km recorridos",
    "n_sessions": "Nº de sesiones",
    "hr": "FC media (ppm)",
    "vo2max": "VO2max medio (mL/kg/min)",
}


@st.cache_data(show_spinner=False)
def _decrypt(name: str):
    key = st.secrets["data_encryption"]["key"]
    return decrypt_csv_file(str(DATA / f"{name}.csv.enc"), key)


@st.cache_data(show_spinner=False)
def load_sessions():
    df = _decrypt("running_sessions")
    df["startTimeLocal"] = pd.to_datetime(df["startTimeLocal"], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def load_aggregations():
    df = _decrypt("aggregations")
    df["year"] = df["year"].astype(str)
    return df


@st.cache_data(show_spinner=False)
def load_heatmap_points():
    return _decrypt("heatmap_points")


@st.cache_data(show_spinner=False)
def load_track():
    return _decrypt("track_destacada")


@st.cache_data(show_spinner=False)
def load_geojson(scope: str):
    with open(CARTO / GEOJSON[scope]) as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def get_aggregation(scope: str, year, metric: str):
    """Devuelve filas (region, value) para un ámbito/año/métrica. year=None -> 'ALL'"""
    df = load_aggregations()
    y = "ALL" if year is None else str(year)
    out = df[(df["scope"] == scope) & (df["year"] == y) & (df["metric"] == metric)]
    return out[["region", "value"]].reset_index(drop=True)
