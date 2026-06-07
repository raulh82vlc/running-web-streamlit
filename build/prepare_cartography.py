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
3 Fase OFFLINE — optimizar la cartografía para carga rápida en web

- Copia barrios de Valencia y boroughs de Londres (no necesitan cambios)
- Filtra España a provincias ES (excluye Canarias) y simplifica la geometría
  para bajar del orden de MB a KB

Uso:
    python build/prepare_cartography.py
"""
import shutil
from pathlib import Path

import geopandas as gpd

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT.parent / "data-nopreprocessed" / "cartography"
OUT = ROOT / "cartography"
OUT.mkdir(exist_ok=True)


def main():
    # Valencia + Londres: copia directa
    for f in ["valencia_barrios.geojson", "london_boroughs.geojson"]:
        shutil.copy(SRC / f, OUT / f)
        print(f"  copiado {f}")

    # España: filtra ES, excluye Canarias (NUTS ES7) y simplifica
    es = gpd.read_file(SRC / "spain_provincias_nuts3.geojson")
    es = es[es["CNTR_CODE"] == "ES"].copy()
    es = es[~es["NUTS_ID"].str.startswith("ES7")]
    es["geometry"] = es["geometry"].simplify(0.005, preserve_topology=True)
    es = es[["NUTS_ID", "NUTS_NAME", "geometry"]].reset_index(drop=True)
    out_path = OUT / "spain_provincias_ES.geojson"
    if out_path.exists():
        out_path.unlink()
    es.to_file(out_path, driver="GeoJSON")
    size_kb = out_path.stat().st_size // 1024
    print(f"  España: {len(es)} provincias -> {out_path.name} ({size_kb} KB)")


if __name__ == "__main__":
    main()
