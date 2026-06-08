# Copyright (c) 2026 Raul Hernandez Lopez
#
# This file is part of the project and is licensed under the
# Creative Commons Attribution-ShareAlike 4.0 International License (CC BY-SA 4.0).
#
# You are free to share and adapt this file under the terms of the CC BY-SA 4.0 license.
# Full license: https://creativecommons.org/licenses/by-sa/4.0/legalcode
#
# @author: Raul Hernandez Lopez

"""Página del análisis del corredor con mapas interactivos de tipo folium"""
import streamlit as st
from streamlit_folium import st_folium

from lib.data_loader import load_heatmap_points, load_track
from lib.charts import heatmap_map, track_map

st.title("🌍 Mapas interactivos (Folium)")

if "heatmap_cities_state" not in st.session_state:
    st.session_state["heatmap_cities_state"] = []
if "track_variant_state" not in st.session_state:
    st.session_state["track_variant_state"] = "Valencia"

# 1 Mapa de calor multiciudad
st.subheader("Mapa de calor de las trazas GPS")
pts = load_heatmap_points()
todas = sorted(pts["city"].unique())

# Widgets interactivos en sidebar
with st.sidebar:
    st.write("**Filtros - Mapa de calor**")
    if not st.session_state["heatmap_cities_state"]:
        st.session_state["heatmap_cities_state"] = todas
    cities = st.multiselect(
        "Ciudades",
        todas,
        default=st.session_state["heatmap_cities_state"],
        key="heatmap_cities_widget",
        on_change=lambda: st.session_state.__setitem__(
            "heatmap_cities_state", st.session_state["heatmap_cities_widget"]
        ),
    )

if cities:
    filtered_pts = pts[pts["city"].isin(cities)]

    # Estadísticas por ciudad (expandible)
    with st.expander("📊 Estadísticas de ciudades", expanded=False):
        cols = st.columns(len(cities))
        for i, city in enumerate(sorted(cities)):
            city_data = filtered_pts[filtered_pts["city"] == city]
            with cols[i]:
                st.metric(city, f"{len(city_data):,} pts")

    # Mapa
    m = heatmap_map(filtered_pts, cities)
    if m is not None:
        st_folium(m, height=560, use_container_width=True,
                  returned_objects=[], key="heatmap")

    # Información interactiva
    st.caption(
        f"**{len(filtered_pts):,} puntos GPS** en {len(cities)} ciudad(es)."
        "Controles: capas (arriba-izq), minimap, pantalla completa."
    )
else:
    st.info("Selecciona al menos una ciudad.")

st.divider()

# 2 Traza de una carrera destacada por FC
st.subheader("Traza destacada coloreada por frecuencia cardíaca")
st.markdown(
    "La actividad **más larga** del conjunto de datos, con cada tramo coloreado según la "
    "FC instantánea (🟢 verde = baja, 🔴 rojo = alta)."
)

with st.sidebar:
    st.write("**Filtros - Traza destacada**")
    track_options = ["Valencia", "London", "Trebujena"]
    if st.session_state["track_variant_state"] not in track_options:
        st.session_state["track_variant_state"] = track_options[0]
    track_label = st.selectbox(
        "Ciudad", track_options,
        index=track_options.index(st.session_state["track_variant_state"]),
        key="track_variant_widget",
        on_change=lambda: st.session_state.__setitem__(
            "track_variant_state", st.session_state["track_variant_widget"]
        ),
    )

track = load_track(track_label)
if track is not None:
    # Estadísticas de la traza
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Puntos GPS", f"{len(track):,}")
    with col2:
        if "hr" in track.columns and track["hr"].notna().any():
            hr_mean = track["hr"].mean()
            st.metric("FC media (ppm)", f"{int(hr_mean)}")
    with col3:
        if "track_distance_km" in track.columns:
            st.metric("Distancia total", f"{track['track_distance_km'].iloc[0]:.2f} km")
        else:
            st.metric("Latitud media", f"{track['latitude'].mean():.3f}°")
    with col4:
        if "track_date" in track.columns:
            st.metric("Fecha de la carrera", track["track_date"].iloc[0])
        elif "track_year" in track.columns:
            st.metric("Año de la carrera", f"{int(track['track_year'].iloc[0])}")

    # Mapa interactivo
    st_folium(track_map(track), height=520, use_container_width=True,
              returned_objects=[], key="track")
    st.caption(
        "🚩 Marcadores: **verde** = inicio, **rojo** = fin, **azules** = cada 5 km con FC instantánea. "
        "Zoom para ver detalles. Pantalla completa disponible."
    )
else:
    st.warning("Sin datos de traza disponible.")
