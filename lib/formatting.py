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
Helpers de formato compartidos:
ritmo en mm:ss y formato de valores numéricos
"""
import numpy as np
import pandas as pd


def decimal_to_mmss(val):
    """Ritmo decimal en min/km a texto estándar 'mm:ss' (5.25 -> '05:15')"""
    if pd.isna(val):
        return ""
    mins = int(val)
    segs = int(round((val - mins) * 60))
    if segs == 60:                       # evita 'mm:60' por redondeo
        mins, segs = mins + 1, 0
    return f"{mins:02d}:{segs:02d}"


def mmss_ticks(series, step=0.5):
    """Posiciones y etiquetas mm:ss para un eje de ritmo en Plotly (marcas cada 30 s)"""
    lo = np.floor(series.min() / step) * step
    hi = np.ceil(series.max() / step) * step
    vals = list(np.arange(lo, hi + step / 2, step))
    return vals, [decimal_to_mmss(v) for v in vals]


def value_format(metric):
    """Formato numérico: recuentos enteros, el resto con 2 decimales"""
    return ".0f" if metric == "n_sessions" else ".2f"
