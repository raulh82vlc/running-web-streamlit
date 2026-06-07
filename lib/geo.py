# Copyright (c) 2026 Raul Hernandez Lopez
#
# This file is part of the project and is licensed under the
# Creative Commons Attribution-ShareAlike 4.0 International License (CC BY-SA 4.0).
#
# You are free to share and adapt this file under the terms of the CC BY-SA 4.0 license.
# Full license: https://creativecommons.org/licenses/by-sa/4.0/legalcode
#
# @author: Raul Hernandez Lopez

"""Utilidades geoespaciales y cálculos de distancia
reutilizable en tiempo de ejecución y offline."""
import numpy as np

R_EARTH = 6371.0  # radio tierra en km


def _haversine_intermediate(lat1_rad, lon1_rad, lat2_rad, lon2_rad):
    """Calcula el intermediate 'a' de la fórmula de Haversine.
    Devuelve array o escalar según entrada.
    """
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    return (np.sin(dlat / 2) ** 2 +
            np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2) ** 2)


def haversine_distance(lat1, lon1, lat2, lon2):
    """Distancia en km entre dos puntos (lat, lon) con fórmula de Haversine.
    Soporta escalares y arrays"""
    lat1_rad = np.radians(lat1)
    lat2_rad = np.radians(lat2)
    lon1_rad = np.radians(lon1)
    lon2_rad = np.radians(lon2)

    a = _haversine_intermediate(lat1_rad, lon1_rad, lat2_rad, lon2_rad)
    return R_EARTH * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def haversine_consecutive(lat_array, lon_array):
    """Distancia Haversine vectorizada entre puntos consecutivos en grados
    Devuelve array de distancias en km
    """
    lat_rad = np.deg2rad(lat_array)
    lon_rad = np.deg2rad(lon_array)

    # Puntos consecutivos: i y i+1
    a = _haversine_intermediate(lat_rad[:-1], lon_rad[:-1],
                                lat_rad[1:], lon_rad[1:])
    seg = R_EARTH * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
    return np.concatenate([[0.0], seg])
