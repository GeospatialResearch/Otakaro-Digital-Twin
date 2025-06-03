# -*- coding: utf-8 -*-
"""
This script retrieves land parcels data from the database and saves it to the specified file path.
"""

import logging
import pathlib

import geopandas as gpd
from sqlalchemy.engine import Engine
from sqlalchemy.sql import text

from src import config
from src.digitaltwin import setup_environment
from src.digitaltwin.utils import LogLevel, setup_logging, get_catchment_area

log = logging.getLogger(__name__)


def get_land_parcels_from_db(engine: Engine, catchment_area: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Retrieve land parcels data from the database that intersects with the given catchment area.

    Parameters
    ----------
    engine : Engine
        The engine used to connect to the database.
    catchment_area : gpd.GeoDataFrame
        A GeoDataFrame representing the catchment area.

    Returns
    -------
    gpd.GeoDataFrame
        A GeoDataFrame containing land parcels data that intersects with the given catchment area.
    """
    # Extract the geometry of the catchment area
    catchment_polygon = catchment_area["geometry"][0]
    # Query to retrieve land parcels that intersect with the catchment polygon
    command_text = """
        SELECT *
        FROM unreal_land_parcels AS land
        WHERE ST_Intersects(land.geometry, ST_GeomFromText(:catchment_polygon, 2193));
        """
    land_parcels_query = text(command_text).bindparams(
        catchment_polygon=str(catchment_polygon)
    )
    # Execute the query and create a GeoDataFrame from the result
    land_parcels_data = gpd.GeoDataFrame.from_postgis(land_parcels_query, engine, geom_col="geometry")
    return land_parcels_data


def save_unreal_fences_to_file(
        land_parcels_data: gpd.GeoDataFrame,
        output_dir: pathlib.Path = None) -> None:
    """
    Save the unreal fences data to a shapefile in the specified directory.

    Parameters
    ----------
    land_parcels_data : gpd.GeoDataFrame
        A GeoDataFrame containing land parcels data.
    output_dir : pathlib.Path = None
        The directory where the unreal fences data will be saved.
    """
    # Get the data directory from the environment variable if no output directory is provided
    if output_dir is None:
        output_dir = config.EnvVariable.DATA_DIR
    # Define the file path for storing the unreal fences data
    fences_output_path = output_dir / "unreal" / "unreal_fences.shp"
    # Create the parent directory if it doesn't exist
    fences_output_path.parent.mkdir(parents=True, exist_ok=True)
    # Save the unreal fences data to the defined file path
    land_parcels_data.to_file(fences_output_path)
    # Log a message indicating the successful saving of the unreal fences data
    log.info(f"Successfully saved the unreal fences data to '{fences_output_path}'.")


def main(
        selected_polygon_gdf: gpd.GeoDataFrame,
        log_level: LogLevel = LogLevel.DEBUG) -> None:
    """
        Retrieve land parcels data from the database that intersects with the given catchment area.

    Retrieve land parcels data from the database for the specified catchment area,
    and save it to the specified file path.

    Parameters
    ----------
    selected_polygon_gdf : gpd.GeoDataFrame
        A GeoDataFrame representing the selected polygon, i.e., the catchment area.
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
    # Retrieve land parcels data from the database for the given catchment area
    land_parcels_data = get_land_parcels_from_db(engine, catchment_area)
    # Save the unreal fences data to a shapefile
    save_unreal_fences_to_file(land_parcels_data)


if __name__ == "__main__":
    sample_polygon = gpd.GeoDataFrame.from_file("otakaro/unreal/selected_polygon.geojson")
    main(
        selected_polygon_gdf=sample_polygon,
        log_level=LogLevel.DEBUG
    )
























