# -*- coding: utf-8 -*-
"""
Associates roads with buildings for rotation purposes.
"""

from typing import Tuple

import geopandas as gpd
import pandas as pd
from sqlalchemy.engine import Engine
from sqlalchemy.sql import text


def get_addresses_from_db(engine: Engine, catchment_area: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Retrieve addresses data from the database that intersects with the given catchment area.

    Parameters
    ----------
    engine : Engine
        The engine used to connect to the database.
    catchment_area : gpd.GeoDataFrame
        A GeoDataFrame representing the catchment area.

    Returns
    -------
    gpd.GeoDataFrame
        A GeoDataFrame containing addresses data that intersects with the given catchment area.
    """
    # Extract the geometry of the catchment area
    catchment_polygon = catchment_area["geometry"][0]
    # Query to retrieve addresses that intersect with the catchment polygon
    command_text = """
        SELECT *
        FROM unreal_addresses AS add
        WHERE ST_Intersects(add.geometry, ST_GeomFromText(:catchment_polygon, 2193));
        """
    addresses_query = text(command_text).bindparams(
        catchment_polygon=str(catchment_polygon)
    )
    # Execute the query and create a GeoDataFrame from the result
    addresses_data = gpd.GeoDataFrame.from_postgis(addresses_query, engine, geom_col="geometry")
    return addresses_data


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


def get_roads_from_db(engine: Engine, catchment_area: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Retrieve roads data from the database that intersects with the given catchment area.

    Parameters
    ----------
    engine : Engine
        The engine used to connect to the database.
    catchment_area : gpd.GeoDataFrame
        A GeoDataFrame representing the catchment area.

    Returns
    -------
    gpd.GeoDataFrame
        A GeoDataFrame containing roads data that intersects with the given catchment area.
    """
    # Extract the geometry of the catchment area
    catchment_polygon = catchment_area["geometry"][0]
    # Query to retrieve roads that intersect with the catchment polygon
    command_text = """
        SELECT *
        FROM unreal_roads AS road
        WHERE ST_Intersects(road.geometry, ST_GeomFromText(:catchment_polygon, 2193));
        """
    roads_query = text(command_text).bindparams(
        catchment_polygon=str(catchment_polygon)
    )
    # Execute the query and create a GeoDataFrame from the result
    roads_data = gpd.GeoDataFrame.from_postgis(roads_query, engine, geom_col="geometry")
    return roads_data


def match_buildings_with_addresses(
        buildings_data: gpd.GeoDataFrame,
        addresses_data: gpd.GeoDataFrame) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    Spatially joins buildings with address points and separates them into two GeoDataFrames based on
    whether a match was found.

    Parameters:
    ----------
    buildings_data : gpd.GeoDataFrame
        A GeoDataFrame containing building footprints.
    addresses_data : gpd.GeoDataFrame
        A GeoDataFrame containing address points.

    Returns
    -------
    Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]
        A tuple of two GeoDataFrames:
        - The first GeoDataFrame contains buildings with a matching address.
        - The second GeoDataFrame contains buildings without a matching address.
    """
    # Perform spatial join to match buildings with addresses they intersect
    joined = gpd.sjoin(buildings_data, addresses_data, how='left', predicate='intersects')
    # Drop irrelevant columns from join
    joined = joined.drop(columns=['index_right', 'full_address_number'])
    # --- Buildings WITH a matching address ---
    # Keep only rows where address_id is present
    with_address = joined[joined['address_id'].notna()].copy()
    # Drop duplicates: one address per building
    with_address = with_address.drop_duplicates(subset=['building_id', 'full_road_name'], keep='first')
    # Ensure address_id is integer type
    with_address['address_id'] = with_address['address_id'].astype('Int64')
    # --- Buildings WITHOUT a matching address ---
    # Keep only rows where address_id is not present
    without_address = joined[joined['address_id'].isna()].copy()
    # Remove address-specific columns for unmatched rows
    without_address = without_address.drop(columns=['address_id', 'full_road_name'])
    return with_address, without_address


def match_buildings_to_land_parcels(
        buildings_data: gpd.GeoDataFrame,
        land_parcels_data: gpd.GeoDataFrame) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    Matches building footprints to land parcels based on spatial intersection.
    For buildings that intersect multiple land parcels, the land parcel with the largest intersection area is selected.

    Parameters:
    ----------
    buildings_data : gpd.GeoDataFrame
        A GeoDataFrame containing building footprints.
    land_parcels_data : gpd.GeoDataFrame
        A GeoDataFrame containing land parcels.

    Returns
    -------
    Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]
        A tuple of two GeoDataFrames:
        - The first GeoDataFrame contains buildings with a matching land parcel.
        - The second GeoDataFrame contains buildings without a matching land parcel.
    """
    # Perform spatial join to find land parcels intersecting with buildings
    bud_joined = gpd.sjoin(buildings_data, land_parcels_data, how='left', predicate='intersects')
    # Remove the extra index column added by spatial join
    bud_joined = bud_joined.drop(columns=['index_right'])
    # --- Buildings WITH a matching land parcel ---
    # Keep only rows where id is present
    bud_w_land = bud_joined[bud_joined['id'].notna()].copy()
    # Separate buildings with unique land parcel matches (no duplicates on building_id)
    bud_w_land_unique = bud_w_land[~bud_w_land.duplicated('building_id', keep=False)]
    # Merge to get full land parcel geometry
    bud_w_land_unique = bud_w_land_unique.merge(land_parcels_data, on='id', how='left')
    # Handle buildings matched to multiple parcels (duplicates on building_id)
    bud_w_land_dup = bud_w_land[bud_w_land.duplicated('building_id', keep=False)]
    # Merge to get full land parcel geometry
    bud_w_land_dup = bud_w_land_dup.merge(land_parcels_data, on='id', how='left')
    # Calculate the intersection area between each building and land parcel geometry
    bud_w_land_dup['intersection_area'] = bud_w_land_dup.apply(
        lambda row: row['geometry_x'].intersection(row['geometry_y']).area, axis=1)
    # For each building, select the land parcel with the largest intersection area
    idx = bud_w_land_dup.groupby('building_id')['intersection_area'].idxmax()
    bud_w_land_dup = bud_w_land_dup.loc[idx].reset_index(drop=True)
    # Drop the temporary intersection_area column
    bud_w_land_dup = bud_w_land_dup.drop(columns=['intersection_area'])
    # Combine unique and resolved duplicate matches into one GeoDataFrame
    bud_w_land = pd.concat([bud_w_land_unique, bud_w_land_dup])
    # Clean up geometry column names and set GeoDataFrame geometry
    bud_w_land = bud_w_land.drop(columns=['geometry_x']).rename(columns={'geometry_y': 'geometry'})
    bud_w_land = gpd.GeoDataFrame(bud_w_land, geometry='geometry')
    # --- Buildings WITHOUT a matching land parcel ---
    bud_wo_land = bud_joined[bud_joined['id'].isna()].copy()
    bud_wo_land = bud_wo_land.drop(columns=['id'])
    return bud_w_land, bud_wo_land


