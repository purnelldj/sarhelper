import glob
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def lin_to_db(pixelData):
    pixelDatadB = 10 * np.log10(np.abs(pixelData))
    return pixelDatadB


def get_filelist(dir: str = None, files: list[str] = None, ext: str = "") -> list[str]:
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
