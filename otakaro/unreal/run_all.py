# -*- coding: utf-8 -*-
"""This script runs each module in the Otakaro Unreal using a Sample Polygon."""

import pathlib

import geopandas as gpd

from otakaro.unreal import unreal_buildings, unreal_fences
from src.digitaltwin import retrieve_from_instructions
from src.digitaltwin.utils import LogLevel
from src.run_all import main


DEFAULT_MODULES_TO_PARAMETERS = {
    retrieve_from_instructions: {
        "log_level": LogLevel.INFO,
        "instruction_json_path": pathlib.Path("otakaro/unreal/static_boundary_instructions.json")
    },
    unreal_buildings: {
        "log_level": LogLevel.INFO,
        "no_house_models": 10
    },
    unreal_fences: {
        "log_level": LogLevel.INFO
    }
}


if __name__ == '__main__':
    # Run all modules with sample polygon
    sample_polygon = gpd.GeoDataFrame.from_file("otakaro/unreal/selected_polygon.geojson")
    main(sample_polygon, DEFAULT_MODULES_TO_PARAMETERS)
