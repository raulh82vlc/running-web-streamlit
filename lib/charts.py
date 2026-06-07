# Copyright (c) 2026 Raul Hernandez Lopez
#
# This file is part of the project and is licensed under the
# Creative Commons Attribution-ShareAlike 4.0 International License (CC BY-SA 4.0).
#
# You are free to share and adapt this file under the terms of the CC BY-SA 4.0 license.
# Full license: https://creativecommons.org/licenses/by-sa/4.0/legalcode
#
# @author: Raul Hernandez Lopez

"""Helper para crear los mapas/figuras de coropleta Plotly y mapas Folium"""
import numpy as np
import pandas as pd
import plotly.express as px
import folium
import branca.colormap as br
from folium.plugins import HeatMap, Fullscreen, MiniMap

from lib.formatting import value_format
from lib.geo import haversine_distance

# centro y zoom por ámbito: (lat, lon, zoom)
CENTER = {
    "valencia": (39.47, -0.38, 11),
    "london": (51.50, -0.12, 9.3),
    "spain": (40.0, -3.6, 4.7),
}
# propiedad del geojson que casa con la columna 'region' de las agregaciones
IDKEY = {
    "valencia": "properties.nombre",
    "london": "properties.name",
    "spain": "properties.NUTS_NAME",
}

# colores
BASE_COLOUR = "YlOrRd"
HR_COLORS = ["green", "yellow", "orange", "red"] # FC: de baja a alta
TRACK_FALLBACK = "#cc0000" # traza sin datos de FC
CITY_GRADIENTS = {
    "Valencia": {0.2: "blue", 0.5: "lime", 0.8: "orange", 1.0: "red"},
    "London": {0.2: "purple", 0.5: "magenta", 0.8: "orange", 1.0: "red"},
    "Cádiz/Trebujena": {0.2: "darkgreen", 0.5: "lime", 0.8: "orange", 1.0: "red"},
}
# escala con colores
SCALE = {"km": BASE_COLOUR, "n_sessions": "Viridis", "hr": "RdBu_r", "vo2max": "RdYlGn"}


def choropleth(df_values, geojson, scope, metric, metric_label):
    """Coropleta interactiva con Plotly"""
    lat, lon, zoom = CENTER[scope]
    fig = px.choropleth_map(
        df_values,
        geojson=geojson,
        locations="region",
        featureidkey=IDKEY[scope],
        color="value",
        color_continuous_scale=SCALE.get(metric, BASE_COLOUR),
        map_style="carto-positron",
        center={"lat": lat, "lon": lon},
        zoom=zoom,
        opacity=0.78,
        hover_name="region",
        labels={"value": metric_label, "region": "Zona"},
    )
    # 2 decimales en los datos del hover (recuentos enteros sin decimales)
    formatted_values = value_format(metric)
    fig.update_traces(
        hovertemplate="<b>%{hovertext}</b><br>" + metric_label + ": %{z:" + formatted_values + "}<extra></extra>"
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=560,
        coloraxis_colorbar_title=metric_label,
    )
    return fig


def heatmap_map(df, cities):
    """HeatMap multiciudad (Folium)"""
    df = df[df["city"].isin(cities)]
    if df.empty:
        return None
    m = folium.Map(
        location=[df.latitude.median(), df.longitude.median()],
        zoom_start=5,
        tiles="CartoDB positron",
        control_scale=True,
    )
    for city in cities:
        sub = df[df.city == city]
        if len(sub):
            HeatMap(
                sub[["latitude", "longitude"]].values.tolist(),
                name=f"{city} ({len(sub):,} pts)",
                radius=6, blur=4, min_opacity=0.3,
                gradient=CITY_GRADIENTS.get(city),
            ).add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    MiniMap(toggle_display=True).add_to(m)
    Fullscreen().add_to(m)
    return m


def track_map(track):
    """Traza coloreada por FC instantánea (Folium ColorLine) con marcadores cada 5 km."""
    track = track.dropna(subset=["latitude", "longitude"]).reset_index(drop=True)
    m = folium.Map(
        location=[track.latitude.mean(), track.longitude.mean()],
        zoom_start=13,
        tiles="CartoDB positron",
        control_scale=True,
    )
    if track["hr"].notna().any():
        hr = track["hr"].fillna(track["hr"].median()).values
        cm = br.LinearColormap(
            HR_COLORS,
            vmin=float(np.nanpercentile(hr, 5)),
            vmax=float(np.nanpercentile(hr, 95)),
            caption="FC (ppm)",
        )
        folium.features.ColorLine(
            list(zip(track.latitude, track.longitude)),
            colors=hr.tolist(), colormap=cm, weight=6,
        ).add_to(m)
        cm.add_to(m)
    else:
        folium.PolyLine(
            list(zip(track.latitude, track.longitude)), color=TRACK_FALLBACK, weight=4
        ).add_to(m)
    folium.Marker(
        [track.iloc[0].latitude, track.iloc[0].longitude],
        popup="Inicio", icon=folium.Icon(color="green", icon="play"),
    ).add_to(m)
    folium.Marker(
        [track.iloc[-1].latitude, track.iloc[-1].longitude],
        popup="Fin", icon=folium.Icon(color="red", icon="stop"),
    ).add_to(m)
    POINT_DISTANCE = 5
    seg_km = [0]  # primer punto: 0 km
    for i in range(1, len(track)):
        dist = haversine_distance(
            track.iloc[i - 1]["latitude"], track.iloc[i - 1]["longitude"],
            track.iloc[i]["latitude"], track.iloc[i]["longitude"]
        )
        seg_km.append(dist)
    track["seg_km"] = seg_km
    track["acum_km"] = track["seg_km"].cumsum()
    next_mark = POINT_DISTANCE
    for _, r in track.iterrows():
        if r["acum_km"] >= next_mark:
            fc_str = f"{int(r['hr'])}" if pd.notna(r['hr']) else "n/d"
            popup = f"<b>Km {next_mark}</b><br>FC: {fc_str} ppm"
            folium.Marker(
                [r["latitude"], r["longitude"]], popup=popup,
                icon=folium.Icon(color="blue", icon="flag")
            ).add_to(m)
            next_mark += POINT_DISTANCE
    Fullscreen().add_to(m)
    return m
