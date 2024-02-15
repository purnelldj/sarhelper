import os
from datetime import datetime as dt
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import rioxarray as rx
from omegaconf import DictConfig

from datamodules.base import Datamod, Product
from datamodules.utils import lin_to_db, save_fig


class RCMGeotiffTP(Datamod):
    def __init__(self, cfg: DictConfig) -> None:
        super().__init__(cfg)

    def read_file(self, file: str) -> Any:
        prod = Product()

        # first get metadata
        metastr = os.path.split(file)[1].split("_")
        dtjoined = metastr[5] + metastr[6]
        prod.datetime = dt.strptime(dtjoined, "%Y%m%d%H%M%S")
        prod.sat = metastr[0]
        prod.mode = metastr[4]

        # now get bands
        dir = file + "/"
        sublist = os.listdir(dir)
        sublist = [file for file in sublist if file[-4:] == ".tif"]
        for file in sublist:
            full_file = dir + file
            filemeta = file.split("_")
            bname = filemeta[6]
            # prod.band_names.append(bname)
            rxt = rx.open_rasterio(full_file)
            rxt.values[rxt.values == 0] = np.nan
            rxt = rxt.squeeze(drop=True)
            if bname == "VV" or bname == "VH":
                rxt.values = lin_to_db(rxt.values)
            prod.bands[bname] = rxt
        return prod

    def plot(self, prod: Product) -> None:
        blen = len(prod.bands)
        bname = [bn for bn in prod.bands]
        plt.rcParams.update({"font.family": "Times New Roman", "font.size": 7})
        plt.subplots_adjust(
            left=0.07, bottom=0.07, right=0.93, top=0.93, wspace=0.015, hspace=0.01
        )
        # plt.figure(figsize=(15, 3))
        _, ax = plt.subplots(1, blen, figsize=[14, 3])
        for i in range(blen):
            band = prod.bands[bname[i]]
            tscale = self.cfg.vars[bname[i]].scale
            cbkw = {}
            cbkw["label"] = None
            band.plot.imshow(
                ax=ax[i], vmin=tscale[0], vmax=tscale[1], cmap="pink", cbar_kwargs=cbkw
            )
            ax[i].set_title(bname[i])
        figt = self.outdir + prod.datetime.strftime("%Y%m%d_%H%M%S.png")
        save_fig(figt)
        plt.close()

    def subset(self, data: Any) -> Any:
        """
        Something like this.

        code:
        import rioxarray
        import geopandas

        geodf = geopandas.read_file(...)
        xds = rioxarray.open_rasterio(...)
        clipped = xds.rio.clip(geodf.geometry.values, geodf.crs)
        """
        pass
