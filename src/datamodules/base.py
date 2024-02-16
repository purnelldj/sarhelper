from omegaconf import DictConfig

from datamodules.utils import checkdir, get_filelist


class Product:
    def __init__(self) -> None:
        Product.datetime = None
        Product.sat = None
        Product.mode = None
        Product.bands = {}


class Datamod:
    def __init__(self, cfg: DictConfig) -> None:
        self.filelist = get_filelist(cfg.dir, cfg.files, cfg.ext)
        print(f"number of files: {len(self.filelist)}")
        self.aoi = cfg.aoi
        self.outdir = cfg.outdir
        checkdir(self.outdir)
        self.lims_for_plotting = cfg.lims_for_plotting
        # self.cfg = cfg

    def read_file(self, file: str) -> Product:
        """Read file and return a Product object."""
        pass

    def subset(self, prod: Product, aoi: str) -> Product:
        """Select a subset from an image given some input geometry."""
        pass

    def plot(self, prod: Product) -> None:
        """Plot data."""
        pass

    def save(self, prod: Product) -> None:
        """Save data."""
        pass
