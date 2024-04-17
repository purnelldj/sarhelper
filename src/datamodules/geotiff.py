import os
import pickle
from datetime import datetime as dt

import matplotlib.pyplot as plt
import numpy as np
import rioxarray as rx
from matplotlib.dates import DateFormatter, date2num
from rioxarray.exceptions import NoDataInBounds

from datamodules.base import Datamod, Product
from datamodules.utils import create_gdf_from_coords, lin_to_db, save_fig


class RCMProd(Product):
    def __init__(
        self,
        file: str,
        meta_map: dict = None,
        subdir: str = "",
        conv_to_db: bool = True,
        crs: str = "EPSG:4326",
        bands_use: list[str] = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        if meta_map is None:
            raise Exception("need to provide meta_map")
        # get metadata
        metastr = os.path.split(file)[1].split("_")
        try:
            self.metadict["datetime"] = dt.strptime(
                metastr[meta_map["date"]] + metastr[meta_map["time"]], "%Y%m%d%H%M%S"
            )
            self.metadict["sat"] = metastr[meta_map["sat"]]
            self.metadict["mode"] = metastr[meta_map["mode"]]
        except Exception as e:
            print(e)
            raise Exception("probably need to change indexes to metadata in filename")

        # get bands
        dir = file + "/" + subdir
        sublist = os.listdir(dir)
        sublist = [file for file in sublist if file[-4:] == ".tif"]
        for file in sublist:
            full_file = dir + file
            file = file.split(".")[0]  # remove ext
            filemeta = file.split("_")
            # bname = filemeta[meta_map["band"]]
            bname = ""
            for i in range(meta_map["band"], len(filemeta)):
                if filemeta[i] in ["orf", "cs", "c2d", "fenhlee"]:
                    continue
                if len(bname) > 0:
                    bname += "_"
                bname += filemeta[i]
            if bands_use is not None and bname not in bands_use:
                continue
            rxt = rx.open_rasterio(full_file)
            rxt.values[rxt.values == 0] = np.nan
            rxt = rxt.squeeze(drop=True)

            # convert to db
            if bname in ["HH", "HV", "CH", "CV"] and conv_to_db:
                rxt.values = lin_to_db(rxt.values)
            print(f"min / max / mean for band {bname}:")
            print(
                f"{np.nanmin(rxt.values):.1f}, {np.nanmax(rxt.values):.1f}, {np.nanmean(rxt.values):.1f}"
            )

            # check crs using: rxt.spatial_ref
            rxt = rxt.rio.write_crs(crs)

            self.bands[bname] = rxt

    def get_band(self, bname: str) -> np.array:
        return self.bands[bname]

    def get_lonlat(self):
        pass


class RCMDM(Datamod):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.prod_kwargs = kwargs
        # self.meta_map = meta_map
        # self.subdir = subdir

    def read_file(self, file: str, to_latlon: bool = True) -> RCMProd:
        # return RCMProd(file, self.meta_map, subdir=self.subdir)
        return RCMProd(file, **self.prod_kwargs)

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
            if bname[i] not in self.lims_for_plotting:
                print(f"need to provide plot limits for var: {bname[i]}")
                continue
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
        figt = self.outdir + prod.metadict["datetime"].strftime(
            prod.metadict["sat"] + "_%Y%m%d_%H%M%S.png"
        )
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
        geodf = create_gdf_from_coords(self.aoi, crs=self.aoi_crs)
        blen = len(prod.bands)
        bname = [bn for bn in prod.bands]
        for i in range(blen):
            band = prod.bands[bname[i]]
            try:
                band = band.rio.clip(geodf.geometry.values, geodf.crs)
            except NoDataInBounds:
                print("No data in bounds")
                return None
            prod.bands[bname[i]] = band
        return prod

    def timeseries(
        self, prods: list[Product], avg_values: bool = True, **kwargs
    ) -> None:
        timeseriesdict = {}
        metas = prods[0].metalist
        bands = [band for band in prods[0].bands]
        for meta in metas:
            timeseriesdict[meta] = []
        for band in bands:
            timeseriesdict[band] = []
        for prod in prods:
            for meta in metas:
                timeseriesdict[meta].append(prod.metadict[meta])
            for band in bands:
                bdata = prod.bands[band].values
                if avg_values:
                    bdata = np.nanmedian(bdata)
                timeseriesdict[band].append(bdata)

        dn = date2num(timeseriesdict["datetime"])
        plt.rcParams.update({"font.family": "Times New Roman", "font.size": 7})
        _, ax = plt.subplots(len(bands), 1, figsize=(4, 2.5 * len(bands)))
        plt.subplots_adjust(
            left=0.07, bottom=0.07, right=0.93, top=0.93, wspace=0.01, hspace=0.3
        )
        dformat = DateFormatter("%y-%m-%d")
        for i, band in enumerate(bands):
            ax[i].plot_date(dn, timeseriesdict[band])
            ax[i].set_title(band)
            ax[i].xaxis.set_major_formatter(dformat)
        figt = self.outdir + "timeseries.png"
        save_fig(figt)
        plt.close()
        print(f"saved plot to: {figt} \n \n")

        savepkl = self.outdir + "timeseries.pkl"
        with open(savepkl, "wb") as f:
            pickle.dump(timeseriesdict, f)
        print(f"saved time series data to: {savepkl}")
