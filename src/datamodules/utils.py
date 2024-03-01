import glob
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from pyproj import Transformer
from shapely.geometry import Polygon
from xarray import DataArray


def crs_transform(xr: DataArray, crs_in: str, crs_out: str) -> DataArray:
    # first convert x, y to 2D
    b = xr.values
    xar = xr["x"].values
    yar = xr["y"].values
    attrs = xr.attrs
    x_2d = np.zeros(b.shape)
    y_2d = np.zeros(b.shape)
    for i in range(x_2d.shape[0]):
        x_2d[i, :] = xar
    for j in range(x_2d.shape[1]):
        y_2d[:, j] = yar
    transformer = Transformer.from_crs(crs_in, crs_out)
    lat, lon = transformer.transform(x_2d, y_2d)
    newcoords = {}
    newcoords["y"] = (["x", "y"], lat)
    newcoords["x"] = (["x", "y"], lon)
    xr_new = DataArray(b, dims=["x", "y"], coords=newcoords, attrs=attrs)
    return xr_new


def lin_to_db(pixelData):
    pixelDatadB = 10 * np.log10(np.abs(pixelData))
    return pixelDatadB


def get_filelist(dir: str = None, files: list[str] = None, ext: str = "") -> list[str]:
    if ext is None:
        ext = ""
    if dir is None and files is None:
        raise Exception("need to provide dir or files to return file list")
    if dir is not None and files is not None:
        raise Exception("need to choose between dir or files to return file list")
    if dir is not None:
        return glob.glob(dir + "*" + ext)
    if files is not None:
        return files


def save_fig(figName, **kwargs):
    figOutDir = ""
    if "figOutDir" in kwargs:
        figOutDir = kwargs.get("figOutDir")
    figName = figOutDir + figName
    plt.savefig(figName, format="png", dpi=300, bbox_inches="tight", pad_inches=0.1)
    # plt.savefig(figName, format='png', dpi=300)


def checkdir(dirstr):
    Path(dirstr).mkdir(parents=True, exist_ok=True)


def create_gdf_from_coords(
    coords: list[float],
    crs: str = "EPSG:4326",
    to_shapefile: bool = False,
    fname: str = "polygon.shp",
) -> gpd.GeoDataFrame:
    """Coords should be [[lon, lat], ...]."""
    polygon_geom = Polygon(coords)
    polygon = gpd.GeoDataFrame(index=[0], crs=crs, geometry=[polygon_geom])
    if to_shapefile:
        polygon.to_file(filename=fname, driver="ESRI Shapefile")
    return polygon