def match_land_parcels_to_addresses(
        land_parcels_data: gpd.GeoDataFrame,
        addresses_data: gpd.GeoDataFrame) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    Matches land parcels to address points based on spatial intersection.
    For each land parcel, if multiple addresses intersect it, the one with the highest address_id is selected.

    Parameters:
    ----------
    land_parcels_data : gpd.GeoDataFrame
        A GeoDataFrame containing land parcels.
    addresses_data : gpd.GeoDataFrame
        A GeoDataFrame containing address points.

    Returns
    -------
    Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]
        A tuple of two GeoDataFrames:
        - The first GeoDataFrame contains land parcels with a matching address.
        - The second GeoDataFrame contains land parcels without a matching address.
    """
    # Perform a spatial join to find which addresses intersect with each land parcel
    matched = gpd.sjoin(land_parcels_data, addresses_data, how='left', predicate='intersects')
    # Drop columns that are not needed for further processing
    matched = matched.drop(columns=['index_right', 'full_address_number'])
    # Sort to prefer higher address_id when choosing one match per land parcel
    matched = matched.sort_values(['building_id', 'address_id'], ascending=[True, False])
    # Remove duplicate building_ids, keeping the first (highest address_id)
    deduped = matched.drop_duplicates(subset='building_id', keep='first').reset_index(drop=True)
    # Convert address_id to integer type for consistency
    deduped['address_id'] = deduped['address_id'].astype('Int64')
    # Split the result into matched and unmatched based on address_id presence
    lp_w_address = deduped[deduped['address_id'].notna()].copy()
    lp_wo_address = deduped[deduped['address_id'].isna()].copy()
    # Remove address-specific columns for unmatched rows
    lp_wo_address = lp_wo_address.drop(columns=['address_id', 'full_road_name'])
    return lp_w_address, lp_wo_address


def find_buildings_nearest_addresses(
        buildings_data: gpd.GeoDataFrame,
        addresses_data: gpd.GeoDataFrame,
        distance: int = 30) -> gpd.GeoDataFrame:
    """
    Find the nearest address point for each building within a specified maximum distance (default is 30).

    Parameters:
    ----------
    buildings_data : gpd.GeoDataFrame
        A GeoDataFrame containing building footprints.
    addresses_data : gpd.GeoDataFrame
        A GeoDataFrame containing address points.
    distance : int = 30
        The maximum search distance to find a nearby address. Default is 20.

    Returns
    -------
    gpd.GeoDataFrame
        A GeoDataFrame of buildings with the nearest address.
    """
    # Perform nearest spatial join to find the closest address within the specified distance
    nearest = gpd.sjoin_nearest(
        buildings_data,
        addresses_data,
        how="left",
        max_distance=distance,
        distance_col="distances")
    # Remove any columns that are completely empty
    nearest = nearest.dropna(axis=1, how='all')
    # Drop unnecessary columns from the join result
    nearest = nearest.drop(columns=['index_right', 'full_address_number', 'distances'])
    # Convert address_id to integer type for consistency
    nearest['address_id'] = nearest['address_id'].astype('Int64')
    return nearest


def get_address_for_buildings(
        engine: Engine,
        catchment_area: gpd.GeoDataFrame,
        buildings_data: gpd.GeoDataFrame,
        distance: int = 30) -> gpd.GeoDataFrame:
    """
    Assign addresses to buildings by spatially matching building footprints with address points and land parcels.
    Medium-sized buildings undergo comprehensive address matching and assignment,
    while non-medium buildings are retained without assigned addresses.

    Parameters
    ----------
    engine : Engine
        The engine used to connect to the database.
    catchment_area : gpd.GeoDataFrame
        A GeoDataFrame representing the catchment area.
    buildings_data : gpd.GeoDataFrame
        A GeoDataFrame containing building footprints.
    distance : int = 30
        The maximum search distance to find a nearby address. Default is 20.

    Returns
    -------
    gpd.GeoDataFrame
        A GeoDataFrame of all buildings where medium-sized buildings have matched addresses and
        non-medium sized buildings remain without addresses.
    """
    # Separate buildings into non-medium (small or large) and medium floor sizes
    non_medium_buildings = buildings_data[buildings_data['floor_size'] != 'medium']
    # Medium-sized buildings will be processed further for rotation and address matching
    medium_buildings = buildings_data[buildings_data['floor_size'] == 'medium']
    # Retrieve address points from the database that intersect with the given catchment area
    full_addresses = get_addresses_from_db(engine, catchment_area)
    full_addresses = full_addresses[['address_id', 'full_address_number', 'full_road_name', 'geometry']]
    # Match medium-sized buildings with address points; split into matched and unmatched
    bud_w_address, bud_wo_address = match_buildings_with_addresses(medium_buildings, full_addresses)
    # Retrieve land parcel geometries that intersect with the catchment area
    land_parcels = get_land_parcels_from_db(engine, catchment_area)  # 221
    land_parcels = land_parcels[['id', 'geometry']]
    # Match buildings without addresses to land parcels; split into matched and unmatched
    bud_w_land, bud_wo_land = match_buildings_to_land_parcels(bud_wo_address, land_parcels)
    # Match land parcels that were matched to buildings with available address points
    lp_w_address, lp_wo_address = match_land_parcels_to_addresses(bud_w_land, full_addresses)
    # For land parcels that still don’t have an address, restore the building geometry
    cleaned_lp_wo_address = (
        lp_wo_address
        .drop(columns=['id', 'geometry'])
        .merge(medium_buildings[['building_id', 'geometry']], on='building_id', how='left')
    )
    # Combine unmatched buildings from land parcel matching with those unmatched after land-to-address matching
    without_address = pd.concat([bud_wo_land, cleaned_lp_wo_address])
    without_address = gpd.GeoDataFrame(without_address, geometry='geometry')
    # Attempt to assign nearest addresses to remaining unmatched buildings within distance threshold
    nearest_address = find_buildings_nearest_addresses(without_address, full_addresses, distance=distance)
    # For land parcels with matched addresses, restore original building geometries
    cleaned_lp_w_address = (
        lp_w_address
        .drop(columns=['id', 'geometry'])
        .merge(medium_buildings[['building_id', 'geometry']], on='building_id', how='left')
    )
    # Combine all medium-sized buildings that have matched addresses from different matching steps
    med_buildings_w_addresses = pd.concat(
        [bud_w_address, cleaned_lp_w_address, nearest_address],
        ignore_index=True
    )
    # Add back non-medium buildings (small or large floor size) which were excluded from matching
    all_buildings_w_addresses = pd.concat(
        [med_buildings_w_addresses, non_medium_buildings],
        ignore_index=True
    )
    # Standardize road names by converting to lowercase and trimming whitespace
    all_buildings_w_addresses['full_road_name'] = all_buildings_w_addresses['full_road_name'].str.lower().str.strip()
    # Convert to a GeoDataFrame and set the active geometry column
    all_buildings_w_addresses = gpd.GeoDataFrame(all_buildings_w_addresses, geometry='geometry')
    # Return the complete set of buildings with assigned addresses
    return all_buildings_w_addresses


def get_roads_for_buildings(
        engine: Engine,
        catchment_area: gpd.GeoDataFrame,
        buildings_data: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Assign roads to buildings.

    Parameters
    ----------
    engine : Engine
        The engine used to connect to the database.
    catchment_area : gpd.GeoDataFrame
        A GeoDataFrame representing the catchment area.
    buildings_data : gpd.GeoDataFrame
        A GeoDataFrame containing building footprints.

    Returns
    -------
    gpd.GeoDataFrame
        A GeoDataFrame of all buildings where medium-sized buildings have matched roads and
        non-medium sized buildings remain without roads.
    """
    # Assign addresses to buildings by spatially matching building footprints with address points and land parcels
    buildings_w_addresses = get_address_for_buildings(engine, catchment_area, buildings_data)
    # Expand the catchment area to include nearby roads just outside the original boundary
    catchment_area['geometry'] = catchment_area['geometry'].buffer(100, join_style="mitre")
    # Retrieve roads data from the database that intersects with the given catchment area
    roads_data = get_roads_from_db(engine, catchment_area)
    roads_data = roads_data[['full_road_name', 'geometry']]
    # Standardize road names by converting to lowercase and trimming whitespace
    roads_data['full_road_name'] = roads_data['full_road_name'].str.lower().str.strip()
    # Merge to get full road geometry
    buildings_w_roads = buildings_w_addresses.merge(roads_data, on='full_road_name', how='left')
    # Clean up geometry column names and set GeoDataFrame geometry (placeholder for now)
    buildings_w_roads = (
        buildings_w_roads
        .drop(columns=['geometry_x', 'address_id'])
        .rename(columns={'geometry_y': 'geometry'})
    )
    buildings_w_roads = gpd.GeoDataFrame(buildings_w_roads, geometry='geometry')
    return buildings_w_roads
