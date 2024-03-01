import os
from datetime import datetime as dt

import matplotlib.pyplot as plt
import numpy as np
import rioxarray as rx

from datamodules.base import Datamod, Product
from datamodules.utils import create_gdf_from_coords, crs_transform, lin_to_db, save_fig


class RCMProd(Product):
    def __init__(self, file: str, to_latlon: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        # get metadata
        metastr = os.path.split(file)[1].split("_")
        try:
            self.datetime = dt.strptime(metastr[4] + metastr[5], "%Y%m%d%H%M%S")
            self.sat = metastr[0]
            self.mode = metastr[3]
        except Exception as e:
            print(e)
            raise Exception("probably need to change indexes to metadata in filename")

        # get bands
        dir = file + "/"
        sublist = os.listdir(dir)
        sublist = [file for file in sublist if file[-4:] == ".tif"]
        for file in sublist:
            full_file = dir + file
            filemeta = file.split("_")
            bname = filemeta[6]
            rxt = rx.open_rasterio(full_file)
            rxt.values[rxt.values == 0] = np.nan
            rxt = rxt.squeeze(drop=True)

            # convert to db
            rxt.values = lin_to_db(rxt.values)

            # convert to latlon
            if to_latlon:
                rxt = crs_transform(rxt, "EPSG:2960", "EPSG:4326")

            # check crs using: rxt.spatial_ref
            rxt = rxt.rio.write_crs("EPSG:4326")

            self.bands[bname] = rxt

    def get_band(self, bname: str) -> np.array:
        return self.bands[bname]

    def get_lonlat(self):
        pass


class RCMDM(Datamod):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def read_file(self, file: str, to_latlon: bool = True) -> RCMProd:
        return RCMProd(file)

    def plot(self, prod: RCMProd, **kwargs) -> None:
        blen = len(prod.bands)
        bname = [bn for bn in prod.bands]
        plt.rcParams.update({"font.family": "Times New Roman", "font.size": 7})
        plt.subplots_adjust(
            left=0.07, bottom=0.07, right=0.93, top=0.93, wspace=0.015, hspace=0.01
        )
        _, ax = plt.subplots(1, blen, figsize=[blen * 4.5, 3])
        for i in range(blen):
            band = prod.bands[bname[i]]
            tscale = self.lims_for_plotting[bname[i]]
            cbkw = {}
            cbkw["label"] = None
            band.plot.imshow(
                ax=ax[i],
                vmin=tscale[0],
                vmax=tscale[1],
                cmap="pink",
                cbar_kwargs=cbkw,
                origin="upper",
            )
            ax[i].set_title(bname[i])
        figt = self.outdir + prod.datetime.strftime(prod.sat + "_%Y%m%d_%H%M%S.png")
        save_fig(figt)
        plt.close()
        print(f"saved plot to: {figt} \n \n")

    def subset(self, prod: RCMProd, **kwargs) -> RCMProd:
        """
        Something like this.

        code:
        import rioxarray
        import geopandas

        geodf = geopandas.read_file(...)
        xds = rioxarray.open_rasterio(...)
        clipped = xds.rio.clip(geodf.geometry.values, geodf.crs)
        """
        geodf = create_gdf_from_coords(self.aoi, crs="EPSG:4326")
        blen = len(prod.bands)
        bname = [bn for bn in prod.bands]
        for i in range(blen):
            band = prod.bands[bname[i]]
            try:
                band = band.rio.clip(geodf.geometry.values, geodf.crs)
            except Exception as e:
                raise e
            prod.bands[bname[i]] = band
        return prod
