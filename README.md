# Ōtākaro Digital Twin
![image](https://github.com/user-attachments/assets/37863f5e-d50d-4c75-b7a5-49258385e2e3)


## Purpose of the Ōtākaro Digital Twin
"To establish an accessible & innovative platform to collect & communicate knowledge about the Ōtākaro River, serving as a tool to give voice to the Ōtākaro and its importance to the community."

The platform will aim to foster collaboration to support and encourage:
- Holistic decision making & governance, to restore te mauri o te awa,
- Environmental health and resilience outcomes,
- Representation of the mauri of the Ōtākaro and;
- Amplify the significance of the Ōtākaro to the region and people by allowing users to model potential future narratives and tell stories of the Ōtākaro’s past & present.

The Ōtākaro Digital Twin purpose is guided by the Te Mana o te Wai framework and aims to be adaptable to other locations and environments. 

## Background
The Ōtākaro Digital Twin was produced by the Geospatial Research Institute (GRI) and Building Innovation Partnership at University of Canterbury, New Zealand.
It was created for Christchurch City Council, using a fork of [GRI's Spatial Digital Twin](https://github.com/GeospatialResearch/Digital-Twins) backend project.
Code developed specifically for the Ōtākaro Digital Twin resides within the `otakaro/` directory, and is owned by Christchurch City Council.

The Ōtākaro Digitial Twin front-end is based on [Terriajs/TerriaMap](https://github.com/TerriaJS/TerriaMap), via [our fork](https://github.com/GeospatialResearch/TerriaMapOtakaro).

## Basic running instructions
The following list defines the basic steps required to set up and run the digital twin.


### Requirements
* [Docker](https://www.docker.com/)


### Required Credentials:
Create API keys for each of these services. You may need to create an account and log in
* [Stats NZ API Key](https://datafinder.stats.govt.nz/my/api/)
* [LINZ API Key](https://data.linz.govt.nz/my/api/)
* [MFE API Key](https://data.mfe.govt.nz/my/api/)
* [NIWA Application API Key](https://developer.niwa.co.nz/) - Create an app that has the Tide API enabled.
* [Cesium Ion Access Token](https://ion.cesium.com/tokens)


### Starting the Digital Twin application (localhost)
1. Clone this repository to your local machine.

1. Create a file called `api_keys.env`, copy the contents of `api_keys.env.template` and fill in the blank values with API credentials from the above links.
   
1. Create a file called `.env` in the project root, copy the contents of `.env.template` and fill in all blank fields unless a comment says you can leave it blank.
Blank fields to fill in include things like the `POSTGRES_PASSWORD` variable and `CESIUM_ACCESS_TOKEN`. You may configure other variables as needed.

1. From the University of Canterbury network drives, copy `U:/Research/FloodRiskResearch/DigitalTwin/stored_data/roof_surfaces_data` to a new directory `Digital-Twins/roof_surfaces_data`.
   * This is a temporary solution until we have full approval for this dataset. [Issue #283](https://github.com/GeospatialResearch/Digital-Twins/issues/283). If you are an external developer in need of access please contact us.
1. From project root, run the command `docker compose up -d` to run the database, backend web servers, and helper services.
   
1. You may inspect the logs of the backend using `docker compose logs -f backend celery_worker`


## Using the Digital Twin application
1. With the docker compose  application running, the default web address is <http://localhost:3001> to view the web application.
   * Choose data catalogue items with the "Explore map data" button.
   * To perform custom modelling, "Ōtākaro Digital Twin Custom Analysis" has configurable models.
1. The API is available by default on <http://localhost:5000>. Visit <https://geospatialresearch.github.io/Digital-Twins/api> for API documentation.


## Setup for ŌDT project software developers
[Visit our the core digital-twin wiki](https://github.com/GeospatialResearch/Digital-Twins/wiki/) for some instructions on how to set up your development machine to work with on the FReDT project.
