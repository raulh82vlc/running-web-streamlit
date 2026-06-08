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
Página del análisis del corredor con gráficas

El widget en barra lateral es un filtro por años.

1. Gráfico de barras funciona combinado entre filtro de años y 
seleccionando en el button widget entre Km y VO2max
2. Gráfico de dispersión mediante filtro por años.
3. Mapa de calor mediante el filtro por años.
4. Gráfica de cajas mediante el filtro por años

"""
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from lib.data_loader import load_sessions
from lib.formatting import decimal_to_mmss, mmss_ticks  # ritmo en mm:ss

# constantes
PRIMARY = "#E8590C" # naranja de marca (config.toml)
KM_SCALE = "Blues"
SCATTER_SCALE = "Viridis"
HEATMAP_SCALE = "YlGnBu"
BOX_COLORS = px.colors.qualitative.Plotly
MONTHS = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

st.title("📈 Análisis temporal y rendimiento del corredor")

df = load_sessions()
yr_min, yr_max = int(df["year"].min()), int(df["year"].max())

if "temporal_year_range_state" not in st.session_state:
    st.session_state["temporal_year_range_state"] = (max(yr_min, 2019), yr_max)
if "temporal_metric_state" not in st.session_state:
    st.session_state["temporal_metric_state"] = "Kilómetros"

with st.sidebar:
    st.header("Filtros")
    rango = st.slider(
        "Rango de años",
        yr_min,
        yr_max,
        value=st.session_state["temporal_year_range_state"],
        key="temporal_year_range_widget",
        on_change=lambda: st.session_state.__setitem__(
            "temporal_year_range_state", st.session_state["temporal_year_range_widget"]
        ),
    )

sel = df[df["year"].between(*rango)].copy()

# Estadísticas generales del corredor
c1, c2 = st.columns(2)
c1.metric("Sesiones", f"{len(sel):,}")
c2.metric("Km", f"{sel['distance_km'].sum():,.2f}")

c3, c4 = st.columns(2)
c3.metric("Ritmo medio", f"{decimal_to_mmss(sel['pace_min_km'].mean())} min/km")
c4.metric("FC media", f"{sel['averageHR'].mean():.0f} ppm")
st.divider()

# 1 Gráfico de barras con la Evolución anual (km o VO2max)
st.subheader("1. Gráfico de barras: Evolución anual")
metrica = st.radio(
    "Variable",
    ["Kilómetros", "VO2max"],
    horizontal=True,
    index=["Kilómetros", "VO2max"].index(st.session_state["temporal_metric_state"]),
    key="temporal_metric_widget",
    on_change=lambda: st.session_state.__setitem__(
        "temporal_metric_state", st.session_state["temporal_metric_widget"]
    ),
)
if metrica == "Kilómetros":
    anual = sel.groupby("year", as_index=False)["distance_km"].sum()
    fig1 = px.bar(
        anual, x="year", y="distance_km", text_auto=".0f",
        labels={"year": "Año", "distance_km": "Km totales"},
        color="distance_km", color_continuous_scale=KM_SCALE,
    )
    fig1.update_traces(hovertemplate="Año %{x}<br>Km totales: %{y:.2f}<extra></extra>")
    fig1.update_layout(coloraxis_showscale=False)
else:
    anual = sel.dropna(subset=["vO2MaxValue"]).groupby("year", as_index=False)["vO2MaxValue"].mean()
    fig1 = px.line(
        anual, x="year", y="vO2MaxValue", markers=True,
        labels={"year": "Año", "vO2MaxValue": "VO2max (mL/kg/min)"},
    )
    fig1.update_traces(
        line_color=PRIMARY,
        hovertemplate="Año %{x}<br>VO2max: %{y:.2f} mL/kg/min<extra></extra>",
    )
fig1.update_xaxes(dtick=1)
st.plotly_chart(fig1, width="stretch")

# 2 Gráfico de Dispersión junto al ritmo-FC
st.subheader("2. Gráfico de dispersión: relación Ritmo – Frecuencia Cardíaca (FC)")
sc = sel.dropna(subset=["pace_min_km", "averageHR"]).copy()
if not sc.empty:
    lo, hi = sc["pace_min_km"].quantile([0.01, 0.99])
    sc = sc[sc["pace_min_km"].between(lo, hi)]
    sc["pace_mmss"] = sc["pace_min_km"].apply(decimal_to_mmss)
    fig2 = px.scatter(
        sc, x="pace_min_km", y="averageHR", color="distance_km",
        custom_data=["pace_mmss", "distance_km"],
        color_continuous_scale=SCATTER_SCALE, opacity=0.6,
        labels={"pace_min_km": "Ritmo (min:seg/km)", "averageHR": "FC media (ppm)",
                "distance_km": "Distancia (km)"},
    )
    fig2.update_traces(
        selector=dict(mode="markers"),
        hovertemplate=("Ritmo: %{customdata[0]} min/km<br>FC: %{y:.0f} ppm"
                       "<br>Distancia: %{customdata[1]:.2f} km<extra></extra>"),
    )
    # recta de regresión lineal
    if sc["pace_min_km"].nunique() > 1:
        coef = np.polyfit(sc["pace_min_km"], sc["averageHR"], 1)
        xs = np.linspace(sc["pace_min_km"].min(), sc["pace_min_km"].max(), 50)
        fig2.add_scatter(
            x=xs, y=np.polyval(coef, xs), mode="lines", name="Tendencia",
            line=dict(color="darkred", dash="dash"),
        )
    # eje X invertido (ritmo más rápido a la derecha) con mm:ss
    tickvals, ticktext = mmss_ticks(sc["pace_min_km"])
    fig2.update_xaxes(autorange="reversed", tickvals=tickvals, ticktext=ticktext)
    fig2.update_layout(height=480)
    st.plotly_chart(fig2, width="stretch")
    st.caption("Eje X invertido: a la derecha, ritmos más rápidos. La recta es una regresión lineal.")

# 3 Heatmap o mapa de calor con el calendario (mes x año)
st.subheader("3. Mapa de calor: Kilómetros (mes y año)")
hm = sel.copy()
hm["month"] = hm["startTimeLocal"].dt.month
pivot = hm.pivot_table(index="month", columns="year", values="distance_km",
                       aggfunc="sum", fill_value=0).reindex(range(1, 13), fill_value=0)
fig3 = px.imshow(
    pivot, labels={"x": "Año", "y": "Mes", "color": "Km"},
    x=[str(c) for c in pivot.columns], y=MONTHS,
    color_continuous_scale=HEATMAP_SCALE, aspect="auto", text_auto=".0f",
)
fig3.update_traces(hovertemplate="Mes %{y} - Año %{x}<br>%{z:.2f} km<extra></extra>")
fig3.update_layout(height=460)
st.plotly_chart(fig3, width="stretch")

# 4 Gráfico de cajas del ritmo por año
st.subheader("4. Gráfica de cajas: Distribución del Ritmo (mm:ss) por año")
vi = sel.dropna(subset=["pace_min_km"])
vi = vi[vi["pace_min_km"].between(*vi["pace_min_km"].quantile([0.01, 0.99]))]
vi = vi.copy()
# Bug arreglado para pintar el ritmo en mm:ss:
# Plotly no dibuja cajas sobre un eje temporal, así al aceptar solo valores numéricos
# Como de manera nativa el box se formatea según el eje (decimales),
# se ha desactivado (hoverinfo="skip") y se
# superpone una capa invisible de puntos que añade el tooltip en mm:ss.
colores = BOX_COLORS
years = sorted(vi["year"].unique())
fig4 = go.Figure()
hx, hy, hcd = [], [], []
for i, y in enumerate(years):
    s = vi.loc[vi["year"] == y, "pace_min_km"]
    q1, med, q3 = s.quantile([0.25, 0.5, 0.75])
    lo, hi = s.min(), s.max()
    fig4.add_trace(go.Box(
        x=[str(y)], q1=[q1], median=[med], q3=[q3], lowerfence=[lo], upperfence=[hi],
        name=str(y), marker_color=colores[i % len(colores)], hoverinfo="skip",
    ))
    cd = [decimal_to_mmss(med), decimal_to_mmss(q1), decimal_to_mmss(q3),
          decimal_to_mmss(lo), decimal_to_mmss(hi)]
    for yy in np.linspace(lo, hi, 20):
        hx.append(str(y)); hy.append(float(yy)); hcd.append(cd)
# Capa invisible: captura el hover sobre toda la caja y muestra las estadísticas en m:ss
fig4.add_trace(go.Scatter(
    x=hx, y=hy, mode="markers", showlegend=False,
    marker=dict(size=22, color="rgba(0,0,0,0)"), customdata=hcd,
    hovertemplate=("<b>Año %{x}</b><br>Mediana: %{customdata[0]}<br>"
                   "Q1: %{customdata[1]} - Q3: %{customdata[2]}<br>"
                   "Mín: %{customdata[3]} - Máx: %{customdata[4]}<extra></extra>"),
))
fig4.update_layout(showlegend=False, height=460, xaxis_title="Año", hovermode="closest")
tickvals, ticktext = mmss_ticks(vi["pace_min_km"])
fig4.update_yaxes(title="Ritmo (min:seg/km)", autorange="reversed",
                  tickvals=tickvals, ticktext=ticktext)
st.plotly_chart(fig4, width="stretch")
