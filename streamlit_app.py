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
Punto de entrada de la web
- multipágina (4)

Ejecutar en local:   streamlit run streamlit_app.py
"""
import sys
from pathlib import Path

import streamlit as st

# Asegura que el paquete lib/ funcione en debugging
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

st.set_page_config(
    page_title="Hogar del corredor con datos Garmin + Strava",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="expanded",
)

VIEWS = ROOT / "views"
nav = st.navigation(
    [
        st.Page(VIEWS / "p1-home.py", title="El hogar del corredor", icon=":material/home:", default=True),
        st.Page(VIEWS / "p2-temporal_analysis.py", title="Evolución temporal", icon=":material/show_chart:"),
        st.Page(VIEWS / "p3-maps_choropleth.py", title="Análisis geográfico y temporal por región", icon=":material/map:"),
        st.Page(VIEWS / "p4-maps_interactive.py", title="Rutas y mapas interactivos", icon=":material/public:"),
    ]
)
nav.run()
