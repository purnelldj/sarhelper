import datetime

import ee
import folium
from geopy.distance import distance


def dist_coords(ll1: list[float], ll2: list[float]) -> float:
    """Input [lon, lat] for each ll."""
    d = distance((ll1[1], ll1[0]), (ll2[1], ll2[0])).m
    return d


def basemaps(mapName):
    """Add custom base maps to folium."""
    basemaps = {
        "Google Maps": folium.TileLayer(
            tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
            attr="Google",
            name="Google Maps",
            overlay=True,
            control=True,
        ),
        "Google Satellite": folium.TileLayer(
            tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
            attr="Google",
            name="Google Satellite",
            overlay=True,
            control=True,
        ),
        "Google Terrain": folium.TileLayer(
            tiles="https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}",
            attr="Google",
            name="Google Terrain",
            overlay=True,
            control=True,
        ),
        "Google Satellite Hybrid": folium.TileLayer(
            tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
            attr="Google",
            name="Google Satellite",
            overlay=True,
            control=True,
        ),
        "Esri Satellite": folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri",
            name="Esri Satellite",
            overlay=True,
            control=True,
        ),
    }
    if mapName in basemaps:
        basemap = basemaps[mapName]
    else:
        print("choose one of these maps as str input")
        print(basemaps.keys())
        basemap = None
    return basemap


def add_ee_layer(self, ee_image_object, vis_params, name):
    """Define a method for displaying Earth Engine image tiles to folium map."""
    map_id_dict = ee.Image(ee_image_object).getMapId(vis_params)
    folium.raster_layers.TileLayer(
        tiles=map_id_dict["tile_fetcher"].url_format,
        attr='Map Data &copy; <a href="https://earthengine.google.com/">Google Earth Engine</a>',
        name=name,
        overlay=True,
        control=True,
    ).add_to(self)
    return


def auth():
    # need to do this once when you set up venv
    ee.Authenticate()


def init():
    ee.Initialize()


def stringdt2eedt(dt: str):
    """Date in format yyy-mm-dd to earth engine date."""
    return ee.Date(dt)


def aoi2eegeo(aoi: list[float], geotype: str = "Polygon", proj: str = None):
    if geotype == "Polygon":
        return ee.Geometry.Polygon(aoi, proj=proj)
    elif geotype == "Point":
        return ee.Geometry.Point(aoi, proj=proj)


def ee2pydt(eedt):
    pydt = datetime.datetime.utcfromtimestamp(eedt.getInfo()["value"] / 1000.0)
    return pydt


def py2eedt(pydt):
    eedt = ee.Date(pydt)
    return eedt


def eetask(
    image,
    geometry,
    description="mock_export",
    folder="gdrive_folder",
    fileNamePrefix="mock_export",
    scale=1000,
    crs="EPSG:4326",
):
    task = ee.batch.Export.image.toDrive(
        image=image,
        region=geometry,
        description=description,
        folder=folder,
        fileNamePrefix=fileNamePrefix,
        scale=scale,
        crs=crs,
    )
    task.start()
    task.status()
    print("repeat command task.status() if necessary")
    return


if __name__ == "__main__":
    auth()
