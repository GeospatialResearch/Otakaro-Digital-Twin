# -*- coding: utf-8 -*-
"""
This script retrieves building outlines data from the database, then organises and modifies the data by
categorising buildings based on their area, assigning random house model IDs to medium-sized buildings,
and generating mesh names for renaming. Finally, it saves the modified data to the specified file path.
"""

import random

import geopandas as gpd
import pandas as pd
from sqlalchemy.engine import Engine
from sqlalchemy.sql import text


def get_buildings_from_db(engine: Engine, catchment_area: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Retrieve building outlines data from the database that intersects with the given catchment area.

    Parameters
    ----------
    engine : Engine
        The engine used to connect to the database.
    catchment_area : gpd.GeoDataFrame
        A GeoDataFrame representing the catchment area.

    Returns
    -------
    gpd.GeoDataFrame
        A GeoDataFrame containing building outlines data that intersects with the given catchment area.
    """
    # Extract the geometry of the catchment area
    catchment_polygon = catchment_area["geometry"][0]
    # Query to retrieve building outlines that intersect with the catchment polygon
    command_text = """
        SELECT *
        FROM unreal_building_outlines AS build
        WHERE ST_Intersects(build.geometry, ST_GeomFromText(:catchment_polygon, 2193));
        """
    buildings_query = text(command_text).bindparams(
        catchment_polygon=str(catchment_polygon)
    )
    # Execute the query and create a GeoDataFrame from the result
    buildings_data = gpd.GeoDataFrame.from_postgis(buildings_query, engine, geom_col="geometry")
    return buildings_data


def assign_house_models_to_buildings(engine: Engine, catchment_area: gpd.GeoDataFrame, no_house_models: int):
    """
    Retrieve building outlines data from the database for the given catchment area,
    then organise and modify it by categorising buildings based on their area,
    randomly assigning house model IDs to medium-sized buildings,
    and generating mesh names for renaming meshes.

    Parameters
    ----------
    engine : Engine
        The engine used to connect to the database.
    catchment_area : gpd.GeoDataFrame
        A GeoDataFrame representing the catchment area.
    no_house_models : int
        The number of house models available for assignment.
        Medium-sized buildings will be randomly assigned a house model ID from this pool.

    Returns
    -------
    gpd.GeoDataFrame
        A GeoDataFrame containing the modified building outlines data with additional columns:
        - 'area': The calculated area of each building.
        - 'floor_size': A categorical classification ('small', 'medium', 'large') based on building area.
        - 'house_id': A randomly assigned house model ID for medium-sized buildings.
        - 'mesh_name': A string used for renaming meshes based on building size and house ID.
    """
    # Retrieve building outlines data from the database for the given catchment area
    buildings_data = get_buildings_from_db(engine, catchment_area)
    # Calculate the area of each building based on its geometry
    buildings_data['area'] = buildings_data['geometry'].area
    # Categorise the buildings based on their area into 'small', 'medium' and 'large'
    buildings_data['floor_size'] = pd.cut(
        buildings_data['area'],
        bins=[0, 60, 300, float('inf')],
        labels=['small', 'medium', 'large']
    )
    buildings_data['floor_size'] = buildings_data['floor_size'].astype('object')
    # Create a list of available house models, numbered from 1 to `no_house_models`
    house_id_list = list(range(1, no_house_models + 1))
    # Assign a random house model ID to medium-sized buildings
    random.seed(10)
    buildings_data['house_id'] = (
        buildings_data['floor_size'].apply(
            lambda x: random.choice(house_id_list) if x == 'medium' else None
        )
    )
    buildings_data['house_id'] = buildings_data['house_id'].astype('Int64')
    # Create a 'mesh_name' for each building to be used for renaming meshes
    buildings_data['mesh_name'] = (
            buildings_data['floor_size'].astype(str) + "_" +
            buildings_data['house_id'].astype(str).replace("<NA>", "nan") + "_"
    )
    # Select the relevant columns
    buildings_data = buildings_data[
        ['building_id', 'suburb_locality', 'town_city', 'territorial_authority', 'area', 'floor_size', 'house_id', 'mesh_name', 'geometry']
    ]
    return buildings_data























