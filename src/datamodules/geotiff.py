import os
import pickle
from datetime import datetime as dt
from math import ceil

import matplotlib.pyplot as plt
import numpy as np
import rioxarray as rx
from matplotlib.dates import DateFormatter, date2num
from rioxarray.exceptions import NoDataInBounds

from datamodules.base import Datamod, Product
from datamodules.utils import (
    checkdir,
    create_gdf_from_coords,
    lin_to_db,
    pload,
    psave,
    save_fig,
)


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
        self.file = os.path.basename(file)
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
                if filemeta[i] in [
                    "orf",
                    "cs",
                    "c2d",
                    "fenhlee",
                    "cp2rrrl",
                    "poldiscr",
                    "txC",
                ]:
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
            db_set = [
                "HH",
                "HV",
                "CH",
                "CV",
                "RLd",
                "RRd",
                "mchi_dbl",
                "mchi_surf",
                "mchi_vol",
                "s0",
                "s1",
                "s2",
                "s3",
            ]
            if bname in db_set and conv_to_db:
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
        if file[-4:] != ".pkl":
            return RCMProd(file, **self.prod_kwargs)
        else:
            return pload(file)

    def plot(self, prod: RCMProd, **kwargs) -> None:
        blen = len(prod.bands)
        if "XC" in prod.bands:
            blen -= 1
        bname = [bn for bn in prod.bands]
        plt.rcParams.update({"font.family": "Times New Roman", "font.size": 7})
        cols = 4
        rows = ceil(blen / cols)
        plt.figure(figsize=[cols * 3, rows * 2.3])
        # _, ax = plt.subplots(rows, cols, figsize=[cols * 4.5, rows * 3])
        rowt = 0
        colt = -1
        ax = {}
        for i in range(blen):
            colt += 1
            if colt > cols - 1:
                colt = 0
                rowt += 1
            ax[i] = plt.subplot(rows, cols, i + 1)
            band = prod.bands[bname[i]]
            if bname[i] == "XC":
                continue
            if bname[i] not in self.lims_for_plotting:
                # print(f"need to provide plot limits for var: {bname[i]}")
                # continue
                tscale = [None, None]
            else:
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
            ax[i].set_xlabel(None)
            ax[i].set_ylabel(None)
            ax[i].set_title(bname[i])
        plt.subplots_adjust(
            left=0.07, bottom=0.07, right=0.93, top=0.93, wspace=0.2, hspace=0.25
        )
        figt = self.outdir + prod.metadict["datetime"].strftime(
            prod.metadict["sat"] + "_%Y%m%d_%H%M%S.png"
        )
        save_fig(figt)
        plt.close()
        print(f"saved plot to: {figt} \n \n")

    def subset(self, prod: RCMProd, **kwargs) -> RCMProd:
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

    def save(self, prod: RCMProd, **kwargs) -> None:
        checkdir(self.savedir)
        full_path = self.savedir + prod.file + ".pkl"
        psave(prod, full_path)
        exit()

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
