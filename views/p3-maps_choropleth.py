# Copyright (c) 2026 Raul Hernandez Lopez
#
# This file is part of the project and is licensed under the
# Creative Commons Attribution-ShareAlike 4.0 International License (CC BY-SA 4.0).
#
# You are free to share and adapt this file under the terms of the CC BY-SA 4.0 license.
# Full license: https://creativecommons.org/licenses/by-sa/4.0/legalcode
#
# @author: Raul Hernandez Lopez

"""Página del análisis del corredor con mapas de coropletas"""
import plotly.express as px
import streamlit as st

from lib.data_loader import (
    SCOPES, YEARS, METRICS, METRIC_LABELS,
    get_aggregation, load_geojson,
)
from lib.charts import choropleth
from lib.formatting import value_format

st.title("🗺️ Mapas de coropletas temporales (año/global)")

if "choropleth_scope_state" not in st.session_state:
    st.session_state["choropleth_scope_state"] = list(SCOPES)[0]
if "choropleth_metric_state" not in st.session_state:
    st.session_state["choropleth_metric_state"] = METRICS[SCOPES[st.session_state["choropleth_scope_state"]]][0]
if "choropleth_all_years_state" not in st.session_state:
    st.session_state["choropleth_all_years_state"] = True

# Widgets en la barra lateral
with st.sidebar:
    st.header("Parámetros")
    scope_label = st.selectbox(
        "Ámbito",
        list(SCOPES),
        index=list(SCOPES).index(st.session_state["choropleth_scope_state"]),
        key="choropleth_scope_widget",
        on_change=lambda: st.session_state.__setitem__(
            "choropleth_scope_state", st.session_state["choropleth_scope_widget"]
        ),
    )
    scope = SCOPES[scope_label]
    if st.session_state["choropleth_metric_state"] not in METRICS[scope]:
        st.session_state["choropleth_metric_state"] = METRICS[scope][0]
    metric = st.selectbox(
        "Métrica",
        METRICS[scope],
        format_func=lambda m: METRIC_LABELS[m],
        index=METRICS[scope].index(st.session_state["choropleth_metric_state"]),
        key="choropleth_metric_widget",
        on_change=lambda: st.session_state.__setitem__(
            "choropleth_metric_state", st.session_state["choropleth_metric_widget"]
        ),
    )
    all_years = st.toggle(
        "Todos los años",
        value=st.session_state["choropleth_all_years_state"],
        key="choropleth_all_years_widget",
        on_change=lambda: st.session_state.__setitem__(
            "choropleth_all_years_state", st.session_state["choropleth_all_years_widget"]
        ),
    )
    years = YEARS[scope]
    if all_years:
        year = None
    else:
        if "choropleth_year_state" not in st.session_state or st.session_state["choropleth_year_state"] not in years:
            st.session_state["choropleth_year_state"] = years[-1]
        year = st.select_slider(
            "Año",
            options=years,
            value=st.session_state["choropleth_year_state"],
            key="choropleth_year_widget",
            on_change=lambda: st.session_state.__setitem__(
                "choropleth_year_state", st.session_state["choropleth_year_widget"]
            ),
        )

metric_label = METRIC_LABELS[metric]
periodo = "todos los años" if year is None else f"año {year}"
st.caption(f"**{scope_label}** - {metric_label} - {periodo}")

# Carga de datos
df = get_aggregation(scope, year, metric)

if df.empty:
    if scope == "london" and year is not None and int(year) >= 2022:
        st.info(
            f"Sin datos en **Londres** para {year}"
        )
    else:
        st.warning("No hay datos para esta combinación de parámetros.")
else:
    # Mapa de coropletas amplio (ancho de pantalla)
    fig = choropleth(df, load_geojson(scope), scope, metric, metric_label)
    st.plotly_chart(fig, width="stretch")

    # Resumen numérico bajo el mapa
    c1, c2, c3 = st.columns(3)
    c1.metric("Zonas con actividad", f"{len(df)}")
    if metric == "km":
        c2.metric(f"Total ({metric_label})", f"{df['value'].sum():,.2f}")
    elif metric == "n_sessions":
        c2.metric(f"Total ({metric_label})", f"{df['value'].sum():,.0f}")
    else:
        c2.metric(f"Media ({metric_label})", f"{df['value'].mean():,.2f}")
    c3.metric("Zona líder", df.loc[df['value'].idxmax(), "region"])

    # Ranking top-8 (DEBAJO del mapa, ancho completo)
    st.subheader("Top 8 zonas")
    top = df.nlargest(8, "value").sort_values("value")
    fig_top = px.bar(
        top, x="value", y="region", orientation="h",
        labels={"value": metric_label, "region": ""},
        text="value", color="value",
        color_continuous_scale=px.colors.sequential.YlOrRd,
    )
    vfmt = value_format(metric)
    fig_top.update_traces(
        texttemplate="%{text:.0f}", textposition="outside", cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>" + metric_label + ": %{x:" + vfmt + "}<extra></extra>",
    )
    fig_top.update_layout(
        height=380, margin=dict(l=0, r=10, t=10, b=0),
        coloraxis_showscale=False, yaxis_title="",
    )
    st.plotly_chart(fig_top, width="stretch")
