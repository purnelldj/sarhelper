import webbrowser
from pathlib import Path

import ee
import folium
import matplotlib.pyplot as plt
import numpy as np

from datamodules.base import Datamod, Product
from datamodules.gee_utils import (
    add_ee_layer,
    aoi2eegeo,
    auth,
    basemaps,
    dist_coords,
    ee2pydt,
    init,
    stringdt2eedt,
)
from datamodules.utils import save_fig


class GEEProdS1(Product):
    def __init__(self, file: str, **kwargs) -> None:
        super().__init__(**kwargs)
        img = ee.Image(file)
        self.datetime = ee2pydt(img.date())
        self.bands = img.bandNames().getInfo()
        self.metadata = img.getInfo()
        str_meta = Path(file).name.split("_")
        self.sat = str_meta[0]
        self.mode = str_meta[1]
        # just saving single image instead
        self.img = img
        """
        # this is all probably shite
        # now adding longitude and latitude..
        # need to do it separately for each band..
        self.imgs = {}
        for band in self.bands:
            self.imgs[band] = img.select(band)
            self.imgs[band] = self.imgs[band].addBands(ee.Image.pixelLonLat())
            timg = self.imgs[band]
            for band in timg.bandNames().getInfo():
                ttimg = timg.select(band)
                tproj = ttimg.projection().getInfo()
                print(band, tproj)
            exit()
        """

    def get_proj(self, img: ee.Image) -> ee.Image:
        return img.projection()

    def get_bnames(self, img: ee.Image) -> ee.Image:
        return img.bandNames().getInfo()

    def get_band(self, feat: ee.feature.Feature, bname: str) -> np.array:
        return np.array(feat.get(bname).getInfo())

    def get_lonlat(self):
        # use this as guide:
        # "https://gis.stackexchange.com/questions/415505/"" + \
        # "how-to-use-pixellonlat-with-samplerectangle-to-get-a-2-d-array-of-lons-and-l"
        pass


class GEEDMS1(Datamod):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        try:
            init()
        except Exception as e:
            print(e)
            print("trying to authenticate earth engine... \n \n")
            auth()
        self.aoi_ee = aoi2eegeo(self.aoi)
        self.filelist = self.search_s1()

    def search_s1(self):
        # search dates
        sdt_ee = stringdt2eedt(self.sdt)
        edt_ee = stringdt2eedt(self.edt)
        date_filter = ee.Filter.date(sdt_ee, edt_ee)
        # aoi
        aoi_ee = self.aoi_ee
        # search collection
        S1 = ee.ImageCollection("COPERNICUS/S1_GRD")
        col = (
            S1.filter(date_filter)
            .filter(ee.Filter.eq("instrumentMode", "IW"))
            .filterBounds(aoi_ee)
        )
        # now get image names
        tinfo = col.getInfo()["features"]  # just the names hopefully?
        ims = []
        for ind in range(len(tinfo)):
            ims = np.append(ims, tinfo[ind]["id"])
        print(f"found {str(len(ims))} images")
        return ims

    def read_file(self, file: str) -> GEEProdS1:
        return GEEProdS1(file)

    def subset(self, prod: GEEProdS1, do_avg: bool = False, **kwargs) -> GEEProdS1:
        prod.feats = {}
        for bname in prod.bands:
            img = prod.img.select(bname)
            proj = prod.get_proj(img)
            imgll = img.addBands(ee.Image.pixelLonLat())
            if do_avg:
                prod.img = prod.img.reduceRegion(
                    reducer=ee.Reducer.mean(), geometry=self.aoi_ee
                )
            else:
                num_pixels = imgll.reduceRegion(
                    reducer=ee.Reducer.count(), geometry=self.aoi_ee
                ).getInfo()
                print(f"num pixels: {num_pixels}")
                # prod.img = prod.img.clip(self.aoi_ee)
                feat = (
                    imgll.unmask(0)
                    .setDefaultProjection(proj)
                    .sampleRectangle(self.aoi_ee)
                )
                prod.feats[bname] = feat
        return prod

    def plot(
        self,
        prod: GEEProdS1,
        stn_coords: list[float] = [None, None],
        plot_type: str = "plt",
        plot_band: str = "VV",
        **kwargs,
    ) -> None:
        if plot_type == "plt":
            feat = prod.feats[plot_band]
            tband = prod.get_band(feat, plot_band)
            plt.rcParams.update({"font.family": "Times New Roman", "font.size": 7})
            fig, ax = plt.subplots(figsize=[2, 1.5])
            plt.subplots_adjust(
                left=0.07, bottom=0.07, right=0.93, top=0.93, wspace=0.015, hspace=0.01
            )
            im = ax.imshow(tband, vmin=-30, vmax=-5, cmap="pink", origin="upper")
            if stn_coords[0] is not None:
                tlon = prod.get_band(feat, "longitude")
                tlat = prod.get_band(feat, "latitude")
                # now find pixel for station
                tlonfl = tlon.flatten()
                tlatfl = tlat.flatten()
                print("looking for pixel with min distance to stn_coords")
                distfl = [
                    dist_coords([lon, lat], stn_coords)
                    for lon, lat in zip(tlonfl, tlatfl)
                ]
                distfl = np.array(distfl)
                min_dist = np.min(distfl)
                dist = np.reshape(distfl, tlon.shape)
                stnp1, stnp2 = np.where(dist == min_dist)
                ax.plot(stnp2, stnp1, "*", color="blue", markersize=5)
            plt.tick_params(
                left=False,
                right=False,
                labelleft=False,
                labelbottom=False,
                bottom=False,
            )
            cblabel = f"{plot_band} backscatter (dB)"
            plt.colorbar(im, cmap="RdBu", fraction=0.039, pad=0.04, label=cblabel)
            # ax.set_title(band)
            figt = self.outdir + prod.datetime.strftime(prod.sat + "_%Y%m%d_%H%M%S.png")
            save_fig(figt)
            print(f"saved image to: {figt}")
            plt.close()

        if plot_type == "folium":
            folium.Map.add_ee_layer = add_ee_layer

            if stn_coords[0] is None:
                raise Exception("missing stn_coords for plotting")

            # Create a folium map object.
            Map = folium.Map(location=[stn_coords[1], stn_coords[0]], zoom_start=14)

            vis_params = {"min": -30, "max": 0, "palette": ["pink", "white", "green"]}
            # Add a layer control panel to the map.
            bm = basemaps("Google Satellite")
            bm.add_to(Map)
            Map.add_ee_layer(prod.img.select(plot_band), vis_params, "test_image")
            Map.add_child(folium.LayerControl())
            # Display the map.
            Map.save("map.html")
            webbrowser.open("map.html")
