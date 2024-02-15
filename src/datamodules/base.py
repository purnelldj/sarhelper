from typing import Any

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
        self.cfg = cfg

    def read_file(self, file: str) -> Any:
        pass

    def subset(self, prod: Product) -> Product:
        pass

    def plot(self, prod: Product) -> None:
        pass

    def save(self, prod: Product) -> None:
        pass
