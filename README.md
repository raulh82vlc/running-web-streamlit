# Web de Visualización de Datos con streamlit

### *Running* georreferenciado con fuentes de datos Garmin Connect + Strava (ciudades principales: Valencia y Londres, y provincias en España)

Aplicación **Streamlit multipágina** que visualiza más de una década de entrenamiento de *running* del autor, cruzando dos fuentes propias (Garmin + Strava) con cartografía administrativa oficial. Incluye una **serie temporal** variada con un análisis del mismo, **mapas de coropletas** parametrizables, por años y **mapas interactivos** (Folium) con datos agregados a lo largo de los años. Los datos personales están **cifrados**.

> Asignatura: *Visualización de datos* (MIARFID).  
> Autor: **Raúl Hernández López**.  
> Licencia: [CC BY-SA 4.0](LICENSE)

---

## 1. Características de las páginas

### 🏠 Página de inicio: "Hogar del corredor"
**Propósito:** Introducción general al proyecto y resumen de los datos.

**Características principales:**
- **Métricas visuales** (`st.metric`): sesiones totales, kilómetros acumulados, período de entrenamiento, ciudades.
- **Tabla de fuentes de datos**: origen, tipo de datos y cobertura de cada fuente (Garmin, Strava, cartografía).
- **Sección de originalidad**: explica qué hace único el proyecto (datos propios, cartografía multi-administrativa, VO2max geolocalizado).
- **Notas técnicas expandibles**: metodología, rendimiento (caché, cálculos realizados, [session_state](https://docs.streamlit.io/develop/concepts/architecture/session-state)), privacidad y cifrado.

**Caso de uso:** Se observa una vista global que responde *qué*, *por qué* y *cómo*.

![Página de inicio](screenshots/home.gif)

---

### 📈 Análisis temporal: "Evolución del rendimiento"
**Propósito:** Analizar cómo cambian el entrenamiento y el rendimiento a lo largo del tiempo.

**Características principales:**
- **Filtro por años** (st.slider): todos los años o rango personalizado.
- **4 gráficas interconectadas** (todas respetan el filtro):
  1. **Evolución anual** (barras o línea): km totales o VO2max medio año a año.
  2. **Dispersión entre ritmo y FC**: cada punto es una sesión, y contiene la relación entre velocidad y frecuencia cardíaca, con línea de tendencia.
  3. **Calendario mes×año** (*heatmap*): km acumulados por mes, visualiza patrones estacionales.
  4. **Distribución del ritmo** (cajas): estadísticas (mediana, Q1, Q3, mín, máx) por año con un pop que muestra valores en **mm:ss** (formato estándar de ritmo para velocidad en *running*).
- **Métricas de resumen**: sesiones, km totales, ritmo y FC media en el período correspondiente.

**Caso de uso:** Con esta vista se espera resolver preguntas como: *¿Mi ritmo ha mejorado?*, *¿Entreno más en verano o invierno?*, *¿Ha bajado mi FC con el entrenamiento?*

![Análisis temporal](screenshots/temporal_analysis.gif)

---

### 🗺️ Mapas de coropletas: "Análisis geográfico y temporal por región"
**Propósito:** Explorar métricas de entrenamiento distribuidas geográficamente y compararlas entre regiones.

**Características principales:**
- **Widgets interactivos en barra lateral:**
  - *Ámbito*: Elegir entre Valencia (barrios), Londres (boroughs) o España (provincias).
  - *Métrica*: kilómetros totales, nº de sesiones, FC media y VO2max media.
  - *Año*: visualiza datos globales o filtra por año específico (2019–2026).
- **Mapa coropleta dinámico** (Plotly): coloreado por la métrica seleccionada, con leyenda de cuantiles.
- **Información al pasar el ratón**: nombre de región, valor de la métrica (con máx. 2 decimales).
- **Ranking top-8** bajo el mapa: las 8 regiones con mayores valores, ordenadas y por color distintivo.
- **Resumen numérico**: total de zonas activas, agregado o media de la métrica, región líder.

**Caso de uso:** Trata de dar respuesta a nivel geográfico a cuestiones como: *¿Dónde corro más km?*, *¿Dónde tengo FC más baja?*, *¿Cómo varían los datos año a año?*

![Mapas de coropletas](screenshots/choropleth_maps.gif)

---

### 🌍 Mapas interactivos: "Rutas y mapas interactivos"
**Propósito:** Visualizar las rutas reales en el mapa con contexto geográfico y métricas en tiempo real.

**Características principales:**
- **Mapa de calor multiciudad** (Folium):
  - Capas por ciudad: Valencia, Londres, Cádiz/Trebujena (con controles para activar/desactivar), se usa `st.write` para poder seleccionar una ciudad si se eliminan todas.
  - Cada ciudad tiene su paleta de color: azul -> rojo (baja -> alta densidad de entrenamientos).
  - Puntos individuales de GPS, al hacer zoom se ven más claramente.
  - **Estadísticas expandibles por ciudad**: cantidad de puntos GPS para cada zona.
- **Traza destacada coloreada por FC**:
  - Selector de ciudad (Valencia/Londres/Trebujena): para cada ámbito se precalcula la actividad
    con mayor distancia recorrida dentro de su *bounding box*, trazada punto a punto.
  - Coloreado por frecuencia cardíaca: verde (FC baja) -> rojo (FC alta).
  - Marcadores en los puntos de inicio (verde, play), fin (rojo, stop) y cada 5 km (azul, bandera) con FC en ese punto.
  - **Métricas de la traza**: puntos GPS, FC media, distancia total y fecha de la carrera.
- **Controles interactivos**: minimap, pantalla completa, marcadores con información cada 5km de FC.

**Caso de uso:** Explorar dónde se ha corrido mayores distancias (mapa de calor más intenso). Ver correlación entre geografía y esfuerzo (FC) en un trayecto exigente, y analizar un entrenamiento específico con estadísticas en tiempo real.

![Mapas interactivos](screenshots/interactive_maps.gif)

---

## 2. Requisitos previos

- **Python 3.10+** (probado con 3.13).
- Los datos cifrados (`data/*.enc`) y la cartografía (`cartography/*.geojson`) ya están en el repositorio, no hace falta nada más para ejecutar/desplegar la web.
- La fase *offline* (regenerar datos) solo se necesita si se quiere reconstruir desde los datos registrados de carreras, esto requiere `geopandas` (ver sección 4).

---

## 3. Despliegue (local)

### 3.1 Entorno e instalación
```bash
cd running-web-streamlit

python3 -m venv .venv
source .venv/bin/activate        # macOS/Linux
# Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 3.2 Configurar el *secret* (contraseña de descifrado)
La app lee la contraseña de `.streamlit/secrets.toml`, por motivos de seguridad **no está en el repositorio**.
Si se clona este repo desde cero, se crea a partir de la plantilla:
```bash
cp secrets.toml.example .streamlit/secrets.toml
```
El fichero debe contener:
```toml
[data_encryption]
key = "cambia-esta-clave"
```
> Importante: Los datos incluidos en el repo están cifrados con la contraseña `cambia-esta-clave`. Cuando se quiera usar una contraseña propia, se deben volver a cifrar los datos (sección 6).

### 3.3 Ejecutar la web en local
```bash
streamlit run streamlit_app.py
```
Se abre en **http://localhost:8501**.

---

## 4. Regenerar el conjunto de datos desde cero — fase *offline* (Opcional)

Solo es necesario si se quiere recrear de nuevo las tablas (CSV) a partir de los datos originales procedentes de Garmin o Strava.
Requiere los CSV de origen en `../data-nopreprocessed/` y las dependencias:

```bash
pip install -r build-requirements.txt          # geopandas, shapely, pyproj

python build/prepare_cartography.py             # filtra/simplifica la cartografía de España
python build/build_aggregations.py              # sjoin puntos y polígonos -> data/*.csv
python build/encrypt_files.py                   # cifra -> data/*.enc  
```

**Por qué esta separación:** el `sjoin` espacial sobre 156131 puntos GPS se hace **una sola vez en local**, esto es importante para optimizar lo máximo posible la ejecución en el servidor.
Por tanto, la web desplegada solo lee tablas pequeñas ya agregadas de manera eficiente y (a priori) rápida.
Se evita de esta forma usar **geopandas** en producción, y con esto posibles incidencias en Streamlit Cloud.

---

## 5. Estructura del proyecto

```
running-web-streamlit/
├── streamlit_app.py          # *entry point* (st.navigation con las 4 páginas)
├── views/                    # una página por *script*
│   ├── p1-home.py            # resumen del proyecto, fuentes, notas técnicas
│   ├── p2-temporal_analysis.py  # análisis temporal con 4 gráficas interactivas
│   ├── p3-maps_choropleth.py    # mapas de coropletas parametrizables
│   └── p4-maps_interactive.py   # mapas interactivos (Folium)
├── lib/
│   ├── data_loader.py        # desencriptar/descifrar + @st.cache_data + metadatos de ámbitos
│   ├── formatting.py         # funciones reutilizables formato datos
│   ├── geo.py                # cálculos geoespaciales y de distancias reutilizables
│   └── charts.py             # coropleta Plotly + mapas Folium
├── encrypt_utils.py          # funciones para desencriptar
├── build/                    # FASE OFFLINE
│   ├── prepare_cartography.py # optimización de mapas si fuera necesario
│   ├── build_aggregations.py # calcular datos para usarse en la web (con geopandas)
│   └── encrypt_files.py      # cifrado/desencriptado (*placeholder* de contraseña)
├── data/                     # SOLO los .enc
│   ├── running_sessions.csv.enc
│   ├── aggregations.csv.enc
│   ├── heatmap_points.csv.enc
│   └── track_destacada.csv.enc
├── cartography/              # GeoJSON público (no se cifra)
│   ├── valencia_barrios.geojson
│   ├── london_boroughs.geojson
│   └── spain_provincias_ES.geojson
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml          # gitignored
├── secrets.toml.example
├── requirements.txt          # dependencias en tiempo de ejecución
├── build-requirements.txt    # dependencias de la fase *offline*
├── LICENSE                   # CC BY-SA 4.0
└── README.md
```

---

## 6. Cifrado y cambio de contraseña

- Esquema: PBKDF2-HMAC-SHA256 -> clave Fernet (AES-128). Cada `.enc` =
  `[16 bytes de salt][datos cifrados]`.
- `encrypt_utils.py` (en el repo) **descifra**; `build/encrypt_files.py` (local) **cifra**.
- **Para usar una contraseña** (con la cuenta de Streamlit):
  1. Añadir *key* en `[data_encryption]` y se usará en `build/encrypt_files.py`.
  2. Volver a generar los `.csv` (`python build/build_aggregations.py`) y encriptarlos posteriormente
     (`python build/encrypt_files.py`).
  3. Recordatorio: poner la misma contraseña en `.streamlit/secrets.toml` (local) y en los *Secrets* de
     Streamlit Cloud.

> `secrets.toml` y los `data/*.csv` iniciales están en `.gitignore`.

---

## 7. Despliegue en Streamlit Cloud

1. El contenido de esta carpeta ha sido subido a este repositorio de GitHub.
2. En [share.streamlit.io](https://share.streamlit.io): *New app* -> se elige repo, rama y `streamlit_app.py` como *main file*.
3. *Advanced settings -> Secrets*: pega
   ```toml
   [data_encryption]
   key = "tu-contraseña"
   ```
4. *Deploy*. En tiempo de ejecución no usa geopandas -> no hace falta `packages.txt` con dependencias de sistema.


## 8. Metodología y fórmulas empleadas

### 8.1 Cálculo de distancia geográfica: Haversine
Para calcular la distancia entre dos puntos GPS consecutivos en una traza (ej: marcadores cada 5 km), 
se emplea la **fórmula de Haversine**:

$$a = \sin^{2}\left(\frac{\Delta\varphi}{2}\right) + \cos\varphi_{1}\cos\varphi_{2}\sin^{2}\left(\frac{\Delta\lambda}{2}\right)$$

$$d = 2R\,\arcsin\left(\sqrt{a}\right)$$

Donde:
- **φ, λ** = latitud, longitud en radianes
- **R** = 6371 km (radio terrestre)
- **d** = distancia en km

Implementación: `lib/geo.py` con dos funciones reutilizables:
- `haversine_distance(lat1, lon1, lat2, lon2)` — distancia entre dos puntos (escalares o arrays)
- `haversine_consecutive(lat_array, lon_array)` — distancia vectorizada entre puntos consecutivos (usada en `build/build_aggregations.py` para offline y en `track_map()` para marcar intervalos de 5 km con FC instantánea)

### 8.2 Cruces espaciales (*point-in-polygon*)
Se realiza un **spatial join** (`geopandas.sjoin`) entre:
- **Puntos GPS** (156131 puntos de Strava con coordenadas lat/lon)
- **Polígonos** (barrios, boroughs, provincias)

Resultado: cada punto GPS se asigna al polígono que lo contiene. Esto permite agregar métricas
por región (ej: km totales por barrio, FC media por provincia).

**Optimización:** Este cálculo se realiza **una sola vez en fase offline**
(`build/build_aggregations.py`) para optimizar recursos en web. La web solo lee las tablas agregadas (CSV descifrado).

### 8.3 Agregaciones por región y año
Las métricas se precalculan por:
- **Región** (barrio, borough, provincia)
- **Año** (o global)
- **Métrica** (km, nº sesiones, FC media, VO2max media)

Almacenadas en `data/aggregations.csv.enc` → acceso O(1) en la web sin recalcular.

### 8.4 Librerías y detalle técnico en la visualización

A continuación, se detallan las librerías empleadas, qué hacen a nivel técnico y donde se usan en el proyecto:

| Librería | Detalle técnico | Aplicación en el proyecto |
|---|---|---|
| Streamlit | Gestiona navegación multipágina, filtros laterales, métricas resumen y componentes de interfaz gráfica | Entrada principal de la app y vistas de inicio, análisis temporal y mapas |
| Plotly | Renderiza gráficas interactivas y coropletas con actualización dinámica según filtros | Serie temporal, dispersión ritmo-FC, heatmap mensual, distribuciones y mapas de coropletas |
| Folium | Construye mapas con marcadores y control de visibilidad | Mapa de calor multiciudad y traza georreferenciada destacada |
| streamlit-folium | Inserta el objeto Folium dentro del layout de Streamlit y lo hace interactivo | Vista de mapas interactivos |
| Pandas | Filtrado y agrupación de datos | Carga de sesiones, agregaciones por año y tablas de resumen |
| NumPy | Vectoriza operaciones numéricas y métricas derivadas sobre series de coordenadas | Haversine, distancias acumuladas y cálculos auxiliares |
| Branca | Define escalas de color, leyendas continuas y normalización cromática | Mapas Folium con gradientes y referencia visual |
| Cryptography | Descifra los CSV almacenados en formato seguro antes de su lectura | Carga inicial de datos personales cifrados |

---

## 9. Datos y fuentes

| Fuente | Uso | Licencia |
|---|---|---|
| Garmin Connect (export propio) | Métricas por sesión (FC, VO2max, cadencia…) | Datos personales (cifrados) |
| Strava (export propio) | Trazas GPS (lat/lon, FC, elevación) | Datos personales (cifrados) |
| Ajuntament de València – Open Data | Barrios (88) | CC BY 4.0 |
| Greater London Authority / ONS | Boroughs (33) | Open Government Licence v3.0 |
| Eurostat GISCO NUTS3 2021 | Provincias de España (52, sin Canarias) | EuroGeographics |

## 10. Referencias y créditos

- Ejemplo del Javier Lluch, profesor de la asignatura de Visualización de Datos (mapa de coropletas en Streamlit Cloud):
  <https://github.com/jlluch/MapaPrecioCarburantes>
- Documentación Streamlit (desarrollador): con ejemplos de `st.navigation`, `st.Page`, `st.cache_data`, etc en <https://docs.streamlit.io/develop>.
- Documentación Plotly <https://plotly.com/python/plotly-express/>
- Galería de Streamlit: <https://streamlit.io/gallery>

## 11. Agradecimientos
Se quiere agradecer la labor docente de Javier Lluch, y, también por compartir los scripts de cifrado (encriptado o desencriptado) que han sido reutilizados y ajustados para este trabajo.

---

## 12. Licencia

[Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)](LICENSE)  
© 2026 Raul Hernandez Lopez

Eres libre de compartir y adaptar este proyecto bajo los términos de esta licencia, siempre que des crédito apropiado y distribuyas las adaptaciones bajo la misma licencia.
