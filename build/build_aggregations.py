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
1 Fase OFFLINE:

Cálculos para usarse en la web (con geopandas) de manera eficiente

sjoin se hace una vez y crea tablas desacopladas en data/*.csv (no encriptadas aún):
  - aggregations.csv -> scope, region, year, metric, value (coropletas, pag. 2)
  - running_sessions.csv -> métricas Garmin por sesión (home pag. 1, gráficas pag. 3)
  - heatmap_points.csv -> GPS submuestreado por ciudad (HeatMap pag. 4)
  - track_destacada.csv -> trazas destacadas con FC (ColorLine pag. 4)

siguiente paso:
  ejecutar build/encrypt_files.py para encriptar/cifrar los datos a data/*.enc.

Uso:
    python build/build_aggregations.py
"""

from pathlib import Path
import sys

import numpy as np
import pandas as pd
import geopandas as gpd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib.geo import haversine_consecutive
# dentro de esta carpeta deben estar los datos que se procesaran offline
SRC = ROOT.parent / "data-nopreprocessed"
CARTO = ROOT / "cartography"
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

POINTS_CSV = SRC / "strava_points.csv"
SUMMARY_CSV = SRC / "strava_activities_summary.csv"
ACTIVITIES_CSV = SRC / "strava" / "activities.csv"
GARMIN_CSV = SRC / "running_dataset.csv"

# Bounding boxes (lon_min, lat_min, lon_max, lat_max)
BBOX_VALENCIA = (-0.50, 39.40, -0.30, 39.55)
BBOX_LONDON = (-0.55, 51.28, 0.30, 51.70)
BBOX_CADIZ = (-6.55, 36.00, -5.20, 36.95)


# helpers para usar offline

def add_segment_km(points):
    """Añade columna seg_km a cada punto, agrupando por actividad"""
    points = points.sort_values(["file_id", "timestamp"]).reset_index(drop=True)
    parts = []
    for _, grp in points.groupby("file_id"):
        segment = grp.copy()
        segment["seg_km"] = haversine_consecutive(segment["latitude"].values, segment["longitude"].values)
        parts.append(segment)
    return pd.concat(parts, ignore_index=True)


def filter_bbox(df, bbox, lon_col="longitude", lat_col="latitude"):
    """Filtra DataFrame por bounding box."""
    lon_min, lat_min, lon_max, lat_max = bbox
    return df[
        df[lon_col].between(lon_min, lon_max)
        & df[lat_col].between(lat_min, lat_max)
    ].copy()


def to_gdf(df):
    return gpd.GeoDataFrame(
        df.copy(), geometry=gpd.points_from_xy(df.longitude, df.latitude), crs="EPSG:4326"
    )


def iter_years(df):
    """Genera ('ALL', df) y luego (año_str, subdf) por cada año.
    Soporta tanto 'timestamp' (puntos GPS) como 'year' (sesiones Garmin)."""
    yield "ALL", df
    # Detectar si tiene columna 'year' (sesiones Garmin) o 'timestamp' (puntos GPS)
    if "year" in df.columns:
        year_col = df["year"]
    elif "timestamp" in df.columns:
        year_col = df["timestamp"].dt.year
    else:
        return
    for y, sub in df.groupby(year_col):
        if pd.notna(y):
            yield str(int(y)), sub


# agregación por ámbito

def aggregate_scope(points_gdf, regions_gdf, region_col, scope, rows):
    joined = gpd.sjoin(
        points_gdf, regions_gdf[[region_col, "geometry"]], how="inner", predicate="within"
    ).rename(columns={region_col: "region"})
    if joined.empty:
        print(f"[{scope}] sin puntos dentro de la cartografía")
        return
    for year, sub in iter_years(joined):
        g = sub.groupby("region")
        km = g["seg_km"].sum()
        ns = g["file_id"].nunique()
        hr = g["hr"].mean()
        for region in km.index:
            rows.append((scope, region, year, "km", round(float(km[region]), 3)))
            rows.append((scope, region, year, "n_sessions", int(ns[region])))
            if pd.notna(hr[region]):
                rows.append((scope, region, year, "hr", round(float(hr[region]), 1)))
    n = joined["region"].nunique()
    print(f"[{scope}] {len(joined):,} puntos en {n} regiones")


# Fusión Garmin + Strava por fecha — reutilizable
def merge_garmin_strava():
    """Fusiona métricas Garmin con ubicaciones centroide de Strava por fecha."""
    garmin = pd.read_csv(GARMIN_CSV)
    garmin["startTimeLocal"] = pd.to_datetime(garmin["startTimeLocal"], errors="coerce")
    garmin["date"] = garmin["startTimeLocal"].dt.date
    garmin = garmin.dropna(subset=["date"])
    cols = [c for c in ["date", "vO2MaxValue"] if c in garmin.columns]
    garmin = garmin[cols + ["distance"]] if "distance" in garmin.columns else garmin[cols]
    garmin = garmin.sort_values("distance", ascending=False).drop_duplicates("date") \
        if "distance" in garmin.columns else garmin.drop_duplicates("date")

    strava = pd.read_csv(ACTIVITIES_CSV)
    strava["Activity Date"] = pd.to_datetime(strava["Activity Date"], errors="coerce")
    strava["date"] = strava["Activity Date"].dt.date
    strava["file_id"] = strava["Filename"].str.extract(r"activities/(\d+)\.")[0]
    strava = strava[strava["Activity Type"].isin(["Run", "Hike", "Walk"])]
    strava = strava.dropna(subset=["date", "file_id"])[["date", "file_id"]].drop_duplicates("date")

    merged = strava.merge(garmin, on="date", how="inner")
    summary = pd.read_csv(SUMMARY_CSV)[["file_id", "lat_centroid", "lon_centroid"]]
    summary["file_id"] = summary["file_id"].astype(str)
    merged["file_id"] = merged["file_id"].astype(str)
    merged = merged.merge(summary, on="file_id", how="left")
    merged["year"] = pd.to_datetime(merged["date"]).dt.year
    return merged


def aggregate_vo2max_by_scope(scope, regions_gdf, region_col, rows, bbox=None):
    """Agrega VO2max (Garmin geolocalizado con Strava) por región y año.

    Parámetros:
    - scope: nombre del ámbito ("valencia", "london", "spain")
    - regions_gdf: GeoDataFrame con polígonos de regiones
    - region_col: nombre de la columna con ID de región en regions_gdf
    - rows: lista donde acumular filas agregadas
    - bbox: (opcional) tupla (lon_min, lat_min, lon_max, lat_max) para filtrar por ubicación
    """
    merged = merge_garmin_strava().dropna(subset=["vO2MaxValue", "lat_centroid", "lon_centroid"])
    if merged.empty:
        print(f"  [{scope}/vo2max] sin datos")
        return

    if bbox:
        merged = filter_bbox(merged, bbox, lon_col="lon_centroid", lat_col="lat_centroid")
    if merged.empty:
        print(f"  [{scope}/vo2max] sin datos dentro de bbox")
        return

    gdf = gpd.GeoDataFrame(
        merged,
        geometry=gpd.points_from_xy(merged.lon_centroid, merged.lat_centroid),
        crs="EPSG:4326",
    )
    joined = gpd.sjoin(
        gdf, regions_gdf[[region_col, "geometry"]], how="inner", predicate="within"
    ).rename(columns={region_col: "region"})

    if joined.empty:
        print(f"  [{scope}/vo2max] sin datos en regiones")
        return

    # Emitir agregaciones por año
    for year, sub in iter_years(joined):
        stat = sub.groupby("region")["vO2MaxValue"].mean()
        for region, v in stat.items():
            rows.append((scope, region, year, "vo2max", round(float(v), 1)))

    n_regions = joined["region"].nunique()
    print(f"  [{scope}/vo2max] {len(joined):,} sesiones en {n_regions} regiones")

# CSV limpios para graficas - previo encriptar
def build_sessions():
    g = pd.read_csv(GARMIN_CSV, parse_dates=["startTimeLocal"])
    g["distance_km"] = g["distance"] / 1000
    g["pace_min_km"] = np.where(g["averageSpeed"] > 0, (1000 / g["averageSpeed"]) / 60, np.nan)
    g["year"] = g["startTimeLocal"].dt.year
    g = g[(g["distance_km"] >= 0.5) & (g["duration"] >= 120)].copy()
    out = g[[
        "startTimeLocal", "year", "distance_km", "pace_min_km",
        "averageHR", "vO2MaxValue", "averageRunningCadenceInStepsPerMinute", "elevationGain",
    ]].rename(columns={"averageRunningCadenceInStepsPerMinute": "cadence"})
    out.to_csv(DATA / "running_sessions.csv", index=False)
    print(f"-> running_sessions.csv: {len(out):,} sesiones")


def build_heatmap(points):
    frames = []
    for name, bbox in [("Valencia", BBOX_VALENCIA), ("London", BBOX_LONDON), ("Cádiz/Trebujena", BBOX_CADIZ)]:
        sub = filter_bbox(points, bbox)[["latitude", "longitude"]].copy()
        sub["city"] = name
        frames.append(sub)
    hm = pd.concat(frames, ignore_index=True).iloc[::3]  # submuestreo 1 de cada 3
    hm.to_csv(DATA / "heatmap_points.csv", index=False)
    print(f"-> heatmap_points.csv: {len(hm):,} puntos ({hm.city.value_counts().to_dict()})")


def build_track_variant(points, track_name, bbox):
    """Construye una traza destacada recortada para un ámbito geográfico"""
    in_bbox = filter_bbox(points, bbox)
    in_bbox = in_bbox.dropna(subset=["latitude", "longitude", "hr"])
    if in_bbox.empty:
        print(f"-> track_destacada[{track_name}]: sin puntos en el bbox")
        return None

    activity_bbox_distance = in_bbox.groupby("file_id")["seg_km"].sum().rename("bbox_distance_km")
    activity_points = in_bbox.groupby("file_id").size().rename("bbox_points")
    cands = pd.concat([activity_bbox_distance, activity_points], axis=1).reset_index()
    cands = cands.sort_values(["bbox_distance_km", "bbox_points"], ascending=[False, False])

    global_distance = points.groupby("file_id")["seg_km"].sum().rename("global_distance_km")
    global_rank = global_distance.sort_values(ascending=False)
    global_fid = global_rank.index[0]
    global_max_distance = float(global_rank.iloc[0])

    fid = cands.iloc[0]["file_id"]
    selected_bbox_distance = float(cands.iloc[0]["bbox_distance_km"])
    selected_global_distance = float(global_distance.loc[fid]) if fid in global_distance.index else selected_bbox_distance
    selected_bbox_points = int(cands.iloc[0]["bbox_points"])

    track = in_bbox[in_bbox["file_id"] == fid].sort_values("timestamp")[["latitude", "longitude", "hr"]].copy()
    track["track"] = track_name
    track["track_scope"] = track_name
    track["track_file_id"] = str(fid)
    track["track_distance_km"] = round(selected_global_distance, 3)
    track["track_bbox_distance_km"] = round(selected_bbox_distance, 3)
    track["track_bbox_points"] = selected_bbox_points
    
    print(
        f"-> track_destacada[{track_name}]: actividad {fid}, {len(track):,} puntos, "
        f"{selected_global_distance:.3f} km totales, {selected_bbox_distance:.3f} km en el ámbito"
    )
    return track


def build_track(points):
    variants = [
        ("Valencia", BBOX_VALENCIA),
        ("London", BBOX_LONDON),
        ("Trebujena", BBOX_CADIZ),
    ]
    tracks = []
    for name, bbox in variants:
        track = build_track_variant(points, name, bbox)
        if track is not None and not track.empty:
            tracks.append(track)

    if not tracks:
        print("-> track_destacada.csv: sin variantes generadas")
        return

    out = pd.concat(tracks, ignore_index=True)
    out.to_csv(DATA / "track_destacada.csv", index=False)
    print(f"-> track_destacada.csv: {len(out):,} puntos totales en {len(tracks)} variantes")

def main():
    print("Cargando puntos GPS...")
    points = pd.read_csv(POINTS_CSV)
    points["timestamp"] = pd.to_datetime(points["timestamp"], errors="coerce", utc=True)
    points = points.dropna(subset=["latitude", "longitude"])

    print("Calculando km entre puntos consecutivos (Haversine)...")
    points = add_segment_km(points)

    print("Cargando cartografía...")
    barrios = gpd.read_file(CARTO / "valencia_barrios.geojson")
    boroughs = gpd.read_file(CARTO / "london_boroughs.geojson")
    provinces = gpd.read_file(CARTO / "spain_provincias_ES.geojson")

    rows = []
    print("Agregando por ámbito (sjoin)...")
    print("[valencia]")
    aggregate_scope(to_gdf(filter_bbox(points, BBOX_VALENCIA)), barrios, "nombre", "valencia", rows)
    aggregate_vo2max_by_scope("valencia", barrios, "nombre", rows, bbox=BBOX_VALENCIA)
    print("[london]")
    aggregate_scope(to_gdf(filter_bbox(points, BBOX_LONDON)), boroughs, "name", "london", rows)
    aggregate_vo2max_by_scope("london", boroughs, "name", rows, bbox=BBOX_LONDON)
    print("[spain]")
    aggregate_scope(to_gdf(points), provinces, "NUTS_NAME", "spain", rows)
    aggregate_vo2max_by_scope("spain", provinces, "NUTS_NAME", rows)

    agg = pd.DataFrame(rows, columns=["scope", "region", "year", "metric", "value"])
    agg.to_csv(DATA / "aggregations.csv", index=False)
    print(f"-> aggregations.csv: {len(agg):,} filas")

    print("Generando CSVs...")
    build_sessions()
    build_heatmap(points)
    build_track(points)

    print("\npreparar los datos encriptados:  python build/encrypt_files.py")


if __name__ == "__main__":
    main()
