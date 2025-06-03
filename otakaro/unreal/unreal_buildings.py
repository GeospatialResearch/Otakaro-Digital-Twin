# -*- coding: utf-8 -*-
"""
This script retrieves building outlines data from the database, then organises and modifies the data by
categorising buildings based on their area, assigning random house model IDs to medium-sized buildings,
and generating mesh names for renaming. It then associates roads with the buildings.
Finally, it saves the modified data to the specified file path.
"""

import logging
import pathlib

import geopandas as gpd

from otakaro.unreal import assign_house_models, buildings_rotation
from src import config
from src.digitaltwin import setup_environment
from src.digitaltwin.utils import LogLevel, setup_logging, get_catchment_area

log = logging.getLogger(__name__)


def save_unreal_buildings_to_file(
        buildings_data: gpd.GeoDataFrame,
        output_dir: pathlib.Path = None) -> None:
    """
    Save the unreal buildings data to a shapefile in the specified directory.

    Parameters
    ----------
    buildings_data : gpd.GeoDataFrame
        A GeoDataFrame containing the unreal buildings data.
    output_dir : pathlib.Path = None
        The directory where the unreal buildings data will be saved.
    """
    # Get the data directory from the environment variable if no output directory is provided
    if output_dir is None:
        output_dir = config.EnvVariable.DATA_DIR
    # Define the file path for storing the unreal buildings data
    buildings_output_path = output_dir / "unreal" / "unreal_buildings.shp"
    # Create the parent directory if it doesn't exist
    buildings_output_path.parent.mkdir(parents=True, exist_ok=True)
    # Save the unreal buildings data to the defined file path
    buildings_data.to_file(buildings_output_path)
    # Log a message indicating the successful saving of the unreal buildings data
    log.info(f"Successfully saved the unreal buildings data to '{buildings_output_path}'.")


def main(
        selected_polygon_gdf: gpd.GeoDataFrame,
        no_house_models: int,
        log_level: LogLevel = LogLevel.DEBUG) -> None:
    """
    Retrieve building outlines data from the database for the specified catchment area, then organise and modify
    the data by categorising buildings based on their area, assigning random house model IDs to medium-sized buildings,
    and generating mesh names for renaming. Finally, save the modified data to the specified file path.

    Parameters
    ----------
    selected_polygon_gdf : gpd.GeoDataFrame
        A GeoDataFrame representing the selected polygon, i.e., the catchment area.
    no_house_models : int
        The number of house models available for assignment.
        Medium-sized buildings will be randomly assigned a house model ID from this pool.
    log_level : LogLevel = LogLevel.DEBUG
        The log level to set for the root logger. Defaults to LogLevel.DEBUG.
        The available logging levels and their corresponding numeric values are:
        - LogLevel.CRITICAL (50)
        - LogLevel.ERROR (40)
        - LogLevel.WARNING (30)
        - LogLevel.INFO (20)
        - LogLevel.DEBUG (10)
        - LogLevel.NOTSET (0)
    """
    # Set up logging with the specified log level
    setup_logging(log_level)
    # Connect to the database
    engine = setup_environment.get_database()
    # Get catchment area
    catchment_area = get_catchment_area(selected_polygon_gdf, to_crs=2193)

    # Retrieve building outlines data from the database for the given catchment area
    # then organise and modify it by categorising buildings based on their area,
    # randomly assigning house model IDs to medium-sized buildings, and creating mesh names for renaming purposes
    buildings_data = assign_house_models.assign_house_models_to_buildings(engine, catchment_area, no_house_models)
    # Assign roads to buildings
    buildings_w_roads = buildings_rotation.get_roads_for_buildings(engine, catchment_area, buildings_data)
    # Save the unreal buildings data to a shapefile (placeholder for now)
    buildings_export = buildings_w_roads.merge(buildings_data[['building_id', 'geometry']], on='building_id', how='left')
    buildings_export = buildings_export.drop(columns=['geometry_x']).rename(columns={'geometry_y': 'geometry'})
    buildings_export = gpd.GeoDataFrame(buildings_export, geometry='geometry')
    save_unreal_buildings_to_file(buildings_export)


if __name__ == "__main__":
    sample_polygon = gpd.GeoDataFrame.from_file("otakaro/unreal/selected_polygon.geojson")
    main(
        selected_polygon_gdf=sample_polygon,
        no_house_models=10,
        log_level=LogLevel.DEBUG
    )
