from omegaconf import OmegaConf

from datamodules.utils import checkdir, get_filelist


class Product:
    def __init__(self, **kwargs) -> None:
        self.datetime = None
        self.sat = None
        self.mode = None
        self.bands = {}

    def get_band(self, bname: str):
        """Get band data."""
        pass


class Datamod:
    def __init__(
        self,
        dir: str = None,
        outdir: str = None,
        files: list[str] = None,
        ext: str = "",
        sdt: str = None,
        edt: str = None,
        aoi: str = None,
        lims_for_plotting: dict = None,
        **kwargs,
    ) -> None:
        if dir is not None:
            self.filelist = get_filelist(dir, files, ext)
            print(f"number of files: {len(self.filelist)}")
        self.aoi = OmegaConf.to_container(aoi)
        self.outdir = outdir
        self.lims_for_plotting = lims_for_plotting
        self.sdt = sdt
        self.edt = edt
        checkdir(self.outdir)

    def read_file(self, file: str, **kwargs) -> Product:
        """Read file and return a Product object."""
        pass

    def subset(self, prod: Product, **kwargs) -> Product:
        """Select a subset from an image given some input geometry."""
        pass

    def plot(self, prod: Product, **kwargs) -> None:
        """Plot data."""
        pass

    def save(self, prod: Product, **kwargs) -> None:
        """Save data."""
        pass
