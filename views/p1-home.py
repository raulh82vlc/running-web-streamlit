# Copyright (c) 2026 Raul Hernandez Lopez
#
# This file is part of the project and is licensed under the
# Creative Commons Attribution-ShareAlike 4.0 International License (CC BY-SA 4.0).
#
# You are free to share and adapt this file under the terms of the CC BY-SA 4.0 license.
# Full license: https://creativecommons.org/licenses/by-sa/4.0/legalcode
#
# @author: Raul Hernandez Lopez

"""Landing page: resumen del proyecto, fuentes, notas técnicas"""
import pandas as pd
import streamlit as st

from lib.data_loader import load_sessions

st.title("🏃 Running georreferenciado - Garmin Connect + Strava")
st.markdown(
"""
Visualización de **más de una década de entrenamiento** de *running* del autor a partir de dos fuentes propias:

- **Garmin Connect** - métricas fisiológicas por sesión: FC, VO2max y ritmo o distancia.
- **Strava** - trazas GPS cruzadas con cartografía oficial de Valencia, Londres y España.

El objetivo es responder a *dónde* se entrena, no solo *cuándo*: qué barrios son rutas habituales,
cómo varía la FC o el VO2max según la zona, y cómo evoluciona todo año a año.
"""
)

df = load_sessions()

c1, c2 = st.columns(2)
c1.metric("Sesiones (Garmin)", f"{len(df):,}")
c2.metric("Km totales", f"{df['distance_km'].sum():,.2f}")

c3, c4 = st.columns(2)
c3.metric("Periodo", f"{int(df['year'].min())}–{int(df['year'].max())}")
c4.metric("Ciudades", "3", help="Valencia, Londres y Cádiz/Trebujena")

st.caption(
    "≈156.000 puntos GPS extraídos de las trazas de Strava, cruzados espacialmente con "
    "88 barrios de Valencia, 33 *boroughs* de Londres y 52 provincias de España."
)

st.divider()

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("¿Qué se puede explorar?")
    st.markdown(
        """
- **🗺️ Mapas de coropletas** - elige ámbito (Valencia/Londres/España), métrica
  (km, sesiones, FC, VO2max) y año; el mapa se recolorea al instante.
- **📈 Análisis temporal** - evolución anual, relación ritmo-FC, calendario de km y
  distribución del ritmo por año, todo filtrable.
- **🌍 Mapas interactivos** - mapa de calor multiciudad y la traza más larga coloreada por FC.
"""
    )
with col_b:
    st.subheader("Originalidad")
    st.markdown(
        """
- **Datos de origen propio**: API de Garmin Connect + exportación de la web de Strava,
  con más de una década de actividad deportiva de correr.
- **Cartografía multi-administrativa**: Eurostat (Europa), Ajuntament de València (municipal)
  y Greater London Authority (municipal británica), bajo licencias abiertas.
- **Fuentes combinadas**: el VO2max (solo Garmin) se geolocaliza con el centroide GPS
  (solo Strava), un dato que ninguna fuente ofrece por separado.
"""
    )

st.subheader("Fuentes de datos")
st.table(
    pd.DataFrame(
        {
            "Fuente": [
                "Garmin Connect", "Strava (trazas GPS)",
                "Ajuntament de València", "Greater London Authority", "Eurostat NUTS3",
            ],
            "Tipo": [
                "Métricas por sesión (FC, VO2max, ritmo, distancia)",
                "Puntos GPS (lat/lon)",
                "Polígonos de barrios", "Polígonos de boroughs", "Polígonos de provincias",
            ],
            "Cobertura": ["2012–2026", "2019–2026", "88 barrios", "33 boroughs", "52 provincias"],
            "Licencia": ["Datos propios", "Datos propios", "CC BY 4.0", "OGL v3.0", "EuroGeographics"],
        }
    )
)

with st.expander("Notas técnicas (metodología, rendimiento y seguridad)"):
    st.markdown(
        """
- **Preparación offline**: los cruces espaciales (*point-in-polygon* sobre ≈156.000 puntos,
  distancias con Haversine) se precomputan una sola vez; la web solo lee tablas agregadas, así
  no ejecuta ningún tipo de cálculos que requieran demasiada computación en tiempo real, y, además,
  al hacer el despliegue no necesita *geopandas*.
- **Caché y estado**: todo el acceso a datos usa `@st.cache_data`, para carga rápida al cambiar un widget solo
  recalcula lo no cacheado. El estado de filtros y selección entre páginas se conserva con
  `st.session_state` ([docs](https://docs.streamlit.io/develop/concepts/architecture/session-state)).
- **Privacidad**: los datos personales se sirven cifrados (Fernet/AES + PBKDF2) y se descifran
  en memoria del servidor con una clave guardada en *secrets*.
- **Librerías**: Streamlit, Plotly (coropletas y gráficas), Folium (mapas interactivos),
  pandas/numpy y cryptography (Fernet/AES + PBKDF2, gracias @jlluch).
"""
)

with st.expander("Conclusiones"):
    st.markdown(
"""
        - El corredor tiene una **concentración geográfica** en el tiempo tras asentar rutar de entrenamiento para eventos concretos como la medio maratón.
        - **Fisiológicamente**: A nivel de *Frecuencia Cardíaca (FC)* y *capacidad aeróbica (VO2max)* se relevan las principales provincias
        que han contribuido al mezclar fuentes heterogéneas de datos (Garmin y Strava).
        - El desglose de gráficos o mapas por página ayuda a leer y entender los contenidos de manera intuitiva.
        - Es fundamental optimizar para visualizar los datos en mapas y gráficos de manera rápida, y, hacerlo de manera segura (cifrado).
"""
)
